import type { LightingSettings } from '../hooks/useLighting'
import './ExperienceControls.css'

interface ExperienceControlsProps {
  settings: LightingSettings
  onModeChange: (
    mode: LightingSettings['mode'],
  ) => void
  onToggleLights: () => void
  onIntensityChange: (value: number) => void
  onMotionChange: (value: number) => void
  onAmbienceChange: (value: number) => void
  onClose: () => void
}

function ExperienceControls({
  settings,
  onModeChange,
  onToggleLights,
  onIntensityChange,
  onMotionChange,
  onAmbienceChange,
  onClose,
}: ExperienceControlsProps) {
  return (
    <aside className="experience-controls">
      <div className="experience-controls-header">
        <span>EXPERIENCE</span>

        <button
          type="button"
          className="experience-controls-close"
          onClick={onClose}
          aria-label="Close experience controls"
        >
          ×
        </button>
      </div>

      <div className="experience-controls-modes">
        <button
          type="button"
          className={
            settings.mode === 'atmosphere'
              ? 'experience-mode experience-mode-active'
              : 'experience-mode'
          }
          onClick={() =>
            onModeChange('atmosphere')
          }
        >
          ATMOSPHERE
        </button>

        <button
          type="button"
          className={
            settings.mode === 'energy'
              ? 'experience-mode experience-mode-active'
              : 'experience-mode'
          }
          onClick={() =>
            onModeChange('energy')
          }
        >
          ENERGY
        </button>

        <button
          type="button"
          className={
            settings.mode === 'party'
              ? 'experience-mode experience-mode-active'
              : 'experience-mode'
          }
          onClick={() =>
            onModeChange('party')
          }
        >
          PARTY
        </button>
      </div>

      <div className="experience-controls-status">
        <button
          type="button"
          className={`lights-toggle ${
            settings.enabled
              ? 'lights-toggle-active'
              : ''
          }`}
          onClick={onToggleLights}
          aria-label={
            settings.enabled
              ? 'Turn lights off'
              : 'Turn lights on'
          }
        >
          <span className="lights-toggle-dot" />

          {settings.enabled ? 'ON' : 'OFF'}
        </button>
      </div>

      <div className="experience-control">
        <div className="control-label">
          <span>INTENSITY</span>

          <span>
            {Math.round(
              settings.intensity * 100,
            )}
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="1.5"
          step="0.01"
          value={settings.intensity}
          onChange={(event) =>
            onIntensityChange(
              Number(event.target.value),
            )
          }
        />
      </div>

      <div className="experience-control">
        <div className="control-label">
          <span>MOTION</span>

          <span>
            {Math.round(
              settings.motion * 100,
            )}
          </span>
        </div>

        <input
          type="range"
          min="0.1"
          max="2"
          step="0.01"
          value={settings.motion}
          onChange={(event) =>
            onMotionChange(
              Number(event.target.value),
            )
          }
        />
      </div>

      <div className="experience-control">
        <div className="control-label">
          <span>AMBIENCE</span>

          <span>
            {Math.round(
              settings.ambience * 100,
            )}
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="1.5"
          step="0.01"
          value={settings.ambience}
          onChange={(event) =>
            onAmbienceChange(
              Number(event.target.value),
            )
          }
        />
      </div>
    </aside>
  )
}

export default ExperienceControls
