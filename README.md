# URL Shortener API

A URL shortener built with FastAPI and PostgreSQL. Two endpoints: create a short link and follow it to the original URL.

## Features

- Shorten any valid URL to a 7-character base62 code.
- Redirect via HTTP 307, preserving the original HTTP method.
- Deduplication: submitting the same URL twice returns the same short code.
- URL normalization: URLs that differ only in case, trailing slash, default port, or fragment hash are treated as duplicates and share one short code.
- Rate limiting: 20 requests per minute on POST /shorten, 100 per minute on GET /{short_code}. Limits are per IP address using fixed-window in-memory storage.
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset) on every rate-limited route.
- Request logging via loguru (method, path, status, duration).
- Custom exception hierarchy keeps the service layer decoupled from HTTP. Status codes are mapped centrally in the app factory.
- Alembic migrations for schema management.
- Unit and integration tests with pytest.

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0 (ORM with mapped_column)
- PostgreSQL 16 (via docker-compose)
- Alembic for database migrations
- Pydantic v2 with HttpUrl validation
- Slowapi for rate limiting
- Loguru for logging
- Pytest with httpx TestClient for testing

## Project Structure

```
.
├── alembic/                  # Database migrations
│   ├── versions/
│   │   ├── 4482ed111fc6_create_urls_table.py
│   │   ├── 8e8b477dccba_add_unique_index_on_long_url.py
│   │   └── 06a52584c319_add_normalized_url_column_for_dedupe.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app, exception handlers, middleware
│   ├── core/
│   │   ├── config.py         # Settings via pydantic-settings
│   │   ├── database.py       # Engine, SessionLocal, get_db
│   │   ├── limiter.py        # Slowapi Limiter singleton
│   │   └── shortcode.py      # Random base62 short code generator
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── url.py            # URLShortenerError, ShortURLNotFoundError, ShortCodeAllocationError
│   ├── middleware/
│   │   ├── logging.py        # RequestLoggingMiddleware
│   │   └── ratelimit.py      # RateLimitHeaderMiddleware
│   ├── models/
│   │   └── url.py            # SQLAlchemy URL model
│   ├── routers/
│   │   └── url.py            # POST /shorten, GET /{short_code}
│   ├── schemas/
│   │   └── url.py            # ShortenRequest, ShortenResponse
│   └── services/
│       └── url_service.py    # URLService: normalize, create, lookup
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test DB setup, client fixture, rate limiter reset
│   ├── test_shortcode.py     # Shortcode generator unit tests
│   ├── test_url.py           # API integration tests
│   └── test_url_service.py   # Service unit tests
├── docker-compose.yml        # PostgreSQL 16 container
├── .env                      # Environment variables
├── .env.example              # Template for .env
├── requirements.txt
├── instruct.txt              # Original assignment brief
└── README.md
```

## How to Run

### Prerequisites

- Docker and Docker Compose
- Python 3.10 or later
- pip (or any Python package manager)

### Setup

1. Clone the repository and enter the directory.

2. Install Python dependencies.

   ```
   pip install -r requirements.txt
   ```

3. Start PostgreSQL.

   ```
   docker compose up -d
   ```

   This starts a PostgreSQL 16 container on port 5433 with user `url_shortener`, password `url_shortener`, and database `url_shortener`.

4. Copy the environment file if needed.

   ```
   cp .env.example .env
   ```

   The defaults in .env work with the docker-compose setup. The two variables are:
   - DATABASE_URL: SQLAlchemy connection string for PostgreSQL.
   - BASE_URL: The base URL used when constructing the short link in the response.

5. Run database migrations.

   ```
   alembic upgrade head
   ```

   This creates the `urls` table with the `short_code`, `long_url`, `normalized_url`, and `created_at` columns.

6. Start the server.

   ```
   uvicorn app.main:app --reload
   ```

   The API is available at http://localhost:8000.

### Verify the API is running

```
curl http://localhost:8000/
```

Response:

```json
{ "message": "URL Shortener API" }
```

## API Reference

### POST /shorten

Create a short URL.

**Request body**

```json
{
  "url": "https://example.com/very/long/path/that/needs/shortening"
}
```

- `url` must be a valid absolute URL (validated by Pydantic's HttpUrl).
- Maximum length of the URL string is 2048 characters.

**Rate limit**: 20 requests per minute per IP address.

**Response 200**

```json
{
  "short_url": "http://localhost:8000/aB3xYzQ",
  "long_url": "https://example.com/very/long/path/that/needs/shortening",
  "short_code": "aB3xYzQ"
}
```

- `short_url` is the full shortened URL combining BASE_URL and the short code.
- `long_url` is the original URL exactly as submitted.
- `short_code` is the 7-character base62 code.

**Response 422** (validation error)

```json
{
  "detail": [
    {
      "type": "url_parsing",
      "loc": ["body", "url"],
      "msg": "Input should be a valid URL",
      "input": "not-a-url"
    }
  ]
}
```

Returned when the URL is not a valid absolute URL or exceeds 2048 characters.

**Response 429** (rate limit exceeded)

```json
{
  "detail": "Rate limit exceeded: 20 per 1 minute"
}
```

### GET /{short_code}

Follow a short URL to its original destination.

**Path parameter**

- `short_code`: the 7-character alphanumeric code returned by POST /shorten.

**Rate limit**: 100 requests per minute per IP address.

**Response 307**

Redirects to the original URL. The HTTP method is preserved (the browser stays on GET or POST).

**Response 404**

```json
{
  "detail": "Short URL not found"
}
```

Returned when the short code does not exist in the database.

**Response 429**

```json
{
  "detail": "Rate limit exceeded: 100 per 1 minute"
}
```

### GET /

Health check.

**Response 200**

```json
{
  "message": "URL Shortener API"
}
```

## Rate Limiting

Rate limiting is implemented with slowapi using in-memory storage. Limits are per IP address and use a fixed-window strategy.

| Route             | Limit          |
| ----------------- | -------------- |
| POST /shorten     | 20 per minute  |
| GET /{short_code} | 100 per minute |

When a request is within the limit, the response includes these headers:

- X-RateLimit-Limit: the maximum number of requests allowed per window.
- X-RateLimit-Remaining: how many requests are left in the current window.
- X-RateLimit-Reset: the number of seconds until the window resets.

When the limit is exceeded, the API returns HTTP 429 with a JSON body describing the limit.

The in-memory storage is per-process and resets on server restart. For production with multiple workers, swap the storage backend to Redis.

## Request Logging

Every request is logged by RequestLoggingMiddleware using loguru. The log format is:

```
{method} {path} {status} {duration:.2f}s
```

Example:

```
GET /shorten 200 0.04s
```

Logs are written to stderr by default.

## Design Decisions

### Normalized URL deduplication

The `long_url` column stores the URL exactly as submitted by the user. A separate `normalized_url` column holds a normalized version used for deduplication lookups. Normalization applies these transformations:

- Lowercase the hostname.
- Remove the default port for the scheme (80 for HTTP, 443 for HTTPS).
- Remove the trailing slash from the path.
- Remove the fragment (the part after #).
- Preserve the query string, custom ports, and userinfo.

This means `https://Example.com/Path/`, `https://example.com/Path`, and `https://example.com:443/Path#section` all resolve to the same normalized URL `https://example.com/Path` and share one short code.

The `normalized_url` column has a unique index. The `short_code` column also has a unique index. The `long_url` column has no uniqueness constraint; the deduplication logic in the service layer prevents duplicate rows.

### Exception handling

Custom exceptions (ShortURLNotFoundError, ShortCodeAllocationError) are raised in the service layer. The app factory in main.py registers exception handlers that map these to HTTP status codes (404 and 500 respectively). This keeps the service layer free of HTTP imports and makes it reusable in non-HTTP contexts.

### HTTP 307 vs 301

The redirect endpoint returns HTTP 307 (Temporary Redirect) instead of 301 (Moved Permanently) or 302 (Found). HTTP 307 guarantees that the browser or client preserves the original HTTP method (POST, PUT, etc.) when following the redirect. This is the safest choice for a general-purpose URL shortener.

### Rate limit headers

Slowapi adds rate limit enforcement but does not attach rate limit headers to the response by default. A custom `RateLimitHeaderMiddleware` reads `request.state.view_rate_limit` (set by slowapi's middleware) and computes the current window stats from the limiter's storage. This is why the middleware runs after slowapi's middleware in the middleware chain.

### Base62 short code generation

Short codes are 7 characters drawn from the full alphanumeric set (a-z, A-Z, 0-9) using the `secrets` module. This gives 62^7 possible values (approximately 3.5 trillion), making collisions extremely unlikely. If a collision does occur (the code already exists in the database), the service retries up to 5 times before raising ShortCodeAllocationError. The retry logic also handles the race condition where another process inserts the same normalized URL between the lookup and the insert.

### Database indexes

- `short_code`: unique index, used for the redirect lookup.
- `normalized_url`: unique index, used for the deduplication lookup.
- `id`: primary key.

The unique index on `long_url` was added in the second migration and dropped in the third, because deduplication is now based on `normalized_url`, not `long_url`.

## Running Tests

Tests use a dedicated PostgreSQL database named `url_shortener_test`. The conftest.py creates it automatically if it does not exist, then builds the schema from the SQLAlchemy models (not from migrations). Each test function runs in a fresh database state: the `urls` table is truncated and the rate limiter is reset before every test.

To run the full test suite:

```
pytest
```

To run with verbose output:

```
pytest -v
```

The test suite covers:

- Shortcode generator (length, alphabet, uniqueness).
- URL normalization (8 parametrized cases covering case, trailing slash, default port, custom port, fragment, query, userinfo, IPv6).
- URL creation, deduplication, and collision exhaustion at the service layer.
- API endpoints: health check, shorten, deduplication, normalized variant deduplication, invalid URL rejection, oversized URL rejection, redirect, 404 for missing code, rate limit headers, and 429 enforcement for both routes.

## Configuration

All configuration is in the .env file. The Settings class in app/core/config.py reads from .env using pydantic-settings.

| Variable     | Default               | Description                                         |
| ------------ | --------------------- | --------------------------------------------------- |
| DATABASE_URL | (required)            | PostgreSQL connection string.                       |
| BASE_URL     | http://localhost:8000 | Base URL used to construct the short link response. |

Example .env file:

```
DATABASE_URL=postgresql+psycopg2://url_shortener:url_shortener@localhost:5433/url_shortener
BASE_URL=http://localhost:8000
```

For tests, the DATABASE_URL is overridden by the TEST_DATABASE_URL environment variable. If not set, it defaults to the same host and port with database `url_shortener_test`.
