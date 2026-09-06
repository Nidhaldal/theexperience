import asyncio
import time

from app.schemas.album import Album
from app.services.cover_art import get_cover_url
from app.services.lastfm import (
    get_album_popularity,
    search_albums_lastfm,
)
from app.services.musicbrainz import find_album_by_id, find_album


async def search_music(
    query: str,
    autocomplete: bool = True,
) -> list[Album]:
    """
    Lightweight album search.

    This function intentionally does only Last.fm search.
    It does not call MusicBrainz, Cover Art Archive,
    or Last.fm popularity.
    """

    total_start = time.perf_counter()

    lastfm_start = time.perf_counter()

    lastfm_candidates = await search_albums_lastfm(
        query,
    )

    lastfm_time = (
        time.perf_counter()
        - lastfm_start
    )

    print(
        f"[TIMING] search.py Last.fm: "
        f"{lastfm_time:.2f}s"
    )

    albums = [
        Album(
            id=album.get(
                "id",
                "",
            ),
            title=album.get(
                "title",
                "",
            ),
            artist=album.get(
                "artist",
                "",
            ),
            listeners=album.get(
                "listeners",
                0,
            ),
            playcount=album.get(
                "playcount",
                0,
            ),
        )
        for album in lastfm_candidates
        if album.get("title")
        and album.get("artist")
    ]

    total_time = (
        time.perf_counter()
        - total_start
    )

    print(
        f"[TIMING] search.py TOTAL: "
        f"{total_time:.2f}s"
    )

    return albums


async def get_album_details(
    title: str,
    artist: str,
    musicbrainz_id: str | None = None,
) -> Album:
    """
    Build the complete album experience for ONE album.

    Flow:

        Last.fm popularity
              +
        MusicBrainz resolution
              ↓
        Cover Art Archive
              ↓
        complete Album
    """

    total_start = time.perf_counter()

    # --------------------------------------------------
    # Last.fm popularity and MusicBrainz can start
    # independently, so run them concurrently.
    # --------------------------------------------------

    lastfm_start = time.perf_counter()

    popularity_task = asyncio.create_task(
        get_album_popularity(
            title,
            artist,
        )
    )

    # If Last.fm gave us a MusicBrainz ID, use it
    # directly. That avoids a MusicBrainz search.
    if musicbrainz_id:
        musicbrainz_task = asyncio.create_task(
            find_album_by_id(
                musicbrainz_id,
                title,
                artist,
            )
        )
    else:
        # Fallback when Last.fm did not provide an MBID.
        musicbrainz_task = asyncio.create_task(
            find_album(
                title,
                artist,
            )
        )

    (
        popularity_result,
        musicbrainz_album,
    ) = await asyncio.gather(
        popularity_task,
        musicbrainz_task,
    )

    listeners, playcount = popularity_result

    lastfm_time = (
        time.perf_counter()
        - lastfm_start
    )

    print(
        f"[TIMING] search.py Last.fm popularity: "
        f"{lastfm_time:.2f}s"
    )

    # --------------------------------------------------
    # MusicBrainz result
    # --------------------------------------------------

    if musicbrainz_album is None:
        print(
            "[TIMING] search.py MusicBrainz: "
            "no match"
        )

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            f"[TIMING] search.py TOTAL: "
            f"{total_time:.2f}s"
        )

        return Album(
            id=musicbrainz_id or "",
            title=title,
            artist=artist,
            listeners=listeners,
            playcount=playcount,
        )

    print(
        "[TIMING] search.py MusicBrainz: "
        "resolved"
    )

    # --------------------------------------------------
    # Cover Art
    #
    # Cover Art Archive needs the MusicBrainz
    # release ID, so this must happen after
    # MusicBrainz resolution.
    # --------------------------------------------------

    cover_start = time.perf_counter()

    cover_url = await get_cover_url(
        musicbrainz_album.release_id
        or musicbrainz_album.id
    )

    cover_time = (
        time.perf_counter()
        - cover_start
    )

    print(
        f"[TIMING] search.py Cover Art: "
        f"{cover_time:.2f}s"
    )

    # --------------------------------------------------
    # Build final album
    # --------------------------------------------------

    final_album = Album(
        id=musicbrainz_album.id,
        title=musicbrainz_album.title,
        artist=musicbrainz_album.artist,
        year=musicbrainz_album.year,
        listeners=listeners,
        playcount=playcount,
        cover_url=cover_url,
        release_id=musicbrainz_album.release_id,
    )

    # --------------------------------------------------
    # Total
    # --------------------------------------------------

    total_time = (
        time.perf_counter()
        - total_start
    )

    print(
        f"[TIMING] search.py TOTAL: "
        f"{total_time:.2f}s"
    )

    return final_album