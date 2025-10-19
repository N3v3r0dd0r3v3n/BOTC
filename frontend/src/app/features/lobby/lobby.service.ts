import { Injectable } from "@angular/core";
import { environment } from "../../environments/environment";
import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Observable } from "rxjs";
import { LobbyResponse } from "../../models/room.model";


@Injectable({
  providedIn: 'root'
})
export class LobbyService {

    private readonly baseUrl = `${environment.botc_service_uri}/lobby`;
    constructor(private http: HttpClient) { }

    httpOptions = {
        headers: new HttpHeaders({ 'Content-Type': 'application/json' })
    };

    getRooms(): Observable<LobbyResponse> {
        return this.http.get<LobbyResponse>(this.baseUrl, this.httpOptions);
    }
}