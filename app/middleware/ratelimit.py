from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.limiter import limiter


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        current = getattr(request.state, "view_rate_limit", None)
        if current is not None:
            rate_limit_item, keys = current
            reset_in, remaining = limiter.limiter.get_window_stats(
                rate_limit_item, *keys
            )
            response.headers["X-RateLimit-Limit"] = str(rate_limit_item.amount)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_in + 1)
        return response
