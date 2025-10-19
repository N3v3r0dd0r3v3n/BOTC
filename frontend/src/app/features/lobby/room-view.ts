import { Component, DestroyRef, inject, signal } from '@angular/core';
import { JsonPipe, AsyncPipe } from '@angular/common';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { RoomSocketService } from './room-socket.service';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs';

@Component({
  selector: 'app-room-view',
  standalone: true,
  imports: [JsonPipe, AsyncPipe, CommonModule],
  templateUrl: './room-view.html',
  styleUrl: './room-view.css'
})
export class RoomViewComponent {
  latest = signal<any | null>(null);

  private readonly url = 'ws://localhost:8765/ws/0c4f65aa/room';
  private route = inject(ActivatedRoute);

  // Convert the paramMap observable into a signal
  gid = toSignal(this.route.paramMap.pipe(
    map(params => params.get('gid')!)
  ));

  constructor(
    private sockets: RoomSocketService,
    private destroyRef: DestroyRef
  ) {
    this.sockets
      .connect(this.url)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: msg => this.latest.set(msg),
        error: err => console.error('stream error', err),
        complete: () => console.log('stream complete'),
      });
  }

  sendPing() {
    // Optional - only if your server supports client messages
    this.sockets.send({ type: 'ping', t: Date.now() });
  }
}
