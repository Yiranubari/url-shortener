#!/usr/bin/env bash
#
# Property-based API testing with Schemathesis.
#
# Starts the API on a throwaway port against the test database with rate
# limiting disabled, runs `st run` against the live OpenAPI schema, then
# tears the server down.
#
# Usage:
#   scripts/schemathesis.sh            # full run (defaults from schemathesis.toml)
#   scripts/schemathesis.sh --checks status_code_conformance --generation-max-examples 20
#
# Env overrides:
#   SCHEMATHESIS_PORT  port to bind (default 8011)
#   SCHEMATHESIS_HOST  host to bind (default 127.0.0.1)
#   TEST_DATABASE_URL  database used by the run (defaults to url_shortener_test)

set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${SCHEMATHESIS_PORT:-8011}"
HOST="${SCHEMATHESIS_HOST:-127.0.0.1}"
BASE_URL="http://${HOST}:${PORT}"
DATABASE_URL="${TEST_DATABASE_URL:-postgresql+psycopg2://url_shortener:url_shortener@localhost:5433/url_shortener_test}"

export DATABASE_URL
export RATE_LIMIT_ENABLED=false
export BASE_URL

# Ensure the test database schema exists (matches the Alembic-applied schema).
python3 -c "
from app.core.database import Base, engine
import app.models.url
Base.metadata.create_all(engine)
"

# Start the API server on a throwaway port.
uvicorn app.main:app --host "$HOST" --port "$PORT" > /tmp/schemathesis_server.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

# Wait until the OpenAPI schema is served.
for _ in $(seq 1 30); do
    if curl -sf "$BASE_URL/openapi.json" > /dev/null 2>&1; then break; fi
    sleep 0.5
done

if ! curl -sf "$BASE_URL/openapi.json" > /dev/null 2>&1; then
    echo "Error: server failed to start." >&2
    cat /tmp/schemathesis_server.log >&2
    exit 1
fi

echo "Running Schemathesis against $BASE_URL ..."
st run "$BASE_URL/openapi.json" "$@"
