import math

from app.schemas.album import Album


def calculate_score(album: Album, query: str) -> float:
    query = query.lower().strip()
    title = album.title.lower().strip()

    score = 0.0

    if title == query:
        score += 100
    elif query in title:
        score += 50

    if album.listeners > 0:
        score += math.log10(album.listeners) * 10

    if album.playcount > 0:
        score += math.log10(album.playcount) * 5

    return score


def rank_albums(albums: list[Album], query: str) -> list[Album]:
    return sorted(
        albums,
        key=lambda album: calculate_score(album, query),
        reverse=True,
    )