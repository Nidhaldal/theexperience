import { Component, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Health } from './services/health';

@Component({
  imports: [RouterOutlet],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('frontend');

  protected readonly backendStatus = signal('Not connected');

  private readonly health = inject(Health);

  constructor() {
    this.health.getHealth().subscribe(response => {
      this.backendStatus.set(response.status);
    });
  }
}