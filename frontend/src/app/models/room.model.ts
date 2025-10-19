export interface Player {
  id?: number;
  name?: string;
  // add more as needed
}

export interface Room {
  gid: string;
  name: string;
  script_name: string;
  max_players: number;
  status: 'open' | 'started' | 'finished';
  seats: any[] | null;   // refine later if you know seat structure
  players: Player[];
  seats_used: number;
}

export interface LobbyResponse {
  rooms: Room[];
}

export interface RoomStateResponse {
  type: 'state';
  view: RoomView;
}

export interface RoomView {
  gid: string;
  status: 'open' | 'started' | 'finished';
  max_players: number;
  seats: Seat[];
  unseated: Player[];
}

export interface Seat {
  seat: number;
  occupant: Player | null;
}
