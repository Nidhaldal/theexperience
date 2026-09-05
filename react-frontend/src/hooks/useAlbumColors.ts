import { useEffect, useState } from 'react'
import {
  extractColors,
  type AlbumPalette,
} from '../utils/colorExtraction'

export function useAlbumColors(
  imageUrl: string | null,
) {
  const [palette, setPalette] =
    useState<AlbumPalette | null>(null)

  const [isExtracting, setIsExtracting] =
    useState(false)

  useEffect(() => {
    if (!imageUrl) {
      setPalette(null)
      setIsExtracting(false)
      return
    }

    let cancelled = false

    setIsExtracting(true)
    setPalette(null)

    extractColors(imageUrl)
      .then((colors) => {
        if (cancelled) return

        setPalette(colors)
      })
      .catch(() => {
        if (cancelled) return

        setPalette(null)
      })
      .finally(() => {
        if (cancelled) return

        setIsExtracting(false)
      })

    return () => {
      cancelled = true
    }
  }, [imageUrl])

  return {
    palette,
    isExtracting,
  }
}