from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter
from app.exceptions import ShortCodeAllocationError, ShortURLNotFoundError
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.ratelimit import RateLimitHeaderMiddleware
from app.routers.url import router

app = FastAPI(title="URL Shortener")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitHeaderMiddleware)

app.include_router(router)


@app.exception_handler(ShortURLNotFoundError)
async def short_url_not_found_handler(
    request: Request, exc: ShortURLNotFoundError
):
    return JSONResponse(
        status_code=404, content={"detail": "Short URL not found"}
    )


@app.exception_handler(ShortCodeAllocationError)
async def short_code_allocation_handler(
    request: Request, exc: ShortCodeAllocationError
):
    return JSONResponse(
        status_code=500, content={"detail": "Failed to allocate a unique short code"}
    )


@app.get("/")
def root():
    return {"message": "URL Shortener API"}

