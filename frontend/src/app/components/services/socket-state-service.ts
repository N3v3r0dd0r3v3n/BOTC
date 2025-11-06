import { computed, effect, inject, Injectable, Injector, signal } from "@angular/core";
import { StoryTellerSocketService } from "../../features/lobby/storyteller-socket.service";
import { PlayerSocketService } from "../../features/lobby/player-socket.service";

@Injectable({ providedIn: 'root' }) 
export class RoomStateStore {

  private injector = inject(Injector);

  constructor(
    private st: StoryTellerSocketService,
    private pl: PlayerSocketService,
  ) {
    console.log('[store] constructed');
  }

  private role = signal<'st'|'player'| null>(null);
  private _latest = signal<any|null>(null);
  private _imperative = signal<any|null>(null);

  latest = this._latest.asReadonly();
  imperative = this._imperative.asReadonly();

  // handy derived signals
  room   = computed(() => this.latest()?.view?.info ?? null);
  seats  = computed(() => this.latest()?.view?.seats ?? []);
  phase  = computed(() => this.latest()?.view?.phase ?? null);

  // mirror whichever socket is active into _latest
  private mirrorLatest = effect(() => {
    const role = this.role();
    console.log('[store] mirrorLatest run; role=', role);
    if (!role) {
      return;
    }

    const source =
      role === 'st' ? this.st.latest() : this.pl.latest();

    // mirror into a single signal consumers read
    console.log('[store] mirrorLatest <-', source);
    this._latest.set(source);
  }, { injector: this.injector, allowSignalWrites: true });

  private mirrorImperative = effect(() => {
    const r = this.role();
    console.log('[store] mirrorImperative run; role=', r);
    if (!r) return;
    const v = r === 'st' ? this.st.imperative() : this.pl.imperative();
    console.log('[store] mirrorImperative <-', v);
    this._imperative.set(v);
  }, { injector: this.injector });

  async connectAsStoryteller(gid: string) {
    await this.st.connect(gid);
    this.role.set('st');
  }

  async connectAsPlayer(gid: string, pid: number) {
    await this.pl.connect(gid, pid);
    this.role.set('player');
  }

  closeAll() {
    this.st.close();
    this.pl.close();
    this.role.set(null);
    this._latest.set(null);
  }
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
