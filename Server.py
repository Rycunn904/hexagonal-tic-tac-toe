import Game
import socket
import threading
import json
import tkinter as tk
from tkinter import scrolledtext
import math
import hashlib
import os

# ---------------- GAME ----------------
game = Game.HexTTT()

clients = []
running = False
server_socket = None
accept_thread = None

# ---------------- OFFICIAL CLIENT HASH ----------------
with open(__file__.replace("Server.py", "Client.py"), "rb") as f:
    OFFICIAL_CLIENT_CODE = f.read()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Hex TTT Server")

# ====== TOP: CONTROLS ======
top = tk.Frame(root)
top.pack(pady=5)

ip_entry = tk.Entry(top, width=15)
ip_entry.insert(0, "127.0.0.1")
ip_entry.grid(row=0, column=0, padx=5)

port_entry = tk.Entry(top, width=8)
port_entry.insert(0, "5000")
port_entry.grid(row=0, column=1, padx=5)

start_button = tk.Button(top, text="Start Server")
start_button.grid(row=0, column=2, padx=5)

quit_button = tk.Button(top, text="Shutdown Server")
quit_button.grid(row=0, column=3, padx=5)

# ====== MIDDLE: BOARD VIEW ======
canvas_size = 600
canvas = tk.Canvas(root, width=canvas_size, height=canvas_size, bg="#111111")
canvas.pack(pady=5)

# ====== BOTTOM: LOG ======
log = scrolledtext.ScrolledText(root, width=90, height=12, state="disabled")
log.pack(padx=10, pady=5)

# ====== COMMAND INPUT ======
cmd_entry = tk.Entry(root, width=70)
cmd_entry.pack(pady=5)

send_button = tk.Button(root, text="Send Command")
send_button.pack()

# ---------------- LOGGING ----------------
def log_print(msg):
    log.config(state="normal")
    log.insert(tk.END, msg + "\n")
    log.yview(tk.END)
    log.config(state="disabled")

# ---------------- HEX DRAW ----------------
SIZE = 18
offset_x = 0
offset_y = 0

def cube_to_pixel(q, r, s):
    x = SIZE * (3/2 * q)
    y = SIZE * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return canvas_size//2 + x + offset_x, canvas_size//2 + y + offset_y

def draw_hex(q, r, s, fill=None, outline="#666"):
    cx, cy = cube_to_pixel(q, r, s)
    points = []
    for i in range(6):
        angle = math.radians(60 * i)
        px = cx + SIZE * math.cos(angle)
        py = cy + SIZE * math.sin(angle)
        points.append((px, py))
    flat = [coord for p in points for coord in p]
    canvas.create_polygon(flat, outline=outline, fill=fill or "", width=1)

def redraw_board():
    canvas.delete("all")
    for (q, r, s), cell in game.board.items():
        color = None
        if cell == 1:
            color = "#cc4444"
        elif cell == 2:
            color = "#4477cc"
        draw_hex(q, r, s, fill=color)

    canvas.create_text(10, 10, anchor="nw",
                       text=f"Turn: Player {game.current_player}",
                       fill="white")

    if game.winner:
        canvas.create_text(10, 30, anchor="nw",
                           text=f"Winner: Player {game.winner}",
                           fill="yellow")

def schedule_redraw():
    root.after(0, redraw_board)

# ---------------- NETWORK ----------------
def broadcast(msg):
    data = msg + "\n"
    for c in clients:
        try:
            c.sendall(data.encode())
        except:
            pass

def broadcast_state():
    state = json.dumps(game.get_game_state())
    broadcast(state)
    schedule_redraw()

# ---------------- GAME HELPERS ----------------
def expand_if_needed(q, r, s):
    max_dist = max(abs(q), abs(r), abs(s))
    if max_dist >= game.current_radius - 2:
        game.current_radius = max(game.current_radius, max_dist + 2)
        game.ensure_radius()
        log_print(f"[BOARD EXPANDED] Radius: {game.current_radius}")

def reset_game():
    global game
    game = Game.HexTTT()
    log_print("[GAME RESET]")
    schedule_redraw()

# ---------------- CLIENT HANDLER ----------------
def handle_client(conn, addr, player_id):
    log_print(f"Incoming connection: {addr}")

    try:
        # ---- STEP 1: SEND CHALLENGE ----
        nonce = os.urandom(16).hex()
        conn.sendall(f"CHALLENGE:{nonce}\n".encode())

        # ---- STEP 2: RECEIVE RESPONSE ----
        response = conn.recv(1024).decode().strip()

        if not response.startswith("RESPONSE:"):
            conn.close()
            return

        client_hash = response.split(":")[1]

        # ---- STEP 3: VERIFY ----
        expected_hash = hashlib.sha256(
            OFFICIAL_CLIENT_CODE + nonce.encode()
        ).hexdigest()

        if client_hash != expected_hash:
            log_print(f"[CHEAT DETECTED] {addr}")
            conn.sendall(b"ERROR:INVALID_CLIENT\n")
            conn.close()
            return

        # ✅ VERIFIED
        conn.sendall(b"OK:CLIENT_VERIFIED\n")

    except Exception as e:
        log_print(f"Verification error: {e}")
        conn.close()
        return

    # -------- NOW ADD CLIENT --------
    clients.append(conn)
    log_print(f"Connected: {addr} as Player {player_id}")

    # ✅ NOW send ID + game state
    conn.sendall(f"ID:{player_id}\n".encode())
    conn.sendall((json.dumps(game.get_game_state()) + "\n").encode())

    buffer = ""

    # -------- GAME LOOP --------
    while running:
        try:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1)

                if msg.startswith("MOVE"):
                    q, r, s = map(int, msg.split(":")[1].split(","))

                    if game.current_player == player_id:
                        if game.place_piece(q, r, s):
                            expand_if_needed(q, r, s)

                            if not game.check_win():
                                game.next_turn()
                            else:
                                game.pieces_to_place = 0

                            broadcast_state()

                log_print(f"{addr}: {msg}")

        except:
            break

    log_print(f"{addr} disconnected")

    conn.close()
    if conn in clients:
        clients.remove(conn)

# ---------------- SERVER ----------------
def accept_clients():
    global server_socket
    player_id = 1

    while running and player_id <= 2:
        try:
            conn, addr = server_socket.accept()  # type: ignore

            # DO NOT add to clients yet
            # DO NOT send ID yet

            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, player_id),
                daemon=True
            )
            thread.start()

            player_id += 1

        except socket.timeout:
            continue
        except OSError:
            break

    log_print("Accept thread stopped.")

def start_server():
    global server_socket, running, accept_thread
    if running:
        log_print("[WARNING] Server already running")
        return

    HOST = ip_entry.get()
    PORT = int(port_entry.get())

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.settimeout(1.0)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    running = True

    start_button.config(state="disabled")
    ip_entry.config(state="disabled")
    port_entry.config(state="disabled")

    log_print(f"Server started on {HOST}:{PORT}")

    accept_thread = threading.Thread(target=accept_clients, daemon=True)
    accept_thread.start()

    schedule_redraw()

def shutdown_server():
    global running, server_socket
    if not running:
        log_print("[WARNING] Server not running")
        return

    log_print("Shutting down server...")
    running = False

    for c in clients:
        try:
            c.close()
        except:
            pass

    clients.clear()

    try:
        server_socket.close() # type: ignore
    except:
        pass

    server_socket = None

    start_button.config(state="normal")
    ip_entry.config(state="normal")
    port_entry.config(state="normal")

    log_print("Server stopped.")

# ---------------- COMMANDS ----------------
def run_command(cmd):
    if cmd == "help":
        log_print("help - Show this message\n"
        "state - Print game state\n"
        "reset - Reset the game\n"
        "expand - Expand the board\n")
    if cmd == "state":
        log_print(json.dumps(game.get_game_state(), indent=2))
    elif cmd == "reset":
        reset_game()
        broadcast_state()
    elif cmd == "expand":
        game.expand_board()
        broadcast_state()
    elif cmd.startswith("say "):
        msg = cmd[4:]
        broadcast(f"SERVER:{msg}")
        log_print(f"[Broadcast] {msg}")
    elif cmd == "quit":
        shutdown_server()
    else:
        log_print("Unknown command")

def send_command():
    cmd = cmd_entry.get()
    cmd_entry.delete(0, tk.END)
    run_command(cmd)

# ---------------- BINDINGS ----------------
start_button.config(command=start_server)
quit_button.config(command=shutdown_server)
send_button.config(command=send_command)
cmd_entry.bind("<Return>", lambda e: send_command())

# ---------------- RUN ----------------
root.mainloop()