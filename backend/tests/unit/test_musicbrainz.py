import httpx
import pytest
from fastapi import HTTPException

from app.services import musicbrainz
from app.services.musicbrainz import (
    _select_best_release_group,
    find_album,
)


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class MockClient:
    def __init__(self, responses=None, exception=None):
        self.responses = list(responses or [])
        self.exception = exception

    async def get(self, *args, **kwargs):
        if self.exception:
            raise self.exception
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def reset_client(monkeypatch):
    original = musicbrainz._client
    yield
    monkeypatch.setattr(musicbrainz, "_client", original)


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
async def test_find_album_returns_album(monkeypatch):
    monkeypatch.setattr(
        musicbrainz,
        "_client",
        MockClient(
            [
                MockResponse(
                    {
                        "release-groups": [
                            {
                                "id": "f32fab67-77d4-4b7e-9062e28e4c37",
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
                ),
                MockResponse({}),
            ]
        ),
    )

    result = await find_album(
        "Thriller",
        "Michael Jackson",
    )

    assert result.id == "f32fab67-77d4-4b7e-9062e28e4c37"
    assert result.title == "Thriller"
    assert result.artist == "Michael Jackson"
    assert result.year == 1982


@pytest.mark.asyncio
async def test_find_album_handles_missing_release_date(
    monkeypatch,
):
    monkeypatch.setattr(
        musicbrainz,
        "_client",
        MockClient(
            [
                MockResponse(
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
                ),
                MockResponse({}),
            ]
        ),
    )

    result = await find_album(
        "Test Album",
        "Test Artist",
    )

    assert result.year is None


@pytest.mark.asyncio
async def test_find_album_handles_invalid_release_date(
    monkeypatch,
):
    monkeypatch.setattr(
        musicbrainz,
        "_client",
        MockClient(
            [
                MockResponse(
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
                ),
                MockResponse({}),
            ]
        ),
    )

    result = await find_album(
        "Test Album",
        "Test Artist",
    )

    assert result.year is None


@pytest.mark.asyncio
async def test_find_album_handles_timeout(monkeypatch):
    monkeypatch.setattr(
        musicbrainz,
        "_client",
        MockClient(
            exception=httpx.TimeoutException("Request timed out")
        ),
    )

    result = await find_album(
        "Thriller",
        "Michael Jackson",
    )

    assert result is None


@pytest.mark.asyncio
async def test_find_album_handles_connection_error(monkeypatch):
    monkeypatch.setattr(
        musicbrainz,
        "_client",
        MockClient(
            exception=httpx.RequestError("Connection failed")
        ),
    )

    result = await find_album(
        "Thriller",
        "Michael Jackson",
    )

    assert result is None


@pytest.mark.asyncio
async def test_request_musicbrainz_raises_after_two_503_responses(
    monkeypatch,
):
    monkeypatch.setattr(
        musicbrainz,
        "_client",
        MockClient(
            [
                MockResponse({}, status_code=503),
                MockResponse({}, status_code=503),
            ]
        ),
    )

    async def mock_sleep(*args, **kwargs):
        pass

    monkeypatch.setattr(
        musicbrainz.asyncio,
        "sleep",
        mock_sleep,
    )

    result = await musicbrainz._request_musicbrainz(
        "https://musicbrainz.org/ws/2/release-group",
        {"query": "test"},
    )

    assert result == {}

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