import { Component, Input} from '@angular/core';
import { GameService } from '../../features/lobby/game.service';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-story-teller',
  imports: [],
  templateUrl: './story-teller.html',
  styleUrl: './story-teller.scss'
})
export class StoryTeller {
  @Input() roomId?: string;
  @Input() phase?: string;

  constructor(private gameService: GameService){}



  async step(roomId: string) {
    await firstValueFrom(this.gameService.step(roomId));
  }

}
