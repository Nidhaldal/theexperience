import { Component, inject, signal } from '@angular/core';

import { AppState } from '../core/services/app-state';
import { ExperienceLoading } from '../shared/components/experience-loading/experience-loading';

@Component({
  imports: [ExperienceLoading],
  selector: 'app-album-experience',
  styleUrl: './album-experience.css',
  templateUrl: './album-experience.html',
})
export class AlbumExperience {
  protected readonly appState = inject(AppState);

  protected readonly isLoading = signal(false);
  protected readonly error = signal<string | null>(null);

  protected exit(): void {
    this.appState.clearAlbum();
  }
}
