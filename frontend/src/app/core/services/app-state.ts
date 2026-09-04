import { Injectable, signal } from '@angular/core';
import { Album } from '../models/album';

@Injectable({
  providedIn: 'root'
})
export class AppState {
  readonly selectedAlbum = signal<Album | null>(null);

  selectAlbum(album: Album): void {
    this.selectedAlbum.set(album);
  }

  clearAlbum(): void {
    this.selectedAlbum.set(null);
  }
}