import re
import unicodedata

from app.schemas.album import Album


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^\w\s]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_artist(value: str) -> str:
    value = normalize_text(value)

    if value.startswith("the "):
        value = value[4:]

    if value.endswith(" the"):
        value = value[:-4]

    return value.strip()


def albums_match(
    musicbrainz_album: Album,
    lastfm_album: dict,
) -> bool:
    musicbrainz_id = musicbrainz_album.id
    lastfm_id = lastfm_album.get("id", "")

    if musicbrainz_id and lastfm_id:
        if musicbrainz_id == lastfm_id:
            return True

    musicbrainz_title = normalize_text(
        musicbrainz_album.title
    )
    lastfm_title = normalize_text(
        lastfm_album.get("title", "")
    )

    musicbrainz_artist = normalize_artist(
        musicbrainz_album.artist
    )
    lastfm_artist = normalize_artist(
        lastfm_album.get("artist", "")
    )

    if not musicbrainz_title or not lastfm_title:
        return False

    if not musicbrainz_artist or not lastfm_artist:
        return False
   
    return (
        musicbrainz_title == lastfm_title
        and musicbrainz_artist == lastfm_artist
    )
