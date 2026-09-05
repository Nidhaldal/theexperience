import type { CSSProperties } from 'react'
import type { AlbumPalette } from './colorExtraction'

export type LightingMode =
  | 'atmosphere'
  | 'energy'
  | 'party'

export interface LightingEngineSettings {
  mode: LightingMode
  intensity: number
  motion: number
  ambience: number
  enabled: boolean
}

export function createLightingStyle(
  palette: AlbumPalette | null,
  settings: LightingEngineSettings,
): CSSProperties {
  if (!palette) {
    return {
      '--light-primary': '#ffffff',
      '--light-secondary': '#ffffff',
      '--light-accent': '#ffffff',
      '--ui-primary': '#ffffff',
      '--ui-secondary': '#ffffff',
      '--ui-accent': '#ffffff',

      '--light-primary-rgb': '255, 255, 255',
      '--light-secondary-rgb': '255, 255, 255',
      '--light-accent-rgb': '255, 255, 255',

      '--light-intensity': '0',
      '--light-ambience': '0',
      '--light-motion': '1',

      '--light-primary-opacity': '0',
      '--light-secondary-opacity': '0',
      '--light-accent-opacity': '0',
      '--light-flash-opacity': '0',

      '--light-mode': settings.mode,
    } as CSSProperties
  }

  const intensity = settings.enabled
    ? settings.intensity
    : 0

  const ambience = settings.enabled
    ? settings.ambience
    : 0

  const motion = Math.max(
    settings.motion,
    0.1,
  )

  return {
    '--light-primary': palette.dominant,
    '--light-secondary': palette.secondary,
    '--light-accent': palette.accent,
    '--ui-primary': palette.dominant,
    '--ui-secondary': palette.secondary,
    '--ui-accent': palette.accent,

    '--light-primary-rgb':
      `${palette.dominantRgb.r}, ${palette.dominantRgb.g}, ${palette.dominantRgb.b}`,

    '--light-secondary-rgb':
      `${palette.secondaryRgb.r}, ${palette.secondaryRgb.g}, ${palette.secondaryRgb.b}`,

    '--light-accent-rgb':
      `${palette.accentRgb.r}, ${palette.accentRgb.g}, ${palette.accentRgb.b}`,

    '--light-intensity':
      intensity.toString(),

    '--light-ambience':
      ambience.toString(),

    '--light-motion':
      motion.toString(),

    '--light-primary-opacity':
      (intensity * 1.15).toString(),

    '--light-secondary-opacity':
      (intensity * 0.95).toString(),

    '--light-accent-opacity':
      (intensity * 0.85).toString(),

    '--light-flash-opacity':
      (intensity * 0.65).toString(),

    '--light-mode':
      settings.mode,
  } as CSSProperties
}