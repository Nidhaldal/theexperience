from fastapi import APIRouter, Query

from app.schemas.album import AlbumSearchResponse
from app.services.search import search_music

router = APIRouter(
    prefix="/albums",
    tags=["albums"]
)


@router.get(
    "/search",
    response_model=AlbumSearchResponse,
)
async def search(query: str = Query(min_length=1)):
    albums = await search_music(query)

    return {
        "results": albums
    }