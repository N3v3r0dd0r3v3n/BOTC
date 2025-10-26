Frontend
node -v
npm i -g @angular/cli@20



# Install Angular CLI 20.x
npm i -g @angular/cli@20


Backend

cd /Users/amb/Documents/git/BOTC/backend
python3 -m venv .venv
source .venv/bin/activate
export PYTHONPATH=$(pwd)

A) Start server
python -m botc.server

B) Create a room
curl -s -X POST http://localhost:8765/api/new | jq

C) Connect a storyteller via WebSocket
wscat -c ws://localhost:8765/ws/abcd1234/st

D) Drive the game step-by-step
curl -s -X POST http://localhost:8765/api/room/abcd1234/step | jq

When a role (e.g., Fortune Teller) asks a question, you’ll see a prompt in the storyteller socket like:
{"type":"prompt","cid":1,"seat":3,"kind":"choose_two","title":"Choose two players","candidates":[1,2,4,5]}

Reply in the storyteller socket:
{"type":"respond","cid":1,"answer":[1,2]}

Repeat step:
curl -s -X POST http://localhost:8765/api/room/abcd1234/step | jq

Nomination/vote prompts will similarly appear; respond with:
{"type":"respond","cid":4,"answer":true}


E) List rooms
curl -s http://localhost:8765/api/lobby

F) Create room
curl -s -X POST http://localhost:8765/api/lobby \
  -H 'Content-Type: application/json' \
  -d '{"name":"Friday BOTC","script":"Trouble Brewing","max_players":10}'

g) Get room details
wscat -c ws://localhost:8765/ws/<gid>/room

h) Join room unseated
curl -s -X POST http://localhost:8765/api/room/<gid>/join -H 'Content-Type: application/json' -d '{"name":"Eve"}'

i) Take seat
curl -s -X POST http://localhost:8765/api/room/236d3b94/sit -H 'Content-Type: application/json' -d '{"player_id":2,"seat":3}'

j) Vacate seat
curl -s -X POST http://localhost:8765/api/room/236d3b94/vacate -H 'Content-Type: application/json' -d '{"player_id":2}'

k) Change capacity
curl -s -X POST http://localhost:8765/api/room/236d3b94/seats -H 'Content-Type: application/json' -d '{"max_players":6}'

{ type: patch, kind: PlayerJoined, data: { spectator_id, spectator_name}}

state = only place the full view is sent.
info vs action is your “two kinds” to the player.
response is the only thing the player sends back for actions.
cid = correlation id so replies pair to requests.

| { type: 'state'; seq?: number; ts?: string; data: { view: RoomView } }

  // Optional small deltas (use later if you want)
  | { type: 'patch'; kind: 'PhaseChanged' | 'SeatTaken' | 'SeatVacated' | string; seq: number; ts?: string; data: any }

  // Storyteller -> Player: information (no response expected)
  | { type: 'info';  to?: number; ts?: string; data: { title?: string; text: string; meta?: any } }

  // Storyteller -> Player: action request (response expected)
  | { type: 'action'; cid: string; to?: number; ts?: string; data: { name: string; prompt?: string; options?: any; constraints?: any } }

  // Player -> Storyteller: response to an action request
  | { type: 'response'; cid: string; from?: number; ts?: string; data: any }

  // Generic acks/errors/ping
  | { type: 'ack'; cid?: string; data?: any }
  | { type: 'error'; cid?: string; error: string }
  | { type: 'pong'; t?: number };



{
  "type": "request",
  "cid": 101,
  "kind": "tell",
  "payload": {
    "text": "You learn who your minions are and three townsfolk bluffs.",
    "minions": self.n1_info.minion_ids,
    "bluffs": self.n1_info.demon_bluffs
  }
}

# For a minion on Night 1
{
  "type": "request",
  "cid": 102,
  "kind": "tell",
  "payload": {
    "text": "You learn who the demon is and who the other minions are.",
    "demon": self.n1_info.demon_id,
    "minions": self.n1_info.minion_ids
  }
}

