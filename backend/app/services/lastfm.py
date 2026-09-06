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

# Reuse one HTTP client so connections can be reused.
LASTFM_CLIENT = httpx.AsyncClient(
    timeout=LASTFM_TIMEOUT,
)

# --------------------------------------------------
# Search cache
# --------------------------------------------------

# query -> (cached_at, results)
_search_cache: dict[
    str,
    tuple[float, list[dict]],
] = {}

_SEARCH_CACHE_TTL = 60 * 5


# --------------------------------------------------
# Popularity cache
# --------------------------------------------------

# (title, artist) -> (cached_at, (listeners, playcount))
_popularity_cache: dict[
    tuple[str, str],
    tuple[float, tuple[int, int]],
] = {}

_POPULARITY_CACHE_TTL = 60 * 15


async def get_album_popularity(
    title: str,
    artist: str,
) -> tuple[int, int]:
    """
    Fetch listeners and playcount for a specific album.

    This is used when the user opens/selects an album,
    not during autocomplete/search.
    """

    if not LASTFM_API_KEY:
        return 0, 0

    cache_key = (
        title.strip().casefold(),
        artist.strip().casefold(),
    )

    cached = _popularity_cache.get(
        cache_key
    )

    if cached:
        cached_at, popularity = cached

        if (
            time.time() - cached_at
            < _POPULARITY_CACHE_TTL
        ):
            print(
                "[Last.fm] popularity cache hit "
                f"album={title} "
                f"artist={artist}"
            )

            return popularity

        del _popularity_cache[
            cache_key
        ]

    popularity_params = {
        "method": "album.getInfo",
        "api_key": LASTFM_API_KEY,
        "artist": artist,
        "album": title,
        "format": "json",
    }

    start = time.perf_counter()

    try:
        response = await LASTFM_CLIENT.get(
            LASTFM_URL,
            params=popularity_params,
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

        popularity = (
            listeners,
            playcount,
        )

        _popularity_cache[
            cache_key
        ] = (
            time.time(),
            popularity,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[TIMING] Last.fm popularity: "
            f"{elapsed:.2f}s"
        )

        return popularity

    except httpx.TimeoutException:
        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[Last.fm] Album popularity request "
            f"timed out after {elapsed:.2f}s"
        )

        return 0, 0

    except httpx.RequestError as exc:
        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[Last.fm] Album popularity request "
            f"failed after {elapsed:.2f}s: {exc}"
        )

        return 0, 0


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

    for position, album in enumerate(albums):
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
) -> list[dict]:
    """
    Search Last.fm for albums.

    This function intentionally performs only the
    album.search request.

    It does NOT:
    - fetch album popularity
    - call MusicBrainz
    - call Cover Art Archive
    """

    total_start = time.perf_counter()

    if not LASTFM_API_KEY:
        raise RuntimeError(
            "LASTFM_API_KEY is not configured."
        )

    # --------------------------------------------------
    # Normalize cache key
    # --------------------------------------------------

    cache_key = query.strip().casefold()

    # --------------------------------------------------
    # Search cache
    # --------------------------------------------------

    cached = _search_cache.get(
        cache_key
    )

    if cached:
        cached_at, results = cached

        if (
            time.time() - cached_at
            < _SEARCH_CACHE_TTL
        ):
            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                f"[Last.fm] search cache hit: "
                f"{query}"
            )

            print(
                f"[TIMING] Last.fm total: "
                f"{total_time:.2f}s"
            )

            return results

        del _search_cache[
            cache_key
        ]

    # --------------------------------------------------
    # Last.fm request
    # --------------------------------------------------

    search_params = {
        "method": "album.search",
        "api_key": LASTFM_API_KEY,
        "album": query,
        "format": "json",
        "limit": LASTFM_SEARCH_LIMIT,
    }

    search_start = time.perf_counter()

    try:
        response = await LASTFM_CLIENT.get(
            LASTFM_URL,
            params=search_params,
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

        # --------------------------------------------------
        # Ranking
        # --------------------------------------------------

        ranked_albums = _rank_albums(
            valid_albums,
            query,
        )

        selected_albums = ranked_albums[
            :LASTFM_RESULT_LIMIT
        ]

        # --------------------------------------------------
        # Store in cache
        # --------------------------------------------------

        _search_cache[
            cache_key
        ] = (
            time.time(),
            selected_albums,
        )

        # --------------------------------------------------
        # Timing
        # --------------------------------------------------

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