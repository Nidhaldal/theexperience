import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AlbumExperience } from './album-experience';

describe('AlbumExperience', () => {
  let component: AlbumExperience;
  let fixture: ComponentFixture<AlbumExperience>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumExperience],
    }).compileComponents();

    fixture = TestBed.createComponent(AlbumExperience);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
