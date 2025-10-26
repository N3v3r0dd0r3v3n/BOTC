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

  radius = 150;
  
  getSeatStyle(index: number, total: number) {
    if (total === 0) return {};

    const angle = (2 * Math.PI * index) / total;
    const x = this.radius * Math.cos(angle);
    const y = this.radius * Math.sin(angle);

    return {
      position: 'absolute',
      left: `calc(50% + ${x}px)`,
      top: `calc(50% + ${y}px)`,
      transform: 'translate(-50%, -50%)',
    };
  }

}
