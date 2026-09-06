from fastapi import APIRouter, Query

from app.schemas.album import AlbumSearchResponse,Album
from app.services.search import (
    get_album_details,
    search_music,
)

router = APIRouter(
    prefix="/albums",
    tags=["albums"],
)


@router.get(
    "/search",
    response_model=AlbumSearchResponse,
)
async def search(
    query: str = Query(min_length=1),
    autocomplete: bool = Query(True),
):
    albums = await search_music(
        query=query,
        autocomplete=autocomplete,
    )

    return {
        "results": albums
    }
    
@router.get(
    "/details",
    response_model=Album,
)
async def album_details(
    title: str = Query(min_length=1),
    artist: str = Query(min_length=1),
    musicbrainz_id: str | None = None,
):
    album = await get_album_details(
        title=title,
        artist=artist,
        musicbrainz_id=musicbrainz_id,
    )

    return album