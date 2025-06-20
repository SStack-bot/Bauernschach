import os
import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

BOARD_SIZE = 3
DB_PATH = os.path.join(os.path.dirname(__file__), "games.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                session_id TEXT PRIMARY KEY,
                board TEXT,
                turn TEXT,
                winner TEXT
            )
        """)

class Game:
    def __init__(self, board=None, turn='w', winner=None):
        if board is None:
            self.board = [['w'] * BOARD_SIZE] + [['.'] * BOARD_SIZE] + [['b'] * BOARD_SIZE]
        else:
            self.board = board
        self.turn = turn
        self.winner = winner

    def get_valid_moves(self, player):
        moves = []
        direction = 1 if player == 'w' else -1
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == player:
                    nr = r + direction
                    if 0 <= nr < BOARD_SIZE and self.board[nr][c] == '.':
                        moves.append(((r, c), (nr, c)))
                    for dc in [-1, 1]:
                        nc = c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if self.board[nr][nc] != '.' and self.board[nr][nc] != player:
                                moves.append(((r, c), (nr, nc)))
        return moves

    def make_move(self, move):
        (r1, c1), (r2, c2) = move
        player = self.board[r1][c1]
        self.board[r1][c1] = '.'
        self.board[r2][c2] = player
        if (player == 'w' and r2 == BOARD_SIZE - 1) or (player == 'b' and r2 == 0):
            self.winner = player
        elif not any('b' in row for row in self.board):
            self.winner = 'w'
        elif not any('w' in row for row in self.board):
            self.winner = 'b'
        else:
            self.turn = 'b' if self.turn == 'w' else 'w'
            if not self.get_valid_moves(self.turn):
                self.winner = "draw"

def save_game(session_id, game):
    with get_db() as db:
        db.execute(
            "REPLACE INTO games (session_id, board, turn, winner) VALUES (?, ?, ?, ?)",
            (session_id, json.dumps(game.board), game.turn, game.winner)
        )

def load_game(session_id):
    db = get_db()
    row = db.execute("SELECT * FROM games WHERE session_id = ?", (session_id,)).fetchone()
    if row:
        board = json.loads(row["board"])
        return Game(board, row["turn"], row["winner"])
    return None

# --- Flask Backend ---
app = Flask(__name__)
CORS(app)
init_db()

@app.route("/new_game", methods=["POST"])
def new_game():
    session_id = request.json.get("session_id")
    game = Game()
    save_game(session_id, game)
    return jsonify({"status": "ok"})

@app.route("/get_state", methods=["GET"])
def get_state():
    session_id = request.args.get("session_id")
    game = load_game(session_id)
    if not game:
        return jsonify({"error": "No such game"}), 404
    return jsonify({
        "board": game.board,
        "turn": game.turn,
        "winner": game.winner
    })

@app.route("/move", methods=["POST"])
def move():
    session_id = request.json.get("session_id")
    move = request.json.get("move")  # [[r1, c1], [r2, c2]]
    game = load_game(session_id)
    if not game:
        return jsonify({"error": "No such game"}), 404
    move_tuple = (tuple(move[0]), tuple(move[1]))
    if move_tuple not in game.get_valid_moves(game.turn):
        return jsonify({"error": "Invalid move"}), 400
    game.make_move(move_tuple)
    save_game(session_id, game)
    return jsonify({
        "board": game.board,
        "turn": game.turn,
        "winner": game.winner
    })

# Wichtig: Kein app.run() am Ende, wenn du auf PythonAnywhere hostest!

# if __name__ == "__main__":
#    app.run(host="0.0.0.0", debug=True)