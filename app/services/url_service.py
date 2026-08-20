from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.shortcode import generate_short_code
from app.models.url import URL


class URLService:
    MAX_ATTEMPTS = 5

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def normalize_url(raw: str) -> str:
        """Lowercases host, strips trailing slash and fragment."""
        parts = urlsplit(raw)
        hostname = parts.hostname or ""
        netloc = f"[{hostname}]" if ":" in hostname else hostname
        if parts.username is not None:
            userinfo = parts.username
            if parts.password is not None:
                userinfo += ":" + parts.password
            netloc = userinfo + "@" + netloc
        if parts.port is not None:
            netloc += ":" + str(parts.port)
        path = parts.path.rstrip("/")
        return urlunsplit((parts.scheme, netloc, path, parts.query, ""))

    def _find_by_long_url(self, long_url: str) -> URL | None:
        return self.db.query(URL).filter(URL.long_url == long_url).first()

    def create_short_url(self, raw_url: str) -> URL:
        """Returns the existing row or creates a new short URL."""
        long_url = self.normalize_url(raw_url)
        existing = self._find_by_long_url(long_url)
        if existing:
            return existing
        for _ in range(self.MAX_ATTEMPTS):
            short_code = generate_short_code()
            url = URL(short_code=short_code, long_url=long_url)
            self.db.add(url)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                existing = self._find_by_long_url(long_url)
                if existing:
                    return existing
                continue
            self.db.refresh(url)
            return url
        raise RuntimeError("could not allocate a unique short code")

    def get_url_by_short_code(self, short_code: str) -> URL | None:
        """Looks up a URL row by short code."""
        return self.db.query(URL).filter(URL.short_code == short_code).first()


