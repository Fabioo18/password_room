import json
import random
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Password Room Live Multiplayer")

PASSWORD_DATABASE = [
    {"password": "VULCANO", "forbidden": ["LAVA", "MAGMA", "ERUZIONE"]},
    {"password": "PIRATA", "forbidden": ["NAVE", "TESORO", "BENDA"]},
    {"password": "CAFFE", "forbidden": ["BAR", "ESPRESSO", "TAZZINA"]},
    {"password": "AEREO", "forbidden": ["VOLARE", "PILOTA", "ALI"]},
    {"password": "CINEMA", "forbidden": ["FILM", "POPCORN", "SCHERMO"]},
    {"password": "CHITARRA", "forbidden": ["CORDE", "SUONARE", "MUSICA"]},
    {"password": "DENTISTA", "forbidden": ["DENTI", "DOLORE", "CARIE"]},
    {"password": "SMARTPHONE", "forbidden": ["TELEFONO", "SCHERMO", "CELLULARE"]},
    {"password": "PISCINA", "forbidden": ["ACQUA", "NUOTARE", "CLORO"]},
    {"password": "DISCOTECA", "forbidden": ["BALLARE", "DJ", "SERATA"]},
    {"password": "CIOCCOLATO", "forbidden": ["DOLCE", "CACAO", "TAVOLETTA"]},
    {"password": "OSPEDALE", "forbidden": ["MEDICO", "MALATO", "DOTTORE"]},
]

POINTS_LADDER = [10, 8, 6, 4, 2]


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


class RoomState:
    def __init__(self):
        self.team_a_name = "Squadra Cyan"
        self.team_b_name = "Squadra Amber"
        self.score_a = 0
        self.score_b = 0
        self.players: Dict[str, dict] = {}
        self.deck = list(PASSWORD_DATABASE)
        random.shuffle(self.deck)
        self.current_round = 0
        self.current_card = None
        self.active_team = "A"
        self.attempt_index = 0
        self.clues_history = []
        self.phase = "LOBBY"


room = RoomState()


def build_public_state():
    return {
        "type": "STATE_UPDATE",
        "phase": room.phase,
        "round": room.current_round,
        "team_a_name": room.team_a_name,
        "team_b_name": room.team_b_name,
        "score_a": room.score_a,
        "score_b": room.score_b,
        "active_team": room.active_team,
        "active_team_name": (
            room.team_a_name if room.active_team == "A" else room.team_b_name
        ),
        "current_points": POINTS_LADDER[
            min(room.attempt_index, len(POINTS_LADDER) - 1)
        ],
        "clues_history": room.clues_history,
        "players_count": len(room.players),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_id = str(id(websocket))

    await websocket.send_json(build_public_state())

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "JOIN_GAME":
                p_name = data.get("name", "Ospite").strip()
                p_team = data.get("team", "A")
                room.players[client_id] = {"name": p_name, "team": p_team}
                await manager.broadcast(build_public_state())

            elif action == "START_ROUND":
                if not room.deck:
                    room.deck = list(PASSWORD_DATABASE)
                    random.shuffle(room.deck)

                room.current_round += 1
                room.current_card = room.deck.pop(0)
                room.clues_history = []
                room.attempt_index = 0
                room.active_team = "A" if (room.current_round % 2 != 0) else "B"
                room.phase = "CAPTAIN_CLUE"

                # 1. Invia stato aggiornato
                await manager.broadcast(build_public_state())

                # 2. Invia la scheda segreta a tutti (il client del capitano la sblocca)
                await manager.broadcast(
                    {
                        "type": "SECRET_CARD_SYNC",
                        "password": room.current_card["password"],
                        "forbidden": room.current_card["forbidden"],
                        "active_team": room.active_team,
                    }
                )

            elif action == "SUBMIT_CLUE":
                clue = data.get("clue", "").strip().upper()
                if " " in clue or "-" in clue or len(clue) < 2:
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "message": "L'indizio deve essere UNA SOLA parola!",
                        }
                    )
                    continue

                pwd = room.current_card["password"].upper()
                forbidden = [f.upper() for f in room.current_card["forbidden"]]

                if clue == pwd or clue in forbidden:
                    if room.active_team == "A":
                        room.score_a = max(0, room.score_a - 3)
                    else:
                        room.score_b = max(0, room.score_b - 3)

                    room.active_team = "B" if room.active_team == "A" else "A"
                    room.attempt_index = min(
                        len(POINTS_LADDER) - 1, room.attempt_index + 1
                    )
                    room.phase = "CAPTAIN_CLUE"

                    await manager.broadcast(
                        {
                            "type": "TABOO_ALERT",
                            "message": f"🚨 VIOLAZIONE TABOO! '{clue}' è vietata! (-3 PUNTI)",
                            "state": build_public_state(),
                        }
                    )
                else:
                    room.clues_history.append(
                        {
                            "team": room.active_team,
                            "team_name": (
                                room.team_a_name
                                if room.active_team == "A"
                                else room.team_b_name
                            ),
                            "clue": clue,
                            "attempt": room.attempt_index + 1,
                        }
                    )
                    room.phase = "TEAM_GUESS"
                    await manager.broadcast(build_public_state())

            elif action == "SUBMIT_GUESS":
                guess = data.get("guess", "").strip().upper()
                correct_pwd = room.current_card["password"].upper()
                pts = POINTS_LADDER[min(room.attempt_index, len(POINTS_LADDER) - 1)]

                if guess == correct_pwd:
                    if room.active_team == "A":
                        room.score_a += pts
                    else:
                        room.score_b += pts

                    room.phase = "ROUND_END"
                    await manager.broadcast(
                        {
                            "type": "CORRECT_GUESS",
                            "winner_team": (
                                room.team_a_name
                                if room.active_team == "A"
                                else room.team_b_name
                            ),
                            "password": correct_pwd,
                            "points": pts,
                            "state": build_public_state(),
                        }
                    )
                else:
                    room.attempt_index += 1
                    room.active_team = "B" if room.active_team == "A" else "A"

                    if room.attempt_index >= len(POINTS_LADDER):
                        room.phase = "ROUND_END"
                        await manager.broadcast(
                            {
                                "type": "EXHAUSTED",
                                "message": f"❌ Tentativi esauriti! La parola era {correct_pwd}",
                                "password": correct_pwd,
                                "state": build_public_state(),
                            }
                        )
                    else:
                        room.phase = "CAPTAIN_CLUE"
                        await manager.broadcast(
                            {
                                "type": "WRONG_GUESS",
                                "message": f"❌ Sbagliato! Tocca a {room.team_a_name if room.active_team == 'A' else room.team_b_name}",
                                "state": build_public_state(),
                            }
                        )

    except WebSocketDisconnect:
        if client_id in room.players:
            del room.players[client_id]
        manager.disconnect(websocket)
        await manager.broadcast(build_public_state())


app.mount("/", StaticFiles(directory="static", html=True), name="static")
