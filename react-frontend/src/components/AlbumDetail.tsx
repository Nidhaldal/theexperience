import { useState ,useRef } from 'react'
import type { Album } from '../types/album'
import { useAlbumColors } from '../hooks/useAlbumColors'
import { useLighting } from '../hooks/useLighting'
import ExperienceControls from './ExperienceControls'
import './AlbumDetail.css'

interface AlbumDetailProps {
  album: Album
  onClose: () => void
}

function AlbumDetail({
  album,
  onClose,
}: AlbumDetailProps) {
  const { palette } = useAlbumColors(
    album.cover_url,
  )

  const {
    settings,
    lightingStyle,
    setMode,
    setIntensity,
    setMotion,
    setAmbience,
    toggleLights,
  } = useLighting(palette)

  const [controlsOpen, setControlsOpen] =
    useState(true)
  const coverRef = useRef<HTMLDivElement>(null)
function handleCoverMouseMove(
  event: React.MouseEvent<HTMLDivElement>,
) {
  const cover = coverRef.current

  if (!cover) return

  const rect = cover.getBoundingClientRect()

  const x =
    (event.clientX - rect.left) / rect.width

  const y =
    (event.clientY - rect.top) / rect.height

  const rotateY = (x - 0.5) * 10
  const rotateX = (0.5 - y) * 10

  cover.style.setProperty(
    '--cover-rotate-x',
    `${rotateX}deg`,
  )

  cover.style.setProperty(
    '--cover-rotate-y',
    `${rotateY}deg`,
  )
}

function handleCoverMouseLeave() {
  const cover = coverRef.current

  if (!cover) return

  cover.style.setProperty(
    '--cover-rotate-x',
    '0deg',
  )

  cover.style.setProperty(
    '--cover-rotate-y',
    '0deg',
  )
}
  return (
    <section
  className={`album-detail album-detail-${settings.mode} album-detail-entering`}
  style={lightingStyle}
>
      <div className="lighting-stage">

        {/* =================================================
            ATMOSPHERIC BASE
            ================================================= */}

        <div className="lighting-field lighting-field-primary" />

        <div className="lighting-field lighting-field-secondary" />

        <div className="lighting-field lighting-field-accent" />

        <div className="lighting-sweep lighting-sweep-one" />

        <div className="lighting-sweep lighting-sweep-two" />

        <div className="lighting-sweep lighting-sweep-three" />

        <div className="lighting-flash" />


        {/* =================================================
            ENERGY — FESTIVAL LIGHTING RIG
            ================================================= */}

        <div className="energy-rig">

          <div className="energy-beam energy-beam-1" />
          <div className="energy-beam energy-beam-2" />
          <div className="energy-beam energy-beam-3" />
          <div className="energy-beam energy-beam-4" />
          <div className="energy-beam energy-beam-5" />
          <div className="energy-beam energy-beam-6" />

          <div className="energy-wash energy-wash-1" />
          <div className="energy-wash energy-wash-2" />

          <div className="energy-hit energy-hit-1" />
          <div className="energy-hit energy-hit-2" />

        </div>


        {/* =================================================
            PARTY — DISCO LIGHTING RIG
            ================================================= */}

        <div className="party-rig">

          <div className="party-beams party-beams-left">
            <span className="party-beam party-beam-1" />
            <span className="party-beam party-beam-2" />
            <span className="party-beam party-beam-3" />
            <span className="party-beam party-beam-4" />
            <span className="party-beam party-beam-5" />
          </div>

          <div className="party-beams party-beams-right">
            <span className="party-beam party-beam-6" />
            <span className="party-beam party-beam-7" />
            <span className="party-beam party-beam-8" />
            <span className="party-beam party-beam-9" />
            <span className="party-beam party-beam-10" />
          </div>

          <div className="party-color-hit party-color-hit-primary" />
          <div className="party-color-hit party-color-hit-secondary" />
          <div className="party-color-hit party-color-hit-accent" />

          <div className="party-strobe party-strobe-1" />
          <div className="party-strobe party-strobe-2" />

          <div className="party-flood party-flood-1" />
          <div className="party-flood party-flood-2" />

        </div>


        {/* =================================================
            FINAL SCREEN LAYERS
            ================================================= */}

        <div className="lighting-vignette" />

      </div>


      {/* =================================================
          ALBUM
          ================================================= */}

      <div className="album-detail-content">

        <div className="album-detail-artwork">

          <button
            type="button"
            className="album-detail-back"
            onClick={onClose}
          >
            ← Back
          </button>

          {album.cover_url && (
            <div
  ref={coverRef}
  className="album-detail-cover-wrap"
  onMouseMove={handleCoverMouseMove}
  onMouseLeave={handleCoverMouseLeave}
>

              <div className="album-detail-cover-glow" />

              <img
                className="album-detail-cover"
                src={album.cover_url}
                alt={album.title}
              />

            </div>
          )}

        </div>


        <div className="album-detail-info">

          <p className="eyebrow">
            ALBUM EXPERIENCE
          </p>
          <div className="experience-status">
  <span className="experience-status-dot" />
  <span>
  {settings.mode.toUpperCase()} · ACTIVE
</span>
</div>

          <h1>{album.title}</h1>

          <h2>{album.artist}</h2>

          {album.year && (
            <p className="album-detail-year">
              {album.year}
            </p>
          )}

          <div className="album-detail-stats">

            <span>
              {album.listeners} listeners
            </span>

            <span>
              {album.playcount} plays
            </span>

          </div>

          {palette && (
  <div className="album-palette">
    <p className="album-palette-label">
      EXTRACTED PALETTE
    </p>

    <div className="album-palette-colors">
      <div className="album-palette-color">
        <span
          className="album-palette-swatch"
          style={{
            background: palette.dominant,
          }}
        />

        <span className="album-palette-value">
          {palette.dominant}
        </span>
      </div>

      <div className="album-palette-color">
        <span
          className="album-palette-swatch"
          style={{
            background: palette.secondary,
          }}
        />

        <span className="album-palette-value">
          {palette.secondary}
        </span>
      </div>

      <div className="album-palette-color">
        <span
          className="album-palette-swatch"
          style={{
            background: palette.accent,
          }}
        />

        <span className="album-palette-value">
          {palette.accent}
        </span>
      </div>
    </div>
  </div>
)}

        </div>

      </div>


      {/* =================================================
          CONTROLS
          ================================================= */}

      {controlsOpen ? (

        <ExperienceControls
          settings={settings}
          onModeChange={setMode}
          onToggleLights={toggleLights}
          onIntensityChange={setIntensity}
          onMotionChange={setMotion}
          onAmbienceChange={setAmbience}
          onClose={() =>
            setControlsOpen(false)
          }
        />

      ) : (

        <button
          type="button"
          className="experience-controls-open"
          onClick={() =>
            setControlsOpen(true)
          }
          aria-label="Open experience controls"
        >
          ✦
        </button>

      )}

    </section>
  )
}

export default AlbumDetail