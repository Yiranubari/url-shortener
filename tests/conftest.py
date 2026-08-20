import os

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://url_shortener:url_shortener@localhost:5433/url_shortener_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.core.limiter import limiter  # noqa: E402
from app.main import app  # noqa: E402


def _ensure_test_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    conn = psycopg2.connect(
        database="postgres",
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (url.database,)
        )
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{url.database}"')
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    _ensure_test_database()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_state():
    limiter.reset()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM urls"))
    yield


@pytest.fixture()
def client():
    return TestClient(app)
