// player-socket.service.ts
import { DestroyRef, Injectable, NgZone, Signal, signal, WritableSignal } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Subscription } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class PlayerSocketService {
  private readonly _latest: WritableSignal<any | null> = signal<any | null>(null);
  public readonly latest = this._latest.asReadonly();
  private readonly _imperative: WritableSignal<any | null> = signal<any | null>(null);
  public readonly imperative = this._imperative.asReadonly();

  private socket?: WebSocketSubject<any>;
  private sub?: Subscription;
  private current?: { gid: string; pid: number };

  constructor(
    private readonly destroyRef: DestroyRef,
    private readonly zone: NgZone
  ) {
    this.destroyRef.onDestroy(() => this.teardown());
  }

  async connect(gid: string, pid: number): Promise<void> {
    if (!gid) throw new Error('Missing gid');
    if (!pid && pid !== 0) throw new Error('Missing pid');
    if (this.socket && !this.socket.closed && this.current?.gid === gid && this.current?.pid === pid) return;

    this.teardown();
    this.current = { gid, pid };

    const url = `${environment.botc_service_ws}/${gid}/player/${pid}`;
    let opened!: () => void;
    const openedPromise = new Promise<void>(res => (opened = res));

    this.socket = webSocket({
      url,
      deserializer: e => JSON.parse((e as MessageEvent).data as string),
      serializer: v => JSON.stringify(v),
      openObserver: { next: () => opened() },
      closeObserver: { 
        next: ev => { 
          console.log('WS closed (player)', gid, pid, ev) 
          console.log("Do something here.  The player needs vacating from the seat/room/world")
        }
      }
    });

    this.sub = this.socket.subscribe({
      next: msg => this.zone.run(() => {
        console.log(msg);
        if (msg.type === "state") {
          this._latest.set(msg)
        } else {
          this._imperative.set(msg)
        }
      }),
      error: err => console.error('WS error (player)', err),
      complete: () => console.log('WS complete (player)')
    });

    await openedPromise;
  }

  send(msg: unknown): void { this.socket?.next(msg); }

  close(): void { this.teardown(); }

  private teardown(): void {
    try { this.sub?.unsubscribe(); } catch {}
    try { this.socket?.complete(); } catch {}
    this.sub = undefined;
    this.socket = undefined;
    this.current = undefined;
    (this.latest as any).set?.(null);
  }
}
