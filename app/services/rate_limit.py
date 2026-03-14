from __future__ import annotations

import time
from typing import Tuple

import redis.asyncio as redis


RATE_LIMIT_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local data = redis.call('HMGET', key, 'tokens', 'last')
local tokens = tonumber(data[1])
local last = tonumber(data[2])

if tokens == nil then
  tokens = capacity
  last = now
end

local delta = math.max(0, now - last)
local refill = (delta / 1000.0) * refill_rate
local new_tokens = math.min(capacity, tokens + refill)

if new_tokens < 1 then
  redis.call('HMSET', key, 'tokens', new_tokens, 'last', last)
  redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
  return {0, new_tokens}
end

new_tokens = new_tokens - 1
redis.call('HMSET', key, 'tokens', new_tokens, 'last', now)
redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
return {1, new_tokens}
"""


class RateLimiter:
    def __init__(self, client: redis.Redis, capacity_per_minute: int) -> None:
        self.client = client
        self.capacity = capacity_per_minute
        self.refill_rate = capacity_per_minute / 60.0
        self._script = self.client.register_script(RATE_LIMIT_LUA)

    async def allow(self, key: str) -> Tuple[bool, float]:
        now_ms = int(time.time() * 1000)
        allowed, remaining = await self._script(keys=[key], args=[self.capacity, self.refill_rate, now_ms])
        return bool(allowed), float(remaining)
