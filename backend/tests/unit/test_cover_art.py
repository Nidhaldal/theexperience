import httpx
import pytest

from app.services import cover_art
from app.services.cover_art import get_cover_url


@pytest.fixture(autouse=True)
def clear_cover_cache():
    cover_art._cover_cache.clear()


class MockResponse:
    def __init__(
        self,
        status_code=200,
        data=None,
    ):
        self.status_code = status_code
        self.url = "https://example.com/cover-art"
        self._data = data or {}
        self.history = []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "HTTP error",
                request=httpx.Request(
                    "GET",
                    "https://coverartarchive.org",
                ),
                response=httpx.Response(
                    self.status_code,
                ),
            )

    def json(self):
        return self._data


@pytest.mark.asyncio
async def test_get_cover_url_returns_large_front_approved_thumbnail(
    monkeypatch,
):
    response = MockResponse(
        data={
            "images": [
                {
                    "front": True,
                    "approved": True,
                    "thumbnails": {
                        "large": "https://example.com/cover.jpg",
                    },
                }
            ]
        }
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result == "https://example.com/cover.jpg"


@pytest.mark.asyncio
async def test_get_cover_url_ignores_non_front_image(
    monkeypatch,
):
    response = MockResponse(
        data={
            "images": [
                {
                    "front": False,
                    "approved": True,
                    "thumbnails": {
                        "large": "https://example.com/back.jpg",
                    },
                }
            ]
        }
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_ignores_unapproved_image(
    monkeypatch,
):
    response = MockResponse(
        data={
            "images": [
                {
                    "front": False,
                    "approved": False,
                    "thumbnails": {
                        "large": "https://example.com/cover.jpg",
                    },
                }
            ]
        }
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_skips_invalid_images_and_finds_valid_one(
    monkeypatch,
):
    response = MockResponse(
        data={
            "images": [
                {
                    "front": False,
                    "approved": True,
                    "thumbnails": {
                        "large": "https://example.com/back.jpg",
                    },
                },
                {
                    "front": False,
                    "approved": False,
                    "thumbnails": {
                        "large": "https://example.com/unapproved.jpg",
                    },
                },
                {
                    "front": True,
                    "approved": True,
                    "thumbnails": {
                        "large": "https://example.com/front.jpg",
                    },
                },
            ]
        }
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result == "https://example.com/front.jpg"


@pytest.mark.asyncio
async def test_get_cover_url_returns_none_when_images_are_missing(
    monkeypatch,
):
    response = MockResponse(
        data={}
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_returns_none_for_404(
    monkeypatch,
):
    response = MockResponse(
        status_code=404
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_returns_none_when_large_thumbnail_is_missing(
    monkeypatch,
):
    response = MockResponse(
        data={
            "images": [
                {
                    "front": True,
                    "approved": True,
                    "thumbnails": {},
                }
            ]
        }
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_handles_timeout(
    monkeypatch,
):
    async def mock_get(self, url):
        raise httpx.TimeoutException(
            "Request timed out"
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_handles_connection_error(
    monkeypatch,
):
    async def mock_get(self, url):
        raise httpx.ConnectError(
            "Connection failed"
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_cover_url_handles_http_error(
    monkeypatch,
):
    response = MockResponse(
        status_code=500
    )

    async def mock_get(self, url):
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await get_cover_url("album-123")

    assert result is None
