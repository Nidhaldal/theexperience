import pytest
import httpx

from app.services.lastfm import search_albums_lastfm


class MockResponse:
    def __init__(self, data: dict):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class MockAsyncClient:
    def __init__(self):
        self.responses = [
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
            ),
            MockResponse(
                {
                    "album": {
                        "listeners": "12345",
                        "playcount": "67890",
                    }
                }
            ),
        ]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def get(self, *args, **kwargs):
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_search_albums_lastfm():
    import app.services.lastfm

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = MockAsyncClient

    try:
        result = await search_albums_lastfm("Let It Bleed")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "test-mbid",
            "title": "Let It Bleed",
            "artist": "The Rolling Stones",
            "listeners": 12345,
            "playcount": 67890,
        }
    ]


@pytest.mark.asyncio
async def test_search_albums_lastfm_returns_empty_list_when_no_results():
    import app.services.lastfm

    class EmptyResultsClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
                MockResponse(
                    {
                        "results": {
                            "albummatches": {
                                "album": []
                            }
                        }
                    }
                )
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = EmptyResultsClient

    try:
        result = await search_albums_lastfm("album-that-does-not-exist")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == []
@pytest.mark.asyncio
async def test_search_albums_lastfm_skips_albums_without_name_or_artist():
    import app.services.lastfm

    class InvalidAlbumsClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
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
                ),
                MockResponse(
                    {
                        "album": {
                            "listeners": "100",
                            "playcount": "200",
                        }
                    }
                ),
                MockResponse(
                    {
                        "album": {
                            "listeners": "300",
                            "playcount": "400",
                        }
                    }
                ),
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = InvalidAlbumsClient

    try:
        result = await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "valid-mbid",
            "title": "Valid Album",
            "artist": "Valid Artist",
            "listeners": 100,
            "playcount": 200,
        },
        {
            "id": "valid-mbid-2",
            "title": "Another Valid Album",
            "artist": "Another Artist",
            "listeners": 300,
            "playcount": 400,
        },
    ]
    
    

@pytest.mark.asyncio
async def test_search_albums_lastfm_raises_error_when_api_returns_error():
    import app.services.lastfm

    class ApiErrorClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
                MockResponse(
                    {
                        "error": 6,
                        "message": "Invalid parameters",
                    }
                )
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = ApiErrorClient

    try:
        with pytest.raises(
            RuntimeError,
            match="Invalid parameters",
        ):
            await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client


@pytest.mark.asyncio
async def test_search_albums_lastfm_raises_error_on_timeout():
    import app.services.lastfm

    class TimeoutClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            raise httpx.TimeoutException("Request timed out")

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = TimeoutClient

    try:
        with pytest.raises(
            RuntimeError,
            match="Last.fm request timed out.",
        ):
            await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_search_albums_lastfm_raises_error_on_connection_failure():
    import app.services.lastfm

    class ConnectionErrorClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            raise httpx.RequestError("Connection failed")

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = ConnectionErrorClient

    try:
        with pytest.raises(
            RuntimeError,
            match="Could not connect to Last.fm.",
        ):
            await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client


@pytest.mark.asyncio
async def test_search_albums_lastfm_uses_zero_popularity_when_data_is_missing():
    import app.services.lastfm

    class MissingPopularityClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
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
                ),
                MockResponse(
                    {
                        "album": {}
                    }
                ),
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = MissingPopularityClient

    try:
        result = await search_albums_lastfm("Let It Bleed")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "test-mbid",
            "title": "Let It Bleed",
            "artist": "The Rolling Stones",
            "listeners": 0,
            "playcount": 0,
        }
    ]

@pytest.mark.asyncio
async def test_search_albums_lastfm_processes_multiple_albums():
    import app.services.lastfm

    class MultipleAlbumsClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
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
                ),
                MockResponse(
                    {
                        "album": {
                            "listeners": "100",
                            "playcount": "200",
                        }
                    }
                ),
                MockResponse(
                    {
                        "album": {
                            "listeners": "300",
                            "playcount": "400",
                        }
                    }
                ),
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = MultipleAlbumsClient

    try:
        result = await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "mbid-one",
            "title": "Album One",
            "artist": "Artist One",
            "listeners": 100,
            "playcount": 200,
        },
        {
            "id": "mbid-two",
            "title": "Album Two",
            "artist": "Artist Two",
            "listeners": 300,
            "playcount": 400,
        },
    ]

@pytest.mark.asyncio
async def test_search_albums_lastfm_uses_zero_popularity_when_info_returns_error():
    import app.services.lastfm

    class PopularityErrorClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
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
                ),
                MockResponse(
                    {
                        "error": 6,
                        "message": "Album not found",
                    }
                ),
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = PopularityErrorClient

    try:
        result = await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "test-mbid",
            "title": "Test Album",
            "artist": "Test Artist",
            "listeners": 0,
            "playcount": 0,
        }
    ]

@pytest.mark.asyncio
async def test_search_albums_lastfm_uses_empty_id_when_mbid_is_missing():
    import app.services.lastfm

    class MissingMbidClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
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
                ),
                MockResponse(
                    {
                        "album": {
                            "listeners": "100",
                            "playcount": "200",
                        }
                    }
                ),
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = MissingMbidClient

    try:
        result = await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "",
            "title": "Test Album",
            "artist": "Test Artist",
            "listeners": 100,
            "playcount": 200,
        }
    ]

@pytest.mark.asyncio
async def test_search_albums_lastfm_defaults_missing_popularity_fields_to_zero():
    import app.services.lastfm

    class PartialPopularityClient(MockAsyncClient):
        def __init__(self):
            self.responses = [
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
                ),
                MockResponse(
                    {
                        "album": {
                            "listeners": "100"
                        }
                    }
                ),
            ]

    original_client = app.services.lastfm.httpx.AsyncClient
    app.services.lastfm.httpx.AsyncClient = PartialPopularityClient

    try:
        result = await search_albums_lastfm("test")
    finally:
        app.services.lastfm.httpx.AsyncClient = original_client

    assert result == [
        {
            "id": "test-mbid",
            "title": "Test Album",
            "artist": "Test Artist",
            "listeners": 100,
            "playcount": 0,
        }
    ]


