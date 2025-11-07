import { Routes } from '@angular/router';
import { Lobby } from './features/lobby/lobby';
import { RoomViewComponent } from './features/room/room-view';
import { AuthGuard } from './core/guards/auth.guard';
import { RegisterComponent } from './features/register/register';

export const routes: Routes = [
    { path: '', pathMatch: 'full', redirectTo: 'lobby' },
    { path: 'lobby', component: Lobby, canActivate: [AuthGuard]},
    { path: 'room/:gid', component: RoomViewComponent, canActivate: [AuthGuard]},
    { path: 'register', component: RegisterComponent},

];
