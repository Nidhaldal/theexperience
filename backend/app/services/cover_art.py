import time

import httpx


COVER_ART_URL = (
    "https://coverartarchive.org/release"
)

COVER_ART_TIMEOUT = 4.0

_client = httpx.AsyncClient(
    follow_redirects=True,
    timeout=COVER_ART_TIMEOUT,
)

_cover_cache: dict[
    str,
    tuple[float, str | None],
] = {}

_COVER_CACHE_TTL = 60 * 60


async def get_cover_url(
    musicbrainz_id: str | None,
) -> str | None:
    """
    Fetch the front-cover image URL for a MusicBrainz release.

    Cover Art is intentionally non-fatal:
    if Cover Art Archive is unavailable or slow,
    the album can still be returned without artwork.
    """

    if not musicbrainz_id:
        return None

    # --------------------------------------------------
    # Cache
    # --------------------------------------------------

    cached = _cover_cache.get(
        musicbrainz_id
    )

    if cached:
        cached_at, cover_url = cached

        if (
            time.time() - cached_at
            < _COVER_CACHE_TTL
        ):
            print(
                f"[COVER] cache hit "
                f"release={musicbrainz_id}"
            )

            return cover_url

        del _cover_cache[
            musicbrainz_id
        ]

    # --------------------------------------------------
    # Request
    # --------------------------------------------------

    start = time.perf_counter()

    url = (
        f"{COVER_ART_URL}/"
        f"{musicbrainz_id}"
    )

    try:
        response = await _client.get(
            url
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
          f"[TIMING] Cover Art "
          f"{musicbrainz_id}: "
          f"{elapsed:.2f}s "
          f"status={response.status_code} "
          f"url={response.url}"
)

        print(
          f"[COVER] redirects="
          f"{len(response.history)}"
)

        # --------------------------------------------------
        # No cover exists
        # --------------------------------------------------

        if response.status_code == 404:
            _cover_cache[
                musicbrainz_id
            ] = (
                time.time(),
                None,
            )

            return None

        # --------------------------------------------------
        # Other HTTP errors
        # --------------------------------------------------

        if response.status_code >= 400:
            print(
                f"[COVER] release="
                f"{musicbrainz_id} "
                f"returned HTTP "
                f"{response.status_code}"
            )

            return None

        data = response.json()

        # --------------------------------------------------
        # Find front cover
        # --------------------------------------------------

        for image in data.get(
            "images",
            [],
        ):
            if not image.get(
                "front",
                False,
            ):
                continue

            thumbnails = image.get(
                "thumbnails",
                {},
            )

            cover_url = (
                thumbnails.get("500")
                or thumbnails.get("1200")
                or thumbnails.get("250")
                or thumbnails.get("large")
            )

            _cover_cache[
                musicbrainz_id
            ] = (
                time.time(),
                cover_url,
            )

            return cover_url

        # --------------------------------------------------
        # No front image found
        # --------------------------------------------------

        _cover_cache[
            musicbrainz_id
        ] = (
            time.time(),
            None,
        )

        return None

    except httpx.TimeoutException:
        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[COVER] release="
            f"{musicbrainz_id} "
            f"failed: timeout after "
            f"{elapsed:.2f}s"
        )

        return None

    except httpx.RequestError as exc:
        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[COVER] release="
            f"{musicbrainz_id} "
            f"failed: "
            f"{type(exc).__name__} "
            f"after {elapsed:.2f}s"
        )

        return None

    except ValueError as exc:
        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[COVER] release="
            f"{musicbrainz_id} "
            f"returned invalid JSON "
            f"after {elapsed:.2f}s: "
            f"{exc}"
        )

        return None