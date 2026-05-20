# Local (offline) two-player play using Game.HexTTT
import pygame
import sys
import math
import Game

# game engine
game = Game.HexTTT()

# display parameters
WIDTH, HEIGHT = 800, 750
SIZE = 30

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Hexagonal TTT - Local Play')
clock = pygame.time.Clock()

# camera offset for panning
offset_x = 0
offset_y = 0
camera_speed = 20

# helper coords

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
    rq = round(q)
    rr = round(r)
    rs = round(s)
    dq = abs(rq - q)
    dr = abs(rr - r)
    ds = abs(rs - s)
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


running = True

camera_movement = {"left": False, "right": False, "up": False, "down": False}

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                game = Game.HexTTT()
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
        elif event.type == pygame.MOUSEBUTTONDOWN and game.winner is None:
            mx, my = event.pos
            q, r, s = pixel_to_cube(mx, my, offset_x, offset_y)
            if game.place_piece(q, r, s):
                # if close to border, expand field
                max_dist = max(abs(q), abs(r), abs(s))
                if max_dist >= game.current_radius - 3:
                    game.current_radius = max(game.current_radius, max_dist + 3)
                    game.ensure_radius()

                if game.check_win():
                    print(f"Player {game.winner} wins!")
                else:
                    game.next_turn()

    if camera_movement["left"]:
        offset_x += camera_speed
    if camera_movement["right"]:
        offset_x -= camera_speed
    if camera_movement["up"]:
        offset_y += camera_speed
    if camera_movement["down"]:
        offset_y -= camera_speed

    screen.fill((10, 10, 10))

    # draw board cells
    for (q, r, s), cell in game.board.items():
        # draw base outline
        draw_hex(screen, q, r, s, (100, 100, 100), 0, 1)

        if cell == 1:
            draw_hex(screen, q, r, s, (220, 80, 80), 5, 0)
        elif cell == 2:
            draw_hex(screen, q, r, s, (80, 120, 220), 5, 0)

    # overlay UI text
    font = pygame.font.SysFont(None, 24)
    turn_text = f"Round {game.round_number}, Player {game.current_player} to move ({game.pieces_to_place} left this turn)"
    if game.winner:
        turn_text = f"Player {game.winner} wins! Press ESC to exit."
    text_surf = font.render(turn_text, True, (255, 255, 255))
    screen.blit(text_surf, (10, 10))

    instruct = font.render('WASD/Arrow pan, click to place. ESC to quit.', True, (200, 200, 200))
    screen.blit(instruct, (10, HEIGHT - 26))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit(0)
