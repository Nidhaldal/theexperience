import pytest

from app.schemas.album import Album
from app.services import search


@pytest.mark.asyncio
async def test_search_music_returns_lastfm_albums(monkeypatch):
    async def mock_search_albums_lastfm(query):
        assert query == "Thriller"

        return [
            {
                "id": "mb-123",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "cover_url": "https://example.com/thriller.jpg",
            }
        ]

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    result = await search.search_music("Thriller")

    assert len(result) == 1
    assert isinstance(result[0], Album)

    assert result[0].id == "mb-123"
    assert result[0].title == "Thriller"
    assert result[0].artist == "Michael Jackson"
    assert result[0].listeners == 0
    assert result[0].playcount == 0
    assert result[0].cover_url == "https://example.com/thriller.jpg"


@pytest.mark.asyncio
async def test_search_music_returns_multiple_albums(monkeypatch):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "id": "album-1",
                "title": "Album One",
                "artist": "Artist One",
                "cover_url": "https://example.com/one.jpg",
            },
            {
                "id": "album-2",
                "title": "Album Two",
                "artist": "Artist Two",
                "cover_url": "https://example.com/two.jpg",
            },
        ]

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    result = await search.search_music("test")

    assert len(result) == 2

    assert result[0].id == "album-1"
    assert result[0].title == "Album One"
    assert result[0].artist == "Artist One"

    assert result[1].id == "album-2"
    assert result[1].title == "Album Two"
    assert result[1].artist == "Artist Two"


@pytest.mark.asyncio
async def test_search_music_skips_invalid_albums(monkeypatch):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "id": "valid",
                "title": "Valid Album",
                "artist": "Valid Artist",
                "cover_url": None,
            },
            {
                "id": "missing-title",
                "title": "",
                "artist": "Artist",
            },
            {
                "id": "missing-artist",
                "title": "Album",
                "artist": "",
            },
            {
                "id": "missing-both",
                "title": "",
                "artist": "",
            },
        ]

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    result = await search.search_music("test")

    assert len(result) == 1
    assert result[0].id == "valid"


@pytest.mark.asyncio
async def test_search_music_defaults_missing_fields(monkeypatch):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "id": "album-1",
                "title": "Test Album",
                "artist": "Test Artist",
            }
        ]

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    result = await search.search_music("test")

    assert len(result) == 1
    assert result[0].id == "album-1"
    assert result[0].title == "Test Album"
    assert result[0].artist == "Test Artist"
    assert result[0].listeners == 0
    assert result[0].playcount == 0
    assert result[0].cover_url is None


@pytest.mark.asyncio
async def test_search_music_propagates_lastfm_error(monkeypatch):
    async def mock_search_albums_lastfm(query):
        raise RuntimeError("Last.fm failed")

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    with pytest.raises(
        RuntimeError,
        match="Last.fm failed",
    ):
        await search.search_music("test")


@pytest.mark.asyncio
async def test_get_album_details_with_musicbrainz_id(monkeypatch):
    async def mock_get_album_popularity(title, artist):
        assert title == "Thriller"
        assert artist == "Michael Jackson"
        return 1000, 5000

    async def mock_find_album_by_id(
        musicbrainz_id,
        title,
        artist,
    ):
        assert musicbrainz_id == "mb-123"
        assert title == "Thriller"
        assert artist == "Michael Jackson"

        return Album(
            id="mb-123",
            title="Thriller",
            artist="Michael Jackson",
            year=1982,
            release_id="release-123",
        )

    async def mock_get_cover_url(release_id):
        assert release_id == "release-123"
        return "https://example.com/thriller.jpg"

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
    )

    monkeypatch.setattr(
        search,
        "find_album_by_id",
        mock_find_album_by_id,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    result = await search.get_album_details(
        "Thriller",
        "Michael Jackson",
        "mb-123",
    )

    assert result.id == "mb-123"
    assert result.title == "Thriller"
    assert result.artist == "Michael Jackson"
    assert result.year == 1982
    assert result.listeners == 1000
    assert result.playcount == 5000
    assert result.cover_url == "https://example.com/thriller.jpg"
    assert result.release_id == "release-123"


@pytest.mark.asyncio
async def test_get_album_details_without_musicbrainz_id(
    monkeypatch,
):
    async def mock_get_album_popularity(title, artist):
        return 100, 200

    async def mock_find_album(title, artist):
        assert title == "Unknown Album"
        assert artist == "Unknown Artist"

        return Album(
            id="resolved-id",
            title="Unknown Album",
            artist="Unknown Artist",
            year=1990,
            release_id="release-456",
        )

    async def mock_get_cover_url(release_id):
        assert release_id == "release-456"
        return "https://example.com/cover.jpg"

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
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

    result = await search.get_album_details(
        "Unknown Album",
        "Unknown Artist",
    )

    assert result.id == "resolved-id"
    assert result.title == "Unknown Album"
    assert result.artist == "Unknown Artist"
    assert result.year == 1990
    assert result.listeners == 100
    assert result.playcount == 200
    assert result.cover_url == "https://example.com/cover.jpg"
    assert result.release_id == "release-456"


@pytest.mark.asyncio
async def test_get_album_details_handles_musicbrainz_miss(
    monkeypatch,
):
    async def mock_get_album_popularity(title, artist):
        return 100, 200

    async def mock_find_album(title, artist):
        return None

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
    )

    monkeypatch.setattr(
        search,
        "find_album",
        mock_find_album,
    )

    result = await search.get_album_details(
        "Unknown Album",
        "Unknown Artist",
    )

    assert result.id == ""
    assert result.title == "Unknown Album"
    assert result.artist == "Unknown Artist"
    assert result.listeners == 100
    assert result.playcount == 200
    assert result.cover_url is None
    assert result.release_id is None


@pytest.mark.asyncio
async def test_get_album_details_musicbrainz_id_miss(
    monkeypatch,
):
    async def mock_get_album_popularity(title, artist):
        return 100, 200

    async def mock_find_album_by_id(
        musicbrainz_id,
        title,
        artist,
    ):
        assert musicbrainz_id == "mb-missing"
        return None

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
    )

    monkeypatch.setattr(
        search,
        "find_album_by_id",
        mock_find_album_by_id,
    )

    result = await search.get_album_details(
        "Missing Album",
        "Missing Artist",
        "mb-missing",
    )

    assert result.id == "mb-missing"
    assert result.title == "Missing Album"
    assert result.artist == "Missing Artist"
    assert result.listeners == 100
    assert result.playcount == 200
    assert result.cover_url is None
    assert result.release_id is None


@pytest.mark.asyncio
async def test_get_album_details_uses_album_id_when_release_id_missing(
    monkeypatch,
):
    async def mock_get_album_popularity(title, artist):
        return 10, 20

    async def mock_find_album_by_id(
        musicbrainz_id,
        title,
        artist,
    ):
        return Album(
            id="album-id",
            title=title,
            artist=artist,
            year=2000,
            release_id=None,
        )

    async def mock_get_cover_url(identifier):
        assert identifier == "album-id"
        return "https://example.com/cover.jpg"

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
    )

    monkeypatch.setattr(
        search,
        "find_album_by_id",
        mock_find_album_by_id,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    result = await search.get_album_details(
        "Test Album",
        "Test Artist",
        "mb-123",
    )

    assert result.cover_url == "https://example.com/cover.jpg"
    assert result.release_id is None


@pytest.mark.asyncio
async def test_get_album_details_propagates_cover_art_error(
    monkeypatch,
):
    async def mock_get_album_popularity(title, artist):
        return 10, 20

    async def mock_find_album_by_id(
        musicbrainz_id,
        title,
        artist,
    ):
        return Album(
            id="album-id",
            title=title,
            artist=artist,
            year=2000,
            release_id="release-id",
        )

    async def mock_get_cover_url(release_id):
        raise RuntimeError("Cover Art failed")

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
    )

    monkeypatch.setattr(
        search,
        "find_album_by_id",
        mock_find_album_by_id,
    )

    monkeypatch.setattr(
        search,
        "get_cover_url",
        mock_get_cover_url,
    )

    with pytest.raises(
        RuntimeError,
        match="Cover Art failed",
    ):
        await search.get_album_details(
            "Test Album",
            "Test Artist",
            "mb-123",
        )


@pytest.mark.asyncio
async def test_get_album_details_propagates_musicbrainz_error(
    monkeypatch,
):
    async def mock_get_album_popularity(title, artist):
        return 10, 20

    async def mock_find_album_by_id(
        musicbrainz_id,
        title,
        artist,
    ):
        raise RuntimeError("MusicBrainz failed")

    monkeypatch.setattr(
        search,
        "get_album_popularity",
        mock_get_album_popularity,
    )

    monkeypatch.setattr(
        search,
        "find_album_by_id",
        mock_find_album_by_id,
    )

    with pytest.raises(
        RuntimeError,
        match="MusicBrainz failed",
    ):
        await search.get_album_details(
            "Test Album",
            "Test Artist",
            "mb-123",
        )