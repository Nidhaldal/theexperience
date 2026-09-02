from app.schemas.album import Album
from app.services.cover_art import get_cover_url
from app.services.lastfm import search_albums_lastfm
from app.services.musicbrainz import find_album


async def search_music(query: str) -> list[Album]:
    lastfm_candidates = await search_albums_lastfm(query)

    albums = []

    for lastfm_album in lastfm_candidates:
        title = lastfm_album.get("title", "")
        artist = lastfm_album.get("artist", "")

        if not title or not artist:
            continue

        musicbrainz_album = await find_album(
            title=title,
            artist=artist,
        )

        if musicbrainz_album:
            musicbrainz_album.listeners = lastfm_album.get(
                "listeners",
                0,
            )
            musicbrainz_album.playcount = lastfm_album.get(
                "playcount",
                0,
            )
            musicbrainz_album.cover_url = await get_cover_url(
                musicbrainz_album.id
            )

            albums.append(musicbrainz_album)
            continue

        albums.append(
            Album(
                id="",
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

    return albums
