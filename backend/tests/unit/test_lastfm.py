import httpx
import pytest

import app.services.lastfm as lastfm
from app.services.lastfm import search_albums_lastfm


class MockResponse:
    def __init__(self, data: dict):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class MockAsyncClient:
    def __init__(self, responses):
        self.responses = list(responses)

    async def get(self, *args, **kwargs):
        return self.responses.pop(0)


def mock_client(monkeypatch, responses):
    client = MockAsyncClient(responses)
    monkeypatch.setattr(lastfm, "LASTFM_CLIENT", client)


@pytest.fixture(autouse=True)
def clear_caches():
    lastfm._search_cache.clear()
    lastfm._popularity_cache.clear()


@pytest.fixture(autouse=True)
def mock_api_key(monkeypatch):
    monkeypatch.setattr(
        lastfm,
        "LASTFM_API_KEY",
        "test-api-key",
    )


@pytest.mark.asyncio
async def test_search_albums_lastfm(monkeypatch):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Let It Bleed",
                                    "artist": "The Rolling Stones",
                                    "mbid": "test-mbid",
                                    "image": [
                                        {
                                            "size": "extralarge",
                                            "#text": (
                                                "https://example.com/"
                                                "cover.jpg"
                                            ),
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("Let It Bleed")

    assert result == [
        {
            "id": "test-mbid",
            "title": "Let It Bleed",
            "artist": "The Rolling Stones",
            "cover_url": "https://example.com/cover.jpg",
        }
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_returns_empty_list_when_no_results(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": []
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm(
        "album-that-does-not-exist"
    )

    assert result == []


@pytest.mark.asyncio
async def test_search_albums_lastfm_skips_albums_without_name_or_artist(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Valid Album",
                                    "artist": "Valid Artist",
                                    "mbid": "valid-mbid",
                                },
                                {
                                    "name": "Missing Artist",
                                    "mbid": "invalid-mbid-1",
                                },
                                {
                                    "artist": "Missing Name",
                                    "mbid": "invalid-mbid-2",
                                },
                                {
                                    "name": "Another Valid Album",
                                    "artist": "Another Artist",
                                    "mbid": "valid-mbid-2",
                                },
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("test")

    assert result == [
        {
            "id": "valid-mbid",
            "title": "Valid Album",
            "artist": "Valid Artist",
            "cover_url": None,
        },
        {
            "id": "valid-mbid-2",
            "title": "Another Valid Album",
            "artist": "Another Artist",
            "cover_url": None,
        },
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_raises_error_when_api_returns_error(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "error": 6,
                    "message": "Invalid parameters",
                }
            )
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Invalid parameters",
    ):
        await search_albums_lastfm("test")


@pytest.mark.asyncio
async def test_search_albums_lastfm_raises_error_on_timeout(
    monkeypatch,
):
    class TimeoutClient:
        async def get(self, *args, **kwargs):
            raise httpx.TimeoutException(
                "Request timed out"
            )

    monkeypatch.setattr(
        lastfm,
        "LASTFM_CLIENT",
        TimeoutClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="Last.fm request timed out.",
    ):
        await search_albums_lastfm("test")


@pytest.mark.asyncio
async def test_search_albums_lastfm_raises_error_on_connection_failure(
    monkeypatch,
):
    class ConnectionErrorClient:
        async def get(self, *args, **kwargs):
            raise httpx.RequestError(
                "Connection failed"
            )

    monkeypatch.setattr(
        lastfm,
        "LASTFM_CLIENT",
        ConnectionErrorClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="Could not connect to Last.fm.",
    ):
        await search_albums_lastfm("test")


@pytest.mark.asyncio
async def test_search_albums_lastfm_uses_zero_popularity_when_data_is_missing(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Let It Bleed",
                                    "artist": "The Rolling Stones",
                                    "mbid": "test-mbid",
                                }
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("Let It Bleed")

    assert result == [
        {
            "id": "test-mbid",
            "title": "Let It Bleed",
            "artist": "The Rolling Stones",
            "cover_url": None,
        }
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_processes_multiple_albums(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Album One",
                                    "artist": "Artist One",
                                    "mbid": "mbid-one",
                                },
                                {
                                    "name": "Album Two",
                                    "artist": "Artist Two",
                                    "mbid": "mbid-two",
                                },
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("test")

    assert result == [
        {
            "id": "mbid-one",
            "title": "Album One",
            "artist": "Artist One",
            "cover_url": None,
        },
        {
            "id": "mbid-two",
            "title": "Album Two",
            "artist": "Artist Two",
            "cover_url": None,
        },
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_uses_zero_popularity_when_info_returns_error(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Test Album",
                                    "artist": "Test Artist",
                                    "mbid": "test-mbid",
                                }
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("test")

    assert result == [
        {
            "id": "test-mbid",
            "title": "Test Album",
            "artist": "Test Artist",
            "cover_url": None,
        }
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_uses_empty_id_when_mbid_is_missing(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Test Album",
                                    "artist": "Test Artist",
                                }
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("test")

    assert result == [
        {
            "id": "",
            "title": "Test Album",
            "artist": "Test Artist",
            "cover_url": None,
        }
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_defaults_missing_popularity_fields_to_zero(
    monkeypatch,
):
    mock_client(
        monkeypatch,
        [
            MockResponse(
                {
                    "results": {
                        "albummatches": {
                            "album": [
                                {
                                    "name": "Test Album",
                                    "artist": "Test Artist",
                                    "mbid": "test-mbid",
                                }
                            ]
                        }
                    }
                }
            )
        ],
    )

    result = await search_albums_lastfm("test")

    assert result == [
        {
            "id": "test-mbid",
            "title": "Test Album",
            "artist": "Test Artist",
            "cover_url": None,
        }
    ]
