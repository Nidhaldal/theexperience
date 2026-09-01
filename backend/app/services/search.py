from app.schemas.album import Album
from app.services.lastfm import (
    get_album_popularity,
    search_albums_lastfm,
)
from app.services.musicbrainz import (
    find_album,
    search_albums,
)
from app.services.normalization import albums_match
from app.services.ranking import rank_albums


async def search_music(query: str) -> list[Album]:
    musicbrainz_albums = await search_albums(query)
    lastfm_albums = await search_albums_lastfm(query)

    candidates = musicbrainz_albums.copy()

    for lastfm_album in lastfm_albums:

        matched_album = None

        for musicbrainz_album in candidates:
            if albums_match(musicbrainz_album, lastfm_album):
                matched_album = musicbrainz_album
                break

        if matched_album:
            matched_album.listeners = lastfm_album["listeners"]
            matched_album.playcount = lastfm_album["playcount"]

        else:
            musicbrainz_album = await find_album(
                title=lastfm_album["title"],
                artist=lastfm_album["artist"],
            )

            if musicbrainz_album:
                musicbrainz_album.listeners = lastfm_album["listeners"]
                musicbrainz_album.playcount = lastfm_album["playcount"]

                candidates.append(musicbrainz_album)

            else:
                candidates.append(
                    Album(
                        id="",
                        title=lastfm_album["title"],
                        artist=lastfm_album["artist"],
                        year=None,
                        listeners=lastfm_album["listeners"],
                        playcount=lastfm_album["playcount"],
                    )
                )

    enriched_albums = []

    for album in candidates:
        try:
            popularity = await get_album_popularity(
                artist=album.artist,
                album=album.title,
            )

            album.listeners = popularity["listeners"]
            album.playcount = popularity["playcount"]

        except Exception:
            pass

        enriched_albums.append(album)

    return rank_albums(enriched_albums, query)
