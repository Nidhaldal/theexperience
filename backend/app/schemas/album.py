from pydantic import BaseModel


class Album(BaseModel):
    id: str
    title: str
    artist: str
    year: int | None = None
    listeners: int = 0
    playcount: int = 0
    cover_url: str | None = None

    
    

class AlbumSearchResponse(BaseModel):
    results: list[Album]