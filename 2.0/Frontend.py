import pygame
import sys
import requests
from Backend import Game, QLearningAI, train_ai_selfplay, reset_ai

BOARD_SIZE = 3
SQUARE_SIZE = 120
WIDTH, HEIGHT = 600, 500
WHITE = (240, 240, 240)
BLACK = (30, 30, 30)
GREEN = (100, 200, 100)
BLUE = (100, 100, 200)
RED = (200, 100, 100)
MENU_BG = (60, 60, 80)
BUTTON_COLOR = (180, 180, 220)
BUTTON_HOVER = (120, 180, 255)
BUTTON_TEXT = (30, 30, 30)

def draw_board(screen, game, selected=None, valid_moves=[]):
    offset_x = (WIDTH - BOARD_SIZE * SQUARE_SIZE) // 2
    offset_y = (HEIGHT - BOARD_SIZE * SQUARE_SIZE) // 2
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            rect = pygame.Rect(offset_x + c*SQUARE_SIZE, offset_y + r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            color = WHITE if (r+c)%2==0 else GREEN
            if selected == (r, c):
                color = BLUE
            elif any(move[1] == (r, c) for move in valid_moves):
                color = RED
            pygame.draw.rect(screen, color, rect)
            piece = game.board[r][c]
            if piece == 'w':
                pygame.draw.circle(screen, (220,220,220), rect.center, SQUARE_SIZE//3)
            elif piece == 'b':
                pygame.draw.circle(screen, (50,50,50), rect.center, SQUARE_SIZE//3)
    pygame.display.flip()

def draw_menu(screen, font, buttons, title="3x3 Schach mit 3 Bauern"):
    screen.fill(MENU_BG)
    title_surf = font.render(title, True, (255,255,255))
    screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 40))
    mouse = pygame.mouse.get_pos()
    for rect, text in buttons:
        color = BUTTON_HOVER if rect.collidepoint(mouse) else BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=10)
        text_surf = font.render(text, True, BUTTON_TEXT)
        screen.blit(text_surf, (rect.x + rect.width//2 - text_surf.get_width()//2,
                                rect.y + rect.height//2 - text_surf.get_height()//2))
    pygame.display.flip()

def menu_loop(screen):
    font = pygame.font.SysFont(None, 36)
    btn_w = 220
    btn_h = 45
    gap = 18
    start_y = 110
    buttons = [
        (pygame.Rect(WIDTH//2 - btn_w//2, start_y + i*(btn_h + gap), btn_w, btn_h), text)
        for i, text in enumerate(["PvE", "PvP (Netzwerk)", "KI trainieren", "KI zurücksetzen"])
    ]
    while True:
        draw_menu(screen, font, buttons)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, (rect, _) in enumerate(buttons):
                    if rect.collidepoint(event.pos):
                        return i+1  # 1: KI, 2: Netzwerk, 3: Training, 4: Reset

def text_input_box(screen, prompt, y, font):
    input_text = ""
    active = True
    while active:
        screen.fill((60, 60, 80))
        prompt_surf = font.render(prompt, True, (255,255,255))
        screen.blit(prompt_surf, (WIDTH//2 - prompt_surf.get_width()//2, y))
        input_surf = font.render(input_text, True, (255,255,0))
        screen.blit(input_surf, (WIDTH//2 - input_surf.get_width()//2, y+50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if len(input_text) < 20:
                        input_text += event.unicode
    return input_text.strip()

def color_choice_box(screen, font):
    while True:
        screen.fill((60, 60, 80))
        prompt = font.render("Welche Farbe spielst du?", True, (255,255,255))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 60))
        w_box = pygame.Rect(WIDTH//2 - 110, HEIGHT//2, 80, 50)
        b_box = pygame.Rect(WIDTH//2 + 30, HEIGHT//2, 80, 50)
        pygame.draw.rect(screen, (220,220,220), w_box)
        pygame.draw.rect(screen, (50,50,50), b_box)
        w_text = font.render("Weiß", True, (0,0,0))
        b_text = font.render("Schwarz", True, (255,255,255))
        screen.blit(w_text, (w_box.x + w_box.width//2 - w_text.get_width()//2, w_box.y + w_box.height//2 - w_text.get_height()//2))
        screen.blit(b_text, (b_box.x + b_box.width//2 - b_text.get_width()//2, b_box.y + b_box.height//2 - b_text.get_height()//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if w_box.collidepoint(event.pos):
                    return "w"
                elif b_box.collidepoint(event.pos):
                    return "b"

def pvp_network_game(screen):
    font = pygame.font.SysFont(None, 36)
    # IP-Adresse und Session-ID abfragen
    server = text_input_box(screen, "Server-IP (z.B. http://192.168.178.42:5000):", HEIGHT//2 - 120, font)
    session_id = text_input_box(screen, "Session-ID für das Spiel eingeben:", HEIGHT//2 - 60, font)
    player = color_choice_box(screen, font)
    try:
        requests.post(f"{server}/new_game", json={"session_id": session_id})
    except Exception as e:
        print("Konnte kein neues Spiel starten:", e)
    selected = None
    valid_moves = []
    running = True
    while running:
        resp = requests.get(f"{server}/get_state", params={"session_id": session_id})
        if resp.status_code != 200:
            print("Fehler beim Abrufen des Spielstands.")
            pygame.time.wait(2000)
            continue
        data = resp.json()
        board = data["board"]
        turn = data["turn"]
        winner = data["winner"]
        # Dummy-Game-Objekt für draw_board
        game = Game()
        game.board = [row[:] for row in board]
        draw_board(screen, game, selected, valid_moves)
        if winner:
            msg = "Unentschieden!" if winner == "draw" else f"Spiel beendet! Gewinner: {winner}"
            text = font.render(msg, True, (255,0,0))
            screen.blit(text, (10, HEIGHT//2-20))
            pygame.display.flip()
            pygame.time.wait(2500)
            running = False
            continue
        if turn != player:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            pygame.time.wait(1000)
            continue
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                offset_x = (WIDTH - BOARD_SIZE * SQUARE_SIZE) // 2
                offset_y = (HEIGHT - BOARD_SIZE * SQUARE_SIZE) // 2
                x, y = event.pos
                r = (y - offset_y) // SQUARE_SIZE
                c = (x - offset_x) // SQUARE_SIZE
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    if selected is None:
                        if board[r][c] == player:
                            selected = (r, c)
                            # valid_moves anzeigen
                            dummy_game = Game()
                            dummy_game.board = [row[:] for row in board]
                            valid_moves = [m for m in dummy_game.get_valid_moves(player) if m[0] == selected]
                    else:
                        move = [list(selected), [r, c]]
                        resp = requests.post(f"{server}/move", json={"session_id": session_id, "move": move})
                        if resp.status_code == 200:
                            selected = None
                            valid_moves = []
                        else:
                            print("Ungültiger Zug!")
                            selected = None
                            valid_moves = []

def gui_game(screen, vs_ai=True):
    font = pygame.font.SysFont(None, 36)
    game = Game()
    ai = QLearningAI('b')
    selected = None
    valid_moves = []
    running = True
    while running:
        draw_board(screen, game, selected, valid_moves)
        if game.is_game_over():
            msg = "Unentschieden!"
            if game.winner == 'w':
                msg = "Weiß gewinnt!"
            elif game.winner == 'b':
                msg = "Schwarz gewinnt!"
            text = font.render(msg, True, (255,0,0))
            screen.blit(text, (10, HEIGHT//2-20))
            pygame.display.flip()
            pygame.time.wait(2500)
            running = False
            continue
        if game.turn == 'w' or not vs_ai:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    offset_x = (WIDTH - BOARD_SIZE * SQUARE_SIZE) // 2
                    offset_y = (HEIGHT - BOARD_SIZE * SQUARE_SIZE) // 2
                    x, y = event.pos
                    r = (y - offset_y) // SQUARE_SIZE
                    c = (x - offset_x) // SQUARE_SIZE
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                        if selected is None:
                            if game.board[r][c] == game.turn:
                                selected = (r, c)
                                valid_moves = [m for m in game.get_valid_moves(game.turn) if m[0] == selected]
                        else:
                            move = (selected, (r, c))
                            if move in game.get_valid_moves(game.turn):
                                game.make_move(move)
                                selected = None
                                valid_moves = []
                            else:
                                selected = None
                                valid_moves = []
        else:
            pygame.time.wait(400)
            move = ai.choose_move(game)
            game.make_move(move)
            reward = 0
            if game.winner == 'b':
                reward = 1
            elif game.winner == 'w':
                reward = -500
            elif game.is_game_over():
                reward = 0.5
            ai.update(reward, game.get_state(), game.is_game_over(), game)
    if vs_ai:
        ai.save_qtable()

def show_training_progress(screen, episodes_done):
    font = pygame.font.SysFont(None, 36)
    msg = f"{episodes_done} Spiele abgeschlossen."
    screen.fill(MENU_BG)
    text = font.render(msg, True, (255,255,255))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
    pygame.display.flip()

def train_ai_selfplay_gui(screen, episodes=5000):
    font = pygame.font.SysFont(None, 36)
    print(f"Starte Selbstlernmodus für {episodes} Spiele ...")
    def progress_callback(episodes_done):
        show_training_progress(screen, episodes_done)
    train_ai_selfplay(episodes, progress_callback)
    print("Training abgeschlossen! Die KI wurde trainiert.")
    screen.fill(MENU_BG)
    text = font.render("Training abgeschlossen!", True, (255,255,255))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
    pygame.display.flip()
    pygame.time.wait(2000)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3x3 Schach mit 3 Bauern (Pygame-GUI)")
    while True:
        mode = menu_loop(screen)
        if mode == 4:
            reset_ai()
            font = pygame.font.SysFont(None, 36)
            screen.fill(MENU_BG)
            text = font.render("KI wurde zurückgesetzt!", True, (255,255,255))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
            pygame.display.flip()
            pygame.time.wait(1500)
        elif mode == 3:
            train_ai_selfplay_gui(screen, 5000)
        elif mode == 2:
            pvp_network_game(screen)
        else:
            gui_game(screen, vs_ai=True)