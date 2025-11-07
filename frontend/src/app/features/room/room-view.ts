import { CommonModule } from '@angular/common';
import { Component, OnInit, Signal, signal, ChangeDetectorRef, effect, WritableSignal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';


import { RoomService } from '../../components/services/room.service';
import { StoryTeller } from "../../components/story-teller/story-teller";
import { Player } from "../../components/player/player";
import { Spectators } from "../../components/spectators/spectators";
import { MatCard, MatCardModule } from "@angular/material/card";
import { MatButtonModule } from '@angular/material/button';
import { Seats } from "../../components/seats/seats";
import { RoomStateStore } from '../../components/services/socket-state-service';

@Component({
  standalone: true,
  selector: 'app-room-view',
  imports: [
    CommonModule, StoryTeller, Spectators, MatCard, MatCardModule, MatButtonModule,
    Seats,
    Player
],
  templateUrl: './room-view.html',
  styleUrl: './room-view.css',
  providers: [
    //StoryTellerSocketService,
    //PlayerSocketService,
    //RoomStateStore
  ]  //TODO Get rid of the other socketServices at some point right.
})
export class RoomViewComponent implements OnInit {
  public latest: Signal<any | null> = signal<any | null>(null);
  //public message = signal<Signal<any | null> | null>(null);

  public storytellerLogs:string[] = [];

  public isSeated = false;
  public role = null;
  private isST = false;
  ready = false;



  constructor(
    private readonly roomService: RoomService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly cd: ChangeDetectorRef,
    private readonly store: RoomStateStore
  ) {
    
    let initialised = false;

    effect(() => {
      const message = this.store.latest()
      //alert("Something changed in the room!");
      console.log(message)
      
      let msg = null;
      if (this.isST) {
        //msg = this.storytellerSocket.imperative();
      } else {
        //msg = this.playerSocket.imperative();
      }

      if (!initialised) {                   // skip the first run
        initialised = true;
        return;
      }

      //PLAYER_TAKEN_SEAT = "PlayerTakenSeat"
      //PLAYER_VACATED_SEAT = "PlayerVacatedSeat"
      
      if (msg != null) {
        console.log(msg);
        console.log(this.isST)
       // console.log(msg.type)
       //console.log(msg.kind)
        let message = null;
        /*
        if (msg.type == "event" && this.isST) {
          //console.log(this.storytellerSocket);
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
        } else if (msg.type == "patch" && this.isST) {
          alert("Ok we have a patch!")
          if (msg.kind == "PhaseChange") {
            alert("Oooo it's night.  Get the wake list up!")
          }

        }
          */

        /*if (msg.type == "info") {
          //message = `You are the ${msg.data.role_name}`
          this.role = msg.data.role_name;
        }*/
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

    
    const roomDetails = await firstValueFrom(this.roomService.getRoomDetails(gid));
    this.isST = roomDetails?.storyteller_id === this.myId();


    if (this.isST) {
      await this.store.connectAsStoryteller(gid);
    } else {
      await this.store.connectAsPlayer(gid, this.myId());
    }
    console.log('[room-view] connected; isST=', this.isST);

    this.latest = this.store.latest;

    await firstValueFrom(this.roomService.joinRoom(gid));

    //Change-detection nudge in case the first push raced the binding
    this.ready = true
    this.cd.detectChanges();
  }

  async sit(seat: number) {
    if (this.isST) {
      return;
    }
    this.isSeated = true;
    const roomId = this.getRoomId();

    await firstValueFrom(this.roomService.sit(roomId, seat));
    return Promise.resolve();
  }

  async vacate(seat: number) {
    if (this.isST) {
      return;
    }
    this.isSeated = false;
    const roomId = this.getRoomId();
    
    await firstValueFrom(this.roomService.vacate(roomId, seat));
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

  private myId() {
    const visitor = safeParse(localStorage.getItem('visitor') || '{}') || {};
    return visitor.id;
  }

  public getVisitor() {
    const visitor = JSON.parse(localStorage.getItem('visitor')!);
    return visitor
  }

  private getRoomId() {
    return this.getRoom().gid;
  }
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
