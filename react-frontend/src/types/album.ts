export interface Album {
  id: string
  title: string
  artist: string
  year: number | null
  listeners: number
  playcount: number
  cover_url: string | null
}

export interface AlbumSearchResponse {
  results: Album[]
}