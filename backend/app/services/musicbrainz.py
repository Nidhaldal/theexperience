import asyncio
import time

import httpx
from fastapi import HTTPException

from app.schemas.album import Album
from app.services.normalization import (
    normalize_artist,
    normalize_text,
)


MUSICBRAINZ_URL = (
    "https://musicbrainz.org/ws/2/release-group"
)

MUSICBRAINZ_RELEASE_URL = (
    "https://musicbrainz.org/ws/2/release"
)

HEADERS = {
    "User-Agent": "TheExperience/0.1.0 (personal-project)"
}

MIN_REQUEST_INTERVAL = 1.0

_last_request_time = 0.0
_request_lock = asyncio.Lock()

_client = httpx.AsyncClient(
    headers=HEADERS,
    timeout=10.0,
)


async def _wait_for_rate_limit() -> None:
    global _last_request_time

    async with _request_lock:
        current_time = time.monotonic()

        wait_time = (
            MIN_REQUEST_INTERVAL
            - (current_time - _last_request_time)
        )

        if wait_time > 0:
            _last_request_time = (
                current_time
                + wait_time
            )
        else:
            _last_request_time = current_time

    if wait_time > 0:
        await asyncio.sleep(wait_time)


async def _request_musicbrainz(
    url: str,
    params: dict,
) -> dict:
    for attempt in range(2):
        await _wait_for_rate_limit()

        start = time.perf_counter()

        try:
            response = await _client.get(
                url,
                params=params,
            )

            elapsed = time.perf_counter() - start

            print(
                f"[TIMING] MusicBrainz request: "
                f"{elapsed:.2f}s"
            )

            if response.status_code == 404:
                return {}

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

    return {}


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

        artist_credit = release_group.get(
            "artist-credit",
            [],
        )

        release_group_artist = normalize_artist(
            artist_credit[0].get("name", "")
            if artist_credit
            else ""
        )

        if release_group_title != normalized_title:
            continue

        if release_group_artist != normalized_artist:
            continue

        if release_group.get(
            "primary-type",
            "",
        ) != "Album":
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


async def find_albums_by_ids(
    lastfm_candidates: list[dict],
) -> dict[str, Album]:
    if not lastfm_candidates:
        return {}

    candidates = [
        album
        for album in lastfm_candidates
        if album.get("id")
    ][:3]

    if not candidates:
        return {}

    start = time.perf_counter()

    results = await asyncio.gather(
        *[
            find_album_by_id(
                album["id"],
                album.get("title", ""),
                album.get("artist", ""),
            )
            for album in candidates
        ],
        return_exceptions=True,
    )

    elapsed = time.perf_counter() - start

    print(
        f"[TIMING] MusicBrainz total: "
        f"{elapsed:.2f}s "
        f"({len(candidates)} candidates)"
    )

    albums = {}

    for candidate, result in zip(
        candidates,
        results,
    ):
        if isinstance(result, Exception):
            continue

        if result:
            albums[candidate["id"]] = result

    return albums



async def find_album_by_id(
    musicbrainz_id: str,
    fallback_title: str = "",
    fallback_artist: str = "",
) -> Album | None:
    params = {
        "inc": "artist-credits+release-groups",
        "fmt": "json",
    }

    url = f"{MUSICBRAINZ_RELEASE_URL}/{musicbrainz_id}"

    data = await _request_musicbrainz(
        url,
        params,
    )

    if not data:
        # Do not perform another MusicBrainz request here.
        #
        # The Last.fm MBID is either invalid or unavailable.
        # We already have the Last.fm title/artist, so returning
        # a lightweight fallback is faster and avoids another
        # rate-limited MusicBrainz request.
        if fallback_title and fallback_artist:
            return Album(
                id=musicbrainz_id,
                title=fallback_title,
                artist=fallback_artist,
            )

        return None

    release_id = data.get(
        "id",
        musicbrainz_id,
    )

    title = data.get(
        "title",
        fallback_title,
    )

    artist_name = fallback_artist

    artist_credit = data.get(
        "artist-credit",
        [],
    )

    if artist_credit:
        artist_name = artist_credit[0].get(
            "name",
            fallback_artist,
        )

    release_date = data.get(
        "date",
        "",
    )

    year = None

    if release_date:
        try:
            year = int(
                release_date[:4]
            )
        except ValueError:
            year = None

    release_group = data.get(
        "release-group",
    )

    if isinstance(
        release_group,
        dict,
    ):
        release_group_id = release_group.get(
            "id"
        )

        first_release_date = (
            release_group.get(
                "first-release-date"
            )
        )

        if first_release_date:
            try:
                year = int(
                    first_release_date[:4]
                )
            except ValueError:
                pass

        if release_group_id:
            return Album(
                id=release_group_id,
                title=title,
                artist=artist_name,
                year=year,
                release_id=release_id,
            )

    return Album(
        id=release_id,
        title=title,
        artist=artist_name,
        year=year,
        release_id=release_id,
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

    data = await _request_musicbrainz(
        MUSICBRAINZ_URL,
        params,
    )

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

    first_release_date = (
        release_group.get(
            "first-release-date"
        )
    )

    year = None

    if first_release_date:
        try:
            year = int(
                first_release_date[:4]
            )
        except ValueError:
            year = None

    release_params = {
        "release-group": release_group_id,
        "fmt": "json",
        "limit": 1,
    }

    release_data = await _request_musicbrainz(
        MUSICBRAINZ_RELEASE_URL,
        release_params,
    )

    releases = release_data.get(
        "releases",
        [],
    )

    release_id = None

    if releases:
        release_id = releases[0].get(
            "id"
        )

    return Album(
        id=release_group_id,
        title=release_group_title,
        artist=artist_name,
        year=year,
        release_id=release_id,
    )
