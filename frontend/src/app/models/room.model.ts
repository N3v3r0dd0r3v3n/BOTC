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
    story_teller_id: number;
    story_teller_name: string;
    script_name: string;
    status: 'open' | 'started' | 'finished';
  }
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
