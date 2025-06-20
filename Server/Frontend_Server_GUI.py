import pygame
import requests
import time

SERVER = "https://swurbs.pythonanywhere.com"

BOARD_SIZE = 3
SQUARE_SIZE = 180
WIDTH, HEIGHT = BOARD_SIZE * SQUARE_SIZE, BOARD_SIZE * SQUARE_SIZE

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
                exit()
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
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if w_box.collidepoint(event.pos):
                    return "w"
                elif b_box.collidepoint(event.pos):
                    return "b"

def get_state(session_id):
    resp = requests.get(f"{SERVER}/get_state", params={"session_id": session_id})
    if resp.status_code != 200:
        return None
    return resp.json()

def send_move(session_id, move):
    resp = requests.post(f"{SERVER}/move", json={"session_id": session_id, "move": move})
    return resp.status_code == 200

def draw_board(screen, board, selected=None):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            rect = pygame.Rect(c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            color = (240,240,240) if (r+c)%2==0 else (100,200,100)
            pygame.draw.rect(screen, color, rect)
            piece = board[r][c]
            if piece == 'w':
                pygame.draw.circle(screen, (220,220,220), rect.center, SQUARE_SIZE//3)
            elif piece == 'b':
                pygame.draw.circle(screen, (50,50,50), rect.center, SQUARE_SIZE//3)
            if selected == (r, c):
                pygame.draw.rect(screen, (100,100,200), rect, 4)
    pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Online Bauernschach")
    font = pygame.font.SysFont(None, 40)

    # Session-ID und Farbe im GUI abfragen
    session_id = text_input_box(screen, "Session-ID für das Spiel eingeben:", HEIGHT//2 - 80, font)
    player = color_choice_box(screen, font)

    # Versuche, ein neues Spiel zu starten (ignoriert Fehler, falls es schon existiert)
    try:
        requests.post(f"{SERVER}/new_game", json={"session_id": session_id})
    except Exception as e:
        print("Konnte kein neues Spiel starten:", e)

    selected = None
    running = True

    while running:
        state = get_state(session_id)
        if not state:
            print("Fehler beim Abrufen des Spielstands.")
            time.sleep(2)
            continue
        board = state["board"]
        turn = state["turn"]
        winner = state["winner"]

        draw_board(screen, board, selected)

        if winner:
            if winner == "draw":
                print("Spiel beendet! Unentschieden!")
            else:
                print(f"Spiel beendet! Gewinner: {winner}")
            time.sleep(3)
            break

        if turn != player:
            # Warte, bis du dran bist
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            time.sleep(1)
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                r, c = y // SQUARE_SIZE, x // SQUARE_SIZE
                if selected is None:
                    if board[r][c] == player:
                        selected = (r, c)
                else:
                    move = [list(selected), [r, c]]
                    if send_move(session_id, move):
                        selected = None
                    else:
                        print("Ungültiger Zug!")
                        selected = None

if __name__ == "__main__":
    main()