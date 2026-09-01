# TheExperience

TheExperience is a music discovery application that combines music metadata and popularity data from multiple sources to help users discover albums and artists.

## Tech Stack

### Frontend
- Angular

### Backend
- Python
- FastAPI

### External APIs
- MusicBrainz
- Last.fm

## Current Features

- Album search
- MusicBrainz metadata retrieval
- Last.fm popularity data
- Album matching between APIs
- Result ranking
- REST API built with FastAPI

## Architecture

Angular frontend
        ↓
FastAPI backend
        ↓
Music search service
        ↓
MusicBrainz + Last.fm
        ↓
Merged and ranked results

## Project Status

TheExperience is currently under development.

The current focus is building the backend search and data integration layer before expanding the frontend experience.

## Future Plans

- Album artwork
- Improved matching between music sources
- Improved ranking
- Music discovery interface
- Album and artist pages
- Recommendations
