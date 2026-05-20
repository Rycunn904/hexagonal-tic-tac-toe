import pygame
import socket
import threading
import math
import json
import Game
import hashlib

# ---------------- GAME STATE ----------------
game = Game.HexTTT()
state = {}

# ---------------- DISPLAY ----------------
WIDTH, HEIGHT = 800, 750
SIZE = 30
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Hexagonal TTT - Network Play')
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# camera
offset_x = 0
offset_y = 0
camera_speed = 20

# networking
sock = None
connected = False
failed = False
connecting = False
ID = None
buffer = ""

# UI input
input_text = ""
typing_active = True

# ---------------- HEX FUNCTIONS ----------------
def cube_to_pixel(q, r, s, ox=0, oy=0):
    x = SIZE * (3/2 * q)
    y = SIZE * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return int(WIDTH/2 + x + ox), int(HEIGHT/2 + y + oy)

def pixel_to_cube(px, py, ox=0, oy=0):
    x = px - WIDTH/2 - ox
    y = py - HEIGHT/2 - oy
    q = (2/3 * x) / SIZE
    r = (-1/3 * x + math.sqrt(3)/3 * y) / SIZE
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    else:
        rs = -rq - rr
    return rq, rr, rs

def draw_hex(surface, q, r, s, color, offset=0, width=2):
    cx, cy = cube_to_pixel(q, r, s, offset_x, offset_y)
    points = []
    for i in range(6):
        angle = math.radians(60 * i)
        px = cx + (SIZE - offset) * math.cos(angle)
        py = cy + (SIZE - offset) * math.sin(angle)
        points.append((px, py))
    pygame.draw.polygon(surface, color, points, width)

# ---------------- NETWORK ----------------
def send_client_checksum(sock):
    with open(__file__, "rb") as f:
        code_bytes = f.read()
    client_hash = hashlib.md5(code_bytes).hexdigest()
    sock.sendall(client_hash.encode())

def receive_data():
    global buffer, state, game, ID
    while True:
        try:
            data = sock.recv(4096) # type: ignore
            if not data:
                break
            buffer += data.decode()
            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1)
                if msg.startswith("ID:"):
                    ID = int(msg.split(":")[1])
                    print(f"You are Player {ID}")
                else:
                    state = json.loads(msg)
                    game.board = {}
                    for key, val in state['board'].items():
                        q, r, s = map(int, key.split(","))
                        game.board[(q, r, s)] = val
                    game.current_player = state['current_player']
                    game.round_number = state['round_number']
                    game.winner = state['winner']
                    game.current_radius = state['current_radius']
                    game.pieces_to_place = state['pieces_to_place']
        except:
            break

def handle_authentication(sock):
    # ---- STEP 1: RECEIVE CHALLENGE ----
    data = sock.recv(1024).decode().strip()

    if not data.startswith("CHALLENGE:"):
        print("Invalid server response")
        return False

    nonce = data.split(":")[1]

    # ---- STEP 2: HASH CLIENT CODE + NONCE ----
    with open(__file__, "rb") as f:
        code_bytes = f.read()

    client_hash = hashlib.sha256(
        code_bytes + nonce.encode()
    ).hexdigest()

    # ---- STEP 3: SEND RESPONSE ----
    sock.sendall(f"RESPONSE:{client_hash}\n".encode())

    # ---- STEP 4: WAIT FOR RESULT ----
    result = sock.recv(1024).decode().strip()

    if result != "OK:CLIENT_VERIFIED":
        print("Verification failed:", result)
        return False

    return True

def connect_to_server(address):
    global sock, connected, failed, connecting, ID
    try:
        connecting = True
        failed = False
        ip, port = address.split(":")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, int(port)))

        if not handle_authentication(sock):
            sock.close()
            failed = True
            connecting = False
            return

        threading.Thread(target=receive_data, daemon=True).start()
        connected = True
        connecting = False
        failed = False
    except Exception as e:
        print("Connection failed:", e)
        connecting = False
        failed = True

# ---------------- MAIN LOOP ----------------
running = True
camera_movement = {"left": False, "right": False, "up": False, "down": False}

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not connected:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    threading.Thread(target=lambda:connect_to_server(input_text)).start()
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    camera_movement["left"] = True
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    camera_movement["right"] = True
                elif event.key in (pygame.K_w, pygame.K_UP):
                    camera_movement["up"] = True
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    camera_movement["down"] = True
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    camera_movement["left"] = False
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    camera_movement["right"] = False
                elif event.key in (pygame.K_w, pygame.K_UP):
                    camera_movement["up"] = False
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    camera_movement["down"] = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ID is not None and game.current_player == ID:
                    mx, my = event.pos
                    q, r, s = pixel_to_cube(mx, my, offset_x, offset_y)
                    sock.sendall(f"MOVE:{q},{r},{s}\n".encode()) # type: ignore

    if camera_movement["left"]:
        offset_x += camera_speed
    if camera_movement["right"]:
        offset_x -= camera_speed
    if camera_movement["up"]:
        offset_y += camera_speed
    if camera_movement["down"]:
        offset_y -= camera_speed

    screen.fill((15, 15, 15))

    if not connected:
        fail_text = font.render("Connection Failed" if failed else "Connecting...", True, (255, 0, 0) if failed else (0, 255, 0))
        title = font.render("Enter Server IP:PORT", True, (255, 255, 255))
        text = font.render(input_text, True, (200, 200, 200))
        if failed or connecting:
            screen.blit(fail_text, (WIDTH//2 - 120, HEIGHT//2 - 80))
        screen.blit(title, (WIDTH//2 - 120, HEIGHT//2 - 40))
        screen.blit(text, (WIDTH//2 - 120, HEIGHT//2))
    else:
        for (q, r, s), cell in game.board.items():
            draw_hex(screen, q, r, s, (100, 100, 100), 0, 1)
            if cell == 1:
                draw_hex(screen, q, r, s, (220, 80, 80), 5, 0)
            elif cell == 2:
                draw_hex(screen, q, r, s, (80, 120, 220), 5, 0)
        player_text = f"You are Player {ID}" if ID else "Connecting..."
        turn_text = f"Current Turn: Player {game.current_player}"
        moves_text = f"Moves Left: {game.pieces_to_place}"
        win_text = f"Player {game.winner} wins!" if game.winner else ""
        screen.blit(font.render(player_text, True, (255, 255, 255)), (10, 10))
        screen.blit(font.render(turn_text, True, (200, 200, 200)), (10, 40))
        screen.blit(font.render(moves_text, True, (200, 200, 200)), (10, 70))
        screen.blit(font.render(win_text, True, (255, 200, 0)), (10, 100))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()