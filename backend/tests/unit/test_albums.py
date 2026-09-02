from fastapi.testclient import TestClient
import fastapi.exceptions
import pytest
from app.main import app
from app.routers import albums


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }


def test_search_returns_albums(monkeypatch):
    async def mock_search_music(query):
        return [
            {
                "id": "mb-123",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "year": 1982,
                "listeners": 1000,
                "playcount": 5000,
                "cover_url": "https://example.com/thriller.jpg",
            }
        ]

    monkeypatch.setattr(
        albums,
        "search_music",
        mock_search_music,
    )

    response = client.get(
        "/albums/search",
        params={"query": "Thriller"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "id": "mb-123",
                "title": "Thriller",
                "artist": "Michael Jackson",
                "year": 1982,
                "listeners": 1000,
                "playcount": 5000,
                "cover_url": "https://example.com/thriller.jpg",
            }
        ]
    }


def test_search_passes_query_to_service(monkeypatch):
    received_query = None

    async def mock_search_music(query):
        nonlocal received_query
        received_query = query
        return []

    monkeypatch.setattr(
        albums,
        "search_music",
        mock_search_music,
    )

    response = client.get(
        "/albums/search",
        params={"query": "Pink Floyd"},
    )

    assert response.status_code == 200
    assert received_query == "Pink Floyd"


def test_search_returns_empty_results(monkeypatch):
    async def mock_search_music(query):
        return []

    monkeypatch.setattr(
        albums,
        "search_music",
        mock_search_music,
    )

    response = client.get(
        "/albums/search",
        params={"query": "unknown"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": []
    }


def test_search_requires_query():
    response = client.get("/albums/search")

    assert response.status_code == 422


def test_search_rejects_empty_query():
    response = client.get(
        "/albums/search",
        params={"query": ""},
    )

    assert response.status_code == 422


def test_search_rejects_missing_query_value():
    response = client.get(
        "/albums/search?query",
    )

    assert response.status_code == 422


def test_search_raises_validation_error_for_invalid_response(
    monkeypatch,
):
    async def mock_search_music(query):
        return [
            {
                "id": "mb-123",
                "title": "Thriller",
            }
        ]

    monkeypatch.setattr(
        albums,
        "search_music",
        mock_search_music,
    )

    with pytest.raises(
        fastapi.exceptions.ResponseValidationError
    ):
        client.get(
            "/albums/search",
            params={"query": "Thriller"},
        )

