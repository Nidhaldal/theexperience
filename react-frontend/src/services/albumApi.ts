import type { AlbumSearchResponse } from '../types/album'

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