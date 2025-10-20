import { CommonModule } from "@angular/common";
import { Component, OnInit, signal } from "@angular/core";
import { LobbyService } from "./lobby.service";
import { firstValueFrom } from "rxjs";
import { Room } from "../../models/room.model";
import { RouterLink } from "@angular/router";
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

  public rooms = signal<Room[]>([]);

  constructor(
    private lobbyService: LobbyService,
    private roomService: RoomService ){}
    
  ngOnInit(): void {
    this.getLobby()
  }
  
  public async getLobby() {
    try {
      const response = await firstValueFrom(this.lobbyService.getRooms());
      this.rooms.set(response.rooms);
      //this.rooms = response.rooms;
      console.log(this.rooms);
    } catch (err) {
      console.error('Failed to rooms:', err);
    }
  }

  public async createRoom() {
    await firstValueFrom(this.roomService.createRoom());
    await this.getLobby();
  }
}
