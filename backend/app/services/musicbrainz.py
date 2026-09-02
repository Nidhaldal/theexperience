import asyncio
import time

import httpx
from fastapi import HTTPException

from app.schemas.album import Album
from app.services.normalization import normalize_artist, normalize_text


MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/release-group"

HEADERS = {
    "User-Agent": "TheExperience/0.1.0 (personal-project)"
}

MIN_REQUEST_INTERVAL = 1.0

_last_request_time = 0.0
_request_lock = asyncio.Lock()


async def _wait_for_rate_limit() -> None:
    global _last_request_time

    async with _request_lock:
        current_time = time.monotonic()
        elapsed = current_time - _last_request_time

        if elapsed < MIN_REQUEST_INTERVAL:
            await asyncio.sleep(
                MIN_REQUEST_INTERVAL - elapsed
            )

        _last_request_time = time.monotonic()


async def _request_musicbrainz(params: dict) -> dict:
    for attempt in range(2):
        await _wait_for_rate_limit()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    MUSICBRAINZ_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=10.0,
                )

            if response.status_code == 503:
                if attempt == 0:
                    await asyncio.sleep(2)
                    continue

                raise HTTPException(
                    status_code=503,
                    detail=(
                        "MusicBrainz is temporarily unavailable. "
                        "Please try again later."
                    ),
                )

            response.raise_for_status()

            return response.json()

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


def _select_best_release_group(
    release_groups: list[dict],
    title: str,
    artist: str,
) -> dict | None:
    normalized_title = normalize_text(title)
    normalized_artist = normalize_artist(artist)

    candidates = []

    for release_group in release_groups:
        release_group_title = normalize_text(
            release_group.get("title", "")
        )

        artist_credit = release_group.get("artist-credit", [])

        release_group_artist = normalize_artist(
    artist_credit[0].get("name", "")
    if artist_credit
    else ""
)

        if release_group_title != normalized_title:
            continue

        if release_group_artist != normalized_artist:
            continue

        primary_type = release_group.get(
            "primary-type",
            ""
        )

        if primary_type != "Album":
            continue

        candidates.append(release_group)

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda release_group: (
            release_group.get("score", 0),
            release_group.get(
                "first-release-date",
                "",
            ),
        ),
    )


async def find_album(
    title: str,
    artist: str,
) -> Album | None:
    params = {
        "query": (
            f'releasegroup:"{title}" '
            f'AND artist:"{artist}"'
        ),
        "fmt": "json",
        "limit": 10,
    }

    data = await _request_musicbrainz(params)

    release_groups = data.get(
        "release-groups",
        [],
    )

    if not release_groups:
        return None

    release_group = _select_best_release_group(
        release_groups,
        title,
        artist,
    )

    if not release_group:
        return None

    release_group_id = release_group.get(
        "id",
        "",
    )

    release_group_title = release_group.get(
        "title",
        title,
    )

    artist_name = artist

    artist_credit = release_group.get(
        "artist-credit",
        [],
    )

    if artist_credit:
        artist_name = artist_credit[0].get(
            "name",
            artist,
        )

    first_release_date = release_group.get(
        "first-release-date"
    )

    year = None

    if first_release_date:
        try:
            year = int(first_release_date[:4])
        except ValueError:
            year = None

    return Album(
        id=release_group_id,
        title=release_group_title,
        artist=artist_name,
        year=year,
    )
