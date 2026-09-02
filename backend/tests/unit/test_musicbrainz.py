import httpx
from app.services import musicbrainz
import pytest
from fastapi import HTTPException

from app.services.musicbrainz import (
    _select_best_release_group,
    find_album,
)


def test_select_best_release_group_returns_matching_album():
    release_groups = [
        {
            "id": "album-1",
            "title": "Thriller",
            "artist-credit": [{"name": "Michael Jackson"}],
            "primary-type": "Album",
            "score": 90,
            "first-release-date": "1982-11-30",
        }
    ]

    result = _select_best_release_group(
        release_groups,
        "Thriller",
        "Michael Jackson",
    )

    assert result["id"] == "album-1"


def test_select_best_release_group_rejects_wrong_title():
    release_groups = [
        {
            "id": "album-1",
            "title": "Bad",
            "artist-credit": [{"name": "Michael Jackson"}],
            "primary-type": "Album",
            "score": 100,
        }
    ]

    result = _select_best_release_group(
        release_groups,
        "Thriller",
        "Michael Jackson",
    )

    assert result is None


def test_select_best_release_group_rejects_wrong_artist():
    release_groups = [
        {
            "id": "album-1",
            "title": "Thriller",
            "artist-credit": [{"name": "Prince"}],
            "primary-type": "Album",
            "score": 100,
        }
    ]

    result = _select_best_release_group(
        release_groups,
        "Thriller",
        "Michael Jackson",
    )

    assert result is None


def test_select_best_release_group_rejects_non_album():
    release_groups = [
        {
            "id": "single-1",
            "title": "Thriller",
            "artist-credit": [{"name": "Michael Jackson"}],
            "primary-type": "Single",
            "score": 100,
        }
    ]

    result = _select_best_release_group(
        release_groups,
        "Thriller",
        "Michael Jackson",
    )

    assert result is None


def test_select_best_release_group_selects_highest_score():
    release_groups = [
        {
            "id": "album-1",
            "title": "Thriller",
            "artist-credit": [{"name": "Michael Jackson"}],
            "primary-type": "Album",
            "score": 80,
            "first-release-date": "1982-11-30",
        },
        {
            "id": "album-2",
            "title": "Thriller",
            "artist-credit": [{"name": "Michael Jackson"}],
            "primary-type": "Album",
            "score": 100,
            "first-release-date": "1982-11-30",
        },
    ]

    result = _select_best_release_group(
        release_groups,
        "Thriller",
        "Michael Jackson",
    )

    assert result["id"] == "album-2"


def test_select_best_release_group_uses_latest_date_when_scores_match():
    release_groups = [
        {
            "id": "album-1",
            "title": "Back to Black",
            "artist-credit": [{"name": "Amy Winehouse"}],
            "primary-type": "Album",
            "score": 100,
            "first-release-date": "2006-10-27",
        },
        {
            "id": "album-2",
            "title": "Back to Black",
            "artist-credit": [{"name": "Amy Winehouse"}],
            "primary-type": "Album",
            "score": 100,
            "first-release-date": "2007-01-01",
        },
    ]

    result = _select_best_release_group(
        release_groups,
        "Back to Black",
        "Amy Winehouse",
    )

    assert result["id"] == "album-2"


def test_select_best_release_group_handles_artist_normalization():
    release_groups = [
        {
            "id": "album-1",
            "title": "The Wall",
            "artist-credit": [{"name": "Pink Floyd"}],
            "primary-type": "Album",
            "score": 100,
        }
    ]

    result = _select_best_release_group(
        release_groups,
        "The Wall",
        "The Pink Floyd",
    )

    assert result is not None
    assert result["id"] == "album-1"


def test_select_best_release_group_returns_none_for_empty_results():
    result = _select_best_release_group(
        [],
        "Thriller",
        "Michael Jackson",
    )

    assert result is None


@pytest.mark.asyncio
async def test_find_album_returns_album():
    import app.services.musicbrainz

    class SuccessClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse(
                {
                    "release-groups": [
                        {
                            "id": "f32fab67",
                            "title": "Thriller",
                            "artist-credit": [
                                {"name": "Michael Jackson"}
                            ],
                            "primary-type": "Album",
                            "score": 100,
                            "first-release-date": "1982-11-30",
                        }
                    ]
                }
            )

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = SuccessClient

    try:
        result = await find_album(
            "Thriller",
            "Michael Jackson",
        )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client

    assert result.id == "f32fab67"
    assert result.title == "Thriller"
    assert result.artist == "Michael Jackson"
    assert result.year == 1982


@pytest.mark.asyncio
async def test_find_album_returns_none_when_no_release_groups():
    import app.services.musicbrainz

    class EmptyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse(
                {
                    "release-groups": []
                }
            )

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = EmptyClient

    try:
        result = await find_album(
            "Unknown Album",
            "Unknown Artist",
        )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client

    assert result is None


@pytest.mark.asyncio
async def test_find_album_returns_none_when_no_matching_album():
    import app.services.musicbrainz

    class NoMatchClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse(
                {
                    "release-groups": [
                        {
                            "id": "wrong",
                            "title": "Bad",
                            "artist-credit": [
                                {"name": "Michael Jackson"}
                            ],
                            "primary-type": "Album",
                            "score": 100,
                        }
                    ]
                }
            )

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = NoMatchClient

    try:
        result = await find_album(
            "Thriller",
            "Michael Jackson",
        )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client

    assert result is None


@pytest.mark.asyncio
async def test_find_album_handles_missing_release_date():
    import app.services.musicbrainz

    class MissingDateClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse(
                {
                    "release-groups": [
                        {
                            "id": "album-1",
                            "title": "Test Album",
                            "artist-credit": [
                                {"name": "Test Artist"}
                            ],
                            "primary-type": "Album",
                            "score": 100,
                        }
                    ]
                }
            )

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = MissingDateClient

    try:
        result = await find_album(
            "Test Album",
            "Test Artist",
        )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client

    assert result.year is None


@pytest.mark.asyncio
async def test_find_album_handles_invalid_release_date():
    import app.services.musicbrainz

    class InvalidDateClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse(
                {
                    "release-groups": [
                        {
                            "id": "album-1",
                            "title": "Test Album",
                            "artist-credit": [
                                {"name": "Test Artist"}
                            ],
                            "primary-type": "Album",
                            "score": 100,
                            "first-release-date": "abcd-01-01",
                        }
                    ]
                }
            )

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = InvalidDateClient

    try:
        result = await find_album(
            "Test Album",
            "Test Artist",
        )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client

    assert result.year is None


@pytest.mark.asyncio
async def test_find_album_handles_timeout():
    import app.services.musicbrainz

    class TimeoutClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            raise httpx.TimeoutException("Request timed out")

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = TimeoutClient

    try:
        with pytest.raises(
            HTTPException,
            match="MusicBrainz request timed out.",
        ):
            await find_album("Thriller", "Michael Jackson")
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client


@pytest.mark.asyncio
async def test_find_album_handles_connection_error():
    import app.services.musicbrainz

    class ConnectionErrorClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            raise httpx.RequestError("Connection failed")

    original_client = app.services.musicbrainz.httpx.AsyncClient
    app.services.musicbrainz.httpx.AsyncClient = ConnectionErrorClient

    try:
        with pytest.raises(
            HTTPException,
            match="Could not connect to MusicBrainz.",
        ):
            await find_album("Thriller", "Michael Jackson")
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_request_musicbrainz_retries_after_503():
    import app.services.musicbrainz

    responses = [
        MockResponse({}),
        MockResponse({"release-groups": []}),
    ]

    responses[0].status_code = 503

    class RetryClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            return responses.pop(0)

    async def mock_sleep(*args, **kwargs):
        pass

    original_client = app.services.musicbrainz.httpx.AsyncClient
    original_sleep = app.services.musicbrainz.asyncio.sleep

    app.services.musicbrainz.httpx.AsyncClient = RetryClient
    app.services.musicbrainz.asyncio.sleep = mock_sleep

    try:
        result = await app.services.musicbrainz._request_musicbrainz(
            {"query": "test"}
        )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client
        app.services.musicbrainz.asyncio.sleep = original_sleep

    assert result == {"release-groups": []}


@pytest.mark.asyncio
async def test_request_musicbrainz_raises_after_two_503_responses(
    
):
    import app.services.musicbrainz

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            response = MockResponse({})
            response.status_code = 503
            return response

    async def mock_sleep(*args, **kwargs):
        pass

    original_client = app.services.musicbrainz.httpx.AsyncClient
    original_sleep = app.services.musicbrainz.asyncio.sleep

    app.services.musicbrainz.httpx.AsyncClient = FailingClient
    app.services.musicbrainz.asyncio.sleep = mock_sleep

    try:
        with pytest.raises(
            HTTPException,
            match="MusicBrainz is temporarily unavailable.",
        ):
            await app.services.musicbrainz._request_musicbrainz(
                {"query": "test"}
            )
    finally:
        app.services.musicbrainz.httpx.AsyncClient = original_client
        app.services.musicbrainz.asyncio.sleep = original_sleep

def test_select_best_release_group_handles_empty_artist_credit():
    release_groups = [
        {
            "id": "mb-123",
            "title": "Thriller",
            "artist-credit": [],
            "primary-type": "Album",
            "score": 100,
            "first-release-date": "1982-11-30",
        }
    ]

    result = musicbrainz._select_best_release_group(
        release_groups,
        "Thriller",
        "Michael Jackson",
    )

    assert result is None

class MockResponse:
    def __init__(self, data):
        self.data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


