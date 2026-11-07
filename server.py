import re
import json
import random
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Password Room Live Multiplayer VIP")

# Dataset di 50 parole e termini vietati (Taboo)
PASSWORD_DATABASE = [
    # OGGETTI E TECNOLOGIA
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
    {"password": "BICICLETTA", "forbidden": ["PEDALI", "RUOTE", "SELLA"]},
    {"password": "OMBRELLO", "forbidden": ["PIOGGIA", "ACQUA", "APRIRE"]},
    {"password": "OROLOGIO", "forbidden": ["TEMPO", "ORE", "POLSO"]},
    {"password": "FORNO", "forbidden": ["PIZZA", "CALDO", "CUCINA"]},
    {"password": "FRIGORIFERO", "forbidden": ["FREDDO", "GHIACCIO", "CIBO"]},
    {"password": "TELEVISIONE", "forbidden": ["CANALI", "TELECOMANDO", "SCHERMO"]},
    {"password": "LAVATRICE", "forbidden": ["PANNI", "BUCATO", "CENTRIFUGA"]},
    {"password": "VALIGIA", "forbidden": ["VIAGGIO", "AEROPORTO", "VESTITI"]},
    {"password": "SPECCHIO", "forbidden": ["RIFLESSO", "VETRO", "GUARDARSI"]},
    {"password": "ZAINO", "forbidden": ["SCUOLA", "SPALLE", "LIBRI"]},
    {"password": "OCCHIALI", "forbidden": ["VISTA", "LENTI", "SOLE"]},
    {"password": "ASCIUGACAPELLI", "forbidden": ["BAGNO", "CALDO", "FON"]},
    {"password": "CHIAVE", "forbidden": ["PORTA", "SERRATURA", "APRIRE"]},
    # NATURA, ANIMALI E AMBIENTE
    {"password": "DESERTO", "forbidden": ["SABBIA", "CAMMELLO", "CALDO"]},
    {"password": "GHIACCIAIO", "forbidden": ["FREDDO", "POLO", "SCIOGLIERSI"]},
    {"password": "FORESTA", "forbidden": ["ALBERI", "BOSCO", "FOGLIE"]},
    {"password": "TERREMOTO", "forbidden": ["SCOSSA", "TREMARE", "TERRA"]},
    {"password": "ARCOBALENO", "forbidden": ["COLORI", "PIOGGIA", "CIELO"]},
    {"password": "SQUALO", "forbidden": ["MARE", "PINNA", "DENTI"]},
    {"password": "LEONE", "forbidden": ["SAVANA", "CRINIERA", "RE"]},
    {"password": "GIRAFFA", "forbidden": ["COLLO", "ALTA", "MACCHIE"]},
    {"password": "PINGUINO", "forbidden": ["FREDDO", "POLO", "BIANCO"]},
    {"password": "DELFINO", "forbidden": ["MARE", "SALTARE", "INTELLIGENTE"]},
    # CIBO E BEVANDE
    {"password": "PIZZA", "forbidden": ["FORNO", "MOZZARELLA", "POMODORO"]},
    {"password": "GELATO", "forbidden": ["CONO", "FREDDO", "GUSTI"]},
    {"password": "SPAGHETTI", "forbidden": ["PASTA", "SUGO", "FORCHETTA"]},
    {"password": "HAMBURGER", "forbidden": ["PANINO", "CARNE", "PATATINE"]},
    {"password": "BIRRA", "forbidden": ["ALCOL", "SCHIUMA", "BIONDA"]},
    {"password": "SUSHI", "forbidden": ["PESCE", "RISO", "GIAPPONE"]},
    # PROFESSIONI E RUOLI
    {"password": "POMPIERE", "forbidden": ["FUOCO", "IDRANTE", "SIRENA"]},
    {"password": "ASTRONAUTA", "forbidden": ["SPAZIO", "LUNA", "RAZZO"]},
    {"password": "MAGO", "forbidden": ["TRUCCO", "BACCHETTA", "CILINDRO"]},
    {"password": "POLIZIOTTO", "forbidden": ["PISTOLA", "MANETTE", "DIVISA"]},
    {"password": "CAMERIERE", "forbidden": ["RISTORANTE", "CONTO", "VASSOIO"]},
    {"password": "ARCHITETTO", "forbidden": ["CASA", "DISEGNO", "PROGETTO"]},
    # LUOGHI E CULTURA POP
    {"password": "COLOSSEO", "forbidden": ["ROMA", "GLADIATORI", "MONUMENTO"]},
    {"password": "PIRAMIDI", "forbidden": ["EGITTO", "FARAONE", "SABBIA"]},
    {"password": "STADIO", "forbidden": ["PARTITA", "CALCIO", "TIFOSI"]},
    {"password": "MUSEO", "forbidden": ["QUADRI", "ARTE", "MOSTRA"]},
    {"password": "TEATRO", "forbidden": ["PALCO", "SPETTACOLO", "ATTORI"]},
]

POINTS_LADDER = [10, 8, 6, 4, 2]

# Vocabolario di parole italiane comuni per bloccare unioni arbitrarie
COMMON_ITALIAN_WORDS = {
    "sole",
    "pioggia",
    "vento",
    "mare",
    "montagna",
    "fiume",
    "lago",
    "terra",
    "fuoco",
    "acqua",
    "casa",
    "porta",
    "finestra",
    "tavolo",
    "sedia",
    "letto",
    "pentola",
    "piatto",
    "bicchiere",
    "oro",
    "argento",
    "ferro",
    "legno",
    "carta",
    "penna",
    "libro",
    "gatto",
    "cane",
    "topo",
    "pane",
    "pasta",
    "pizza",
    "vino",
    "birra",
    "carne",
    "pesce",
    "mela",
    "pera",
    "latte",
    "notte",
    "giorno",
    "luce",
    "ombra",
    "cielo",
    "stella",
    "luna",
    "strada",
    "auto",
    "treno",
    "rosso",
    "blu",
    "verde",
    "giallo",
    "nero",
    "bianco",
    "bello",
    "grande",
    "piccolo",
    "caldo",
    "freddo",
    "dolce",
    "amaro",
    "forte",
    "piano",
    "testa",
    "mano",
    "piede",
    "occhio",
    "bocca",
    "barca",
    "albero",
    "fiore",
    "prato",
    "bosco",
    "neve",
    "ghiaccio",
    "tempo",
    "ora",
    "anno",
    "uomo",
    "donna",
    "bimbo",
    "amico",
    "cuore",
    "mente",
    "corpo",
    "vita",
    "cosa",
    "modo",
}


def is_compound_word(raw_text: str) -> bool:
    w = raw_text.strip()

    # 1. Caratteri non ammessi (spazi, trattini, punteggiatura, numeri)
    if not re.match(r"^[a-zA-ZàèéìòùÀÈÉÌÒÙ]+$", w):
        return True

    # 2. Rilevazione CamelCase (es. "SolePioggia", "PentolaDoro")
    if re.search(r"[a-zàèéìòù][A-ZÀÈÉÌÒÙ]", w):
        return True

    w_lower = w.lower()

    # 3. Lunghezza anomala per singola parola italiana comune
    if len(w_lower) > 13:
        return True

    # 4. Controllo segmentazione: verifica se è l'unione di due parole di senso compiuto
    for i in range(3, len(w_lower) - 2):
        prefix = w_lower[:i]
        suffix = w_lower[i:]
        if prefix in COMMON_ITALIAN_WORDS and suffix in COMMON_ITALIAN_WORDS:
            return True

    return False


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
        self.reset()

    def reset(self):
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
        self.guesses_history = []
        self.phase = "LOBBY"

    def get_captain_name(self, team: str) -> Optional[str]:
        for p in self.players.values():
            if p.get("team") == team and p.get("is_captain"):
                return p.get("name")
        return None


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
        "guesses_history": room.guesses_history,
        "captain_a": room.get_captain_name("A"),
        "captain_b": room.get_captain_name("B"),
        "has_active_card": room.current_card is not None,
    }


def get_secret_payload():
    if not room.current_card:
        return None
    return {
        "type": "SECRET_CARD_SYNC",
        "password": room.current_card["password"],
        "forbidden": room.current_card["forbidden"],
        "active_team": room.active_team,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_id = str(id(websocket))

    await websocket.send_json(build_public_state())
    secret = get_secret_payload()
    if secret:
        await websocket.send_json(secret)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "JOIN_GAME":
                p_name = data.get("name", "Ospite").strip()
                p_team = data.get("team", "A")
                room.players[client_id] = {
                    "name": p_name,
                    "team": p_team,
                    "is_captain": False,
                }
                await manager.broadcast(build_public_state())
                secret = get_secret_payload()
                if secret:
                    await websocket.send_json(secret)

            elif action == "CLAIM_CAPTAIN":
                player = room.players.get(client_id)
                if not player or player["team"] == "REGIA":
                    continue

                team = player["team"]
                current_captain = room.get_captain_name(team)

                if current_captain and current_captain != player["name"]:
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "message": f"Attenzione: {current_captain} è già il Capitano della tua squadra!",
                        }
                    )
                    continue

                player["is_captain"] = not player.get("is_captain", False)
                await manager.broadcast(build_public_state())

            elif action == "RESET_GAME":
                room.reset()
                await manager.broadcast(build_public_state())

            elif action == "START_ROUND":
                if not room.deck:
                    room.deck = list(PASSWORD_DATABASE)
                    random.shuffle(room.deck)

                room.current_round += 1
                room.current_card = room.deck.pop(0)
                room.clues_history = []
                room.guesses_history = []
                room.attempt_index = 0
                room.active_team = "A" if (room.current_round % 2 != 0) else "B"
                room.phase = "CAPTAIN_CLUE"

                await manager.broadcast(build_public_state())
                await manager.broadcast(get_secret_payload())

            elif action == "SUBMIT_CLUE":
                raw_clue = data.get("clue", "").strip()

                if is_compound_word(raw_clue) or len(raw_clue) < 2:
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "message": "⚠️ VIOLAZIONE: L'indizio deve essere UNA SOLA parola semplice! Vietato unire parole (es. 'solepioggia' o 'PentolaDoro').",
                        }
                    )
                    continue

                clue = raw_clue.upper()
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
                            "message": f"🚨 VIOLAZIONE TABOO! '{clue}' è vietata! (-3 Punti)",
                            "state": build_public_state(),
                        }
                    )
                    await manager.broadcast(get_secret_payload())
                else:
                    player = room.players.get(client_id, {})
                    room.clues_history.append(
                        {
                            "team": room.active_team,
                            "team_name": (
                                room.team_a_name
                                if room.active_team == "A"
                                else room.team_b_name
                            ),
                            "clue": clue,
                            "captain_name": player.get("name", "Capitano"),
                            "attempt": room.attempt_index + 1,
                        }
                    )
                    room.phase = "TEAM_GUESS"
                    await manager.broadcast(build_public_state())

            elif action == "CHALLENGE_CLUE":
                # Contestazione indizio illecito azionabile dalla Regia o squadra avversaria
                if room.phase == "TEAM_GUESS" and room.clues_history:
                    bad_clue = room.clues_history[-1]["clue"]
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
                            "message": f"🚨 INDIZIO CONTESTATO! '{bad_clue}' considerata parola composta/irregolare! (-3 Punti)",
                            "state": build_public_state(),
                        }
                    )
                    await manager.broadcast(get_secret_payload())

            elif action == "SUBMIT_GUESS":
                player = room.players.get(client_id, {})
                raw_guess = data.get("guess", "").strip()

                if not re.match(r"^[a-zA-ZàèéìòùÀÈÉÌÒÙ]+$", raw_guess):
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "message": "Inserisci una singola parola valida!",
                        }
                    )
                    continue

                guess = raw_guess.upper()
                correct_pwd = room.current_card["password"].upper()
                pts = POINTS_LADDER[min(room.attempt_index, len(POINTS_LADDER) - 1)]
                p_name = player.get("name", "Giocatore")

                room.guesses_history.append(
                    {"player": p_name, "guess": guess, "team": room.active_team}
                )

                if guess == correct_pwd:
                    # Uno del team ha indovinato: vittoria immediata
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
                            "guesser": p_name,
                            "password": correct_pwd,
                            "points": pts,
                            "state": build_public_state(),
                        }
                    )
                else:
                    # Errato: la squadra può continuare a provare liberamente
                    await manager.broadcast(
                        {
                            "type": "WRONG_ATTEMPT",
                            "player": p_name,
                            "guess": guess,
                            "message": f"❌ {p_name} ha provato '{guess}': errato! Altri del team possono tentare!",
                            "state": build_public_state(),
                        }
                    )

            elif action == "PASS_TURN":
                room.attempt_index += 1
                room.active_team = "B" if room.active_team == "A" else "A"

                if room.attempt_index >= len(POINTS_LADDER):
                    room.phase = "ROUND_END"
                    correct_pwd = room.current_card["password"].upper()
                    await manager.broadcast(
                        {
                            "type": "EXHAUSTED",
                            "message": f"❌ Tentativi esauriti! La parola corretta era: {correct_pwd}",
                            "password": correct_pwd,
                            "state": build_public_state(),
                        }
                    )
                else:
                    room.phase = "CAPTAIN_CLUE"
                    await manager.broadcast(
                        {
                            "type": "TURN_PASSED",
                            "message": f"La mano passa a {room.team_a_name if room.active_team == 'A' else room.team_b_name}!",
                            "state": build_public_state(),
                        }
                    )
                    await manager.broadcast(get_secret_payload())

    except WebSocketDisconnect:
        if client_id in room.players:
            del room.players[client_id]
        manager.disconnect(websocket)
        await manager.broadcast(build_public_state())


app.mount("/", StaticFiles(directory="static", html=True), name="static")
