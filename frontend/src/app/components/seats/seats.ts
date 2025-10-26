import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { Seat } from '../../models/room.model';

@Component({
  selector: 'app-seats',
  imports: [
    CommonModule,
    MatIconModule
  ],
  templateUrl: './seats.html',
  styleUrl: './seats.scss'
})
export class Seats {
  @Input() seats:Seat[] = [];
  @Input() isStoryteller:boolean = false;
  seatClass=""

}
