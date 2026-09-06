import type { Album, AlbumSearchResponse } from '../types/album'

const API_URL = 'http://localhost:8000'

export async function searchAlbums(
  query: string,
  autocomplete = false,
): Promise<AlbumSearchResponse> {
  const response = await fetch(
    `${API_URL}/albums/search?query=${encodeURIComponent(query)}&autocomplete=${autocomplete}`,
  )

  if (!response.ok) {
    throw new Error('Failed to search albums')
  }

  return response.json()
}

export async function getAlbumDetails(
  album: Album,
): Promise<Album> {
  const params = new URLSearchParams({
    title: album.title,
    artist: album.artist,
  })

  if (album.id) {
    params.set(
      'musicbrainz_id',
      album.id,
    )
  }

  const response = await fetch(
    `${API_URL}/albums/details?${params.toString()}`,
  )

  if (!response.ok) {
    throw new Error(
      'Failed to load album details',
    )
  }

  return response.json()
}