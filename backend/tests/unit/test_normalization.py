import pytest
from app.schemas.album import Album
from app.services.normalization import albums_match
from app.services.normalization import normalize_artist, normalize_text


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("Hello World", "hello world"),
        ("  Hello   World  ", "hello world"),
        ("Héllo Wörld", "hello world"),
        ("Hello, World!", "hello world"),
        ("HELLO WORLD", "hello world"),
        ("Rock & Roll", "rock roll"),
    ],
)
def test_normalize_text(input_value, expected):
    assert normalize_text(input_value) == expected


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("The Beatles", "beatles"),
        ("the Beatles", "beatles"),
        ("Beatles", "beatles"),
        ("Beatles The", "beatles"),
        ("The Rolling Stones", "rolling stones"),
        ("  The Rolling Stones  ", "rolling stones"),
    ],
)
def test_normalize_artist(input_value, expected):
    assert normalize_artist(input_value) == expected


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("", ""),
        ("!!!", ""),
        ("   ", ""),
        ("Hello     World", "hello world"),
        ("Café del Mar", "cafe del mar"),
        ("Beyoncé", "beyonce"),
    ],
)
def test_normalize_text_edge_cases(input_value, expected):
    assert normalize_text(input_value) == expected


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("", ""),
        ("The", "the"),
        ("THE", "the"),
        ("The The", "the"),
        ("The Beyoncé", "beyonce"),
        ("Beyoncé The", "beyonce"),
    ],
)
def test_normalize_artist_edge_cases(input_value, expected):
    assert normalize_artist(input_value) == expected


def test_albums_match_returns_true_when_ids_match():
    musicbrainz_album = Album(
        id="same-id",
        title="Thriller",
        artist="Michael Jackson",
    )

    lastfm_album = {
        "id": "same-id",
        "title": "Completely Different",
        "artist": "Completely Different",
    }

    assert albums_match(
        musicbrainz_album,
        lastfm_album,
    ) is True


def test_albums_match_falls_back_to_title_and_artist_when_ids_differ():
    musicbrainz_album = Album(
        id="mb-id",
        title="The Wall",
        artist="Pink Floyd",
    )

    lastfm_album = {
        "id": "lastfm-id",
        "title": "The Wall",
        "artist": "The Pink Floyd",
    }

    assert albums_match(
        musicbrainz_album,
        lastfm_album,
    ) is True


def test_albums_match_returns_false_when_title_is_missing():
    musicbrainz_album = Album(
        id="mb-id",
        title="The Wall",
        artist="Pink Floyd",
    )

    lastfm_album = {
        "id": "lastfm-id",
        "title": "",
        "artist": "Pink Floyd",
    }

    assert albums_match(
        musicbrainz_album,
        lastfm_album,
    ) is False


def test_albums_match_returns_false_when_artist_is_missing():
    musicbrainz_album = Album(
        id="mb-id",
        title="The Wall",
        artist="Pink Floyd",
    )

    lastfm_album = {
        "id": "lastfm-id",
        "title": "The Wall",
        "artist": "",
    }

    assert albums_match(
        musicbrainz_album,
        lastfm_album,
    ) is False


def test_albums_match_returns_false_when_title_does_not_match():
    musicbrainz_album = Album(
        id="mb-id",
        title="The Wall",
        artist="Pink Floyd",
    )

    lastfm_album = {
        "id": "lastfm-id",
        "title": "Animals",
        "artist": "Pink Floyd",
    }

    assert albums_match(
        musicbrainz_album,
        lastfm_album,
    ) is False


def test_albums_match_returns_false_when_artist_does_not_match():
    musicbrainz_album = Album(
        id="mb-id",
        title="The Wall",
        artist="Pink Floyd",
    )

    lastfm_album = {
        "id": "lastfm-id",
        "title": "The Wall",
        "artist": "David Bowie",
    }

    assert albums_match(
        musicbrainz_album,
        lastfm_album,
    ) is False