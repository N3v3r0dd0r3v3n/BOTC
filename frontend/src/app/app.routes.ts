import { Routes } from '@angular/router';
import { Lobby } from './features/lobby/lobby';
import { RoomViewComponent } from './features/lobby/room-view';

export const routes: Routes = [
    { path: '', pathMatch: 'full', redirectTo: 'lobby' },
    { path: 'lobby', component: Lobby},
    { path: 'room/:gid', component: RoomViewComponent},

];
