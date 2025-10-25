import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StoryTeller } from './story-teller';

describe('StoryTeller', () => {
  let component: StoryTeller;
  let fixture: ComponentFixture<StoryTeller>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StoryTeller]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StoryTeller);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
