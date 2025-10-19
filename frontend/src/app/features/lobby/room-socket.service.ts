import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Observable, retry, tap, timer } from 'rxjs'; // note: timer, not delay()

@Injectable({ providedIn: 'root' })
export class RoomSocketService {
  private socket?: WebSocketSubject<any>;

  connect(url: string): Observable<any> {
    if (!this.socket || this.socket.closed) {
      this.socket = webSocket({
        url,
        deserializer: e => JSON.parse(e.data),
        serializer: v => JSON.stringify(v),
        openObserver: { next: () => console.log('WS open') },
        closeObserver: { next: ev => console.log('WS closed', ev) },
      });
    }

    return this.socket.pipe(
      retry({
        count: Number.POSITIVE_INFINITY, // or a finite number like 10
        delay: (_err, retryCount) =>
          timer(Math.min(1000 * retryCount, 5000)), // backoff: 1s, 2s, … max 5s
      }),
      tap({ error: err => console.error('WS error', err) })
    );
  }

  send(msg: unknown) {
    this.socket?.next(msg);
  }

  close() {
    this.socket?.complete();
  }
}
