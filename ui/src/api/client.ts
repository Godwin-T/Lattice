const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type ApiError = {
  message: string;
  status: number;
};

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!res.ok) {
    const text = await res.text();
    throw {
      message: text || res.statusText,
      status: res.status
    } as ApiError;
  }

  if (res.status === 204) {
    return {} as T;
  }
  return (await res.json()) as T;
}
