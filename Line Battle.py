import pygame
import sys
import random

# Initialize Pygame
pygame.init()

pygame.mixer.init()

# Constants
WINDOW_SIZE = 620
PLAY_AREA = 500
CELL_SIZE = 20
FPS = 60

# Fonts and Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)
HIGHLIGHT_COLOR = (80, 80, 0)

color_inactive = pygame.Color('lightskyblue3')
color_active = pygame.Color('dodgerblue2')
font_grid = pygame.font.SysFont(None, 36)
font_box = pygame.font.Font(None, 32)
font_btn = pygame.font.Font(None, 24)

# Setup the display
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("50x50 Grid & Text Box")
clock = pygame.time.Clock()

try:
    pygame.mixer.music.load(r"C:\Users\rep39\Downloads\erik2.mp3")
    pygame.mixer.music.play(loops=-1)
    pygame.mixer.music.set_volume(0.5)
except pygame.error as e:
    print(f"Error loading sound file: {e}")

# Load sound effects
try:
    fire_sound = pygame.mixer.Sound(r"C:\Users\rep39\Downloads\PairDrop_files_20260821_1058\Laser_1_(Gravity_Sound).mp3")
    hit_sound = pygame.mixer.Sound(r"C:\Users\rep39\Downloads\PairDrop_files_20260821_1058\Laser_5_(Gravity_Sound).mp3")
    
    # Optional volume settings (0.0 to 1.0)
    fire_sound.set_volume(0.6)
    hit_sound.set_volume(0.8)
except pygame.error as e:
    print(f"Error loading sound effects: {e}")
    fire_sound = None
    hit_sound = None

# --- Spawning System ---
def spawn_entity(w_cells, h_cells, col_range, row_range, existing_rects):
    """Spawns an entity ensuring it doesn't overlap or touch existing entities."""
    for _ in range(100): # Attempt up to 100 times to find a valid spot
        c = random.randint(col_range[0], col_range[1])
        r = random.randint(row_range[0], row_range[1])
        new_rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, w_cells * CELL_SIZE, h_cells * CELL_SIZE)
    
        check_rect = new_rect.inflate(CELL_SIZE * 2, CELL_SIZE * 2)
        
        overlap = False
        for ex_rect in existing_rects:
            if check_rect.colliderect(ex_rect):
                overlap = True
                break
        
        if not overlap:
            return new_rect
            
    return pygame.Rect(col_range[0] * CELL_SIZE, row_range[0] * CELL_SIZE, w_cells * CELL_SIZE, h_cells * CELL_SIZE)

def get_all_occupied_rects(exclude_player=None):
    """Gets bounding boxes for all current objects to check against during respawns"""
    rects = []
    if exclude_player != 1:
        rects.append(pygame.Rect(player1[0][0], player1[0][1], CELL_SIZE, CELL_SIZE))
    if exclude_player != 2:
        rects.append(pygame.Rect(player2[0][0], player2[0][1], CELL_SIZE, CELL_SIZE))
    for obs in obstacles:
        rects.append(pygame.Rect(obs[0], obs[1], CELL_SIZE * 3, CELL_SIZE * 3))
    return rects

# --- Game State Variables ---
def reset_game():
    global player1, player2, player1_lives, player2_lives
    global obstacles, turn, drawn_curves, active_line, highlighted_cells
    global game_over, text, active, current_mode, last_equation_text
    
    player1_lives = 3
    player2_lives = 3
    
    existing_rects = []
    
    # Spawn Obstacles (Center-ish area)
    obstacles = []
    for _ in range(5):
        obs_rect = spawn_entity(3, 3, (5, 19), (5, 19), existing_rects)
        obstacles.append([obs_rect.x, obs_rect.y])
        existing_rects.append(obs_rect)

    # Spawn P1 (Top Left area)
    p1_rect = spawn_entity(1, 1, (0, 10), (0, 10), existing_rects)
    player1 = [[p1_rect.x, p1_rect.y]]
    existing_rects.append(p1_rect)
    
    # Spawn P2 (Bottom Right area)
    p2_rect = spawn_entity(1, 1, (14, 24), (14, 24), existing_rects)
    player2 = [[p2_rect.x, p2_rect.y]]
    existing_rects.append(p2_rect)
    
    turn = 1
    drawn_curves = []
    active_line = None        
    highlighted_cells = set() 
    game_over = False
    text = ''
    active = False
    current_mode = "linear"
    last_equation_text = ""

# Initialize game state
reset_game()

# Text Box Variables
input_box = pygame.Rect(0, 500, 500, 40)
arrow_key_text = "" 

# Button Variables
linear_button_rect = pygame.Rect(500, 50, 100, 50)
linear_button_text = "y=mx"

quadratic_button_rect = pygame.Rect(500, 150, 100, 50) 
quadratic_button_text = "y=ax²+bx"

cubic_button_rect = pygame.Rect(500, 250, 100, 50)
cubic_button_text = "y=ax³+bx²+cx"

def next_turn():
    global turn
    turn = 2 if turn == 1 else 1

def select_linear():
    global current_mode
    current_mode = "linear"

def select_quadratic():
    global current_mode
    current_mode = "quadratic"

def select_cubic():
    global current_mode
    current_mode = "cubic"

def draw_grid():
    """Draws the 50x50 grid of squares with white outlines."""
    for x in range(0, PLAY_AREA, CELL_SIZE):
        for y in range(0, PLAY_AREA, CELL_SIZE):
            grid_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, WHITE, grid_rect, 1)

def create_line_points(func, turn, start_x, start_y):
    """Generates points scaled to the grid (1 unit = 1 grid square)"""
    points = []
    step = 0.5 if turn == 1 else -0.5 
    for i in range(1200): 
        x_pixel_offset = i * step
        math_x = x_pixel_offset / CELL_SIZE
        math_y = func(math_x)
        y_pixel_offset = math_y * CELL_SIZE
        
        screen_x = start_x + x_pixel_offset
        screen_y = start_y - y_pixel_offset
        points.append((screen_x, screen_y))
    return points

def check_collision(pt, target_player_pos):
    """Checks if a point hits the wall, an obstacle, or a player"""
    cx, cy = int(pt[0] // CELL_SIZE), int(pt[1] // CELL_SIZE)
    
    if cx < 0 or cx >= 25 or cy < 0 or cy >= 25:
        return "wall"
        
    for obs in obstacles:
        ox, oy = obs[0] // CELL_SIZE, obs[1] // CELL_SIZE
        if ox <= cx < ox + 3 and oy <= cy < oy + 3:
            obstacles.remove(obs) 
            return "obstacle"
            
    tx, ty = target_player_pos[0][0] // CELL_SIZE, target_player_pos[0][1] // CELL_SIZE
    if cx == tx and cy == ty:
        return "player"
        
    return None

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not game_over and active_line is None:
                if linear_button_rect.collidepoint(event.pos):
                    select_linear()
                elif quadratic_button_rect.collidepoint(event.pos):
                    select_quadratic()
                elif cubic_button_rect.collidepoint(event.pos):
                    select_cubic()
                
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
            
        elif event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_r:
                    reset_game()
            elif active and active_line is None:
                if event.key == pygame.K_RETURN:
                    try:
                        params = [float(val.strip()) for val in text.split(',')]
                        valid_input = False 
                        func = None

                        if current_mode == "linear" and len(params) == 1:
                            m = params[0]
                            func = lambda x, m=m: m * x
                            last_equation_text = f"y = {m}x"
                            valid_input = True
                        elif current_mode == "quadratic" and len(params) == 2:
                            a, b = params
                            func = lambda x, a=a, b=b: a * (x**2) + b * x
                            last_equation_text = f"y = {a}x² + {b}x"
                            valid_input = True
                        elif current_mode == "cubic" and len(params) == 3:
                            a, b, c = params
                            func = lambda x, a=a, b=b, c=c: a * (x**3) + b * (x**2) + c * x
                            last_equation_text = f"y = {a}x³ + {b}x² + {c}x"
                            valid_input = True
                        else:
                            print(f"Invalid parameters for {current_mode} mode!")

                        if valid_input:
                            drawn_curves.clear()
                            highlighted_cells.clear()
                            
                            curr_player = player1 if turn == 1 else player2
                            start_x = curr_player[0][0] + CELL_SIZE // 2
                            start_y = curr_player[0][1] + CELL_SIZE // 2
                            
                            line_color = BLUE if turn == 1 else RED
                            pts = create_line_points(func, turn, start_x, start_y)
                            
                            active_line = {
                                'points': pts,
                                'current_idx': 0,
                                'color': line_color,
                                'drawn_points': []
                            }
                            if fire_sound:
                                    fire_sound.play()
                            
                    except ValueError:
                        print("Invalid input! Use numbers and commas.")

                    text = '' 
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

    # Update Game Logic
    if active_line is not None and not game_over:
        pts = active_line['points']
        idx = active_line['current_idx']
        anim_speed = 20 
        
        target_player = player2 if turn == 1 else player1
        
        for i in range(anim_speed):
            if idx >= len(pts):
                drawn_curves.append((active_line['drawn_points'], active_line['color']))
                active_line = None
                next_turn()
                break
                
            pt = pts[idx]
            col_res = check_collision(pt, target_player)
            
            cx, cy = int(pt[0] // CELL_SIZE), int(pt[1] // CELL_SIZE)
            if 0 <= cx < 25 and 0 <= cy < 25:
                highlighted_cells.add((cx, cy))
                
            active_line['drawn_points'].append(pt)
            
            if col_res: 

                if hit_sound:
                        hit_sound.play()

                if col_res == "player":
                    if turn == 1:
                        player2_lives -= 1
                        if player2_lives > 0:
                            occupied = get_all_occupied_rects(exclude_player=2)
                            new_rect = spawn_entity(1, 1, (14, 24), (14, 24), occupied)
                            player2[0] = [new_rect.x, new_rect.y]
                        else:
                            game_over = True
                    else:
                        player1_lives -= 1
                        if player1_lives > 0:
                            occupied = get_all_occupied_rects(exclude_player=1)
                            new_rect = spawn_entity(1, 1, (0, 10), (0, 10), occupied)
                            player1[0] = [new_rect.x, new_rect.y]
                        else:
                            game_over = True
                            
                drawn_curves.append((active_line['drawn_points'], active_line['color']))
                active_line = None
                if not game_over:
                    next_turn()
                break
                
            idx += 1
            
        if active_line is not None:
            active_line['current_idx'] = idx

    # Draw Everything
    screen.fill(BLACK)
    
    for cx, cy in highlighted_cells:
        rect = pygame.Rect(cx * CELL_SIZE, cy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect)
        
    draw_grid()

    for segment in obstacles:
        pygame.draw.rect(screen, GRAY, (segment[0], segment[1], CELL_SIZE * 3, CELL_SIZE * 3))

    for segment in player1:
        pygame.draw.rect(screen, BLUE, (segment[0], segment[1], CELL_SIZE, CELL_SIZE))
    for segment in player2:
        pygame.draw.rect(screen, RED, (segment[0], segment[1], CELL_SIZE, CELL_SIZE))

    for points, line_color in drawn_curves:
        if len(points) >= 2:
            pygame.draw.lines(screen, line_color, False, points, 3)
            
    if active_line is not None:
        if len(active_line['drawn_points']) >= 2:
            pygame.draw.lines(screen, active_line['color'], False, active_line['drawn_points'], 3)

    # UI Base Components
    color = color_active if active else color_inactive
    txt_surface = font_box.render(text, True, WHITE)
    width = max(500, txt_surface.get_width() + 10)
    input_box.w = width
    screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
    pygame.draw.rect(screen, color, input_box, 2)

    # Draw Buttons
    for rect, txt, mode in [(linear_button_rect, linear_button_text, "linear"),
                            (quadratic_button_rect, quadratic_button_text, "quadratic"),
                            (cubic_button_rect, cubic_button_text, "cubic")]:
        btn_color = GREEN if current_mode == mode else GRAY
        pygame.draw.rect(screen, btn_color, rect) 
        btn_surface = font_btn.render(txt, True, BLACK) 
        btn_text_rect = btn_surface.get_rect(center=rect.center) 
        screen.blit(btn_surface, btn_text_rect) 

    # --- Draw Player 1 Lives & Coordinates ---
    p1_label = font_box.render("P1:", True, WHITE)
    screen.blit(p1_label, (10, 550))
    for i in range(player1_lives):
        pygame.draw.rect(screen, BLUE, (10 + (i * 25), 570, 15, 15))
    
    p1_coords = f"({int(player1[0][0] // CELL_SIZE)}, {int(player1[0][1] // CELL_SIZE)})"
    p1_coord_surf = font_box.render(p1_coords, True, BLUE)
    screen.blit(p1_coord_surf, (90, 565))

    # --- Draw Last Fired Equation ---
    if last_equation_text:
        eq_surf = font_btn.render(last_equation_text, True, WHITE)
        eq_rect = eq_surf.get_rect(center=(400, 520))
        screen.blit(eq_surf, eq_rect)

    # --- Draw Player 2 Lives & Coordinates ---
    p2_label = font_box.render("P2:", True, WHITE)
    screen.blit(p2_label, (340, 550)) # Adjusted X slightly to make room for coordinates
    for i in range(player2_lives):
        pygame.draw.rect(screen, RED, (340 + (i * 25), 570, 15, 15))
        
    p2_coords = f"({int(player2[0][0] // CELL_SIZE)}, {int(player2[0][1] // CELL_SIZE)})"
    p2_coord_surf = font_box.render(p2_coords, True, RED)
    screen.blit(p2_coord_surf, (420, 565))

    # Game Over Overlay
    if game_over:
        font_over = pygame.font.SysFont(None, 72)
        font_sub = pygame.font.SysFont(None, 36)
        winner = "Player 1" if player2_lives <= 0 else "Player 2"
        over_surf = font_over.render(f"{winner} Wins!", True, WHITE)
        sub_surf = font_sub.render("Press 'R' to Restart", True, WHITE)
        screen.blit(over_surf, (250 - over_surf.get_width()//2, 200))
        screen.blit(sub_surf, (250 - sub_surf.get_width()//2, 260))
        
    # Current Turn indicator
    turn_text = f"P{turn}'s Turn"
    turn_surf = font_grid.render(turn_text, True, BLUE if turn == 1 else RED)
    screen.blit(turn_surf, (500, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
