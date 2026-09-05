import { useMemo, useState } from 'react'
import type { AlbumPalette } from '../utils/colorExtraction'
import {
  createLightingStyle,
  type LightingEngineSettings,
  type LightingMode,
} from '../utils/lightingEngine'

export type { LightingMode }

export interface LightingSettings
  extends LightingEngineSettings {}

const MODE_PRESETS: Record<
  LightingMode,
  Omit<LightingSettings, 'mode' | 'enabled'>
> = {
  atmosphere: {
    intensity: 0.75,
    motion: 0.55,
    ambience: 1.35,
  },

  energy: {
    intensity: 1.1,
    motion: 1.2,
    ambience: 1,
  },

  party: {
    intensity: 1.5,
    motion: 2,
    ambience: 1.25,
  },
}

export function useLighting(
  palette: AlbumPalette | null,
) {
  const [settings, setSettings] =
    useState<LightingSettings>({
      mode: 'atmosphere',
      intensity:
        MODE_PRESETS.atmosphere.intensity,
      motion:
        MODE_PRESETS.atmosphere.motion,
      ambience:
        MODE_PRESETS.atmosphere.ambience,
      enabled: true,
    })

  const lightingStyle = useMemo(
    () =>
      createLightingStyle(
        palette,
        settings,
      ),
    [palette, settings],
  )

  function setMode(mode: LightingMode) {
    const preset = MODE_PRESETS[mode]

    setSettings((current) => ({
      ...current,
      mode,
      intensity: preset.intensity,
      motion: preset.motion,
      ambience: preset.ambience,
    }))
  }

  function setIntensity(value: number) {
    setSettings((current) => ({
      ...current,
      intensity: Math.max(
        0,
        Math.min(value, 1.5),
      ),
    }))
  }

  function setMotion(value: number) {
    setSettings((current) => ({
      ...current,
      motion: Math.max(
        0.1,
        Math.min(value, 2),
      ),
    }))
  }

  function setAmbience(value: number) {
    setSettings((current) => ({
      ...current,
      ambience: Math.max(
        0,
        Math.min(value, 1.5),
      ),
    }))
  }

  function toggleLights() {
    setSettings((current) => ({
      ...current,
      enabled: !current.enabled,
    }))
  }

  return {
    settings,
    lightingStyle,
    setMode,
    setIntensity,
    setMotion,
    setAmbience,
    toggleLights,
  }
}