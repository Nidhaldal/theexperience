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

    return value


def albums_match(
    musicbrainz_album: Album,
    lastfm_album: dict,
) -> bool:

    musicbrainz_title = normalize_text(musicbrainz_album.title)
    lastfm_title = normalize_text(lastfm_album["title"])

    musicbrainz_artist = normalize_artist(musicbrainz_album.artist)
    lastfm_artist = normalize_artist(lastfm_album["artist"])

    return (
        musicbrainz_title == lastfm_title
        and musicbrainz_artist == lastfm_artist
    )
