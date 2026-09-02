import httpx
import pytest
from fastapi import HTTPException

from app.schemas.album import Album
from app.services import search


@pytest.mark.asyncio
async def test_search_music_returns_empty_list_when_lastfm_returns_nothing(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return []

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    result = await search.search_music("Thriller")

    assert result == []


@pytest.mark.asyncio
async def test_search_music_skips_album_with_missing_title(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "",
                "artist": "Michael Jackson",
                "listeners": 100,
                "playcount": 200,
            }
        ]

    async def mock_find_album(title, artist):
        raise AssertionError(
            "MusicBrainz should not be called"
        )

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    result = await search.search_music("Thriller")

    assert result == []


@pytest.mark.asyncio
async def test_search_music_skips_album_with_missing_artist(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Thriller",
                "artist": "",
                "listeners": 100,
                "playcount": 200,
            }
        ]

    async def mock_find_album(title, artist):
        raise AssertionError(
            "MusicBrainz should not be called"
        )

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    result = await search.search_music("Thriller")

    assert result == []


@pytest.mark.asyncio
async def test_search_music_returns_musicbrainz_metadata(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Thriller",
                "artist": "Michael Jackson",
                "listeners": 500,
                "playcount": 1000,
            }
        ]

    async def mock_find_album(title, artist):
        return Album(
            id="mb-123",
            title="Thriller",
            artist="Michael Jackson",
            year=1982,
        )

    async def mock_get_cover_url(musicbrainz_id):
        return "https://example.com/thriller.jpg"

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    result = await search.search_music("Thriller")

    assert len(result) == 1
    assert result[0].id == "mb-123"
    assert result[0].title == "Thriller"
    assert result[0].artist == "Michael Jackson"
    assert result[0].year == 1982
    assert result[0].listeners == 500
    assert result[0].playcount == 1000
    assert result[0].cover_url == (
        "https://example.com/thriller.jpg"
    )


@pytest.mark.asyncio
async def test_search_music_preserves_lastfm_order(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Album One",
                "artist": "Artist One",
                "listeners": 100,
                "playcount": 200,
            },
            {
                "title": "Album Two",
                "artist": "Artist Two",
                "listeners": 300,
                "playcount": 400,
            },
            {
                "title": "Album Three",
                "artist": "Artist Three",
                "listeners": 500,
                "playcount": 600,
            },
        ]

    async def mock_find_album(title, artist):
        return Album(
            id=f"{title}-id",
            title=title,
            artist=artist,
            year=2000,
        )

    async def mock_get_cover_url(musicbrainz_id):
        return f"https://example.com/{musicbrainz_id}.jpg"

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    result = await search.search_music("test")

    assert [album.title for album in result] == [
        "Album One",
        "Album Two",
        "Album Three",
    ]


@pytest.mark.asyncio
async def test_search_music_uses_lastfm_data_when_musicbrainz_has_no_match(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "listeners": 123,
                "playcount": 456,
            }
        ]

    async def mock_find_album(title, artist):
        return None

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    result = await search.search_music("Unknown Album")

    assert len(result) == 1
    assert result[0].id == ""
    assert result[0].title == "Unknown Album"
    assert result[0].artist == "Unknown Artist"
    assert result[0].listeners == 123
    assert result[0].playcount == 456
    assert result[0].year is None
    assert result[0].cover_url is None


@pytest.mark.asyncio
async def test_search_music_handles_multiple_albums(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Album One",
                "artist": "Artist One",
                "listeners": 100,
                "playcount": 200,
            },
            {
                "title": "Album Two",
                "artist": "Artist Two",
                "listeners": 300,
                "playcount": 400,
            },
        ]

    async def mock_find_album(title, artist):
        return Album(
            id=f"{title}-id",
            title=title,
            artist=artist,
            year=2020,
        )

    async def mock_get_cover_url(musicbrainz_id):
        return f"https://example.com/{musicbrainz_id}.jpg"

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    result = await search.search_music("test")

    assert len(result) == 2
    assert result[0].id == "Album One-id"
    assert result[1].id == "Album Two-id"


@pytest.mark.asyncio
async def test_search_music_does_not_request_cover_when_musicbrainz_has_no_match(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "listeners": 100,
                "playcount": 200,
            }
        ]

    async def mock_find_album(title, artist):
        return None

    async def mock_get_cover_url(musicbrainz_id):
        raise AssertionError(
            "Cover Art Archive should not be called"
        )

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    result = await search.search_music("Unknown Album")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_search_music_propagates_musicbrainz_http_exception(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Thriller",
                "artist": "Michael Jackson",
                "listeners": 100,
                "playcount": 200,
            }
        ]

    async def mock_find_album(title, artist):
        raise HTTPException(
            status_code=503,
            detail="MusicBrainz unavailable",
        )

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    with pytest.raises(HTTPException) as exc_info:
        await search.search_music("Thriller")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "MusicBrainz unavailable"
    )


@pytest.mark.asyncio
async def test_search_music_propagates_cover_art_http_exception(
    monkeypatch,
):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "title": "Thriller",
                "artist": "Michael Jackson",
                "listeners": 100,
                "playcount": 200,
            }
        ]

    async def mock_find_album(title, artist):
        return Album(
            id="mb-123",
            title="Thriller",
            artist="Michael Jackson",
            year=1982,
        )

    async def mock_get_cover_url(musicbrainz_id):
        raise HTTPException(
            status_code=504,
            detail="Cover Art Archive timed out",
        )

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    with pytest.raises(HTTPException) as exc_info:
        await search.search_music("Thriller")

    assert exc_info.value.status_code == 504
    assert exc_info.value.detail == (
        "Cover Art Archive timed out"
    )