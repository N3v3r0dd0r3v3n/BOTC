import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Spectators } from './spectators';

describe('Spectators', () => {
  let component: Spectators;
  let fixture: ComponentFixture<Spectators>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Spectators]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Spectators);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
