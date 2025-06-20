import random
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

BOARD_SIZE = 3

class Game:
    def __init__(self):
        self.board = [['w'] * BOARD_SIZE] + [['.'] * BOARD_SIZE] + [['b'] * BOARD_SIZE]
        self.turn = 'w'
        self.winner = None

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
            # Prüfe nach dem Zug, ob der nächste Spieler noch Züge hat
            if not self.get_valid_moves(self.turn):
                self.winner = "draw"

    def is_game_over(self):
        return self.winner is not None

    def get_state(self):
        return tuple(tuple(row) for row in self.board), self.turn

# --- Flask Backend ---
app = Flask(__name__)
CORS(app)

games = {}  # session_id -> Game

@app.route("/new_game", methods=["POST"])
def new_game():
    session_id = request.json.get("session_id")
    games[session_id] = Game()
    return jsonify({"status": "ok"})

@app.route("/get_state", methods=["GET"])
def get_state():
    session_id = request.args.get("session_id")
    game = games.get(session_id)
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
    game = games.get(session_id)
    if not game:
        return jsonify({"error": "No such game"}), 404
    move_tuple = (tuple(move[0]), tuple(move[1]))
    if move_tuple not in game.get_valid_moves(game.turn):
        return jsonify({"error": "Invalid move"}), 400
    game.make_move(move_tuple)
    return jsonify({
        "board": game.board,
        "turn": game.turn,
        "winner": game.winner
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)