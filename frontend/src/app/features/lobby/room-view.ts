import { CommonModule } from '@angular/common';
import { Component, OnInit, Signal, signal, ChangeDetectorRef, effect, WritableSignal } from '@angular/core';
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
  public message = signal<Signal<any | null> | null>(null);

  public storytellerLogs:string[] = [];

  public isSeated = false;
  public role = null;
  private isST = false;



  constructor(
    private readonly spectatorSocket: SpectatorSocketService,
    private readonly playerSocket: PlayerSocketService,
    private readonly storytellerSocket: StoryTellerSocketService,
    private readonly roomService: RoomService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly cd: ChangeDetectorRef,
  ) {

    let initialised = false;

    effect(() => {
      let msg = null;
      if (this.isST) {
        msg = this.storytellerSocket.imperative();
      } else {
        msg = this.playerSocket.imperative();
      }

      if (!initialised) {                   // skip the first run
        initialised = true;
        return;
      }

      //PLAYER_TAKEN_SEAT = "PlayerTakenSeat"
      //PLAYER_VACATED_SEAT = "PlayerVacatedSeat"
      
      if (msg != null) {
        console.log(msg);
        let message = null;
        if (msg.type == "event" && this.isST) {
          let details = "";
          const spectator_name = msg.data.spectator_name;
          if (msg.kind == "SpectatorJoined") {
            details = "is spectating";
          } else if (msg.kind == "PlayerTakenSeat") {
            details = `has taken seat ${msg.data.seat}`;
          } else if (msg.kind == "PlayerVacatedSeat") {
            details = `has vacated seat ${msg.data.seat} and is now spectating`;
          }
          message = `${spectator_name} ${details}`
        }

        if (msg.type == "info") {
          //message = `You are the ${msg.data.role_name}`
          this.role = msg.data.role_name;
        }
        if (message) {
          alert(message)
        }

        if (this.isST) {
          this.storytellerLogs.push(message!)
        }
        
      }

    });

    /*
    don't uncomment me yet
    effect(() => {
      const s = this.playerSocket.state();
      if (this.isST || !this.isSeated) return;        // player only when seated (and not ST)
      if (s.status === 'closed' || s.status === 'error') {
        this.onDisconnect('player', s.reason ?? `code:${s.code}`);
      }
    });

    private reconnecting = false;
private retry = 0;

private async onDisconnect(kind: 'st'|'spectator'|'player', reason: string) {
  console.warn(`[WS ${kind}] disconnected: ${reason}`);
  // Example reactions:
  // 1) update local UI flags / logs
  this.storytellerLogs.push(`${kind.toUpperCase()} socket dropped: ${reason}`);

  // 2) Optional auto-reconnect with backoff (kept simple)
  if (this.reconnecting) return;
  this.reconnecting = true;
  try {
    const delay = Math.min(15000, 500 * Math.pow(2, this.retry++)); // 0.5s, 1s, 2s, ... max 15s
    await new Promise(r => setTimeout(r, delay));
    const gid = this.latest()?.view?.room?.gid || this.route.snapshot.paramMap.get('gid') || '';

    if (!gid) return;
    if (kind === 'st') {
      await this.storytellerSocket.connect(gid);
      this.latest = this.storytellerSocket.latest;
    } else if (kind === 'spectator') {
      await this.spectatorSocket.connect(gid);
      this.latest = this.spectatorSocket.latest;
    } else {
      const pid = this.myId();
      if (pid != null) {
        await this.playerSocket.connect(gid, pid);
        this.latest = this.playerSocket.latest;
      }
    }
    this.cd.detectChanges();
    this.retry = 0; // success
  } catch (e) {
    // optional: if too many failures, navigate away or surface a banner
    console.error('reconnect failed', e);
  } finally {
    this.reconnecting = false;
  }
}
*/











  }

  async ngOnInit(): Promise<void> {
    const gid = this.route.snapshot.paramMap.get('gid') ?? '';
    if (!gid) return;

    
    const meta = await firstValueFrom(this.roomService.getRoomDetails(gid));
    this.isST = meta?.storyteller_id === this.myId();

    this.latest = this.isST ? this.storytellerSocket.latest : this.spectatorSocket.latest; 

    // Make sure the template notices the new signal reference immediately
    this.cd.detectChanges();

    if (this.isST) {
      await this.storytellerSocket.connect(gid);        
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
    alert("Starting game")
    const gid = this.getRoomId();
    if (gid) {
      const response = firstValueFrom(this.roomService.startGame(gid));
      console.log(response);
    }
  }

  sendPing(): void {
    const payload = { type: 'ping', t: Date.now() };
    if (this.isST) this.storytellerSocket.send(payload);
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
    const roomId = this.getRoomId();

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
    const roomId = this.getRoomId();
    
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
    const roomSt = this.getRoom().story_teller_id ?? this.getRoom().storyteller_id;
    return !!roomSt && roomSt === v?.id;
  }

  getRoom() { 
    return this.latest()?.view?.info ?? null; 
  }

  getSeats() { 
    return this.latest()?.view?.seats ?? []; 
  }

  getSpectators() { 
    return this.latest()?.view?.spectators ?? []; 
  }

  private updateSeatCount(seatCount: number) {
    const gid = this.getRoomId();
    if (gid) return firstValueFrom(this.roomService.updateSeatCount(gid, seatCount));
    return Promise.resolve();
  }

  private myId() {
    const visitor = safeParse(localStorage.getItem('visitor') || '{}') || {};
    return visitor.id;
  }

  private getRoomId() {
    return this.getRoom().gid;
  }
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
