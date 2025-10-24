import { DestroyRef, Injectable, NgZone, Signal, signal, WritableSignal } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Subscription } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable()
export class StoryTellerSocketService {
  //public latest: Signal<any | null> = signal<any | null>(null);
  public readonly lastMessage: Signal<any | null> = signal<any | null>(null);

  private readonly _latest: WritableSignal<any | null> = signal<any | null>(null);
  public readonly latest = this._latest.asReadonly();
  private readonly _imperative: WritableSignal<any | null> = signal<any | null>(null);
  public readonly imperative = this._imperative.asReadonly();

  private socket?: WebSocketSubject<any>;
  private sub?: Subscription;
  private currentGid?: string;

  constructor(
    private readonly destroyRef: DestroyRef,
    private readonly zone: NgZone
  ) {
    this.destroyRef.onDestroy(() => this.teardown());
  }

  async connect(gid: string): Promise<void> {
    if (!gid) throw new Error('Missing gid');
    if (this.socket && !this.socket.closed && this.currentGid === gid) return;

    this.teardown();
    this.currentGid = gid;

    const url = `${environment.botc_service_ws}/${gid}/st`;

    let opened!: () => void;
    const openedPromise = new Promise<void>(res => (opened = res));

    this.socket = webSocket({
      url,
      deserializer: e => JSON.parse((e as MessageEvent).data as string),
      serializer: v => JSON.stringify(v),
      openObserver: { next: () => opened() },
      closeObserver: { next: ev => console.log('WS closed (st)', gid, ev) }
    });

    this.sub = this.socket.subscribe({
      next: msg => this.zone.run(() => {
        console.log(msg)
        //(this.latest as any).set?.(msg);
        if (msg.type === "state") {
          this._latest.set(msg);
        } else if (msg.type === "event") {
          this._imperative.set(msg);
        }
        
      }),
      error: err => console.error('WS error (st)', err),
      complete: () => console.log('WS complete (st)')
    });

    await openedPromise;
  }

  send(msg: unknown): void {
    this.socket?.next(msg);
  }

  close(): void {
    this.teardown();
  }

  private teardown(): void {
    try { this.sub?.unsubscribe(); } catch {}
    try { this.socket?.complete(); } catch {}
    this.sub = undefined;
    this.socket = undefined;
    this.currentGid = undefined;
    
    this._latest.set(null)
    this._imperative.set(null)

  }
}
