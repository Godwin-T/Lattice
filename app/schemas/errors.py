from typing import Any, Optional
from fastapi.responses import JSONResponse


class OpenAIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_type: str = "invalid_request_error",
        code: Optional[str] = None,
        param: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.code = code
        self.param = param


def openai_error_response(error: OpenAIError) -> JSONResponse:
    payload: dict[str, Any] = {
        "error": {
            "message": error.message,
            "type": error.error_type,
            "param": error.param,
            "code": error.code,
        }
    }
    return JSONResponse(status_code=error.status_code, content=payload)
