export interface Player {
  id?: number;
  name?: string;
  role: Role;
}

export interface Role {
  id: String;   //It's actually the name!
}

export interface Room {
  info: {
    gid: string;
    name: string;
    storyteller_id: number;
    storyteller_name: string;
    script_name: string;
    status: 'open' | 'started' | 'finished';
  },
  players: number
  seats: Seat[]
}

export interface LobbyResponse {
  lobby: Room[];
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
