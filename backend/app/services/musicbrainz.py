import asyncio

import httpx
from fastapi import HTTPException

from app.schemas.album import Album


MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/release-group"

HEADERS = {
    "User-Agent": "TheExperience/0.1.0 (personal-project)"
}


async def search_albums(query: str) -> list[Album]:
    params = {
        "query": f'releasegroup:"{query}"',
        "fmt": "json",
        "limit": 10,
    }

    async with httpx.AsyncClient() as client:
        for attempt in range(2):
            try:
                response = await client.get(
                    MUSICBRAINZ_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=10.0,
                )

                if response.status_code == 503:
                    if attempt == 0:
                        await asyncio.sleep(1)
                        continue

                    raise HTTPException(
                        status_code=503,
                        detail="MusicBrainz is temporarily unavailable. Please try again later.",
                    )

                response.raise_for_status()
                break

            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=504,
                    detail="MusicBrainz request timed out.",
                )

            except httpx.RequestError:
                raise HTTPException(
                    status_code=503,
                    detail="Could not connect to MusicBrainz.",
                )

    data = response.json()

    albums = []

    for release_group in data.get("release-groups", []):
        artist_credit = release_group.get("artist-credit", [])

        if not artist_credit:
            continue

        artist = artist_credit[0].get("name")

        if not artist:
            continue

        first_release_date = release_group.get("first-release-date")
        year = None

        if first_release_date:
            try:
                year = int(first_release_date[:4])
            except ValueError:
                year = None

        album = Album(
            id=release_group["id"],
            title=release_group["title"],
            artist=artist,
            year=year,
        )

        albums.append(album)

    return albums


async def find_album(
    title: str,
    artist: str,
) -> Album | None:
    params = {
        "query": f'releasegroup:"{title}" AND artist:"{artist}"',
        "fmt": "json",
        "limit": 1,
    }

    async with httpx.AsyncClient() as client:
        for attempt in range(2):
            try:
                response = await client.get(
                    MUSICBRAINZ_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=10.0,
                )

                if response.status_code == 503:
                    if attempt == 0:
                        await asyncio.sleep(1)
                        continue

                    raise HTTPException(
                        status_code=503,
                        detail="MusicBrainz is temporarily unavailable. Please try again later.",
                    )

                response.raise_for_status()
                break

            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=504,
                    detail="MusicBrainz request timed out.",
                )

            except httpx.RequestError:
                raise HTTPException(
                    status_code=503,
                    detail="Could not connect to MusicBrainz.",
                )

    data = response.json()

    release_groups = data.get("release-groups", [])

    if not release_groups:
        return None

    release_group = release_groups[0]

    first_release_date = release_group.get("first-release-date")
    year = None

    if first_release_date:
        try:
            year = int(first_release_date[:4])
        except ValueError:
            year = None

    artist_credit = release_group.get("artist-credit", [])

    artist_name = artist

    if artist_credit:
        artist_name = artist_credit[0].get("name", artist)

    return Album(
        id=release_group["id"],
        title=release_group["title"],
        artist=artist_name,
        year=year,
    )
