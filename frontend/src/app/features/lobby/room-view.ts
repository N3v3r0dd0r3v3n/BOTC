import { CommonModule } from '@angular/common';
import { Component, OnInit, signal, Signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { RoomSocketService } from './room-socket.service';
import { Room } from '../../models/room.model';
import { RoomService } from './room.service';
import { first, firstValueFrom } from 'rxjs';
import { StoryTellerSocketService } from './storyteller-socket.service';

@Component({
  standalone: true,
  selector: 'app-room-view',
  imports: [CommonModule],
  templateUrl: './room-view.html',
  styleUrl: './room-view.css',
  // Component-scoped instance so it dies with the page
  providers: [
    RoomSocketService,
    StoryTellerSocketService
  ]
})
export class RoomViewComponent implements OnInit {
  public latest: Signal<any | null> = signal(null);
  public isSeated: boolean = false;

  private isST: boolean = false;

  constructor(
    private readonly spectatorSocket: RoomSocketService,
    private readonly stSocket: StoryTellerSocketService,
    private readonly roomService: RoomService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {
  }

  async ngOnInit(): Promise<void> {
    const gid = this.route.snapshot.paramMap.get('gid') ?? '';
    if (!gid) {
      return;
    }

    const visitor = JSON.parse(localStorage.getItem('visitor') || '{}');
    const response = await firstValueFrom(this.roomService.getRoomDetails(gid));
    this.isST = response?.storyteller_id === visitor?.id;

    console.log(response?.storyteller_id)
    console.log(visitor?.id)

    if (this.isST) {
      this.latest = this.stSocket.latest;
      await this.stSocket.connect(gid);
      this.stSocket.send({ type: 'get_state' }); 
    } else {
      this.latest = this.spectatorSocket.latest;
      await this.spectatorSocket.connect(gid);
      this.spectatorSocket.send({ type: 'get_state' });    // request 
    }

    await firstValueFrom(this.roomService.joinRoom(gid));
    
  }

  hasMinimumPlayers(): boolean {
    if (this.latest().view.players > 4) {
      return false
    } else {
      return true
    }
  }

  setupGame(): void {
    firstValueFrom(this.roomService.startGame(this.getRoom()?.gid))
  }

  sendPing(): void {
    if (this.isST) {
      this.stSocket.send({ type: 'ping', t: Date.now() });
    } else {
      this.spectatorSocket.send({ type: 'ping', t: Date.now() });
    }
  }

  async addChair() {
    const newSeatCount = this.getSeats().length + 1;
    this.updateSeatCount(newSeatCount);
  }

  removeChair() {
    const newSeatCount = this.getSeats().length - 1;
    this.updateSeatCount(newSeatCount);
  }

  sit(seat: number) {
    this.isSeated = true;
    return firstValueFrom(this.roomService.sit(this.getRoom()?.gid, seat))
  }

  vacate(seat: number) {
    this.isSeated = false;
    return firstValueFrom(this.roomService.vacate(this.getRoom()?.gid, seat))
  }

  leave() {
    this.isSeated = false;
    firstValueFrom(this.roomService.leave(this.getRoom()?.gid));
    this.router.navigate(['/lobby']);
  }

  isMySeat(seat: any) {
    const v = JSON.parse(localStorage.getItem('visitor') || '{}');
    return seat.occupant.id == v.id
  }
  
  isStoryTeller(): boolean {
    const v = JSON.parse(localStorage.getItem('visitor') || '{}');
    return !!this.getRoom()?.story_teller_id && this.getRoom().story_teller_id === v?.id;
  }

  private updateSeatCount(seatCount: number) {
    return firstValueFrom(this.roomService.updateSeatCount(this.getRoom()?.gid, seatCount));
  }

  private getRoom() {
    return this.latest().view.room;
  }

  public getSeats() {
    return this.latest().view.seats;
  }
}
