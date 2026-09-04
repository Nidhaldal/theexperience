import { TestBed } from '@angular/core/testing';
import { AlbumApi } from './album-api';

describe('AlbumApi', () => {
  let service: AlbumApi;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AlbumApi);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
