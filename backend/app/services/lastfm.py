import asyncio
import os
import time

import httpx
from dotenv import load_dotenv


load_dotenv()

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

LASTFM_SEARCH_LIMIT = 30
LASTFM_RESULT_LIMIT = 6
LASTFM_TIMEOUT = 10.0


async def get_album_popularity(
    title: str,
    artist: str,
) -> tuple[int, int]:
    """
    Fetch listeners and playcount for a specific album.

    This is used when the user opens/selects an album,
    not during autocomplete.
    """

    if not LASTFM_API_KEY:
        return 0, 0

    popularity_params = {
        "method": "album.getInfo",
        "api_key": LASTFM_API_KEY,
        "artist": artist,
        "album": title,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient() as client:

            response = await client.get(
                LASTFM_URL,
                params=popularity_params,
                timeout=LASTFM_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return 0, 0

            album_data = data.get(
                "album",
                {},
            )

            try:
                listeners = int(
                    album_data.get(
                        "listeners",
                        0,
                    )
                )
            except (TypeError, ValueError):
                listeners = 0

            try:
                playcount = int(
                    album_data.get(
                        "playcount",
                        0,
                    )
                )
            except (TypeError, ValueError):
                playcount = 0

            return listeners, playcount

    except httpx.TimeoutException:
        print(
            "[Last.fm] Album popularity request timed out."
        )
        return 0, 0

    except httpx.RequestError as exc:
        print(
            f"[Last.fm] Album popularity request failed: {exc}"
        )
        return 0, 0


async def _get_album_popularity(
    client: httpx.AsyncClient,
    title: str,
    artist: str,
) -> tuple[int, int]:
    """
    Internal version used when fetching popularity
    for multiple search results with a shared client.
    """

    popularity_params = {
        "method": "album.getInfo",
        "api_key": LASTFM_API_KEY,
        "artist": artist,
        "album": title,
        "format": "json",
    }

    response = await client.get(
        LASTFM_URL,
        params=popularity_params,
        timeout=LASTFM_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        return 0, 0

    album_data = data.get(
        "album",
        {},
    )

    try:
        listeners = int(
            album_data.get(
                "listeners",
                0,
            )
        )
    except (TypeError, ValueError):
        listeners = 0

    try:
        playcount = int(
            album_data.get(
                "playcount",
                0,
            )
        )
    except (TypeError, ValueError):
        playcount = 0

    return listeners, playcount


def _score_album(
    album: dict,
    query: str,
    lastfm_position: int,
) -> tuple[int, int]:

    query_normalized = query.strip().casefold()

    title = album.get(
        "title",
        "",
    ).strip().casefold()

    artist = album.get(
        "artist",
        "",
    ).strip().casefold()

    score = 0

    if title == query_normalized:
        if len(query_normalized) <= 3:
            score += 900
        else:
            score += 1200

    elif title.startswith(query_normalized):
        score += 1000

    elif query_normalized in title:
        score += 500

    if artist == query_normalized:
        score += 100

    elif artist.startswith(query_normalized):
        score += 75

    elif query_normalized in artist:
        score += 25

    lastfm_score = max(
        0,
        LASTFM_SEARCH_LIMIT - lastfm_position,
    )

    return score, lastfm_score


def _rank_albums(
    albums: list[dict],
    query: str,
) -> list[dict]:

    scored = []

    for position, album in enumerate(
        albums
    ):
        relevance_score = _score_album(
            album,
            query,
            position,
        )

        scored.append(
            (
                relevance_score,
                position,
                album,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0][0],
            item[0][1],
            -item[1],
        ),
        reverse=True,
    )

    return [
        item[2]
        for item in scored
    ]


async def search_albums_lastfm(
    query: str,
    include_popularity: bool = False,
) -> list[dict]:

    total_start = time.perf_counter()

    search_params = {
        "method": "album.search",
        "api_key": LASTFM_API_KEY,
        "album": query,
        "format": "json",
        "limit": LASTFM_SEARCH_LIMIT,
    }

    try:

        async with httpx.AsyncClient() as client:

            # -------------------------
            # Last.fm search
            # -------------------------

            search_start = time.perf_counter()

            response = await client.get(
                LASTFM_URL,
                params=search_params,
                timeout=LASTFM_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            search_time = (
                time.perf_counter()
                - search_start
            )

            if "error" in data:
                raise RuntimeError(
                    data.get(
                        "message",
                        "Last.fm request failed.",
                    )
                )

            results = data.get(
                "results",
                {},
            ).get(
                "albummatches",
                {},
            ).get(
                "album",
                [],
            )

            valid_albums = []

            for album in results:

                title = album.get(
                    "name",
                    "",
                )

                artist = album.get(
                    "artist",
                    "",
                )

                if not title or not artist:
                    continue

                valid_albums.append(
                    {
                        "id": album.get(
                            "mbid",
                            "",
                        ),
                        "title": title,
                        "artist": artist,
                    }
                )

            # -------------------------
            # Ranking
            # -------------------------

            ranked_albums = _rank_albums(
                valid_albums,
                query,
            )

            selected_albums = ranked_albums[
                :LASTFM_RESULT_LIMIT
            ]

            # -------------------------
            # Popularity
            #
            # Only enabled for a real
            # album search/details flow.
            #
            # Autocomplete remains cheap.
            # -------------------------

            if include_popularity:

                popularity_start = (
                    time.perf_counter()
                )

                popularity_results = (
                    await asyncio.gather(
                        *[
                            _get_album_popularity(
                                client,
                                album["title"],
                                album["artist"],
                            )
                            for album in selected_albums
                        ],
                        return_exceptions=True,
                    )
                )

                popularity_time = (
                    time.perf_counter()
                    - popularity_start
                )

                albums = []

                for album, popularity in zip(
                    selected_albums,
                    popularity_results,
                ):

                    if isinstance(
                        popularity,
                        Exception,
                    ):
                        listeners = 0
                        playcount = 0

                    else:
                        listeners, playcount = (
                            popularity
                        )

                    albums.append(
                        {
                            **album,
                            "listeners": listeners,
                            "playcount": playcount,
                        }
                    )

                selected_albums = albums

                print(
                    f"[TIMING] Last.fm popularity: "
                    f"{popularity_time:.2f}s"
                )

            # -------------------------
            # Timing
            # -------------------------

            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                f"[TIMING] Last.fm search: "
                f"{search_time:.2f}s"
            )

            print(
                f"[TIMING] Last.fm total: "
                f"{total_time:.2f}s"
            )

            return selected_albums

    except httpx.TimeoutException:
        raise RuntimeError(
            "Last.fm request timed out."
        )

    except httpx.RequestError:
        raise RuntimeError(
            "Could not connect to Last.fm."
        )
