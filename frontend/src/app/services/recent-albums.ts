import { Injectable } from '@angular/core';
import { Album } from '../core/models/album';

@Injectable({
  providedIn: 'root',
})
export class RecentAlbums {
  private readonly storageKey = 'theexperience-recent-albums';
  private readonly maxAlbums = 5;

  getAlbums(): Album[] {
    const stored = localStorage.getItem(this.storageKey);

    if (!stored) {
      return [];
    }

    try {
      return JSON.parse(stored) as Album[];
    } catch {
      return [];
    }
  }

  addAlbum(album: Album): void {
    const albums = this.getAlbums().filter(
      (item) => item.id !== album.id,
    );

    albums.unshift(album);

    localStorage.setItem(
      this.storageKey,
      JSON.stringify(albums.slice(0, this.maxAlbums)),
    );
  }
}
