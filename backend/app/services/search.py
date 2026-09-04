import asyncio
import time

from app.schemas.album import Album
from app.services.cover_art import get_cover_url
from app.services.lastfm import search_albums_lastfm
from app.services.musicbrainz import find_albums_by_ids


async def search_music(
    query: str,
    autocomplete: bool = True,
) -> list[Album]:

    total_start = time.perf_counter()

    # -------------------------
    # Last.fm
    # -------------------------
    lastfm_start = time.perf_counter()

    lastfm_candidates = await search_albums_lastfm(
        query,
        include_popularity=not autocomplete,
    )

    lastfm_time = (
        time.perf_counter()
        - lastfm_start
    )

    print(
        f"[TIMING] search.py Last.fm: "
        f"{lastfm_time:.2f}s"
    )

    # -------------------------
    # Autocomplete
    #
    # Only return:
    # - title
    # - artist
    # - Last.fm MBID when available
    #
    # No MusicBrainz.
    # No Cover Art.
    # No popularity requests.
    # -------------------------
    if autocomplete:

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            "[TIMING] search.py MusicBrainz: "
            "SKIPPED (autocomplete)"
        )

        print(
            "[TIMING] search.py Cover Art: "
            "SKIPPED (autocomplete)"
        )

        print(
            f"[TIMING] search.py TOTAL: "
            f"{total_time:.2f}s"
        )

        return [
            Album(
                id=album.get("id", ""),
                title=album.get("title", ""),
                artist=album.get("artist", ""),
                listeners=0,
                playcount=0,
            )
            for album in lastfm_candidates
            if album.get("title")
            and album.get("artist")
        ]

    # -------------------------
    # MusicBrainz
    #
    # Real search only.
    # MusicBrainz enriches the
    # Last.fm candidates with:
    # - year
    # - release_id
    # - canonical MBID
    # -------------------------
    musicbrainz_start = time.perf_counter()

    musicbrainz_albums = (
        await find_albums_by_ids(
            lastfm_candidates
        )
    )

    musicbrainz_time = (
        time.perf_counter()
        - musicbrainz_start
    )

    print(
        f"[TIMING] search.py MusicBrainz: "
        f"{musicbrainz_time:.2f}s"
    )

    albums: list[Album] = []

    for lastfm_album in lastfm_candidates:

        title = lastfm_album.get(
            "title",
            "",
        )

        artist = lastfm_album.get(
            "artist",
            "",
        )

        lastfm_id = lastfm_album.get(
            "id",
            "",
        )

        if not title or not artist:
            continue

        # -------------------------
        # MusicBrainz match
        # -------------------------
        musicbrainz_album = (
            musicbrainz_albums.get(
                lastfm_id
            )
        )

        if musicbrainz_album:

            # IMPORTANT:
            # Keep the popularity data
            # obtained from Last.fm.
            musicbrainz_album.listeners = (
                lastfm_album.get(
                    "listeners",
                    0,
                )
            )

            musicbrainz_album.playcount = (
                lastfm_album.get(
                    "playcount",
                    0,
                )
            )

            albums.append(
                musicbrainz_album
            )

        else:

            # No MusicBrainz match.
            # Still return the Last.fm
            # result with its popularity.
            albums.append(
                Album(
                    id=lastfm_id,
                    title=title,
                    artist=artist,
                    listeners=lastfm_album.get(
                        "listeners",
                        0,
                    ),
                    playcount=lastfm_album.get(
                        "playcount",
                        0,
                    ),
                )
            )

    # -------------------------
    # Cover Art
    #
    # Real search only.
    # Fetch covers only for albums
    # that have a MusicBrainz
    # release_id.
    # -------------------------
    cover_start = time.perf_counter()

    cover_targets = [
        album
        for album in albums
        if album.release_id
    ]

    cover_results = await asyncio.gather(
        *[
            get_cover_url(
                album.release_id
            )
            for album in cover_targets
        ],
        return_exceptions=True,
    )

    for album, result in zip(
        cover_targets,
        cover_results,
    ):
        if isinstance(
            result,
            Exception,
        ):
            continue

        album.cover_url = result

    cover_time = (
        time.perf_counter()
        - cover_start
    )

    print(
        f"[TIMING] search.py Cover Art: "
        f"{cover_time:.2f}s"
    )

    # -------------------------
    # Total
    # -------------------------
    total_time = (
        time.perf_counter()
        - total_start
    )

    print(
        f"[TIMING] search.py TOTAL: "
        f"{total_time:.2f}s"
    )

    return albums