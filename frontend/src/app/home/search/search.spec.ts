import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { Search } from './search';
import { AlbumApi } from '../../core/services/album-api';
import { AppState } from '../../core/services/app-state';
import { Album } from '../../core/models/album';

describe('Search', () => {
  let component: Search;
  let fixture: ComponentFixture<Search>;

  const album: Album = {
    id: '1',
    title: 'Illmatic',
    artist: 'Nas',
    year: 1994,
    listeners: 1000,
    playcount: 5000,
    cover_url: 'https://example.com/illmatic.jpg',
  };

  const secondAlbum: Album = {
    id: '2',
    title: 'Stillmatic',
    artist: 'Nas',
    year: 2001,
    listeners: 2000,
    playcount: 6000,
    cover_url: 'https://example.com/stillmatic.jpg',
  };

  const albumApiMock = {
    autocompleteAlbums: vi.fn(),
    searchAlbums: vi.fn(),
  };

  const appStateMock = {
    selectedAlbum: signal<Album | null>(null),
    selectAlbum: vi.fn(),
    clearAlbum: vi.fn(),
  };

  beforeEach(async () => {
    albumApiMock.autocompleteAlbums.mockReset();
    albumApiMock.searchAlbums.mockReset();
    appStateMock.selectAlbum.mockReset();

    albumApiMock.autocompleteAlbums.mockReturnValue(
      of({
        results: [album, secondAlbum],
      }),
    );

    albumApiMock.searchAlbums.mockReturnValue(
      of({
        results: [album, secondAlbum],
      }),
    );

    await TestBed.configureTestingModule({
      imports: [Search],
      providers: [
        {
          provide: AlbumApi,
          useValue: albumApiMock,
        },
        {
          provide: AppState,
          useValue: appStateMock,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Search);
    component = fixture.componentInstance;

    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with empty results and suggestions', () => {
    expect(component['albums']()).toEqual([]);
    expect(component['suggestions']()).toEqual([]);
    expect(component['isLoading']()).toBeFalsy();
    expect(component['error']()).toBeNull();
  });

  it('should autocomplete after the debounce period', async () => {
    vi.useFakeTimers();

    component['query'].setValue('ill');

    expect(
      albumApiMock.autocompleteAlbums,
    ).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(299);

    expect(
      albumApiMock.autocompleteAlbums,
    ).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);

    expect(
      albumApiMock.autocompleteAlbums,
    ).toHaveBeenCalledWith('ill');

    expect(component['suggestions']()).toEqual([
      album,
      secondAlbum,
    ]);
  });

  it('should not autocomplete queries shorter than two characters', async () => {
    vi.useFakeTimers();

    component['query'].setValue('i');

    await vi.advanceTimersByTimeAsync(300);

    expect(
      albumApiMock.autocompleteAlbums,
    ).not.toHaveBeenCalled();
  });

  it('should limit autocomplete suggestions to six albums', async () => {
    vi.useFakeTimers();

    const albums = Array.from(
      { length: 8 },
      (_, index) => ({
        ...album,
        id: String(index),
      }),
    );

    albumApiMock.autocompleteAlbums.mockReturnValue(
      of({
        results: albums,
      }),
    );

    component['query'].setValue('ill');

    await vi.advanceTimersByTimeAsync(300);

    expect(component['suggestions']().length).toBe(6);
  });

  it('should handle autocomplete errors', async () => {
    vi.useFakeTimers();

    albumApiMock.autocompleteAlbums.mockReturnValue(
      throwError(() => new Error('API error')),
    );

    component['query'].setValue('ill');

    await vi.advanceTimersByTimeAsync(300);

    expect(component['suggestions']()).toEqual([]);

    expect(component['error']()).toBe(
      'Unable to retrieve album suggestions.',
    );
  });

  it('should perform a full search', () => {
    component['query'].setValue('illmatic');

    component.search();

    expect(
      albumApiMock.searchAlbums,
    ).toHaveBeenCalledWith('illmatic');

    expect(component['albums']()).toEqual([
      album,
      secondAlbum,
    ]);
  });

  it('should trim the query before a full search', () => {
    component['query'].setValue('  illmatic  ');

    component.search();

    expect(
      albumApiMock.searchAlbums,
    ).toHaveBeenCalledWith('illmatic');
  });

  it('should not search when the query is empty', () => {
    component['query'].setValue('   ');

    component.search();

    expect(
      albumApiMock.searchAlbums,
    ).not.toHaveBeenCalled();
  });

  it('should handle full search errors', () => {
    albumApiMock.searchAlbums.mockReturnValue(
      throwError(() => new Error('API error')),
    );

    component['query'].setValue('illmatic');

    component.search();

    expect(component['albums']()).toEqual([]);

    expect(component['error']()).toBe(
      'Unable to complete the search.',
    );
  });

  it('should select an album', () => {
    component.selectAlbum(album);

    expect(
      appStateMock.selectAlbum,
    ).toHaveBeenCalledWith(album);

    expect(component['query'].value).toBe('Illmatic');

    expect(component['suggestions']()).toEqual([]);

    expect(component['error']()).toBeNull();
  });
});

