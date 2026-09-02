from fastapi.testclient import TestClient

from app.main import app
from app.services import search


client = TestClient(app)


def test_album_search_full_pipeline(monkeypatch):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "id": "lastfm-1",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "listeners": 1000,
                "playcount": 5000,
            },
            {
                "id": "lastfm-2",
                "title": "Bad",
                "artist": "Michael Jackson",
                "listeners": 800,
                "playcount": 4000,
            },
        ]

    async def mock_find_album(title, artist):
        from app.schemas.album import Album

        albums = {
            "Thriller": {
                "id": "mb-thriller",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "year": 1982,
            },
            "Bad": {
                "id": "mb-bad",
                "title": "Bad",
                "artist": "Michael Jackson",
                "year": 1987,
            },
        }

        return Album(**albums[title])

    async def mock_get_cover_url(musicbrainz_id):
        covers = {
            "mb-thriller": "https://example.com/thriller.jpg",
            "mb-bad": "https://example.com/bad.jpg",
        }

        return covers[musicbrainz_id]

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

    response = client.get(
        "/albums/search",
        params={"query": "Michael Jackson"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "id": "mb-thriller",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "year": 1982,
                "listeners": 1000,
                "playcount": 5000,
                "cover_url": "https://example.com/thriller.jpg",
            },
            {
                "id": "mb-bad",
                "title": "Bad",
                "artist": "Michael Jackson",
                "year": 1987,
                "listeners": 800,
                "playcount": 4000,
                "cover_url": "https://example.com/bad.jpg",
            },
        ]
    }
def test_album_search_handles_musicbrainz_miss(monkeypatch):
    async def mock_search_albums_lastfm(query):
        return [
            {
                "id": "lastfm-1",
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "listeners": 500,
                "playcount": 2000,
            }
        ]

    async def mock_find_album(title, artist):
        return None

    async def mock_get_cover_url(musicbrainz_id):
        return "https://example.com/should-not-be-called.jpg"

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

    response = client.get(
        "/albums/search",
        params={"query": "Unknown Artist"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "id": "",
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "year": None,
                "listeners": 500,
                "playcount": 2000,
                "cover_url": None,
            }
        ]
    }
    
def test_album_search_handles_lastfm_failure(monkeypatch):
    from fastapi import HTTPException

    async def mock_search_albums_lastfm(query):
        raise HTTPException(
            status_code=503,
            detail="Last.fm is temporarily unavailable.",
        )

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    response = client.get(
        "/albums/search",
        params={"query": "Michael Jackson"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Last.fm is temporarily unavailable."
    }