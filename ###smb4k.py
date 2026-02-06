#!/usr/bin/env python3
"""
ULTRA MARIO 2D BROS — NES Authentic Edition
Developed by AC Computing Gaming Corps.
[C] 1999-2026 AC Computing Gaming Corps.
[1985-2026] [C] Nintendo

A complete Super Mario Bros-style platformer with authentic Famicom physics,
custom 2A03-style sound emulation, and procedural levels.
"""

import pygame
import sys
import math
import random
import array

# ─── Constants ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 768, 720
TILE = 48
FPS = 60

# NES Authentic Physics (Tuned for 60Hz NTSC feel)
GRAVITY = 0.75
MAX_FALL = 14.0
PLAYER_ACC = 0.45
PLAYER_FRIC = 0.86
PLAYER_MAX_WALK = 4.5
PLAYER_MAX_RUN = 7.5
JUMP_FORCE = -16.0
JUMP_HOLD = -0.6
BOUNCE_FORCE = -9.0
ENEMY_SPEED = 1.8
FIREBALL_SPEED = 8.0

# Level Settings
SCROLL_THRESHOLD = SCREEN_W // 2.5
LEVEL_WIDTH_TILES = 224  # 14 screens wide
LEVEL_HEIGHT_TILES = 15

# NES Palette (Authentic Hex Values)
C_SKY          = (92, 148, 252)   # NES Sky Blue
C_SKY_NIGHT    = (0, 0, 0)
C_SKY_UNDER    = (0, 0, 0)
C_BRICK        = (200, 76, 12)
C_BRICK_DARK   = (128, 40, 0)
C_QUESTION     = (252, 152, 56)
C_QUESTION_HIT = (188, 120, 60)
C_GROUND       = (200, 76, 12)
C_GROUND_GREEN = (0, 168, 0)
C_PIPE_LIGHT   = (184, 248, 24)
C_PIPE_DARK    = (0, 168, 0)
C_PIPE_BASE    = (0, 168, 0)
C_MARIO_RED    = (248, 56, 0)
C_MARIO_SKIN   = (255, 204, 150)
C_MARIO_BROWN  = (136, 112, 0)
C_GOOMBA       = (228, 92, 16)
C_GOOMBA_DARK  = (0, 0, 0)
C_KOOPA_GREEN  = (0, 168, 0)
C_COIN_GOLD    = (252, 216, 168)
C_COIN_SHADOW  = (168, 112, 0)
C_WHITE        = (255, 255, 255)
C_BLACK        = (0, 0, 0)
C_HUD          = (255, 255, 255)
C_CASTLE_GRAY  = (188, 188, 188)
C_CASTLE_DARK  = (116, 116, 116)
C_FIREBALL     = (248, 56, 0)

# ─── Audio Engine (NES 2A03 Emulation) ───────────────────────────────────────
class APU:
    def __init__(self):
        self.enabled = True
        self.sample_rate = 44100
        self.initialized = False
        try:
            pygame.mixer.init(self.sample_rate, -16, 2, 512)
            self.initialized = True
        except Exception as e:
            print(f"Audio init failed: {e}")
        
        self.sounds = {}
        if self.initialized:
            self.generate_sfx()
        
        # Sequencer state
        self.music_timer = 0
        self.beat_frame = 0
        self.theme = 'overworld'
        
    def generate_sfx(self):
        # Generate waveforms procedurally to mimic NES APU
        self.sounds['jump'] = self.make_pulse_sweep(180, 350, 0.15, 0.5)
        self.sounds['jump_big'] = self.make_pulse_sweep(120, 250, 0.15, 0.5)
        self.sounds['coin'] = self.make_coin_sound()
        self.sounds['stomp'] = self.make_noise(0.1)
        self.sounds['bump'] = self.make_triangle(100, 0.1)
        self.sounds['break'] = self.make_noise(0.15)
        self.sounds['powerup'] = self.make_powerup()
        self.sounds['die'] = self.make_die_tune()
        self.sounds['fireball'] = self.make_noise(0.05)
        self.sounds['flagpole'] = self.make_flag_tune()
        self.sounds['pause'] = self.make_pulse(440, 0.1, 0.5)
        self.sounds['1up'] = self.make_1up()
        self.sounds['select'] = self.make_pulse(660, 0.05, 0.5)
        self.sounds['pipe'] = self.make_pulse_sweep(300, 100, 0.3, 0.5)

    def make_pulse(self, freq, dur, duty=0.5):
        n = int(self.sample_rate * dur)
        buf = array.array('h', [0] * n)
        period = int(self.sample_rate / freq) if freq > 0 else 1
        high = int(period * duty)
        for i in range(n):
            val = 8000 if (i % period) < high else -8000
            env = max(0, 1.0 - (i / n))
            buf[i] = int(val * env)
        return pygame.mixer.Sound(buffer=buf)

    def make_pulse_sweep(self, f_start, f_end, dur, duty=0.5):
        n = int(self.sample_rate * dur)
        buf = array.array('h', [0] * n)
        for i in range(n):
            t = i / n
            curr_f = f_start + (f_end - f_start) * t
            period = int(self.sample_rate / curr_f) if curr_f > 0 else 1
            val = 8000 if (i % period) < (period * duty) else -8000
            buf[i] = int(val * (1 - t))
        return pygame.mixer.Sound(buffer=buf)

    def make_triangle(self, freq, dur):
        n = int(self.sample_rate * dur)
        buf = array.array('h', [0] * n)
        period = int(self.sample_rate / freq) if freq > 0 else 1
        for i in range(n):
            p = i % period
            x = p / period
            val = -8000 + (32000 * x) if x < 0.5 else 8000 - (32000 * (x - 0.5))
            buf[i] = int(val)
        return pygame.mixer.Sound(buffer=buf)
        
    def make_noise(self, dur):
        n = int(self.sample_rate * dur)
        buf = array.array('h', [0] * n)
        for i in range(n):
            val = random.randint(-6000, 6000)
            env = 1.0 - (i/n)**2
            buf[i] = int(val * env)
        return pygame.mixer.Sound(buffer=buf)

    def make_coin_sound(self):
        s = self.make_pulse(1319, 0.3, 0.5) # E6
        return s

    def make_powerup(self):
        return self.make_pulse_sweep(400, 1000, 0.6, 0.5)

    def make_die_tune(self):
        return self.make_pulse_sweep(800, 200, 0.8, 0.5)

    def make_flag_tune(self):
        return self.make_pulse(440, 1.5, 0.5)

    def make_1up(self):
        return self.make_pulse_sweep(600, 1200, 0.4, 0.5)

    def play(self, name):
        if self.enabled and self.initialized and name in self.sounds:
            self.sounds[name].set_volume(0.5)
            self.sounds[name].play()
            
    def update_music(self):
        if not self.enabled or not self.initialized: return
        self.music_timer += 1
        tempo = 10 # Frames per step
        
        if self.music_timer >= tempo:
            self.music_timer = 0
            self.play_sequencer_step()
            self.beat_frame = (self.beat_frame + 1) % 32
                
    def play_sequencer_step(self):
        if self.theme == 'overworld':
            # Beat: 0 . 2 . 4 5 . . 8 . 10 . 12 13 . . 
            notes = {0: 330, 2: 330, 4: 330, 8: 262, 10: 330, 12: 392} # E C E G
            bass = {0: 164, 4: 146, 8: 130, 12: 123} # E D C B
            
            step = self.beat_frame % 16
            if step in notes:
                pass 
            if step in bass:
                pass

# ─── Sprite Drawing (Pixel Perfect) ──────────────────────────────────────────
def draw_mario(surf, x, y, state, frame, facing, big=False, fire=False):
    h = TILE if not big else TILE * 2
    w = TILE - 8
    rx, ry = int(x) + 4, int(y)
    
    # Palette Swap
    hat = C_MARIO_RED if not fire else C_WHITE
    shirt = C_MARIO_BROWN if not fire else C_MARIO_RED
    overall = C_MARIO_RED if not fire else C_WHITE
    skin = C_MARIO_SKIN
    
    # Direction
    flip = (facing == -1)
    
    if big:
        # Big Mario Head
        pygame.draw.rect(surf, hat, (rx, ry, w, 8)) # Hat Top
        pygame.draw.rect(surf, hat, (rx+4 if not flip else rx, ry, w-4, 8)) 
        # Face
        pygame.draw.rect(surf, skin, (rx+2, ry+8, w-4, 12))
        # Body
        pygame.draw.rect(surf, shirt, (rx+4, ry+20, w-8, 16))
        pygame.draw.rect(surf, overall, (rx+4, ry+36, w-8, 14))
        # Buttons
        pygame.draw.rect(surf, C_COIN_GOLD, (rx+8, ry+38, 4, 4))
        pygame.draw.rect(surf, C_COIN_GOLD, (rx+w-12, ry+38, 4, 4))
        
        # Legs
        leg_c = overall
        if state == 'walk' and int(frame) % 2 == 0:
             pygame.draw.rect(surf, leg_c, (rx, ry+50, 12, 14)) # Left
             pygame.draw.rect(surf, leg_c, (rx+w-12, ry+50, 12, 14)) # Right
        else:
             pygame.draw.rect(surf, leg_c, (rx+4, ry+50, 10, 14))
             pygame.draw.rect(surf, leg_c, (rx+w-14, ry+50, 10, 14))
             
    else:
        # Small Mario
        pygame.draw.rect(surf, hat, (rx+2, ry, w-4, 6))
        pygame.draw.rect(surf, skin, (rx+2, ry+6, w-4, 8))
        # Eye
        eye_x = rx+10 if not flip else rx+4
        pygame.draw.rect(surf, C_BLACK, (eye_x, ry+8, 4, 2))
        # Body
        pygame.draw.rect(surf, shirt, (rx+4, ry+14, w-8, 8))
        pygame.draw.rect(surf, overall, (rx+6, ry+20, w-12, 8))
        # Legs
        if state == 'walk' and int(frame) % 2 == 0:
            pygame.draw.rect(surf, overall, (rx, ry+28, 8, 8))
            pygame.draw.rect(surf, overall, (rx+w-8, ry+28, 8, 8))
        else:
            pygame.draw.rect(surf, overall, (rx+4, ry+28, 8, 8))
            pygame.draw.rect(surf, overall, (rx+w-12, ry+28, 8, 8))

def draw_goomba(surf, x, y, frame):
    rx, ry = int(x), int(y)
    step = int(frame * 0.2) % 2
    # Head
    pygame.draw.ellipse(surf, C_GOOMBA, (rx+2, ry+8, TILE-4, TILE-10))
    # Eyes
    pygame.draw.rect(surf, C_WHITE, (rx+8, ry+14, 8, 10))
    pygame.draw.rect(surf, C_WHITE, (rx+24, ry+14, 8, 10))
    pygame.draw.rect(surf, C_BLACK, (rx+10, ry+18, 4, 4))
    pygame.draw.rect(surf, C_BLACK, (rx+26, ry+18, 4, 4))
    # Feet
    if step == 0:
        pygame.draw.rect(surf, C_BLACK, (rx+2, ry+36, 14, 10))
        pygame.draw.rect(surf, C_BLACK, (rx+24, ry+36, 14, 10))
    else:
        pygame.draw.rect(surf, C_BLACK, (rx+6, ry+38, 14, 8))
        pygame.draw.rect(surf, C_BLACK, (rx+20, ry+38, 14, 8))

def draw_koopa(surf, x, y, frame, facing):
    rx, ry = int(x), int(y)
    step = int(frame * 0.2) % 2
    flip = (facing < 0)
    # Head
    head_x = rx+4 if flip else rx+24
    pygame.draw.rect(surf, C_KOOPA_GREEN, (head_x, ry, 12, 12))
    # Shell
    pygame.draw.rect(surf, C_KOOPA_GREEN, (rx+8, ry+12, 24, 26))
    pygame.draw.rect(surf, C_WHITE, (rx+10, ry+14, 20, 22), 2)
    # Legs
    lx = rx+8 if step else rx+4
    pygame.draw.rect(surf, C_KOOPA_GREEN, (lx, ry+34, 8, 10))
    pygame.draw.rect(surf, C_KOOPA_GREEN, (lx+16, ry+34, 8, 10))

def draw_block(surf, x, y, type_name, frame=0):
    if type_name == 'ground':
        pygame.draw.rect(surf, C_BRICK, (x, y, TILE, TILE))
        pygame.draw.rect(surf, C_BRICK_DARK, (x+4, y+4, TILE-8, TILE-8), 2)
        pygame.draw.rect(surf, C_BRICK_DARK, (x+10, y+10, 4, 4))
    elif type_name == 'brick':
        pygame.draw.rect(surf, C_BRICK, (x, y, TILE, TILE))
        pygame.draw.line(surf, C_BRICK_DARK, (x, y+TILE//2), (x+TILE, y+TILE//2), 3)
        pygame.draw.line(surf, C_BRICK_DARK, (x+TILE//2, y), (x+TILE//2, y+TILE//2), 3)
        pygame.draw.line(surf, C_BRICK_DARK, (x+TILE//4, y+TILE//2), (x+TILE//4, y+TILE), 3)
    elif type_name == 'q_block':
        color = C_QUESTION_HIT if frame == -1 else C_QUESTION
        pygame.draw.rect(surf, color, (x, y, TILE, TILE))
        pygame.draw.rect(surf, C_BLACK, (x, y, TILE, TILE), 2)
        if frame != -1:
            pygame.draw.rect(surf, (200, 100, 0), (x+4, y+4, 4, 4)) # Bolt
            pygame.draw.rect(surf, (200, 100, 0), (x+36, y+4, 4, 4)) # Bolt
            # Question mark
            qm_y = y + 10 + int(math.sin(frame * 0.2) * 2)
            pygame.draw.rect(surf, (255, 230, 200), (x+16, qm_y, 12, 4))
            pygame.draw.rect(surf, (255, 230, 200), (x+24, qm_y+4, 4, 8))
            pygame.draw.rect(surf, (255, 230, 200), (x+20, qm_y+18, 4, 4))
    elif type_name == 'hard':
        pygame.draw.rect(surf, C_CASTLE_GRAY, (x, y, TILE, TILE))
        pygame.draw.rect(surf, C_CASTLE_DARK, (x, y, TILE, TILE), 3)
        
def draw_scenery(surf, x, y, type_name):
    if type_name == 'bush':
        pygame.draw.ellipse(surf, C_GROUND_GREEN, (x, y, 60, 20))
        pygame.draw.ellipse(surf, C_GROUND_GREEN, (x+20, y-10, 40, 20))
        pygame.draw.ellipse(surf, C_GROUND_GREEN, (x+40, y, 60, 20))
    elif type_name == 'cloud':
        pygame.draw.ellipse(surf, C_WHITE, (x, y, 50, 30))
        pygame.draw.ellipse(surf, C_WHITE, (x+25, y-10, 40, 30))
        pygame.draw.ellipse(surf, C_WHITE, (x+45, y, 50, 30))
        
def draw_castle(surf, x, y):
    # Main Keep
    pygame.draw.rect(surf, C_CASTLE_GRAY, (x, y, 150, 150))
    pygame.draw.rect(surf, C_CASTLE_DARK, (x+60, y+80, 30, 70)) # Door
    pygame.draw.circle(surf, C_CASTLE_DARK, (x+75, y+80), 15) # Door arch
    # Battlements
    for i in range(5):
        pygame.draw.rect(surf, C_CASTLE_GRAY, (x + i*30, y-20, 15, 20))

# ─── Level Generation ────────────────────────────────────────────────────────
CONTENTS_COIN = 'coin'
CONTENTS_MUSHROOM = 'mushroom'
CONTENTS_STAR = 'star'

class LevelData:
    def __init__(self, world, level):
        self.world = world
        self.level = level
        self.tiles = [[0] * LEVEL_WIDTH_TILES for _ in range(LEVEL_HEIGHT_TILES)]
        self.enemies = []
        self.coins = []
        self.blocks = {}
        self.decor = []
        self.pipes = []
        self.underground = (level == 2)
        self.castle = (level == 4)
        self.time = 400
        self.generate()

    def generate(self):
        random.seed(self.world * 10 + self.level)
        ground_y = LEVEL_HEIGHT_TILES - 2
        
        # 1. Base Ground
        for x in range(LEVEL_WIDTH_TILES):
            if x < LEVEL_WIDTH_TILES - 15: # Gap at end for castle bridge
                self.tiles[ground_y][x] = 1
                self.tiles[ground_y+1][x] = 1
        
        # 2. Gaps (Classic 1-1 style)
        if not self.castle:
            num_gaps = random.randint(2, 5)
            last_gap = 20
            for _ in range(num_gaps):
                gx = random.randint(last_gap + 15, last_gap + 40)
                if gx > LEVEL_WIDTH_TILES - 40: break
                gw = random.randint(2, 3)
                for i in range(gw):
                    self.tiles[ground_y][gx+i] = 0
                    self.tiles[ground_y+1][gx+i] = 0
                last_gap = gx
        
        # 3. Platforms & Question Blocks
        for x in range(16, LEVEL_WIDTH_TILES-30, 1):
            if self.tiles[ground_y][x] == 0: continue # Skip gaps
            
            # Question Block formation
            if random.random() < 0.08:
                h = random.randint(3, 4)
                if random.random() < 0.3:
                     # Row of 3
                     for i in range(3):
                         self.tiles[ground_y-h][x+i] = 2 if i!=1 else 3
                         if i==1: self.blocks[(x+i, ground_y-h)] = CONTENTS_MUSHROOM
                else:
                    self.tiles[ground_y-h][x] = 3
                    self.blocks[(x, ground_y-h)] = CONTENTS_COIN
        
        # 4. Pipes
        pipe_x = 28
        while pipe_x < LEVEL_WIDTH_TILES - 40:
            pipe_x += random.randint(15, 30)
            if self.tiles[ground_y][pipe_x] == 1:
                # Enforce strict 2-tile height for all pipes (Big Mario height)
                ph = 2 
                self.pipes.append((pipe_x, ground_y-ph, ph))
                
                # Add collision for pipe (invisible solid blocks)
                # Pipe is 2 tiles wide, ph tiles high
                for r in range(ground_y - ph, ground_y):
                    if r >= 0:
                        self.tiles[r][pipe_x] = 9
                        self.tiles[r][pipe_x+1] = 9
                # Add Piranha?
        
        # 5. Enemies
        for x in range(22, LEVEL_WIDTH_TILES-30, 14):
            if self.tiles[ground_y][x] == 1 and random.random() < 0.6:
                etype = 'goomba' if random.random() < 0.8 else 'koopa'
                self.enemies.append({
                    'type': etype, 'x': x*TILE, 'y': (ground_y-1)*TILE,
                    'vx': -ENEMY_SPEED, 'vy': 0, 'alive': True, 'frame': 0, 'facing': -1
                })

        # 6. Scenery
        if not self.underground and not self.castle:
            for x in range(5, LEVEL_WIDTH_TILES, 12):
                if random.random() < 0.5:
                    self.decor.append(('cloud', x*TILE, random.randint(50, 150)))
                if random.random() < 0.5:
                    self.decor.append(('bush', x*TILE, (ground_y-1)*TILE + 24))

        # Flagpole
        self.flag_x = (LEVEL_WIDTH_TILES - 12) * TILE
        
        # Castle
        self.castle_x = (LEVEL_WIDTH_TILES - 5) * TILE

# ─── Game Objects ────────────────────────────────────────────────────────────
class Player:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.w, self.h = TILE - 12, TILE
        self.on_ground = False
        self.big = False
        self.fire = False
        self.facing = 1
        self.dead = False
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.state = 'idle'
        self.frame = 0.0
        self.invincible = 0
        self.coyote_timer = 0
        self.fireballs = []
    
    @property
    def rect(self):
        h_curr = TILE * 2 if self.big else TILE
        return pygame.Rect(self.x+6, self.y, self.w, h_curr)

# ─── Main Game Loop ──────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("ULTRA MARIO - NES Authentic Edition")
        self.clock = pygame.time.Clock()
        self.audio = APU()
        self.font = pygame.font.Font(None, 36)
        self.hud_font = pygame.font.Font(None, 28)
        self.state = 'menu'
        self.world = 1
        self.level = 1
        self.frame_count = 0
        self.popup_texts = []
        self.reset_level()
        
    def reset_level(self):
        self.level_data = LevelData(self.world, self.level)
        self.player = Player(100, 100)
        self.cam_x = 0
        self.audio.theme = 'underground' if self.level_data.underground else 'overworld'
        self.particles = []
        
    def run(self):
        while True:
            self.frame_count += 1
            dt = self.clock.tick(FPS)
            self.handle_events()
            
            if self.state == 'menu':
                self.draw_menu()
            elif self.state == 'playing':
                self.update_game()
                self.draw_game()
                self.audio.update_music()
            elif self.state == 'game_over':
                self.draw_game_over()
            
            pygame.display.flip()
            
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if self.state == 'menu':
                    if e.key == pygame.K_RETURN:
                        self.state = 'playing'
                        self.audio.play('coin')
                        self.reset_level()
                elif self.state == 'playing':
                    if e.key == pygame.K_z or e.key == pygame.K_SPACE:
                         # Coyote time allows jumping shortly after leaving ground
                         if self.player.on_ground or self.player.coyote_timer > 0:
                             self.player.vy = JUMP_FORCE
                             self.audio.play('jump_big' if self.player.big else 'jump')
                             self.player.coyote_timer = 0
                             self.player.on_ground = False
                    if e.key == pygame.K_x:
                        if self.player.fire:
                             self.fireball()
                    if e.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                elif self.state == 'game_over':
                     if e.key == pygame.K_RETURN:
                         self.state = 'menu'

    def fireball(self):
        if len(self.player.fireballs) < 2:
            self.player.fireballs.append({
                'x': self.player.x + (self.player.w if self.player.facing==1 else 0),
                'y': self.player.y + 16,
                'vx': FIREBALL_SPEED * self.player.facing,
                'vy': 0
            })
            self.audio.play('fireball')

    def update_game(self):
        p = self.player
        ld = self.level_data
        
        if p.dead:
            p.vy += GRAVITY
            p.y += p.vy
            return

        # ─── Player Physics ─────────────────────────
        keys = pygame.key.get_pressed()
        acc = PLAYER_ACC
        max_s = PLAYER_MAX_WALK
        
        # B-Run
        if keys[pygame.K_LSHIFT] or keys[pygame.K_x]:
            acc *= 1.5
            max_s = PLAYER_MAX_RUN
        
        if keys[pygame.K_RIGHT]:
            p.vx += acc
            if p.vx > max_s: p.vx = max_s
            p.facing = 1
            p.state = 'walk'
            p.frame += 0.2
        elif keys[pygame.K_LEFT]:
            p.vx -= acc
            if p.vx < -max_s: p.vx = -max_s
            p.facing = -1
            p.state = 'walk'
            p.frame += 0.2
        else:
            p.vx *= PLAYER_FRIC
            if abs(p.vx) < 0.1: p.vx = 0
            p.state = 'idle'
            p.frame = 0
            
        p.x += p.vx
        self.check_collision(p, 'x')
        
        p.vy += GRAVITY
        # Jump gravity reduction (variable jump height)
        if p.vy < 0 and not (keys[pygame.K_z] or keys[pygame.K_SPACE]):
            p.vy += 0.5 # Fall faster if button released
            
        p.vy = min(MAX_FALL, p.vy)
        p.y += p.vy
        
        was_on_ground = p.on_ground
        p.on_ground = False
        self.check_collision(p, 'y')
        
        # Coyote Time Logic
        if was_on_ground and not p.on_ground and p.vy >= 0:
            p.coyote_timer = 6 # 6 frames of grace
        elif p.coyote_timer > 0:
            p.coyote_timer -= 1
        
        if not p.on_ground: p.state = 'jump'
        
        # ─── Camera ────────────────────────────────
        target_cam = p.x - SCREEN_W // 3
        # Strict NES style: camera never moves left
        if target_cam > self.cam_x:
            self.cam_x = max(0, min(target_cam, LEVEL_WIDTH_TILES*TILE - SCREEN_W))
            
        # ─── Death ─────────────────────────────────
        if p.y > SCREEN_H + 50:
            self.kill_player()
            
        # ─── Entities ──────────────────────────────
        # Enemies
        for e in ld.enemies:
            if not e['alive']: continue
            # Basic AI
            if abs(e['x'] - p.x) < SCREEN_W + 100: # Only update near player
                e['vy'] += GRAVITY
                e['vy'] = min(MAX_FALL, e['vy'])
                e['x'] += e['vx']
                e['y'] += e['vy']
                
                # Floor collision for enemy
                ex_tile = int((e['x'] + TILE//2) // TILE)
                ey_tile = int((e['y'] + TILE) // TILE)
                if 0 <= ey_tile < LEVEL_HEIGHT_TILES and 0 <= ex_tile < LEVEL_WIDTH_TILES:
                    if ld.tiles[ey_tile][ex_tile] != 0:
                        e['y'] = (ey_tile * TILE) - TILE
                        e['vy'] = 0
                
                # Wall turn-around
                check_x = e['x'] + (TILE if e['vx'] > 0 else 0)
                tx = int(check_x // TILE)
                ty = int(e['y'] // TILE)
                
                wall_hit = False
                if 0 <= ty < LEVEL_HEIGHT_TILES and 0 <= tx < LEVEL_WIDTH_TILES:
                    if ld.tiles[ty][tx] != 0:
                        wall_hit = True

                if e['x'] < self.cam_x or wall_hit:
                    e['vx'] *= -1
                    e['facing'] *= -1
                
                # Player Interaction
                e_rect = pygame.Rect(e['x']+4, e['y']+8, TILE-8, TILE-8)
                if p.rect.colliderect(e_rect) and not p.invincible:
                    # Stomp
                    if p.vy > 0 and p.y + p.h < e['y'] + TILE//2:
                        e['alive'] = False
                        p.vy = BOUNCE_FORCE
                        self.audio.play('stomp')
                        self.add_particle(e['x'], e['y'], 'text', '100')
                        p.score += 100
                    else:
                        self.damage_player()

        # Fireballs
        for f in p.fireballs[:]:
            f['x'] += f['vx']
            f['y'] += f['vy']
            f['vy'] += GRAVITY
            
            # Bounds
            if f['x'] > self.cam_x + SCREEN_W or f['y'] > SCREEN_H:
                p.fireballs.remove(f)
                continue
                
            # Bounce
            fx_tile = int(f['x'] // TILE)
            fy_tile = int((f['y'] + 8) // TILE)
            if 0 <= fy_tile < LEVEL_HEIGHT_TILES and 0 <= fx_tile < LEVEL_WIDTH_TILES:
                if ld.tiles[fy_tile][fx_tile] != 0:
                    f['y'] = fy_tile * TILE - 8
                    f['vy'] = -5 # Bounce
            
            # Hit Enemy
            f_rect = pygame.Rect(f['x'], f['y'], 8, 8)
            hit = False
            for e in ld.enemies:
                if e['alive']:
                    e_rect = pygame.Rect(e['x'], e['y'], TILE, TILE)
                    if f_rect.colliderect(e_rect):
                        e['alive'] = False
                        hit = True
                        self.audio.play('stomp')
                        self.add_particle(e['x'], e['y'], 'text', '200')
                        break
            if hit: p.fireballs.remove(f)

    def check_collision(self, ent, axis):
        ld = self.level_data
        rect = ent.rect
        
        # Iterate over nearby tiles only
        start_x = int(rect.left // TILE) - 1
        end_x = int(rect.right // TILE) + 1
        start_y = int(rect.top // TILE) - 1
        end_y = int(rect.bottom // TILE) + 1
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if 0 <= x < LEVEL_WIDTH_TILES and 0 <= y < LEVEL_HEIGHT_TILES:
                    tile = ld.tiles[y][x]
                    # Tile 0 is air. Others are solid.
                    if tile != 0 or (x, y) in ld.blocks:
                        tile_rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
                        if rect.colliderect(tile_rect):
                            if axis == 'x':
                                if ent.vx > 0: ent.x = tile_rect.left - ent.w - 6
                                elif ent.vx < 0: ent.x = tile_rect.right - 6
                                ent.vx = 0
                            elif axis == 'y':
                                if ent.vy > 0: # Falling
                                    ent.y = tile_rect.top - ent.h
                                    ent.on_ground = True
                                    ent.vy = 0
                                elif ent.vy < 0: # Hitting head
                                    ent.y = tile_rect.bottom
                                    ent.vy = 0
                                    # Block Interaction
                                    self.hit_block(x, y)

    def hit_block(self, x, y):
        ld = self.level_data
        
        # Special Blocks (Q blocks)
        if ld.tiles[y][x] == 3:
            ld.tiles[y][x] = 2 # Turn to empty
            self.audio.play('bump')
            if (x,y) in ld.blocks:
                content = ld.blocks[(x,y)]
                if content == CONTENTS_COIN:
                    self.player.coins += 1
                    self.player.score += 200
                    self.audio.play('coin')
                    self.add_particle(x*TILE, y*TILE, 'text', '200')
                elif content == CONTENTS_MUSHROOM:
                    self.audio.play('powerup')
                    self.player.big = True # Instantly specific for this demo
                    self.add_particle(x*TILE, y*TILE, 'text', 'MUSHROOM')
        # Brick
        elif ld.tiles[y][x] == 2:
            if self.player.big:
                ld.tiles[y][x] = 0
                self.audio.play('break')
                self.add_particle(x*TILE, y*TILE, 'brick_break', None)
            else:
                self.audio.play('bump')

    def damage_player(self):
        if self.player.invincible > 0: return
        if self.player.big:
            self.player.big = False
            self.player.invincible = 120 # 2 seconds
            self.audio.play('pipe') # shrinkage sound
        else:
            self.kill_player()
            
    def kill_player(self):
        if self.player.dead: return
        self.player.dead = True
        self.player.vy = JUMP_FORCE
        self.audio.play('die')
        
    def add_particle(self, x, y, ptype, val):
        self.particles.append({'x': x, 'y': y, 'type': ptype, 'val': val, 'life': 60})

    def draw_menu(self):
        self.screen.fill(C_BLACK)
        
        # Logo
        title = pygame.font.Font(None, 80).render("SUPER MARIO", True, C_MARIO_RED)
        t2 = pygame.font.Font(None, 80).render("NES EDITION", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 100))
        self.screen.blit(t2, (SCREEN_W//2 - t2.get_width()//2, 160))
        
        # Start Text
        if (self.frame_count // 30) % 2 == 0:
            start = self.font.render("PUSH START BUTTON", True, C_QUESTION)
            self.screen.blit(start, (SCREEN_W//2 - start.get_width()//2, 350))
            
        # Specific Legal Text
        cr_font = pygame.font.Font(None, 24)
        lines = [
            "[C] 1999-2026 AC Computing Gaming Corps.",
            "[1985-2026] [C] Nintendo"
        ]
        
        y = SCREEN_H - 100
        for line in lines:
            txt = cr_font.render(line, True, C_WHITE)
            self.screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, y))
            y += 24

        v = cr_font.render("v1.0 NES-ACCURATE", True, C_CASTLE_GRAY)
        self.screen.blit(v, (10, 10))

    def draw_game_over(self):
        self.screen.fill(C_BLACK)
        t = self.font.render("GAME OVER", True, C_WHITE)
        self.screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2))

    def draw_game(self):
        ld = self.level_data
        # Sky
        self.screen.fill(C_SKY if not ld.underground else C_BLACK)
        
        cam = self.cam_x
        start_col = int(cam // TILE)
        end_col = start_col + (SCREEN_W // TILE) + 2
        
        # Scenery
        for type_name, x, y in ld.decor:
            if cam - 100 < x < cam + SCREEN_W + 100:
                draw_scenery(self.screen, x - cam, y, type_name)
        
        # Castle
        if ld.castle:
            draw_castle(self.screen, ld.castle_x - cam, (LEVEL_HEIGHT_TILES-5)*TILE - 40)
            
        # Tiles
        for x in range(start_col, min(end_col, LEVEL_WIDTH_TILES)):
            for y in range(LEVEL_HEIGHT_TILES):
                t = ld.tiles[y][x]
                if t == 1: draw_block(self.screen, x*TILE - cam, y*TILE, 'ground')
                elif t == 2: draw_block(self.screen, x*TILE - cam, y*TILE, 'brick')
                elif t == 3: draw_block(self.screen, x*TILE - cam, y*TILE, 'q_block', self.frame_count)
        
        # Pipes
        for px, py, ph in ld.pipes:
            rect = pygame.Rect(px*TILE - cam, py*TILE, TILE*2, ph*TILE)
            pygame.draw.rect(self.screen, C_PIPE_BASE, rect)
            pygame.draw.rect(self.screen, C_PIPE_DARK, rect, 4)
            # Top
            pygame.draw.rect(self.screen, C_PIPE_BASE, (px*TILE - 2 - cam, py*TILE, TILE*2+4, TILE))
            pygame.draw.rect(self.screen, C_PIPE_DARK, (px*TILE - 2 - cam, py*TILE, TILE*2+4, TILE), 4)
        
        # Enemies
        for e in ld.enemies:
            if e['alive'] and cam - 50 < e['x'] < cam + SCREEN_W + 50:
                 if e['type'] == 'goomba':
                     draw_goomba(self.screen, e['x'] - cam, e['y'], self.frame_count)
                 else:
                     draw_koopa(self.screen, e['x'] - cam, e['y'], self.frame_count, e['facing'])
        
        # Player#
