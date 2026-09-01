import os

import httpx
from dotenv import load_dotenv


load_dotenv()

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


async def get_album_popularity(
    artist: str,
    album: str,
) -> dict:
    params = {
        "method": "album.getInfo",
        "api_key": LASTFM_API_KEY,
        "artist": artist,
        "album": album,
        "format": "json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            LASTFM_URL,
            params=params,
            timeout=10.0,
        )

    response.raise_for_status()

    data = response.json()

    album_data = data["album"]

    return {
        "listeners": int(album_data.get("listeners", 0)),
        "playcount": int(album_data.get("playcount", 0)),
    }


async def search_albums_lastfm(query: str) -> list[dict]:
    params = {
        "method": "album.search",
        "api_key": LASTFM_API_KEY,
        "album": query,
        "format": "json",
        "limit": 20,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            LASTFM_URL,
            params=params,
            timeout=10.0,
        )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", {}).get("albummatches", {}).get("album", [])

    albums = []

    for album in results:
        albums.append(
            {
                "title": album.get("name", ""),
                "artist": album.get("artist", ""),
                "listeners": int(album.get("listeners", 0)),
                "playcount": 0,
            }
        )

    return albums