import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            "{method} {path} {status} {duration:.2f}s",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=duration,
        )
        return response
