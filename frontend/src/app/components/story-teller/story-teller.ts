import { Component, Input} from '@angular/core';
import { GameService } from '../../features/lobby/game.service';
import { firstValueFrom } from 'rxjs';
import { RoomService } from '../../features/lobby/room.service';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-story-teller',
  imports: [MatButtonModule],
  templateUrl: './story-teller.html',
  styleUrl: './story-teller.scss'
})
export class StoryTeller {
  @Input() roomId?: string;
  @Input() phase?: string;
  @Input() playerCount: number = 0;

  constructor(
    private gameService: GameService,
    private roomService: RoomService
  ){}

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

}
