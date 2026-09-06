import {
  useEffect,
  useRef,
  useState,
} from 'react'
import { searchAlbums,getAlbumDetails } from '../services/albumApi'
import type { Album } from '../types/album'
import AlbumDetail from './AlbumDetail'
import { useRecentAlbums } from '../hooks/useRecentAlbums'
import './Discovery.css'

type LoadingState =
  | 'welcome'
  | 'searching'
  | 'preparing'
  | null

function ExperienceLoader({
  message,
}: {
  message: string
}) {
  return (
    <div
      className="experience-loader"
      role="status"
      aria-live="polite"
    >
      <div className="experience-loader-orbit">
        <div className="experience-loader-core" />
      </div>

      <p className="experience-loader-message">
        {message}
      </p>
    </div>
  )
}

function Discovery() {
  const [query, setQuery] = useState('')
  const [albums, setAlbums] = useState<Album[]>([])
  const [selectedAlbum, setSelectedAlbum] =
    useState<Album | null>(null)

  const [activeIndex, setActiveIndex] =
    useState(-1)

  const [loadingState, setLoadingState] =
    useState<LoadingState>('welcome')

  const [isTransitioning, setIsTransitioning] =
    useState(false)

  const searchRequestRef = useRef(0)

  const inputRef =
    useRef<HTMLInputElement | null>(null)

  const { recentAlbums, addRecentAlbum } =
    useRecentAlbums()

  /*
   * -------------------------------------------------------
   * INITIAL WELCOME
   * -------------------------------------------------------
   *
   * Gives the application a deliberate entrance instead
   * of immediately throwing the user into the interface.
   */

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLoadingState(null)
    }, 1600)

    return () => clearTimeout(timeout)
  }, [])


  /*
   * -------------------------------------------------------
   * AUTOCOMPLETE
   * -------------------------------------------------------
   */

  useEffect(() => {
    const trimmedQuery = query.trim()

    if (!trimmedQuery) {
      setAlbums([])
      setActiveIndex(-1)

      if (loadingState === 'searching') {
        setLoadingState(null)
      }

      return
    }

    const requestId =
      ++searchRequestRef.current

    setLoadingState('searching')
    setActiveIndex(-1)

    const timeout = setTimeout(async () => {
      try {
        const response = await searchAlbums(
          trimmedQuery,
          true,
        )

        /*
         * Ignore an older request if the user has
         * already typed something newer.
         */
        if (
          requestId !==
          searchRequestRef.current
        ) {
          return
        }

        setAlbums(response.results)
      } catch {
        if (
          requestId !==
          searchRequestRef.current
        ) {
          return
        }

        setAlbums([])
      } finally {
        if (
          requestId ===
          searchRequestRef.current
        ) {
          setLoadingState(null)
        }
      }
    }, 300)

    return () => {
      clearTimeout(timeout)
    }
  }, [query])


  /*
   * -------------------------------------------------------
   * FULL SEARCH
   * -------------------------------------------------------
   */

  async function handleSearch() {
    const trimmedQuery = query.trim()

    if (!trimmedQuery) return

    setLoadingState('searching')
    setAlbums([])
    setActiveIndex(-1)

    try {
      const response = await searchAlbums(
        trimmedQuery,
        false,
      )

      setAlbums(response.results)
    } catch {
      setAlbums([])
    } finally {
      setLoadingState(null)
    }
  }


  /*
   * -------------------------------------------------------
   * SELECT ALBUM
   * -------------------------------------------------------
   */

async function selectAlbum(
  album: Album,
) {
  setLoadingState('preparing')

  setAlbums([])
  setActiveIndex(-1)

  try {
    const fullAlbum =
      await getAlbumDetails(album)

    addRecentAlbum(fullAlbum)

    /*
     * Small transition state gives the
     * experience a deliberate handoff.
     */
    setIsTransitioning(true)

    setTimeout(() => {
      setSelectedAlbum(fullAlbum)
      setLoadingState(null)
      setIsTransitioning(false)
    }, 900)
  } catch {
    addRecentAlbum(album)

    setIsTransitioning(true)

    setTimeout(() => {
      setSelectedAlbum(album)
      setLoadingState(null)
      setIsTransitioning(false)
    }, 900)
  }
}

  /*
   * -------------------------------------------------------
   * KEYBOARD NAVIGATION
   * -------------------------------------------------------
   */

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>,
  ) {
    /*
     * Arrow Down
     */
    if (
      event.key === 'ArrowDown' &&
      albums.length > 0
    ) {
      event.preventDefault()

      setActiveIndex((current) =>
        current < albums.length - 1
          ? current + 1
          : 0,
      )

      return
    }

    /*
     * Arrow Up
     */
    if (
      event.key === 'ArrowUp' &&
      albums.length > 0
    ) {
      event.preventDefault()

      setActiveIndex((current) =>
        current > 0
          ? current - 1
          : albums.length - 1,
      )

      return
    }

    /*
     * Enter
     */
    if (event.key === 'Enter') {
      event.preventDefault()

      if (
        activeIndex >= 0 &&
        albums[activeIndex]
      ) {
        selectAlbum(
          albums[activeIndex],
        )
      } else {
        handleSearch()
      }

      return
    }

    /*
     * Escape
     */
    if (event.key === 'Escape') {
      event.preventDefault()

      setAlbums([])
      setActiveIndex(-1)

      inputRef.current?.blur()
    }
  }


  /*
   * -------------------------------------------------------
   * CLOSE EXPERIENCE
   * -------------------------------------------------------
   */

  function closeAlbum() {
    setSelectedAlbum(null)
    setAlbums([])
    setActiveIndex(-1)
    setQuery('')
    setLoadingState(null)
    setIsTransitioning(false)
  }


  /*
   * -------------------------------------------------------
   * ALBUM EXPERIENCE
   * -------------------------------------------------------
   */

  if (selectedAlbum) {
    return (
      <AlbumDetail
        album={selectedAlbum}
        onClose={closeAlbum}
      />
    )
  }


  /*
   * -------------------------------------------------------
   * LOADING / TRANSITION SCREEN
   * -------------------------------------------------------
   */

  if (
  loadingState === 'welcome' ||
  loadingState === 'preparing' ||
  isTransitioning
) {
    return (
      <section className="discovery discovery-loading">
        <ExperienceLoader
          message={
            isTransitioning
              ? 'PREPARING YOUR EXPERIENCE'
              : 'WELCOME TO THE EXPERIENCE'
          }
        />
      </section>
    )
  }


  /*
   * -------------------------------------------------------
   * DISCOVERY
   * -------------------------------------------------------
   */

  return (
    <section className="discovery">
      <div className="discovery-content">

        <h1>
          Discover an album
        </h1>


        {/* SEARCH */}

        <div className="search">
          <input
            ref={inputRef}
            value={query}
            onChange={(event) =>
              setQuery(
                event.target.value,
              )
            }
            onKeyDown={handleKeyDown}
            placeholder="Search for an album..."
            autoComplete="off"
            aria-label="Search for an album"
            aria-autocomplete="list"
            aria-controls={
              albums.length > 0
                ? 'album-results'
                : undefined
            }
            aria-activedescendant={
              activeIndex >= 0
                ? `album-result-${activeIndex}`
                : undefined
            }
          />

          <button
            type="button"
            onClick={handleSearch}
            aria-label="Search"
            disabled={
              !query.trim() ||
              loadingState ===
                'searching'
            }
          >
            →
          </button>
        </div>


        {/* SEARCH LOADING */}

        {loadingState === 'searching' && (
          <div className="search-status">
            <span className="search-status-loader" />

            <span>
              WAITING FOR YOUR ALBUMS
            </span>
          </div>
        )}


        {/* SEARCH RESULTS */}

        {loadingState === null &&
          albums.length > 0 && (
            <div
              id="album-results"
              className="results"
              role="listbox"
              aria-label="Album suggestions"
            >
              {albums.map(
                (album, index) => (
                  <button
                    key={
                      album.id ||
                      `${album.title}-${album.artist}-${index}`
                    }
                    id={`album-result-${index}`}
                    type="button"
                    role="option"
                    aria-selected={
                      activeIndex ===
                      index
                    }
                    className={`result ${
                      activeIndex ===
                      index
                        ? 'result-active'
                        : ''
                    }`}
                    onMouseEnter={() =>
                      setActiveIndex(
                        index,
                      )
                    }
                    onClick={() =>
                      selectAlbum(
                        album,
                      )
                    }
                  >
                    {album.cover_url ? (
                      <img
                        className="result-cover"
                        src={
                          album.cover_url
                        }
                        alt=""
                      />
                    ) : (
                      <div className="result-cover-placeholder" />
                    )}

                    <span className="result-info">
                      <span className="result-title">
                        {album.title}
                      </span>

                      <span className="result-artist">
                        {album.artist}
                      </span>
                    </span>
                  </button>
                ),
              )}
            </div>
          )}


        {/* RECENT */}

        {!query.trim() &&
          loadingState === null &&
          recentAlbums.length > 0 && (
            <div className="recent">
              <p className="recent-label">
                RECENTLY EXPERIENCED
              </p>

              {recentAlbums.map(
                (album, index) => (
                  <button
                    key={
                      album.id ||
                      `${album.title}-${album.artist}-${index}`
                    }
                    type="button"
                    className="recent-album"
                    onClick={() =>
                      selectAlbum(
                        album,
                      )
                    }
                  >
                    {album.cover_url ? (
                      <img
                        className="recent-cover"
                        src={
                          album.cover_url
                        }
                        alt=""
                      />
                    ) : (
                      <div className="recent-cover-placeholder" />
                    )}

                    <span className="result-info">
                      <span className="result-title">
                        {album.title}
                      </span>

                      <span className="result-artist">
                        {album.artist}
                      </span>
                    </span>
                  </button>
                ),
              )}
            </div>
          )}


        {/* FUTURE RECOMMENDATIONS */}

        {!query.trim() &&
          loadingState === null && (
            <div className="might-like">
              <p className="might-like-label">
                YOU MIGHT ALSO LIKE
              </p>

              <div className="might-like-list">
                {/* Recommendations will be
                    implemented later. */}
              </div>
            </div>
          )}

      </div>
    </section>
  )
}

export default Discovery