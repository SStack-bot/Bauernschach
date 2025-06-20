import requests
import time

SERVER = "http://10.0.3.104:5000"
SESSION_ID = input("Session-ID für das Spiel eingeben (z.B. 'spiel123'): ")
PLAYER = input("Welche Farbe spielst du? (w für Weiß, b für Schwarz): ").strip().lower()

def print_board(board):
    print("  0 1 2")
    for i, row in enumerate(board):
        print(f"{i} " + " ".join(row))
    print()

def main():
    try:
        requests.post(f"{SERVER}/new_game", json={"session_id": SESSION_ID})
    except Exception as e:
        print("Konnte kein neues Spiel starten:", e)

    last_board = None
    last_turn = None

    while True:
        resp = requests.get(f"{SERVER}/get_state", params={"session_id": SESSION_ID})
        if resp.status_code != 200:
            print("Fehler beim Abrufen des Spielstands:", resp.text)
            break
        data = resp.json()
        board = data["board"]
        turn = data["turn"]
        winner = data["winner"]

        # Nur anzeigen, wenn sich Brett oder Spieler geändert hat
        if board != last_board or turn != last_turn:
            print_board(board)
            print(f"Am Zug: {turn}")
            last_board = [row[:] for row in board]
            last_turn = turn

        if winner:
            print(f"Spiel beendet! Gewinner: {winner}")
            break

        if turn != PLAYER:
            time.sleep(2)
            continue

        move_str = input("Dein Zug (z.B. 0 0 1 0): ")
        try:
            r1, c1, r2, c2 = map(int, move_str.strip().split())
            move = [[r1, c1], [r2, c2]]
        except Exception:
            print("Ungültiges Format!")
            continue
        resp = requests.post(f"{SERVER}/move", json={"session_id": SESSION_ID, "move": move})
        if resp.status_code != 200:
            print("Ungültiger Zug, bitte nochmal!", resp.text)

if __name__ == "__main__":
    main()