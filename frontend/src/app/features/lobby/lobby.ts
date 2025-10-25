import { CommonModule } from "@angular/common";
import { Component, OnInit, signal } from "@angular/core";
import { LobbyService } from "./lobby.service";
import { firstValueFrom } from "rxjs";
import { Room } from "../../models/room.model";
import { Router, RouterLink } from "@angular/router";
import { RoomService } from "./room.service";

@Component({
  standalone: true,
  selector: 'app-hello-component',
  imports: [
    CommonModule,
    RouterLink
],
  templateUrl: './lobby.html',
  styleUrl: './lobby.css'
})
export class Lobby implements OnInit {

  public lobby = signal<Room[]>([]);

  constructor(
    private lobbyService: LobbyService,
    private roomService: RoomService,
    private router: Router){}
    
  ngOnInit(): void {
    this.getLobby()
  }
  
  public async getLobby() {
    try {
      const response = await firstValueFrom(this.lobbyService.getLobby());
      this.lobby.set(response.lobby);
    } catch (err) {
      console.error('Failed to get rooms:', err);
    }
  }

  public async createRoom() {
    const response = await firstValueFrom(this.roomService.createRoom());
    this.router.navigate(['/room/' + response.gid]);
  }
}
