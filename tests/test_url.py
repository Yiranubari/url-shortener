def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "URL Shortener API"}


def test_shorten_creates_short_url(client):
    r = client.post("/shorten", json={"url": "https://example.com/MyPath/"})
    assert r.status_code == 200
    body = r.json()
    assert body["long_url"] == "https://example.com/MyPath/"
    assert body["short_code"]
    assert body["short_url"].endswith(body["short_code"])


def test_shorten_accepts_long_url(client):
    long_url = "https://example.com/" + "a" * 2000
    r = client.post("/shorten", json={"url": long_url})
    assert r.status_code == 200


def test_shorten_deduplicates_same_url(client):
    first = client.post(
        "/shorten", json={"url": "https://example.com/page"}
    ).json()
    second = client.post(
        "/shorten", json={"url": "https://example.com/page"}
    ).json()
    assert first["short_code"] == second["short_code"]


def test_shorten_deduplicates_normalized_variants(client):
    base = client.post(
        "/shorten", json={"url": "https://example.com/Page/"}
    ).json()
    for variant in [
        "https://example.com/Page",
        "https://example.com:443/Page/",
        "https://example.com/Page#frag",
    ]:
        r = client.post("/shorten", json={"url": variant})
        assert r.status_code == 200
        assert r.json()["short_code"] == base["short_code"], variant


def test_shorten_rejects_invalid_url(client):
    r = client.post("/shorten", json={"url": "not-a-url"})
    assert r.status_code == 422


def test_shorten_rejects_oversized_url(client):
    r = client.post(
        "/shorten", json={"url": "https://example.com/" + "a" * 2100}
    )
    assert r.status_code == 422


def test_redirect_returns_307_to_original_url(client):
    created = client.post(
        "/shorten", json={"url": "https://example.com/Path/"}
    ).json()
    r = client.get(f"/{created['short_code']}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com/Path/"


def test_redirect_missing_returns_404(client):
    r = client.get("/nope123")
    assert r.status_code == 404
    assert r.json() == {"detail": "Short URL not found"}


def test_reserved_path_not_treated_as_short_code(client):
    r = client.get("/shorten", follow_redirects=False)
    assert r.status_code == 404
    assert r.json() == {"detail": "Short URL not found"}


def test_rate_limit_headers_present(client):
    r = client.post("/shorten", json={"url": "https://example.com/x"})
    assert r.status_code == 200
    assert int(r.headers["x-ratelimit-limit"]) == 20
    assert int(r.headers["x-ratelimit-remaining"]) == 19


def test_shorten_rate_limit_exceeded(client):
    for i in range(20):
        r = client.post("/shorten", json={"url": f"https://h{i}.example.com/x"})
        assert r.status_code == 200
    r = client.post("/shorten", json={"url": "https://over.example.com/x"})
    assert r.status_code == 429


def test_redirect_rate_limit_exceeded(client):
    code = client.post(
        "/shorten", json={"url": "https://example.com/x"}
    ).json()["short_code"]
    for _ in range(100):
        r = client.get(f"/{code}", follow_redirects=False)
        assert r.status_code == 307
    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 429

