import { Routes } from '@angular/router';
import { Lobby } from './features/lobby/lobby';

export const routes: Routes = [
    { path: '', pathMatch: 'full', redirectTo: 'lobby' },
    { path: 'lobby', component: Lobby},
];
