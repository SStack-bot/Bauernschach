import random
import pickle
import os

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
        self.turn = 'b' if self.turn == 'w' else 'w'

    def is_game_over(self):
        return self.winner is not None or not self.get_valid_moves(self.turn)

    def get_state(self):
        return tuple(tuple(row) for row in self.board), self.turn

class QLearningAI:
    def __init__(self, player, alpha=0.1, gamma=0.9, epsilon=0.05, qfile="qtable.pkl"):
        self.player = player
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.qfile = qfile
        self.q_table = self.load_qtable()
        self.last_state = None
        self.last_move = None

    def load_qtable(self):
        if os.path.exists(self.qfile):
            with open(self.qfile, "rb") as f:
                return pickle.load(f)
        return {}

    def save_qtable(self):
        with open(self.qfile, "wb") as f:
            pickle.dump(self.q_table, f)

    def choose_move(self, game):
        state = game.get_state()
        moves = game.get_valid_moves(self.player)
        if not moves:
            return None
        if random.random() < self.epsilon:
            move = random.choice(moves)
        else:
            qs = [self.q_table.get((state, m), 0) for m in moves]
            max_q = max(qs)
            best_moves = [m for m, q in zip(moves, qs) if q == max_q]
            move = random.choice(best_moves)
        self.last_state = state
        self.last_move = move
        return move

    def update(self, reward, new_state, done, game):
        if self.last_state is None or self.last_move is None:
            return
        old_q = self.q_table.get((self.last_state, self.last_move), 0)
        future_q = 0 if done else max([self.q_table.get((new_state, m), 0) for m in game.get_valid_moves(self.player)] + [0])
        self.q_table[(self.last_state, self.last_move)] = old_q + self.alpha * (reward + self.gamma * future_q - old_q)

def train_ai_selfplay(episodes=5000, progress_callback=None):
    ai_black = QLearningAI('b', epsilon=0.05)
    ai_white = QLearningAI('w', epsilon=0.05, qfile="qtable_white.pkl")
    for episode in range(episodes):
        game = Game()
        ai_black.last_state = None
        ai_black.last_move = None
        ai_white.last_state = None
        ai_white.last_move = None
        while not game.is_game_over():
            if game.turn == 'w':
                move = ai_white.choose_move(game)
                game.make_move(move)
            else:
                move = ai_black.choose_move(game)
                game.make_move(move)
            if game.is_game_over():
                if game.winner == 'b':
                    ai_black.update(1, game.get_state(), True, game)
                    ai_white.update(-500, game.get_state(), True, game)
                elif game.winner == 'w':
                    ai_black.update(-500, game.get_state(), True, game)
                    ai_white.update(1, game.get_state(), True, game)
                else:
                    ai_black.update(0.5, game.get_state(), True, game)
                    ai_white.update(0.5, game.get_state(), True, game)
        if progress_callback and (episode+1) % 500 == 0:
            progress_callback(episode+1)
    ai_black.save_qtable()
    ai_white.save_qtable()

def reset_ai():
    """Löscht die Q-Table-Dateien der KI."""
    for fname in ["qtable.pkl", "qtable_white.pkl"]:
        if os.path.exists(fname):
            os.remove(fname)