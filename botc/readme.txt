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