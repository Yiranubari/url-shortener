from unittest.mock import patch

import pytest

from app.core.database import SessionLocal
from app.exceptions import ShortCodeAllocationError, ShortURLNotFoundError
from app.models.url import URL
from app.services.url_service import URLService


@pytest.fixture()
def svc():
    db = SessionLocal()
    yield URLService(db)
    db.close()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://EXAMPLE.com/Path/", "https://example.com/Path"),
        ("https://example.com:443/Path/", "https://example.com/Path"),
        ("http://example.com:80/x/", "http://example.com/x"),
        ("https://example.com:8443/Path", "https://example.com:8443/Path"),
        ("https://example.com/path#frag", "https://example.com/path"),
        ("https://example.com/path?q=1#frag", "https://example.com/path?q=1"),
        ("https://user:pass@EXAMPLE.com:8443/x/", "https://user:pass@example.com:8443/x"),
        ("https://[::1]:8443/x", "https://[::1]:8443/x"),
    ],
)
def test_normalize_url(raw, expected):
    assert URLService.normalize_url(raw) == expected


def test_create_short_url_stores_original_and_normalized(svc):
    url = svc.create_short_url("https://EXAMPLE.com/Path/")
    assert url.long_url == "https://EXAMPLE.com/Path/"
    assert url.normalized_url == "https://example.com/Path"


def test_create_short_url_deduplicates(svc):
    first = svc.create_short_url("https://example.com/path")
    second = svc.create_short_url("https://example.com/path")
    assert first.id == second.id
    assert svc.db.query(URL).count() == 1


def test_create_short_url_exhausts_collisions(svc):
    url = svc.create_short_url("https://example.com/first")
    with patch(
        "app.services.url_service.generate_short_code",
        return_value=url.short_code,
    ):
        with pytest.raises(ShortCodeAllocationError):
            svc.create_short_url("https://example.com/second")


def test_get_url_by_short_code_returns_row(svc):
    url = svc.create_short_url("https://example.com/path")
    found = svc.get_url_by_short_code(url.short_code)
    assert found.id == url.id


def test_get_url_by_short_code_raises_when_missing(svc):
    with pytest.raises(ShortURLNotFoundError):
        svc.get_url_by_short_code("missing")
