import { ChangeDetectorRef, Component, effect, Input, OnInit, Signal, signal} from '@angular/core';
import { GameService } from '../../features/lobby/game.service';
import { firstValueFrom } from 'rxjs';
import { RoomService } from '../services/room.service';
import { MatButtonModule } from '@angular/material/button';
import { Seat } from '../../models/room.model';
import { RoomStateStore } from '../services/socket-state-service';
import { MatDialog } from '@angular/material/dialog';
import { Dialog } from '../dialog/selection-dialog';
import { Task } from '../../models/message.model';

@Component({
  selector: 'app-story-teller',
  imports: [MatButtonModule],
  templateUrl: './story-teller.html',
  styleUrl: './story-teller.scss',
  standalone: true
})
export class StoryTeller  {
  @Input() roomId?: string;
  @Input() phase?: string;
  @Input() playerCount: number = 0;
  @Input() seats:Seat[] = [];

  constructor(
    private gameService: GameService,
    private roomService: RoomService,
    private socketStateStore: RoomStateStore,
    private dialog: MatDialog
  ){
    console.log('[StoryTeller] ngOnInit');
    effect(() => {
      const message = this.socketStateStore.imperative();
      if (!message.type) {
        return
      }
      if (message.type == "event") {
        console.log(message)
        if (message.event == "setup_tasks") {
          
          for (let index = 0; index < message.tasks.length; index++) {
            const task = message.tasks[index];
            this.performSelection(task);
          }

        } else {
          alert("@@@@@@ " + message.event);
        }
      } else if (message.type == "patch") {
        if (message.kind == "PhaseChange") {
          alert("Phase changed.  But to what?????")
        }
      }
      //console.log("Imperative has been updated")
      //console.log('[StoryTeller] imperative seen:', message);
     });  
  }
  
  async step(roomId: string) {
    await firstValueFrom(this.gameService.step(roomId));
  }

  setupGame(): void {
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


  private performSelection(task: Task) {
    const dialogRef = this.dialog.open(Dialog, {
      position: {
        left: '10px'
      },
      width: '300px',
      data: { 
        title: task.prompt,
        options: task.options }
    });

    dialogRef.afterClosed().subscribe(selection => {
      if (selection) {
        console.log(selection)
        //add the selection to a list of commands to send back to the server.
        const message = {
          "id": task.id,
          "type": "command",
          "task": {
            "kind": task.kind,
            "role": task.role,
            "owner_id": task.owner_id,
            "selection": selection
          }
        }
        this.socketStateStore.send(message);
      }
    });
  }



}
