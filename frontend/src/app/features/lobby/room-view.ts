import { CommonModule } from '@angular/common';
import { Component, OnInit, Signal, signal, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { SpectatorSocketService } from './spectator-socket.service';
import { StoryTellerSocketService } from './storyteller-socket.service';
import { RoomService } from './room.service';
import { PlayerSocketService } from './player-socket.service';

@Component({
  standalone: true,
  selector: 'app-room-view',
  imports: [CommonModule],
  templateUrl: './room-view.html',
  styleUrl: './room-view.css',
  providers: [
    SpectatorSocketService, 
    StoryTellerSocketService,
    PlayerSocketService]
})
export class RoomViewComponent implements OnInit {
  // PUBLIC so the template can call latest()
  public latest: Signal<any | null> = signal<any | null>(null);
  public room = "Hello room"

  public isSeated = false;
  private isST = false;

  constructor(
    private readonly spectatorSocket: SpectatorSocketService,
    private readonly playerSocket: PlayerSocketService,
    private readonly stSocket: StoryTellerSocketService,
    private readonly roomService: RoomService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly cd: ChangeDetectorRef,
  ) {}

  async ngOnInit(): Promise<void> {
    const gid = this.route.snapshot.paramMap.get('gid') ?? '';
    if (!gid) return;

    
    const meta = await firstValueFrom(this.roomService.getRoomDetails(gid));
    this.isST = meta?.storyteller_id === this.myId();

    this.latest = this.isST ? this.stSocket.latest : this.spectatorSocket.latest;

    // Make sure the template notices the new signal reference immediately
    this.cd.detectChanges();

    if (this.isST) {
      await this.stSocket.connect(gid);        
    } else {
      await this.spectatorSocket.connect(gid); 
    }

    await firstValueFrom(this.roomService.joinRoom(gid));

    //Change-detection nudge in case the first push raced the binding
    this.cd.detectChanges();
  }

  hasMinimumPlayers(): boolean {
    const players = this.latest()?.view?.players ?? [];
    return players.length < 5;
  }

  setupGame(): void {
    const gid = this.latest()?.view?.room?.gid;
    if (gid) void firstValueFrom(this.roomService.startGame(gid));
  }

  sendPing(): void {
    const payload = { type: 'ping', t: Date.now() };
    if (this.isST) this.stSocket.send(payload);
    else this.spectatorSocket.send(payload);
  }

  async addChair() {
    const seats = this.getSeats();
    this.updateSeatCount(seats.length + 1);
  }

  removeChair() {
    const seats = this.getSeats();
    this.updateSeatCount(seats.length - 1);
  }

  async sit(seat: number) {
    if (this.isST) {
      return;
    }
    this.isSeated = true;
    const roomId = this.roomId();

    await firstValueFrom(this.roomService.sit(roomId, seat));

    // close viewer socket before connecting as player
    this.spectatorSocket.close();

    if (this.myId != null) {
      await this.playerSocket.connect(roomId, this.myId());
      this.latest = this.playerSocket.latest;
      this.cd.detectChanges();
    }

    return Promise.resolve();
  }

  async vacate(seat: number) {
    if (this.isST) {
      return;
    }
    this.isSeated = false;
    const roomId = this.roomId();
    
    await firstValueFrom(this.roomService.vacate(roomId, seat));

    // close player socket before switching back
    
    this.playerSocket.close();

    if (this.myId != null) {
      await this.spectatorSocket.connect(roomId);  // reopen viewer
      this.latest = this.spectatorSocket.latest;
      this.cd.detectChanges();
    }
    return Promise.resolve();
  }

  leave() {
    this.isSeated = false;
    const gid = this.latest()?.view?.room?.gid;
    if (gid) void firstValueFrom(this.roomService.leave(gid));
    this.router.navigate(['/lobby']);
  }

  isMySeat(seat: any) {
    const v = safeParse(localStorage.getItem('visitor') || '{}') || {};
    return seat?.occupant?.id === v.id;
  }

  isStoryTeller(): boolean {
    const v = safeParse(localStorage.getItem('visitor') || '{}') || {};
    const roomSt = this.latest()?.view?.room?.story_teller_id ?? this.latest()?.view?.room?.storyteller_id;
    return !!roomSt && roomSt === v?.id;
  }

  private updateSeatCount(seatCount: number) {
    const gid = this.latest()?.view?.room?.gid;
    if (gid) return firstValueFrom(this.roomService.updateSeatCount(gid, seatCount));
    return Promise.resolve();
  }

  private myId() {
    const visitor = safeParse(localStorage.getItem('visitor') || '{}') || {};
    return visitor.id;
  }

  private roomId() {
    return this.getRoom().gid;
  }

  private getRoom() { return this.latest()?.view?.room ?? null; }
  public  getSeats() { return this.latest()?.view?.seats ?? []; }
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
