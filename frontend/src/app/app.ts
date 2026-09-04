import { Component, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Health } from './services/health';
import { Home } from './home/home';
import { AlbumExperience } from './album-experience/album-experience';
import { AppState } from './core/services/app-state';

@Component({
  imports: [RouterOutlet, Home, AlbumExperience],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('frontend');
  protected readonly backendStatus = signal('Not connected');
  protected readonly appState = inject(AppState);
  private readonly health = inject(Health);

  constructor() {
    this.health.getHealth().subscribe(response => {
      this.backendStatus.set(response.status);
    });
  }
}