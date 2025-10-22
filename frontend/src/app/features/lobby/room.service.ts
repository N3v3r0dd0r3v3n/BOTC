import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class RoomService {
  private readonly baseUrl = `${environment.botc_service_uri}/rooms`;

  constructor(private http: HttpClient) {}

  private httpOptions = {
    headers: new HttpHeaders({ 'Content-Type': 'application/json' })
  };

  createRoom() {
    const raw = localStorage.getItem('visitor') || '{}';
    const visitor = safeParse(raw); // { id, name } expected

    const body = {
      creator: {
        id: visitor?.id ?? null,
        name: visitor?.name ?? null,
      }
    };

    return this.http.post<any>(this.baseUrl, body, this.httpOptions);
  }

  getRoomDetails(roomId: string) {
    return this.http.get<any>(`${this.baseUrl}/${roomId}`)
  }


  joinRoom(roomId: string) {
    const raw = localStorage.getItem('visitor') || '{}';
    const visitor = safeParse(raw); //

    const body = {
        id: visitor?.id ?? null,
        name: visitor?.name ?? null,
    }
    return this.http.post<any>(`${this.baseUrl}/${roomId}/join`, body, this.httpOptions)
  }

  updateSeatCount(roomId: string, seatCount: number) {
    //TODO Backend check to ensure you can only do this if you are the owner!
    const body = {
        seat_count: seatCount
    }
    return this.http.post<any>(`${this.baseUrl}/${roomId}/seats`, body, this.httpOptions)
  }

  sit(roomId: string, seat: number) {
    const visitor = this.getVisitor();
    const body = {
        spectator_id: visitor?.id ?? null,
        seat: seat
    }
    
    return this.http.post<any>(`${this.baseUrl}/${roomId}/sit`, body, this.httpOptions)
  }

  vacate (roomId: string, seat: number) {
    const visitor = this.getVisitor();
    const body = {
        player_id: visitor?.id ?? null,
        seat: seat
    }
    return this.http.post<any>(`${this.baseUrl}/${roomId}/vacate`, body, this.httpOptions)
  }

  leave(roomId: string) {
    const visitor = this.getVisitor();
    const body = {
        player_id: visitor?.id ?? null
    }
    return this.http.post<any>(`${this.baseUrl}/${roomId}/leave`, body, this.httpOptions)
  }

  startGame(roomId: string) {
    return this.http.post<any>(`${this.baseUrl}/${roomId}/start`, this.httpOptions)
  }

  private getVisitor() {
    const raw = localStorage.getItem('visitor') || '{}';
    const visitor = safeParse(raw);
    return visitor
  }

 
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
