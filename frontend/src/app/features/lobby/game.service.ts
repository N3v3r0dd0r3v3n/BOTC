import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class GameService {
  private readonly baseUrl = `${environment.botc_service_uri}/rooms`;

  constructor(private http: HttpClient) {}

  private httpOptions = {
    headers: new HttpHeaders({ 'Content-Type': 'application/json' })
  };

  step(roomId: string) {

    const body = {}
    console.log(roomId)
    console.log(`${this.baseUrl}/${roomId}/step`)
    return this.http.post<any>(`${this.baseUrl}/${roomId}/step`, body, this.httpOptions);
  }
}

function safeParse(s: string) {
  try { return JSON.parse(s); } catch { return null; }
}
