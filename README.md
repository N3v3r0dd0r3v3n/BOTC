python3 -m venv .venv
source .venv/bin/activate

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



