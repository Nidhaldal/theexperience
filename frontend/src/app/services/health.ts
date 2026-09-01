import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Service()
export class Health {

  private readonly http = inject(HttpClient);

  getHealth(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(
      'http://127.0.0.1:8000/health'
    );
  }
}