import httpx
from fastapi import HTTPException


COVER_ART_URL = "https://coverartarchive.org/release-group"


async def get_cover_url(
    musicbrainz_id: str,
) -> str | None:
    url = f"{COVER_ART_URL}/{musicbrainz_id}"

    try:
        async with httpx.AsyncClient(
    follow_redirects=True
) as client:
            response = await client.get(
                url,
                timeout=10.0,
            )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        data = response.json()

        for image in data.get("images", []):
            if not image.get("front", False):
                continue

            if not image.get("approved", False):
                continue

            thumbnails = image.get(
                "thumbnails",
                {},
            )

            cover_url = thumbnails.get("large")

            if cover_url:
                return cover_url

        return None

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Cover Art Archive request timed out.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Cover Art Archive.",
        )
