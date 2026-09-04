import { Component, DestroyRef, inject, signal } from '@angular/core'
import { takeUntilDestroyed } from '@angular/core/rxjs-interop'
import { FormControl, ReactiveFormsModule } from '@angular/forms'
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  filter,
  finalize,
  of,
  Subject,
  switchMap,
  tap,
} from 'rxjs'
import { Album, AlbumSearchResponse } from '../../core/models/album'
import { AlbumApi } from '../../core/services/album-api'
import { AppState } from '../../core/services/app-state'

@Component({
  imports: [ReactiveFormsModule],
  selector: 'app-search',
  styleUrl: './search.css',
  templateUrl: './search.html',
})
export class Search {
  private readonly albumApi = inject(AlbumApi)
  private readonly appState = inject(AppState)
  private readonly destroyRef = inject(DestroyRef)

  protected readonly query = new FormControl('', {
    nonNullable: true,
  })

  protected readonly albums = signal<Album[]>([])
  protected readonly suggestions = signal<Album[]>([])
  protected readonly isLoading = signal(false)
  protected readonly error = signal<string | null>(null)

  private readonly searchRequests$ = new Subject<string>()

  constructor() {
    this.query.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        filter((query) => query.trim().length >= 2),
        tap(() => {
          this.isLoading.set(true)
          this.error.set(null)
        }),
        switchMap((query) =>
          this.albumApi.autocompleteAlbums(query.trim()).pipe(
            catchError(() => {
              this.error.set(
                'Unable to retrieve album suggestions.',
              )
              return of({
                results: [],
              } as AlbumSearchResponse)
            }),
            finalize(() => {
              this.isLoading.set(false)
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (response: AlbumSearchResponse) => {
          this.suggestions.set(
            response.results.slice(0, 6),
          )
        },
      })

    this.searchRequests$
      .pipe(
        filter((query) => query.length > 0),
        tap(() => {
          this.isLoading.set(true)
          this.error.set(null)
        }),
        switchMap((query) =>
          this.albumApi.searchAlbums(query).pipe(
            catchError(() => {
              this.error.set(
                'Unable to complete the search.',
              )
              return of({
                results: [],
              } as AlbumSearchResponse)
            }),
            finalize(() => {
              this.isLoading.set(false)
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (response: AlbumSearchResponse) => {
          this.albums.set(response.results)
        },
      })
  }

  selectAlbum(album: Album): void {
    this.appState.selectAlbum(album)
    this.query.setValue(album.title, {
      emitEvent: false,
    })
    this.suggestions.set([])
    this.error.set(null)
  }

  search(): void {
    const query = this.query.value.trim()

    if (!query) {
      return
    }

    this.suggestions.set([])
    this.error.set(null)
    this.searchRequests$.next(query)
  }
}
