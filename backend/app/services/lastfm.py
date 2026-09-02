import os

import httpx
from dotenv import load_dotenv


load_dotenv()

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

LASTFM_SEARCH_LIMIT = 6
LASTFM_TIMEOUT = 10.0


async def search_albums_lastfm(query: str) -> list[dict]:
    search_params = {
        "method": "album.search",
        "api_key": LASTFM_API_KEY,
        "album": query,
        "format": "json",
        "limit": LASTFM_SEARCH_LIMIT,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                LASTFM_URL,
                params=search_params,
                timeout=LASTFM_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

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

            albums = []

            for album in results:
                title = album.get("name", "")
                artist = album.get("artist", "")

                if not title or not artist:
                    continue

                popularity_params = {
                    "method": "album.getInfo",
                    "api_key": LASTFM_API_KEY,
                    "artist": artist,
                    "album": title,
                    "format": "json",
                }

                popularity_response = await client.get(
                    LASTFM_URL,
                    params=popularity_params,
                    timeout=LASTFM_TIMEOUT,
                )

                popularity_response.raise_for_status()

                popularity_data = popularity_response.json()

                listeners = 0
                playcount = 0

                if "error" not in popularity_data:
                    album_data = popularity_data.get(
                        "album",
                        {},
                    )

                    listeners = int(
                        album_data.get(
                            "listeners",
                            0,
                        )
                    )

                    playcount = int(
                        album_data.get(
                            "playcount",
                            0,
                        )
                    )

                albums.append(
                    {
                        "id": album.get("mbid", ""),
                        "title": title,
                        "artist": artist,
                        "listeners": listeners,
                        "playcount": playcount,
                    }
                )

            return albums

    except httpx.TimeoutException:
        raise RuntimeError(
            "Last.fm request timed out."
        )

    except httpx.RequestError:
        raise RuntimeError(
            "Could not connect to Last.fm."
        )
