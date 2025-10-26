import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { Seat } from '../../models/room.model';
import { MatMenuModule } from '@angular/material/menu';

@Component({
  selector: 'app-seats',
  imports: [
    CommonModule,
    MatIconModule,
    MatMenuModule
  ],
  templateUrl: './seats.html',
  styleUrl: './seats.scss'
})
export class Seats {
isMenuDisabled(_t8: Seat) {
throw new Error('Method not implemented.');
}

  @Input() seats:Seat[] = [];
  @Input() isStoryteller:boolean = false;
  @Output() takeSeat = new EventEmitter<number>();

  seatClass=""

  radius   = 0   // * this.seats.length;  // seat ring radius in px
  seatSize = 80;   // diameter of each chair
  labelGap = 12;    // distance from seat edge to label
  labelPad = 1;    // small margin to keep everything inside


  menu: any;

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

  getRoleFontSize(role: string | undefined): string {
    if (!role) return '12px';
    const len = role.length;
    if (len <= 3) return '13px';
    if (len <= 6) return '11px';
    if (len <= 10) return '9px';
    return '8px';
  }

  ngOnChanges() {
    console.log("Changed")
    this.radius = 150 + (this.seats.length * 7.5)
  }

  sit(seat: Seat) {
    if (this.isStoryteller) {
      return;
    }
    if (!seat.occupant) {
      this.takeSeat.emit(seat.seat)
    }
  }

}
