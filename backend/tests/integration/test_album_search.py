from fastapi.testclient import TestClient

from app.main import app
from app.services import search


client = TestClient(app)


def test_album_search_full_pipeline(monkeypatch):
    async def mock_search_albums_lastfm(query):
        assert query == "Michael Jackson"

        return [
            {
                "id": "lastfm-1",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "cover_url": "https://example.com/thriller.jpg",
            },
            {
                "id": "lastfm-2",
                "title": "Bad",
                "artist": "Michael Jackson",
                "cover_url": "https://example.com/bad.jpg",
            },
        ]

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    response = client.get(
        "/albums/search",
        params={"query": "Michael Jackson"},
    )

    assert response.status_code == 200

    assert response.json() == {
        "results": [
            {
                "id": "lastfm-1",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "year": None,
                "listeners": 0,
                "playcount": 0,
                "cover_url": "https://example.com/thriller.jpg",
                "release_id": None,
            },
            {
                "id": "lastfm-2",
                "title": "Bad",
                "artist": "Michael Jackson",
                "year": None,
                "listeners": 0,
                "playcount": 0,
                "cover_url": "https://example.com/bad.jpg",
                "release_id": None,
            },
        ]
    }


def test_album_search_handles_musicbrainz_miss(monkeypatch):
    async def mock_search_albums_lastfm(query):
        assert query == "Unknown Artist"

        return [
            {
                "id": "lastfm-1",
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "cover_url": None,
            }
        ]

    monkeypatch.setattr(
        search,
        "search_albums_lastfm",
        mock_search_albums_lastfm,
    )

    response = client.get(
        "/albums/search",
        params={"query": "Unknown Artist"},
    )

    assert response.status_code == 200

    assert response.json() == {
        "results": [
            {
                "id": "lastfm-1",
                "title": "Unknown Album",
                "artist": "Unknown Artist",
                "year": None,
                "listeners": 0,
                "playcount": 0,
                "cover_url": None,
                "release_id": None,
            }
        ]
    }