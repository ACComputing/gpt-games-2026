#!/usr/bin/env python3
# Ultra!Pong — pure pygame, no audio files, one file only
# Optimized for consistent 60fps with Windows XP speed

import pygame
import math
import random
import array

# =====================
# CONFIG - OPTIMIZED FOR 60FPS
# =====================
INTERNAL_W, INTERNAL_H = 256, 240
SCALE = 3
WIN_W, WIN_H = INTERNAL_W * SCALE, INTERNAL_H * SCALE
FPS = 60
TARGET_FRAME_TIME = 1000 / FPS

# Windows XP-style speeds
PADDLE_W = 6
PADDLE_H = 36
BALL_SIZE = 4
PADDLE_MARGIN = 10

# Physics constants
PADDLE_SPEED = 180.0
AI_SPEED = 155.0
BALL_BASE_SPEED = 145.0
BALL_MAX_SPEED = 320.0
BALL_ACCEL = 1.035
MAX_BOUNCE_ANGLE = 60
MAX_SERVE_ANGLE = 25

# Colors
DEFAULT_BG = (0, 0, 128)      # Classic XP blue
FG = (240, 240, 240)          # XP silver/gray
DIM = (192, 192, 192)         # Light gray
DEFAULT_ACCENT = (10, 36, 106) # XP dark blue
HIGHLIGHT = (255, 255, 255)   # White
BUTTON_HOVER = (60, 60, 180)  # Lighter blue for hover

# Game States
STATE_MENU = 0
STATE_PLAY = 1
STATE_HELP = 2
STATE_CREDITS = 3
STATE_ABOUT = 4

# =====================
# HELPERS
# =====================
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def generate_beep(frequency=440, duration=0.1, volume=0.3):
    """Generates a square wave beep sound in memory."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buffer = array.array('h', [0] * n_samples)
    amplitude = int(32767 * volume)
    period = sample_rate / frequency
    
    for i in range(n_samples):
        if (i // (period / 2)) % 2 == 0:
            buffer[i] = amplitude
        else:
            buffer[i] = -amplitude
            
    return pygame.mixer.Sound(buffer)

# =====================
# MAIN
# =====================
def main():
    # Pre-init mixer for low latency procedural sound
    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()
    
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("ACS!Pong 0.1 [C] AC Gaming Division")
    
    # Pre-create surfaces
    frame = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.HWSURFACE)
    scaled = pygame.Surface((WIN_W, WIN_H), pygame.HWSURFACE)
    clock = pygame.time.Clock()
    
    # Fonts
    font = pygame.font.Font(None, 18)
    big_font = pygame.font.Font(None, 28)
    title_font = pygame.font.Font(None, 40)
    
    # Generate Sounds
    try:
        snd_paddle = generate_beep(440, 0.05)
        snd_wall = generate_beep(220, 0.05)
        snd_score = generate_beep(880, 0.2)
        snd_start = generate_beep(660, 0.1)
        sound_enabled = True
    except:
        sound_enabled = False
        print("Audio initialization failed. Sound disabled.")

    def play_sound(snd):
        if sound_enabled:
            snd.play()

    # Pre-render static text
    title_text = big_font.render("ACS!Pong 0.1", True, HIGHLIGHT)
    paused_text = big_font.render("PAUSED", True, HIGHLIGHT)
    
    # Scanlines
    scanlines = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
    for y in range(0, INTERNAL_H, 2):
        pygame.draw.line(scanlines, (0, 0, 0, 35), (0, y), (INTERNAL_W, y))
    
    # Global Game State
    current_state = STATE_MENU
    
    # Gameplay settings
    famicom_visuals = True
    famicom_mouse = True
    mouse_grab = False # Released by default in menu
    mouse_sens = 1.2
    single_player = True
    paused = False
    serving = True
    
    bg_color = DEFAULT_BG
    
    # Paddle/Ball Init
    left_y = right_y = (INTERNAL_H - PADDLE_H) / 2.0
    left_x = float(PADDLE_MARGIN)
    right_x = float(INTERNAL_W - PADDLE_MARGIN - PADDLE_W)
    score_l = score_r = 0
    ball_speed = BALL_BASE_SPEED
    ball_x = ball_y = 0
    ball_vx = ball_vy = 0.0
    serve_dir = 1
    
    # Frame timing
    last_time = pygame.time.get_ticks()
    frame_count = 0
    fps_display = 0

    # =====================
    # LOGIC HELPERS
    # =====================
    def reset_game_state():
        nonlocal score_l, score_r, left_y, right_y, bg_color
        score_l = score_r = 0
        left_y = right_y = (INTERNAL_H - PADDLE_H) / 2.0
        bg_color = DEFAULT_BG
        reset_ball(random.choice([-1, 1]))

    def reset_ball(dir):
        nonlocal serving, ball_x, ball_y, ball_vx, ball_vy, ball_speed, serve_dir
        serving = True
        serve_dir = dir
        ball_speed = BALL_BASE_SPEED
        ball_x = (INTERNAL_W - BALL_SIZE) / 2.0
        ball_y = random.uniform(30, INTERNAL_H - 30)
        ball_vx = ball_vy = 0.0
    
    def serve():
        nonlocal serving, ball_vx, ball_vy
        if not serving: return
        ang = math.radians(random.uniform(-MAX_SERVE_ANGLE, MAX_SERVE_ANGLE))
        ball_vx = serve_dir * ball_speed * math.cos(ang)
        ball_vy = ball_speed * math.sin(ang)
        serving = False
        play_sound(snd_start)

    # Initialize ball for the first time
    reset_ball(1)

    # =====================
    # MENU SYSTEM
    # =====================
    menu_options = ["Play Game", "How to Play", "Credits", "About", "Exit"]
    
    def draw_menu_button(surface, text, y_pos, selected):
        rect_w, rect_h = 140, 25
        rect_x = (INTERNAL_W - rect_w) // 2
        
        color = BUTTON_HOVER if selected else DEFAULT_ACCENT
        border = HIGHLIGHT
        
        # Draw button body
        pygame.draw.rect(surface, color, (rect_x, y_pos, rect_w, rect_h))
        pygame.draw.rect(surface, border, (rect_x, y_pos, rect_w, rect_h), 1)
        
        # Draw text
        txt_surf = font.render(text, True, HIGHLIGHT)
        txt_x = rect_x + (rect_w - txt_surf.get_width()) // 2
        txt_y = y_pos + (rect_h - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (txt_x, txt_y))
        
        return pygame.Rect(rect_x, y_pos, rect_w, rect_h)

    def draw_text_centered(surface, text, y, font_obj=font, color=HIGHLIGHT):
        txt = font_obj.render(text, True, color)
        surface.blit(txt, ((INTERNAL_W - txt.get_width()) // 2, y))

    # =====================
    # GAME LOOP
    # =====================
    running = True
    while running:
        # Time Management
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        last_time = current_time
        if dt > 0.05: dt = 0.05
        
        # FPS
        frame_count += 1
        if current_time // 1000 > (current_time - dt * 1000) // 1000:
            fps_display = frame_count
            frame_count = 0
            
        # Helper for mouse pos
        mx, my = pygame.mouse.get_pos()
        mx_rel, my_rel = pygame.mouse.get_rel()
        mx_int = mx / SCALE
        my_int = my / SCALE

        # Event Handling
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            
            # Global Keybinds
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_f:
                    famicom_visuals = not famicom_visuals
                
                # ESC Handling logic
                if e.key == pygame.K_ESCAPE:
                    if current_state == STATE_PLAY:
                        if paused:
                            # Return to menu
                            current_state = STATE_MENU
                            mouse_grab = False
                            pygame.event.set_grab(False)
                            pygame.mouse.set_visible(True)
                            paused = False
                        else:
                            paused = True # Pause first
                    elif current_state == STATE_MENU:
                        running = False
                    else:
                        current_state = STATE_MENU # Back to menu from sub-screens

                # Play State Inputs
                if current_state == STATE_PLAY:
                    if e.key in (pygame.K_SPACE, pygame.K_RETURN) and not paused:
                        serve()
                    elif e.key == pygame.K_p:
                        paused = not paused
                    elif e.key == pygame.K_r:
                        score_l = score_r = 0
                        reset_ball(random.choice([-1, 1]))
                    elif e.key == pygame.K_TAB:
                        single_player = not single_player
                    elif e.key == pygame.K_m:
                        famicom_mouse = not famicom_mouse
                    elif e.key == pygame.K_g:
                        mouse_grab = not mouse_grab
                        pygame.event.set_grab(mouse_grab)
                        pygame.mouse.set_visible(not mouse_grab)
                    elif e.key == pygame.K_x:
                        if bg_color == DEFAULT_BG:
                            bg_color = (12, 12, 18)
                        else:
                            bg_color = DEFAULT_BG
                
            if e.type == pygame.MOUSEBUTTONDOWN and current_state == STATE_PLAY:
                if e.button == 1 and not paused:
                    serve()
                elif e.button == 3:
                    paused = not paused

        # LOGIC & RENDER BY STATE
        frame.fill(bg_color)
        
        if current_state == STATE_MENU:
            # Menu Logic
            draw_text_centered(frame, "ACS!Pong 0.1", 30, title_font)
            draw_text_centered(frame, "Select an Option", 60, font, DIM)
            
            start_y = 80
            gap = 30
            
            # Handle Menu Clicks
            for i, opt in enumerate(menu_options):
                btn_rect = draw_menu_button(frame, opt, start_y + i * gap, False)
                # Check hover/click (using scaled coordinates)
                if btn_rect.collidepoint(mx_int, my_int):
                    draw_menu_button(frame, opt, start_y + i * gap, True) # Redraw highlighted
                    if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                        play_sound(snd_start)
                        if i == 0: # Play
                            reset_game_state()
                            current_state = STATE_PLAY
                            mouse_grab = True
                            pygame.event.set_grab(True)
                            pygame.mouse.set_visible(False)
                        elif i == 1: current_state = STATE_HELP
                        elif i == 2: current_state = STATE_CREDITS
                        elif i == 3: current_state = STATE_ABOUT
                        elif i == 4: running = False

        elif current_state == STATE_HELP:
            draw_text_centered(frame, "HOW TO PLAY", 20, big_font)
            instructions = [
                "Mouse Up/Down to move paddle",
                "SPACE or Click to Serve",
                "ESC to Pause/Menu",
                "TAB: Toggle 1P/2P Mode",
                "G: Toggle Mouse Grab",
                "X: Toggle Visual Style"
            ]
            for i, line in enumerate(instructions):
                draw_text_centered(frame, line, 60 + i * 20)
            
            draw_menu_button(frame, "Back", 200, False)
            if pygame.Rect((INTERNAL_W-140)//2, 200, 140, 25).collidepoint(mx_int, my_int):
                 draw_menu_button(frame, "Back", 200, True)
                 if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                     current_state = STATE_MENU

        elif current_state == STATE_CREDITS:
            draw_text_centered(frame, "CREDITS", 20, big_font)
            lines = [
                "[C] AC Gaming Division",
                "",
                "Original Pong (1972):",
                "Allan Alcorn & Nolan Bushnell",
                "",
                "Engine: Pygame CE"
            ]
            for i, line in enumerate(lines):
                draw_text_centered(frame, line, 60 + i * 20)
            
            draw_menu_button(frame, "Back", 200, False)
            if pygame.Rect((INTERNAL_W-140)//2, 200, 140, 25).collidepoint(mx_int, my_int):
                 draw_menu_button(frame, "Back", 200, True)
                 if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                     current_state = STATE_MENU
                     
        elif current_state == STATE_ABOUT:
            draw_text_centered(frame, "ABOUT", 20, big_font)
            lines = [
                "ACS!Pong 0.1",
                "Version 2.0 (Sound Update)",
                "",
                "A lightweight, single-file",
                "Pong clone designed to run",
                "smoothly on any system.",
                "",
                "No external assets required."
            ]
            for i, line in enumerate(lines):
                draw_text_centered(frame, line, 60 + i * 18)
            
            draw_menu_button(frame, "Back", 200, False)
            if pygame.Rect((INTERNAL_W-140)//2, 200, 140, 25).collidepoint(mx_int, my_int):
                 draw_menu_button(frame, "Back", 200, True)
                 if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                     current_state = STATE_MENU

        elif current_state == STATE_PLAY:
            # --- GAME LOGIC ---
            if not paused:
                # Paddle Movement
                if famicom_mouse:
                    dy = my_rel / SCALE * mouse_sens
                    left_y += dy
                else:
                    target_y = my_int - PADDLE_H / 2
                    left_y += (target_y - left_y) * 0.3
                left_y = clamp(left_y, 0, INTERNAL_H - PADDLE_H)
                
                # AI / Player 2
                if single_player:
                    if ball_vx > 0:
                        # Prediction
                        time_to_reach = abs(right_x - ball_x) / abs(ball_vx) if ball_vx != 0 else 0
                        pred_y = ball_y + ball_vy * time_to_reach
                        while pred_y < 0 or pred_y > INTERNAL_H - BALL_SIZE:
                            if pred_y < 0: pred_y = -pred_y
                            else: pred_y = 2 * (INTERNAL_H - BALL_SIZE) - pred_y
                        target = pred_y
                    else:
                        target = INTERNAL_H / 2
                    
                    center = right_y + PADDLE_H / 2
                    move = clamp(target - center, -AI_SPEED * dt, AI_SPEED * dt)
                    right_y += move * 0.7
                else:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_UP]: right_y -= PADDLE_SPEED * dt
                    if keys[pygame.K_DOWN]: right_y += PADDLE_SPEED * dt
                right_y = clamp(right_y, 0, INTERNAL_H - PADDLE_H)
            
            # Physics
            left_rect = pygame.Rect(int(left_x), int(left_y), PADDLE_W, PADDLE_H)
            right_rect = pygame.Rect(int(right_x), int(right_y), PADDLE_W, PADDLE_H)
            
            if not paused and not serving:
                ball_x += ball_vx * dt
                ball_y += ball_vy * dt
                
                # Wall collisions
                if ball_y <= 0:
                    ball_y = 0
                    ball_vy = abs(ball_vy)
                    play_sound(snd_wall)
                elif ball_y + BALL_SIZE >= INTERNAL_H:
                    ball_y = INTERNAL_H - BALL_SIZE
                    ball_vy = -abs(ball_vy)
                    play_sound(snd_wall)
                
                ball_rect = pygame.Rect(int(ball_x), int(ball_y), BALL_SIZE, BALL_SIZE)
                
                # Paddle collisions
                if ball_vx < 0 and ball_rect.colliderect(left_rect):
                    impact = ((ball_y + BALL_SIZE/2) - left_rect.centery) / (PADDLE_H/2)
                    ang = math.radians(clamp(impact, -1, 1) * MAX_BOUNCE_ANGLE)
                    ball_speed = min(BALL_MAX_SPEED, ball_speed * BALL_ACCEL)
                    ball_vx = abs(ball_speed * math.cos(ang))
                    ball_vy = ball_speed * math.sin(ang)
                    ball_x = left_rect.right
                    play_sound(snd_paddle)
                    
                elif ball_vx > 0 and ball_rect.colliderect(right_rect):
                    impact = ((ball_y + BALL_SIZE/2) - right_rect.centery) / (PADDLE_H/2)
                    ang = math.radians(clamp(impact, -1, 1) * MAX_BOUNCE_ANGLE)
                    ball_speed = min(BALL_MAX_SPEED, ball_speed * BALL_ACCEL)
                    ball_vx = -abs(ball_speed * math.cos(ang))
                    ball_vy = ball_speed * math.sin(ang)
                    ball_x = right_rect.left - BALL_SIZE
                    play_sound(snd_paddle)
                
                # Scoring
                if ball_x < -BALL_SIZE:
                    score_r += 1
                    play_sound(snd_score)
                    reset_ball(-1)
                elif ball_x > INTERNAL_W + BALL_SIZE:
                    score_l += 1
                    play_sound(snd_score)
                    reset_ball(1)

            # --- RENDER GAME ---
            # Center line
            for y in range(4, INTERNAL_H, 12):
                pygame.draw.rect(frame, HIGHLIGHT, (INTERNAL_W//2 - 1, y, 2, 6))
            
            # Draw Objects
            for r in [left_rect, right_rect]:
                pygame.draw.rect(frame, FG, r)
                # 3D bevel effect
                pygame.draw.line(frame, HIGHLIGHT, (r.left, r.top), (r.left, r.bottom), 1)
                pygame.draw.line(frame, HIGHLIGHT, (r.left, r.top), (r.right, r.top), 1)
            
            pygame.draw.rect(frame, HIGHLIGHT, (int(ball_x), int(ball_y), BALL_SIZE, BALL_SIZE))
            
            # UI
            score_text = big_font.render(f"{score_l}   {score_r}", True, HIGHLIGHT)
            frame.blit(score_text, (INTERNAL_W//2 - score_text.get_width()//2, 6))
            
            if paused:
                frame.blit(paused_text, (INTERNAL_W//2 - paused_text.get_width()//2, INTERNAL_H//2))
                draw_text_centered(frame, "Press ESC for Menu", INTERNAL_H//2 + 30, font)
            
            if serving:
                draw_text_centered(frame, "Press SPACE to serve", INTERNAL_H//2 + 20, font)

        # Global Overlays
        if famicom_visuals:
            frame.blit(scanlines, (0, 0))
        
        fps_text = font.render(f"{fps_display}", True, DIM)
        frame.blit(fps_text, (INTERNAL_W - fps_text.get_width() - 2, INTERNAL_H - 12))

        # Output to screen
        pygame.transform.scale(frame, (WIN_W, WIN_H), scaled)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
