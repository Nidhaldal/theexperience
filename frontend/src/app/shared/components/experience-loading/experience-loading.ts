import { Component, OnDestroy, OnInit, signal } from '@angular/core';

@Component({
  selector: 'app-experience-loading',
  imports: [],
  templateUrl: './experience-loading.html',
  styleUrl: './experience-loading.css',
})
export class ExperienceLoading implements OnInit, OnDestroy {
  protected readonly messages = [
    'Wait for your experience...',
    'Experiences do take time.',
    'Preparing your atmosphere...',
    'Finding the right colors...',
    'Tuning the experience...',
    'Almost there...',
  ];

  protected readonly message = signal(this.messages[0]);

  private intervalId?: ReturnType<typeof setInterval>;
  private messageIndex = 0;

  ngOnInit(): void {
    this.intervalId = setInterval(() => {
      this.messageIndex =
        (this.messageIndex + 1) % this.messages.length;

      this.message.set(this.messages[this.messageIndex]);
    }, 2200);
  }

  ngOnDestroy(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }
}
