import { CommonModule } from '@angular/common';
import { Component, OnInit, Signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { RoomSocketService } from './room-socket.service';

@Component({
  standalone: true,
  selector: 'app-room-view',
  imports: [CommonModule],
  templateUrl: './room-view.html',
  styleUrl: './room-view.css',
  // Component-scoped instance so it dies with the page
  providers: [RoomSocketService]
})
export class RoomViewComponent implements OnInit {
  public latest!: Signal<any | null>;

  constructor(
    private readonly sockets: RoomSocketService,
    private readonly route: ActivatedRoute
  ) {
    this.latest = this.sockets.latest;
  }

  async ngOnInit(): Promise<void> {
    const gid = this.route.snapshot.paramMap.get('gid') ?? '';
    if (!gid) {
      console.error('No gid in route');
      return;
    }
    try {
      await this.sockets.connect(gid);
    } catch (err) {
      console.error('Failed to open room socket:', err);
    }
  }

  sendPing(): void {
    this.sockets.send({ type: 'ping', t: Date.now() });
  }
}
