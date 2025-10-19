import { CommonModule } from "@angular/common";
import { Component, OnInit, signal } from "@angular/core";
import { LobbyService } from "./lobby.service";
import { firstValueFrom } from "rxjs";
import { Room } from "../../models/room.model";

@Component({
  standalone: true,
  selector: 'app-hello-component',
  imports: [
    CommonModule
],
  templateUrl: './lobby.html',
  styleUrl: './lobby.css'
})
export class Lobby implements OnInit {

  public rooms = signal<Room[]>([]);

  constructor(
    private lobbyService: LobbyService){}
    
  ngOnInit(): void {
    this.getLobby()
  }
  
  public async getLobby() {
    console.log("Heere")
    try {
      const response = await firstValueFrom(this.lobbyService.getRooms());
      this.rooms.set(response.rooms);
      console.log(this.rooms);
    } catch (err) {
      console.error('Failed to rooms:', err);
    }
  }
}
