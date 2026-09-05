export interface AlbumPalette {
  dominant: string
  secondary: string
  accent: string

  dominantRgb: RGB
  secondaryRgb: RGB
  accentRgb: RGB
}

interface RGB {
  r: number
  g: number
  b: number
}

export function extractColors(
  imageUrl: string,
): Promise<AlbumPalette> {
  return new Promise((resolve, reject) => {
    const image = new Image()

    image.crossOrigin = 'anonymous'

    image.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        const context = canvas.getContext('2d')

        if (!context) {
          reject(new Error('Canvas context unavailable'))
          return
        }

        const size = 100

        canvas.width = size
        canvas.height = size

        context.drawImage(image, 0, 0, size, size)

        const { data } = context.getImageData(
          0,
          0,
          size,
          size,
        )

        const colors: RGB[] = []

        // Sample every 16th pixel to keep extraction lightweight.
        for (let i = 0; i < data.length; i += 16) {
          const r = data[i]
          const g = data[i + 1]
          const b = data[i + 2]
          const alpha = data[i + 3]

          if (alpha < 128) continue

          // Ignore extremely dark pixels.
          if (r + g + b < 30) continue

          colors.push({ r, g, b })
        }

        if (colors.length === 0) {
          reject(new Error('No colors extracted'))
          return
        }

        const palette = buildPalette(colors)

        resolve(palette)
      } catch {
        reject(
          new Error('Unable to extract image colors'),
        )
      }
    }

    image.onerror = () => {
      reject(
        new Error('Unable to load image for color extraction'),
      )
    }

    image.src = imageUrl
  })
}

function buildPalette(colors: RGB[]): AlbumPalette {
  const buckets = new Map<
    string,
    {
      color: RGB
      count: number
    }
  >()

  /*
   * Reduce each RGB channel to 8 levels.
   *
   * This groups visually similar colors together.
   */
  for (const color of colors) {
    const r = Math.floor(color.r / 32)
    const g = Math.floor(color.g / 32)
    const b = Math.floor(color.b / 32)

    const key = `${r}-${g}-${b}`

    const existing = buckets.get(key)

    if (existing) {
      existing.count += 1
    } else {
      buckets.set(key, {
        color: {
          r: Math.min(r * 32 + 16, 255),
          g: Math.min(g * 32 + 16, 255),
          b: Math.min(b * 32 + 16, 255),
        },
        count: 1,
      })
    }
  }

  const ranked = Array.from(buckets.values())
    .sort((a, b) => b.count - a.count)

  const dominant = ranked[0]?.color ?? colors[0]

  /*
   * Find a secondary color that is meaningfully
   * different from the dominant color.
   */
  const secondary =
    ranked.find(
      (item) =>
        colorDistance(item.color, dominant) > 55,
    )?.color ?? createVariation(dominant, -30)

  /*
   * Find an accent that differs even more from
   * the dominant color.
   */
  const accent =
    ranked.find(
      (item) =>
        colorDistance(item.color, dominant) > 90 &&
        colorDistance(item.color, secondary) > 45,
    )?.color ?? createVariation(dominant, 45)

  return {
    dominant: rgbToHex(dominant),
    secondary: rgbToHex(secondary),
    accent: rgbToHex(accent),

    dominantRgb: dominant,
    secondaryRgb: secondary,
    accentRgb: accent,
  }
}

function colorDistance(
  first: RGB,
  second: RGB,
): number {
  const red = first.r - second.r
  const green = first.g - second.g
  const blue = first.b - second.b

  return Math.sqrt(
    red * red +
      green * green +
      blue * blue,
  )
}

function createVariation(
  color: RGB,
  amount: number,
): RGB {
  return {
    r: clamp(color.r + amount),
    g: clamp(color.g + amount),
    b: clamp(color.b + amount),
  }
}

function clamp(value: number): number {
  return Math.min(255, Math.max(0, value))
}

function rgbToHex(color: RGB): string {
  return (
    '#' +
    [color.r, color.g, color.b]
      .map((value) =>
        value.toString(16).padStart(2, '0'),
      )
      .join('')
  )
}