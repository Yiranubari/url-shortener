from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.url import ShortenRequest, ShortenResponse
from app.services.url_service import URLService

router = APIRouter()


def get_url_service(db: Session = Depends(get_db)) -> URLService:
    return URLService(db)


@router.post("/shorten", response_model=ShortenResponse)
@limiter.limit("20/minute")
def shorten_url(
    request: Request,
    body: ShortenRequest,
    svc: URLService = Depends(get_url_service),
):
    url = svc.create_short_url(str(body.url))
    short_url = f"{settings.base_url.rstrip('/')}/{url.short_code}"
    return ShortenResponse(
        short_url=short_url,
        long_url=url.long_url,
        short_code=url.short_code,
    )


@router.get("/{short_code}")
@limiter.limit("100/minute")
def redirect_url(
    request: Request,
    short_code: str,
    svc: URLService = Depends(get_url_service),
):
    url = svc.get_url_by_short_code(short_code)
    return RedirectResponse(
        url=url.long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )

