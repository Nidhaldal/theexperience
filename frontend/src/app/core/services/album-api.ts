import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Album, AlbumSearchResponse } from '../models/album';

@Injectable({
  providedIn: 'root'
})
export class AlbumApi {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8000';

  autocompleteAlbums(query: string) {
    return this.http.get<AlbumSearchResponse>(
      `${this.apiUrl}/albums/search`,
      {
        params: {
          query,
          autocomplete: true
        }
      }
    );
  }

  searchAlbums(query: string) {
    return this.http.get<AlbumSearchResponse>(
      `${this.apiUrl}/albums/search`,
      {
        params: {
          query,
          autocomplete: false
        }
      }
    );
  }
}