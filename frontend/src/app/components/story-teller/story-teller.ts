import { ChangeDetectorRef, Component, Input, OnInit, Signal, signal} from '@angular/core';
import { GameService } from '../../features/lobby/game.service';
import { firstValueFrom } from 'rxjs';
import { RoomService } from '../../features/lobby/room.service';
import { MatButtonModule } from '@angular/material/button';
import { Seat } from '../../models/room.model';
import { StoryTellerSocketService } from '../../features/lobby/storyteller-socket.service';

@Component({
  selector: 'app-story-teller',
  imports: [MatButtonModule],
  templateUrl: './story-teller.html',
  styleUrl: './story-teller.scss'
})
export class StoryTeller implements OnInit {
  @Input() roomId?: string;
  @Input() phase?: string;
  @Input() playerCount: number = 0;
  @Input() seats:Seat[] = [];

  public latest: Signal<any | null> = signal<any | null>(null);

  constructor(
    private gameService: GameService,
    private roomService: RoomService,
    private readonly storytellerSocket: StoryTellerSocketService,
    private readonly cd: ChangeDetectorRef
  ){}
  
  async ngOnInit(): Promise<void> {
    this.latest = this.storytellerSocket.latest; 
    this.cd.detectChanges();
    await this.storytellerSocket.connect(this.roomId!);        
  }

  async step(roomId: string) {
    await firstValueFrom(this.gameService.step(roomId));
  }

  setupGame(): void {
    alert("Starting game")
    const response = firstValueFrom(this.roomService.startGame(this.roomId!));
    console.log(response);
  }

  hasMinimumPlayers(): boolean {
    return this.playerCount < 5;
  }

  async addSeat() {
    this.updateSeatCount(this.seats.length + 1);
  }

  removeSeat() {
    this.updateSeatCount(this.seats.length - 1);
  }

  hasMaximumSeats(): boolean {
    return this.seats.length > 19 ? true : false;
  }

  hasMinimumSeats(): boolean {
    return this.seats.length < 6 ? true : false;
  }

  private updateSeatCount(seatCount: number) {
    const gid = this.roomId;
    if (gid) return firstValueFrom(this.roomService.updateSeatCount(gid, seatCount));
    return Promise.resolve();
  }



}
