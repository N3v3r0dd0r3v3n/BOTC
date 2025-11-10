import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NightRotaDialog } from './night-rota-dialog';

describe('SelectionDialog', () => {
  let component: NightRotaDialog;
  let fixture: ComponentFixture<NightRotaDialog>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NightRotaDialog]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NightRotaDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
