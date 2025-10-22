import { CommonModule } from '@angular/common';
import { Component, OnInit, Signal, signal, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { RoomSocketService } from './room-socket.service';
import { StoryTellerSocketService } from './storyteller-socket.service';
import { RoomService } from './room.service';

@Component({
  standalone: true,
  selector: 'app-room-view',
  imports: [CommonModule],
  templateUrl: './room-view.html',
  styleUrl: './room-view.css',
  providers: [RoomSocketService, StoryTellerSocketService]
})
export class RoomViewComponent implements OnInit {
  // PUBLIC so the template can call latest()
  public latest: Signal<any | null> = signal<any | null>(null);

  public isSeated = false;
  private isST = false;

  constructor(
    private readonly spectatorSocket: RoomSocketService,
    private readonly stSocket: StoryTellerSocketService,
    private readonly roomService: RoomService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly cd: ChangeDetectorRef,
  ) {}

  async ngOnInit(): Promise<void> {
    const gid = this.route.snapshot.paramMap.get('gid') ?? '';
    if (!gid) return;

    const visitor = safeParse(localStorage.getItem('visitor') || '{}') || {};
    const meta = await firstValueFrom(this.roomService.getRoomDetails(gid));
    this.isST = meta?.storyteller_id === visitor?.id;

    // Bind latest to the chosen service signal BEFORE connecting
    this.latest = this.isST ? this.stSocket.latest : this.spectatorSocket.latest;

    // Make sure the template notices the new signal reference immediately
    this.cd.detectChanges();

    // Connect the chosen socket
    if (this.isST) {
      await this.stSocket.connect(gid);        // ST open() sends initial state
    } else {
      await this.spectatorSocket.connect(gid); // Viewer open() sends initial state
    }

    // Join the room (server may broadcast; we are already connected)
    await firstValueFrom(this.roomService.joinRoom(gid));

    // Ask for state explicitly as a belt-and-braces
    if (this.isST) this.stSocket.send({ type: 'get_state' });
    else this.spectatorSocket.send({ type: 'get_state' });

    // One more change-detection nudge in case the first push raced the binding
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

  sit(seat: number) {
    this.isSeated = true;
    const gid = this.latest()?.view?.room?.gid;
    if (gid) return firstValueFrom(this.roomService.sit(gid, seat));
    return Promise.resolve();
  }

  vacate(seat: number) {
    this.isSeated = false;
    const gid = this.latest()?.view?.room?.gid;
    if (gid) return firstValueFrom(this.roomService.vacate(gid, seat));
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

  private getRoom() { return this.latest()?.view?.room ?? null; }
  public  getSeats() { return this.latest()?.view?.seats ?? []; }
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
