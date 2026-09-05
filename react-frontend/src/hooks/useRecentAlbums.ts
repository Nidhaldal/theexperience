import { useEffect, useState } from 'react'
import type { Album } from '../types/album'

const STORAGE_KEY = 'theexperience-recent-albums'
const MAX_RECENT = 5

export function useRecentAlbums() {
  const [recentAlbums, setRecentAlbums] = useState<Album[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)

      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(recentAlbums),
    )
  }, [recentAlbums])

  function addRecentAlbum(album: Album) {
    setRecentAlbums((current) => {
      const filtered = current.filter(
        (item) =>
          !(
            item.title.toLowerCase() === album.title.toLowerCase() &&
            item.artist.toLowerCase() === album.artist.toLowerCase()
          ),
      )

      return [album, ...filtered].slice(0, MAX_RECENT)
    })
  }

  return {
    recentAlbums,
    addRecentAlbum,
  }
}
