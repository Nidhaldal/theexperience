import httpx
from fastapi import HTTPException
import time

COVER_ART_URL = (
    "https://coverartarchive.org/release"
)

_client = httpx.AsyncClient(
    follow_redirects=True,
    timeout=10.0,
)


async def get_cover_url(
    musicbrainz_id: str | None,
) -> str | None:

    if not musicbrainz_id:
        return None

    start = time.perf_counter()

    url = f"{COVER_ART_URL}/{musicbrainz_id}"

    try:
        response = await _client.get(url)

        elapsed = time.perf_counter() - start

        print(
            f"[TIMING] Cover Art "
            f"{musicbrainz_id}: {elapsed:.2f}s"
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        data = response.json()

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

            return (
                thumbnails.get("500")
                or thumbnails.get("1200")
                or thumbnails.get("250")
                or thumbnails.get("large")
            )

        return None

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=(
                "Cover Art Archive request timed out."
            ),
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to Cover Art Archive."
            ),
        )