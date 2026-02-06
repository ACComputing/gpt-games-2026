#!/usr/bin/env python3
"""
ULTRA MARIO BROS: FAMICOM ULTIMATE EDITION
A monumental, procedural recreation of the 1985 classic.
Contains a full physics engine, synthesizer, procedural generation,
and entity system in a single file.

Requirements: pip install pygame
Run: python mario_bros_nes.py
"""

import pygame
import sys
import math
import random
import array
import time
from enum import Enum

# ─── CONFIGURATION & CONSTANTS ───────────────────────────────────────────────
SCREEN_SCALE = 3
NES_W, NES_H = 256, 240
SCREEN_W, SCREEN_H = NES_W * SCREEN_SCALE, NES_H * SCREEN_SCALE
TILE_SIZE = 16 * SCREEN_SCALE
FPS = 60

# Physics Constants
GRAVITY = 0.5
MAX_FALL = 10.0
ACCEL = 0.15
FRICTION = 0.90
MAX_WALK = 3.5
MAX_RUN = 6.0
JUMP_FORCE = -11.0 # Short jump
JUMP_HOLD_FORCE = -0.4 # Gravity reduction while holding
BOUNCE_FORCE = -6.0
ENEMY_SPEED = 1.5
SHELL_SPEED = 7.0

# Input
KEY_JUMP = [pygame.K_z, pygame.K_SPACE, pygame.K_UP]
KEY_RUN  = [pygame.K_x, pygame.K_LSHIFT, pygame.K_RSHIFT]
KEY_LEFT = [pygame.K_LEFT]
KEY_RIGHT = [pygame.K_RIGHT]
KEY_DOWN = [pygame.K_DOWN]

# Colors (NES Palette Approximation)
C_SKY          = (92, 148, 252)
C_SKY_BLACK    = (0, 0, 0)
C_GROUND       = (200, 76, 12)
C_BRICK        = (180, 60, 0)
C_BRICK_DARK   = (120, 40, 0)
C_BLOCK        = (252, 152, 56)
C_BLOCK_USED   = (180, 120, 80)
C_PIPE         = (0, 168, 0)
C_PIPE_L       = (184, 248, 24)
C_PIPE_D       = (0, 110, 0)
C_MARIO_RED    = (248, 56, 0)
C_MARIO_SKIN   = (255, 204, 150)
C_MARIO_BROWN  = (136, 112, 0)
C_LUIGI_GREEN  = (0, 168, 0)
C_WHITE        = (255, 255, 255)
C_BLACK        = (0, 0, 0)
C_GOOMBA       = (228, 92, 16)
C_KOOPA        = (0, 168, 0)
C_KOOPA_WING   = (255, 255, 255)
C_CLOUD        = (255, 255, 255)
C_BUSH         = (0, 168, 0)
C_CASTLE       = (160, 160, 160)
C_FIREBAR      = (248, 56, 0)
C_COIN         = (252, 216, 60)
C_UI           = (255, 255, 255)

# ─── AUDIO ENGINE ────────────────────────────────────────────────────────────
class AudioEngine:
    """
    Real-time Synthesizer mimicking the NES RP2A03 Chip.
    Generates Square, Triangle, and Noise channels.
    """
    def __init__(self):
        self.sample_rate = 44100
        self.volume = 0.2
        self.enabled = False
        try:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=1024)
            self.enabled = True
        except:
            print("Audio Init Failed. Running in silent mode.")

        # Pre-calculated frequencies for notes
        self.notes = {}
        base_a4 = 440.0
        keys = ['c','c#','d','d#','e','f','f#','g','g#','a','a#','b']
        for oct in range(2, 7):
            for i, k in enumerate(keys):
                n_idx = (oct * 12 + i) - 57
                freq = base_a4 * (2 ** (n_idx / 12.0))
                self.notes[f"{k}{oct}"] = freq
        self.notes['rest'] = 0

        # SFX Cache
        self.sounds = {}
        if self.enabled:
            self._generate_sfx()

        # Music State
        self.music_queue = []
        self.music_timer = 0
        self.current_note = 0
        self.track_name = None

    def _gen_tone(self, freq, duration, wave_type='square', duty=0.5, slide=0):
        if not self.enabled: return None
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            t = i / self.sample_rate
            current_freq = freq + (slide * t)
            if current_freq <= 0: current_freq = 1
            
            phase = (t * current_freq) % 1.0
            
            val = 0.0
            if wave_type == 'square':
                val = 1.0 if phase < duty else -1.0
            elif wave_type == 'triangle':
                val = 2.0 * abs(2.0 * phase - 1.0) - 1.0
            elif wave_type == 'noise':
                val = random.uniform(-1, 1)
            elif wave_type == 'saw':
                val = 2.0 * (phase - 0.5)

            # Envelope
            vol = self.volume * 32000
            if i < 500: vol *= (i/500)
            if i > n_samples - 500: vol *= ((n_samples - i)/500)
            
            buf[i] = int(val * vol)
            
        return pygame.mixer.Sound(buffer=buf)

    def _generate_sfx(self):
        self.sounds['jump_s'] = self._gen_tone(220, 0.15, 'square', slide=200)
        self.sounds['jump_l'] = self._gen_tone(150, 0.20, 'square', slide=150)
        self.sounds['coin'] = self._gen_tone(900, 0.1, 'square', duty=0.1, slide=500)
        self.sounds['stomp'] = self._gen_tone(100, 0.05, 'noise')
        self.sounds['bump'] = self._gen_tone(80, 0.05, 'square', duty=0.2)
        self.sounds['break'] = self._gen_tone(100, 0.1, 'noise')
        self.sounds['powerup'] = self._gen_tone(300, 0.6, 'triangle', slide=600)
        self.sounds['shrink'] = self._gen_tone(600, 0.5, 'triangle', slide=-400)
        self.sounds['fireball'] = self._gen_tone(800, 0.05, 'noise')
        self.sounds['die'] = self._gen_tone(500, 0.8, 'saw', slide=-300)
        self.sounds['pause'] = self._gen_tone(400, 0.1, 'square', duty=0.8)
        self.sounds['kick'] = self._gen_tone(100, 0.1, 'noise')
        self.sounds['flag'] = self._gen_tone(300, 1.5, 'square', slide=-50)

    def play_sfx(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def play_music(self, track_name):
        self.track_name = track_name
        self.current_note = 0
        self.music_timer = time.time()
        
        # Define Tracks
        if track_name == 'overworld':
            # Simplified theme
            self.music_queue = [
                ('e4',0.15), ('e4',0.15), ('rest',0.15), ('e4',0.15), ('rest',0.15), ('c4',0.15), ('e4',0.3), ('g4',0.3), ('rest',0.3), ('g3',0.3), ('rest',0.3),
                ('c4',0.45), ('g3',0.45), ('e3',0.45), ('a3',0.3), ('b3',0.3), ('a#3',0.15), ('a3',0.3), ('g3',0.2), ('e4',0.2), ('g4',0.2), ('a4',0.3), ('f4',0.15), ('g4',0.15)
            ]
        elif track_name == 'underground':
            self.music_queue = [
                ('c4',0.11), ('c5',0.11), ('a3',0.11), ('a4',0.11), ('a#3',0.11), ('a#4',0.11), ('rest',0.2)
            ]
        elif track_name == 'castle':
            self.music_queue = [
                ('d4',0.08), ('d#4',0.08), ('d4',0.08), ('rest',0.08), ('a3',0.08), ('rest',0.1),
                ('d3',0.08), ('d#3',0.08), ('d3',0.08)
            ]
        elif track_name == 'star':
             self.music_queue = [
                ('c4',0.1), ('c4',0.1), ('d4',0.1), ('c4',0.1), ('f4',0.1), ('e4',0.1),
                ('d4',0.1), ('d4',0.1), ('e4',0.1), ('d4',0.1), ('g4',0.1), ('f4',0.1)
             ]
        else:
            self.music_queue = []

    def update(self):
        if not self.enabled or not self.music_queue: return
        
        if time.time() >= self.music_timer:
            if self.current_note >= len(self.music_queue):
                self.current_note = 0
            
            note, dur = self.music_queue[self.current_note]
            freq = self.notes.get(note, 0)
            
            if freq > 0:
                s = self._gen_tone(freq, dur * 0.9, 'square', duty=0.5)
                if s: s.play()
            
            self.music_timer = time.time() + dur
            self.current_note += 1

# ─── RENDERING SYSTEM ────────────────────────────────────────────────────────
class Renderer:
    """Handles procedural pixel art drawing."""
    
    @staticmethod
    def draw_pixel_rect(surf, color, rect, border=None):
        pygame.draw.rect(surf, color, rect)
        if border:
            pygame.draw.rect(surf, border, rect, 2)

    @staticmethod
    def draw_mario(surf, x, y, frame, facing, state, powerup):
        # 0=Small, 1=Big, 2=Fire
        is_big = powerup > 0
        h = TILE_SIZE * 2 if is_big else TILE_SIZE
        w = TILE_SIZE
        
        # Colors
        c_hat = C_WHITE if powerup == 2 else C_MARIO_RED
        c_shirt = C_MARIO_RED if powerup == 2 else C_BRICK
        c_over = C_WHITE if powerup == 2 else C_MARIO_BROWN

        sx = int(x)
        sy = int(y)
        
        # Facing flip
        offset_x = 0
        
        # Body
        body_h = h // 2
        Renderer.draw_pixel_rect(surf, c_shirt, (sx + 2, sy + (h//2), w-4, body_h))
        
        # Overalls
        Renderer.draw_pixel_rect(surf, c_over, (sx + 2, sy + (h//2) + 4, w-4, 8))
        Renderer.draw_pixel_rect(surf, C_COIN, (sx + 4, sy + (h//2) + 6, 2, 2)) # Button
        
        # Head
        head_y = sy
        Renderer.draw_pixel_rect(surf, C_MARIO_SKIN, (sx + 2, head_y + 4, w-4, 12)) # Face
        Renderer.draw_pixel_rect(surf, c_hat, (sx, head_y, w, 6)) # Hat Top
        Renderer.draw_pixel_rect(surf, c_hat, (sx + (0 if facing == -1 else 4), head_y + 4, 12, 4)) # Hat Brim
        
        # Eye / Moustache
        eye_x = sx + 8 if facing == 1 else sx + 4
        Renderer.draw_pixel_rect(surf, C_BLACK, (eye_x, head_y + 8, 2, 4))
        mustache_x = sx + 8 if facing == 1 else sx + 2
        Renderer.draw_pixel_rect(surf, C_BLACK, (mustache_x, head_y + 12, 6, 2))

        # Animation State
        if state == 'run':
            swing = int(math.sin(frame) * 4)
            Renderer.draw_pixel_rect(surf, c_shirt, (sx - 2 + swing, sy + (h//2) + 4, 4, 4)) # Hand

    @staticmethod
    def draw_goomba(surf, x, y, frame):
        sx, sy = int(x), int(y)
        # Head
        pygame.draw.ellipse(surf, C_GOOMBA, (sx, sy, TILE_SIZE, TILE_SIZE-4))
        # Eyes
        pygame.draw.ellipse(surf, C_WHITE, (sx + 4, sy + 8, 10, 10))
        pygame.draw.ellipse(surf, C_WHITE, (sx + 20, sy + 8, 10, 10))
        pygame.draw.circle(surf, C_BLACK, (sx + 8, sy + 12), 2)
        pygame.draw.circle(surf, C_BLACK, (sx + 24, sy + 12), 2)
        # Feet animation
        step = int(frame * 0.2) % 2
        foot_color = C_BLACK
        if step == 0:
            pygame.draw.ellipse(surf, foot_color, (sx, sy + TILE_SIZE - 6, 12, 6))
            pygame.draw.ellipse(surf, foot_color, (sx + 20, sy + TILE_SIZE - 6, 12, 6))
        else:
            pygame.draw.ellipse(surf, foot_color, (sx + 4, sy + TILE_SIZE - 6, 12, 6))
            pygame.draw.ellipse(surf, foot_color, (sx + 16, sy + TILE_SIZE - 6, 12, 6))

    @staticmethod
    def draw_koopa(surf, x, y, frame, facing, flying=False):
        sx, sy = int(x), int(y)
        h = TILE_SIZE * 1.5
        
        # Head
        head_x = sx + 4 if facing == -1 else sx + 16
        pygame.draw.rect(surf, C_COIN, (head_x, sy, 12, 12))
        pygame.draw.rect(surf, C_BLACK, (head_x + (2 if facing == -1 else 8), sy + 4, 2, 2))
        
        # Shell
        pygame.draw.rect(surf, C_KOOPA, (sx + 4, sy + 12, 24, 24))
        pygame.draw.rect(surf, C_WHITE, (sx + 8, sy + 16, 16, 16), 2)
        
        # Wings
        if flying:
            wing_y = sy + 4 + int(math.sin(frame*0.5)*4)
            pygame.draw.polygon(surf, C_KOOPA_WING, [(sx+8, wing_y), (sx-4, wing_y-8), (sx+4, wing_y-12)])

        # Feet
        step = int(frame * 0.2) % 2
        if step == 0:
            pygame.draw.rect(surf, C_COIN, (sx + 4, sy + 32, 8, 8))
            pygame.draw.rect(surf, C_COIN, (sx + 20, sy + 32, 8, 8))
        else:
            pygame.draw.rect(surf, C_COIN, (sx + 2, sy + 30, 8, 8))
            pygame.draw.rect(surf, C_COIN, (sx + 22, sy + 30, 8, 8))

    @staticmethod
    def draw_bowser(surf, x, y, frame, facing):
        sx, sy = int(x), int(y)
        w, h = TILE_SIZE * 2, TILE_SIZE * 2
        
        # Body
        pygame.draw.rect(surf, C_KOOPA, (sx + 10, sy + 20, w-20, h-30))
        pygame.draw.rect(surf, C_COIN, (sx + 16, sy + 30, w-32, h-40)) # Belly
        
        # Shell (Spiked)
        shell_x = sx + w - 16 if facing == -1 else sx
        pygame.draw.rect(surf, C_PIPE_D, (shell_x, sy + 24, 16, 32))
        
        # Head
        head_x = sx if facing == -1 else sx + w - 30
        pygame.draw.rect(surf, C_KOOPA, (head_x, sy, 30, 24))
        
        # Mouth open/close
        mouth_open = (frame % 20) < 10
        if mouth_open:
            pygame.draw.rect(surf, C_MARIO_RED, (head_x + 10, sy + 16, 10, 8))

    @staticmethod
    def draw_block(surf, x, y, type, theme='overworld'):
        rect = (x, y, TILE_SIZE, TILE_SIZE)
        
        if type == 'ground':
            c_main = C_BRICK if theme == 'castle' else C_GROUND
            if theme == 'underground': c_main = C_BRICK_DARK
            pygame.draw.rect(surf, c_main, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
            pygame.draw.line(surf, C_BLACK, (x + 8, y), (x + 8, y + TILE_SIZE), 2)
        
        elif type == 'brick':
            c_main = C_BRICK_DARK if theme == 'underground' else C_BRICK
            if theme == 'castle': c_main = C_CASTLE
            pygame.draw.rect(surf, c_main, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
            pygame.draw.line(surf, C_BLACK, (x, y + TILE_SIZE//2), (x + TILE_SIZE, y + TILE_SIZE//2), 2)
            pygame.draw.line(surf, C_BLACK, (x + TILE_SIZE//2, y), (x + TILE_SIZE//2, y + TILE_SIZE//2), 2)
            pygame.draw.line(surf, C_BLACK, (x + TILE_SIZE//4, y + TILE_SIZE//2), (x + TILE_SIZE//4, y + TILE_SIZE), 2)
        
        elif type == 'hard':
            pygame.draw.rect(surf, C_BLOCK_USED, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
            pygame.draw.rect(surf, C_BLACK, (x + 4, y + 4, 4, 4))
            pygame.draw.rect(surf, C_BLACK, (x + TILE_SIZE - 8, y + TILE_SIZE - 8, 4, 4))

        elif type == 'q_block':
            ticks = pygame.time.get_ticks()
            flash = (ticks // 200) % 4
            color = C_BLOCK if flash != 0 else C_BLOCK_USED
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
            pygame.draw.rect(surf, C_BLACK, (x+4, y+4, 4, 4))
            pygame.draw.rect(surf, C_BLACK, (x+TILE_SIZE-8, y+4, 4, 4))
            pygame.draw.rect(surf, C_BLACK, (x+4, y+TILE_SIZE-8, 4, 4))
            pygame.draw.rect(surf, C_BLACK, (x+TILE_SIZE-8, y+TILE_SIZE-8, 4, 4))
            # Question Mark
            if flash != 0:
                pygame.draw.rect(surf, C_BRICK_DARK, (x + 14, y + 8, 12, 4))
                pygame.draw.rect(surf, C_BRICK_DARK, (x + 22, y + 12, 4, 8))
                pygame.draw.rect(surf, C_BRICK_DARK, (x + 18, y + 24, 4, 4))

        elif type == 'used':
            pygame.draw.rect(surf, C_BLOCK_USED, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
        
        elif type == 'pipe':
            pygame.draw.rect(surf, C_PIPE, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
            pygame.draw.rect(surf, C_PIPE_L, (x + 4, y, 6, TILE_SIZE))
        
        elif type == 'pipe_top':
            pygame.draw.rect(surf, C_PIPE, rect)
            pygame.draw.rect(surf, C_BLACK, rect, 2)
            pygame.draw.rect(surf, C_BLACK, (x, y + TILE_SIZE - 4, TILE_SIZE, 2)) # Lip

# ─── PARTICLE SYSTEM ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, type, val=None):
        self.x, self.y = x, y
        self.type = type
        self.life = 60
        self.val = val
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, -6)
        
    def update(self):
        self.life -= 1
        if self.type == 'debris':
            self.x += self.vx
            self.y += self.vy
            self.vy += 0.4 # Gravity
        elif self.type == 'score':
            self.y -= 1
        elif self.type == 'fireball_explode':
            pass

    def draw(self, surf, cam_x):
        sx = self.x - cam_x
        if self.type == 'debris':
            pygame.draw.rect(surf, C_BRICK, (sx, self.y, 8, 8))
        elif self.type == 'score':
            font = pygame.font.Font(None, 24)
            t = font.render(str(self.val), True, C_WHITE)
            surf.blit(t, (sx, self.y))
        elif self.type == 'fireball_explode':
            radius = (60 - self.life) // 2
            pygame.draw.circle(surf, C_MARIO_RED, (int(sx), int(self.y)), radius, 2)

# ─── ENTITY SYSTEM ───────────────────────────────────────────────────────────
class Entity:
    def __init__(self, x, y, w, h):
        self.x, self.y = float(x), float(y)
        self.w, self.h = w, h
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = False
        self.alive = True
        self.facing = -1
        self.rect_cache = pygame.Rect(x, y, w, h)

    def update_rect(self):
        self.rect_cache = pygame.Rect(self.x, self.y, self.w, self.h)

    @property
    def rect(self):
        return self.rect_cache

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, TILE_SIZE - 10, TILE_SIZE)
        self.powerup = 0 # 0=small, 1=big, 2=fire
        self.state = 'idle'
        self.frame = 0
        self.coyote_timer = 0
        self.jump_hold = False
        self.iframes = 0
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.fireballs = []
        self.flag_slide = False
        self.level_complete_timer = 0
        self.growth_timer = 0

    def update(self, keys, level, audio):
        # Fireball Logic
        for f in self.fireballs:
            f.update(level)
        self.fireballs = [f for f in self.fireballs if f.alive]

        # Growth Animation
        if self.growth_timer > 0:
            self.growth_timer -= 1
            return # Freeze while growing

        # Level Completion Logic
        if self.flag_slide:
            self.x = level.flag_x + 6
            if self.y < level.floor_y - TILE_SIZE:
                self.y += 4
                self.state = 'climb'
            else:
                self.flag_slide = False
                self.vx = 2
                self.state = 'walk'
                self.facing = 1
                level.complete = True
            self.update_rect()
            return
        
        if level.complete:
            self.x += 2
            self.state = 'walk'
            self.frame += 0.2
            if self.x > level.castle_x + TILE_SIZE:
                self.alive = False # End level signal
            return

        # Death
        if self.state == 'dead':
            self.y += self.vy
            self.vy += GRAVITY
            return

        # Movement
        acc = ACCEL
        max_v = MAX_WALK
        if any(keys[k] for k in KEY_RUN):
            max_v = MAX_RUN
            acc *= 1.5

        if any(keys[k] for k in KEY_RIGHT):
            self.vx += acc
            self.facing = 1
            self.state = 'run'
        elif any(keys[k] for k in KEY_LEFT):
            self.vx -= acc
            self.facing = -1
            self.state = 'run'
        else:
            self.vx *= FRICTION
            if abs(self.vx) < 0.1: self.vx = 0
            self.state = 'idle'

        self.vx = max(-max_v, min(max_v, self.vx))
        self.x += self.vx
        self.resolve_collisions(level, True)

        # Jumping
        if self.on_ground:
            self.coyote_timer = 6
        else:
            self.coyote_timer -= 1
        
        jump_pressed = any(keys[k] for k in KEY_JUMP)
        if jump_pressed and not self.jump_hold and self.coyote_timer > 0:
            self.vy = JUMP_FORCE
            self.jump_hold = True
            self.on_ground = False
            self.coyote_timer = 0
            audio.play_sfx('jump_l' if self.powerup > 0 else 'jump_s')
        
        if not jump_pressed:
            self.jump_hold = False
        
        # Gravity
        g = GRAVITY
        if self.jump_hold and self.vy < 0:
            g += JUMP_HOLD_FORCE
        
        self.vy += g
        self.vy = min(self.vy, MAX_FALL)
        self.y += self.vy
        self.on_ground = False
        self.resolve_collisions(level, False)

        if not self.on_ground:
            self.state = 'jump'

        # Animation Frame
        self.frame += abs(self.vx) * 0.15

        # Interactions
        if self.y > SCREEN_H + 64:
            self.die(audio)
        
        if self.iframes > 0: self.iframes -= 1

    def resolve_collisions(self, level, x_axis):
        self.update_rect()
        player_rect = self.rect
        
        # Grid range to check
        start_col = int(player_rect.left // TILE_SIZE) - 1
        end_col = int(player_rect.right // TILE_SIZE) + 1
        start_row = int(player_rect.top // TILE_SIZE) - 1
        end_row = int(player_rect.bottom // TILE_SIZE) + 1

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile = level.get_tile(col, row)
                if tile and tile not in ('bush', 'cloud', 'hill'):
                    # Check passability
                    if tile in ('pipe_top', 'pipe') or tile == 'ground' or tile == 'brick' or tile == 'q_block' or tile == 'hard' or tile == 'used':
                         tile_rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                         if player_rect.colliderect(tile_rect):
                            if x_axis:
                                if self.vx > 0: self.x = tile_rect.left - self.w
                                elif self.vx < 0: self.x = tile_rect.right
                                self.vx = 0
                            else:
                                if self.vy > 0:
                                    self.y = tile_rect.top - self.h
                                    self.on_ground = True
                                    self.vy = 0
                                elif self.vy < 0:
                                    self.y = tile_rect.bottom
                                    self.vy = 0
                                    level.hit_block(col, row, self)
                            self.update_rect()

    def shoot(self, audio):
        if self.powerup == 2 and len(self.fireballs) < 2:
            fb = Fireball(self.x + (self.w if self.facing == 1 else 0), self.y + 16, self.facing)
            self.fireballs.append(fb)
            audio.play_sfx('fireball')

    def get_hit(self, audio):
        if self.iframes > 0: return
        if self.powerup > 0:
            self.powerup = 0
            self.growth_timer = 60 # Hit stun
            self.iframes = 120
            self.h = TILE_SIZE
            self.y += TILE_SIZE
            audio.play_sfx('shrink')
        else:
            self.die(audio)

    def die(self, audio):
        if self.state != 'dead':
            self.state = 'dead'
            self.vy = -10
            self.alive = False
            audio.play_sfx('die')
            audio.track_name = None # Stop music

class Fireball(Entity):
    def __init__(self, x, y, direction):
        super().__init__(x, y, 12, 12)
        self.vx = direction * 8.0
        self.vy = 2.0
        self.bounces = 0
    
    def update(self, level):
        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY
        
        # Simple tile checks
        cx, cy = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
        t = level.get_tile(cx, cy)
        
        # Ground hit (Bounce)
        if self.vy > 0 and level.get_tile(cx, cy+1) in ('ground', 'brick', 'hard', 'q_block', 'used', 'pipe'):
            self.vy = -6.0
        
        # Wall hit
        if level.get_tile(int((self.x + self.vx) // TILE_SIZE), cy) in ('ground', 'brick', 'hard', 'q_block', 'used', 'pipe'):
            self.alive = False
            level.particles.append(Particle(self.x, self.y, 'fireball_explode'))

        if self.y > SCREEN_H: self.alive = False
        self.update_rect()

class Enemy(Entity):
    def __init__(self, x, y, type):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE)
        self.type = type
        self.vx = -ENEMY_SPEED
        self.active = False
        self.state = 'walk' # walk, shell, dead
        self.frame = 0
        self.dead_timer = 0
        self.hp = 1
        
        if type == 'bowser':
            self.hp = 5
            self.w = TILE_SIZE * 2
            self.h = TILE_SIZE * 2
            self.y -= TILE_SIZE
            self.shoot_timer = 0

    def update(self, level, player, audio):
        dist = abs(self.x - player.x)
        if not self.active:
            if dist < SCREEN_W + 100: self.active = True
            return

        if dist > SCREEN_W * 2 and self.type != 'bowser':
            self.alive = False # Despawn

        # Dead logic
        if self.state == 'dead':
            self.dead_timer += 1
            if self.dead_timer > 30: self.alive = False
            return
        
        # Bowser Logic
        if self.type == 'bowser':
            if player.x < self.x: self.facing = -1
            else: self.facing = 1
            
            # Jump
            if self.on_ground and random.random() < 0.02:
                self.vy = -8.0
                
            # Fire
            self.shoot_timer += 1
            if self.shoot_timer > 120:
                self.shoot_timer = 0
                audio.play_sfx('fireball')
                # Spawn hammer/fire (abstracted)
            
            # Move bounds
            if self.x < level.camera_x + TILE_SIZE * 5: self.vx = ENEMY_SPEED
            if self.x > level.camera_x + SCREEN_W - TILE_SIZE * 5: self.vx = -ENEMY_SPEED

        # Shell Logic
        if self.state == 'shell':
            if abs(self.vx) > 0:
                # Sliding collision
                next_x = self.x + self.vx
                cx = int((next_x + self.w/2) // TILE_SIZE)
                cy = int((self.y + self.h/2) // TILE_SIZE)
                if level.get_tile(cx, cy):
                    self.vx *= -1
                    audio.play_sfx('bump')
                
                # Hit enemies
                rect = self.rect
                for other in level.enemies:
                    if other != self and other.alive and other.state != 'dead' and rect.colliderect(other.rect):
                        other.die(level, audio, score_val=500)
            else:
                self.vx = 0

        # General Physics
        self.vy += GRAVITY
        self.y += self.vy
        
        # Floor
        bot_y = int((self.y + self.h) // TILE_SIZE)
        mid_x = int((self.x + self.w/2) // TILE_SIZE)
        
        # Simple floor collision
        t_below = level.get_tile(mid_x, bot_y)
        if t_below and t_below not in ('bush', 'cloud'):
            self.y = bot_y * TILE_SIZE - self.h
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # Wall Turn
        next_x = self.x + self.vx
        side_x = int((next_x + (0 if self.vx < 0 else self.w)) // TILE_SIZE)
        mid_y = int((self.y + self.h/2) // TILE_SIZE)
        
        if self.type != 'bowser' and self.state != 'shell':
            if level.get_tile(side_x, mid_y):
                self.vx *= -1
                self.facing *= -1
        
        self.x += self.vx
        self.frame += 1
        self.update_rect()
        
        if self.y > SCREEN_H + 64: self.alive = False

    def die(self, level, audio, score_val=100):
        if self.type == 'bowser':
            self.hp -= 1
            if self.hp > 0: return
            level.complete = True # Defeated Bowser
            
        audio.play_sfx('stomp')
        level.particles.append(Particle(self.x, self.y, 'score', score_val))
        
        if self.type == 'koopa' and self.state != 'shell':
            self.state = 'shell'
            self.vx = 0
            self.y += TILE_SIZE // 2
            self.h = TILE_SIZE
        else:
            self.state = 'dead'

# ─── LEVEL SYSTEM ────────────────────────────────────────────────────────────
class Level:
    def __init__(self, world, stage):
        self.width = 300 # Wide levels
        self.height = 15
        self.tiles = {}
        self.enemies = []
        self.particles = []
        self.camera_x = 0
        self.world = world
        self.stage = stage
        self.complete = False
        self.theme = 'overworld'
        
        if stage == 2: self.theme = 'underground'
        elif stage == 3: self.theme = 'athletic'
        elif stage == 4: self.theme = 'castle'

        self.generate()

    def generate(self):
        # 1. Terrain Generation
        self.floor_y = (self.height - 2) * TILE_SIZE
        ground_h = 2
        
        # Fill ground
        for x in range(self.width):
            # Pit logic
            if self.theme != 'castle' and 30 < x < self.width - 30:
                if random.random() < 0.05: continue 
            
            for y in range(self.height - ground_h, self.height):
                self.tiles[(x,y)] = 'ground'
        
        # Ceiling (Underground/Castle)
        if self.theme in ('underground', 'castle'):
            for x in range(self.width):
                self.tiles[(x,0)] = 'hard'
                self.tiles[(x,1)] = 'hard'
        
        # 2. Features Pass
        x = 10
        while x < self.width - 30:
            x += random.randint(3, 8)
            
            # Pipes
            if self.theme == 'overworld' and random.random() < 0.2:
                h = random.randint(2, 4)
                self.tiles[(x, self.height - 3)] = 'pipe_top'
                for i in range(1, h):
                    self.tiles[(x, self.height - 3 - i)] = 'pipe'
                # Piranha Plant opportunity
                x += 2
                continue
            
            # Structures
            struct_type = random.choice(['row', 'pyramid', 'q_formation'])
            y_base = self.height - 6
            
            if struct_type == 'row':
                w = random.randint(3, 7)
                for i in range(w):
                    self.tiles[(x+i, y_base)] = 'brick'
                    if random.random() < 0.3:
                        self.enemies.append(Enemy((x+i)*TILE_SIZE, (y_base-1)*TILE_SIZE, 'goomba'))
            
            elif struct_type == 'q_formation':
                self.tiles[(x, y_base)] = 'q_block'
                self.tiles[(x+1, y_base)] = 'brick'
                self.tiles[(x+2, y_base)] = 'q_block'
                self.tiles[(x+1, y_base-4)] = 'q_block'
                if random.random() < 0.5:
                     self.enemies.append(Enemy((x+1)*TILE_SIZE, (y_base-5)*TILE_SIZE, 'koopa'))

            x += 5

        # 3. Castle / Flag
        self.flag_x = (self.width - 15) * TILE_SIZE
        self.castle_x = (self.width - 8) * TILE_SIZE
        
        # Flagpole
        for i in range(2, 11):
            self.tiles[(self.width - 15, self.height - i)] = 'pole' # Just visual logic handled in drawing
        
        # Castle Structure
        cx = self.width - 8
        cy = self.height - 3
        # Simple blocks for castle
        for i in range(5):
            for j in range(5):
                 self.tiles[(cx+i, cy-j)] = 'hard'
        
        # Bowser?
        if self.theme == 'castle':
            self.enemies.append(Enemy((self.width - 20) * TILE_SIZE, (self.height - 5)*TILE_SIZE, 'bowser'))

    def get_tile(self, x, y):
        return self.tiles.get((x, y))

    def hit_block(self, x, y, player):
        t = self.tiles.get((x,y))
        
        if t == 'q_block':
            self.tiles[(x,y)] = 'used'
            player.coins += 1
            player.score += 200
            self.particles.append(Particle(x*TILE_SIZE, y*TILE_SIZE, 'score', 200))
            
            # Mushroom spawn logic
            if random.random() < 0.2 and player.powerup == 0:
                player.powerup = 1
                player.y -= TILE_SIZE
                player.h = TILE_SIZE * 2
                player.growth_timer = 30
            elif random.random() < 0.2 and player.powerup == 1:
                player.powerup = 2 # Fire flower
                player.growth_timer = 20
                
        elif t == 'brick':
            if player.powerup > 0:
                del self.tiles[(x,y)]
                # Debris
                for _ in range(4):
                    self.particles.append(Particle(x*TILE_SIZE + 8, y*TILE_SIZE + 8, 'debris'))
            else:
                # Bump animation (simplified)
                pass

# ─── MAIN GAME CLASS ─────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Ultra Mario Bros: Famicom Ultimate")
        self.clock = pygame.time.Clock()
        self.audio = AudioEngine()
        self.font = pygame.font.Font(None, 40)
        self.sfont = pygame.font.Font(None, 24)
        
        self.state = 'TITLE'
        self.world = 1
        self.stage = 1
        self.lives = 3
        
        # Star effect
        self.star_timer = 0
        self.title_timer = 0

    def start_level(self):
        self.level = Level(self.world, self.stage)
        self.player = Player(100, 100)
        self.camera_x = 0
        
        track = 'overworld'
        if self.level.theme == 'underground': track = 'underground'
        elif self.level.theme == 'castle': track = 'castle'
        self.audio.play_music(track)

    def run(self):
        running = True
        while running:
            # Events
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == 'TITLE' and event.key == pygame.K_RETURN:
                        self.state = 'LOAD'
                        self.load_timer = 120
                        self.audio.play_sfx('coin')
                    
                    if self.state == 'PLAY':
                        if event.key == pygame.K_x or event.key == pygame.K_LSHIFT:
                            self.player.shoot(self.audio)

            # Update & Draw
            if self.state == 'TITLE':
                self.update_title()
            elif self.state == 'LOAD':
                self.update_load()
            elif self.state == 'PLAY':
                self.update_play(keys)
            elif self.state == 'GAMEOVER':
                self.update_gameover()
            
            self.audio.update()
            self.clock.tick(FPS)
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

    def update_title(self):
        self.screen.fill(C_SKY)
        self.title_timer += 1
        
        # Draw Logo
        title_y = 100 + int(math.sin(self.title_timer * 0.05) * 10)
        t1 = self.font.render("SUPER MARIO BROS", True, C_MARIO_RED)
        t2 = self.font.render("FAMICOM ULTIMATE", True, C_BLOCK)
        
        self.screen.blit(t1, (SCREEN_W//2 - t1.get_width()//2, title_y))
        self.screen.blit(t2, (SCREEN_W//2 - t2.get_width()//2, title_y + 40))
        
        if (self.title_timer // 30) % 2 == 0:
            msg = self.font.render("PRESS START", True, C_WHITE)
            self.screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, 400))
        
        # Decoration
        Renderer.draw_mario(self.screen, 100, 560, self.title_timer * 0.2, 1, 'run', 0)
        Renderer.draw_goomba(self.screen, 300, 560, self.title_timer * 0.2)
        
        # Floor
        pygame.draw.rect(self.screen, C_GROUND, (0, 600, SCREEN_W, 120))

    def update_load(self):
        self.screen.fill(C_BLACK)
        self.load_timer -= 1
        
        info = self.font.render(f"WORLD {self.world}-{self.stage}", True, C_WHITE)
        lives = self.font.render(f"x {self.lives}", True, C_WHITE)
        Renderer.draw_mario(self.screen, SCREEN_W//2 - 60, SCREEN_H//2, 0, 1, 'idle', 0)
        
        self.screen.blit(info, (SCREEN_W//2 - info.get_width()//2, 250))
        self.screen.blit(lives, (SCREEN_W//2, SCREEN_H//2 + 20))
        
        if self.load_timer <= 0:
            self.state = 'PLAY'
            self.start_level()

    def update_play(self, keys):
        # 1. Update Player
        self.player.update(keys, self.level, self.audio)
        
        # 2. Camera
        target = self.player.x - SCREEN_W // 3
        self.level.camera_x = max(self.level.camera_x, target) # Only scroll right
        
        # 3. Enemies
        player_rect = self.player.rect
        for e in self.level.enemies:
            if not e.alive: continue
            
            e.update(self.level, self.player, self.audio)
            
            # Interaction
            if e.active and e.state != 'dead':
                e_rect = e.rect
                if player_rect.colliderect(e_rect):
                    # Stomp Logic
                    stomped = False
                    if self.player.vy > 0 and self.player.y < e.y:
                        stomped = True
                        self.player.vy = BOUNCE_FORCE
                        e.die(self.level, self.audio)
                    
                    if not stomped and not self.player.iframes:
                         # Hit Logic
                         if e.state == 'shell' and e.vx == 0:
                             # Kick shell
                             direction = 1 if self.player.x < e.x else -1
                             e.vx = direction * SHELL_SPEED
                             e.x += e.vx # Bump out
                             self.audio.play_sfx('kick')
                             self.player.iframes = 20 # Brief immunity so you don't instant-die kicking
                         else:
                             self.player.get_hit(self.audio)

        # 4. Particles
        for p in self.level.particles:
            p.update()
        self.level.particles = [p for p in self.level.particles if p.life > 0]

        # 5. Check Level End conditions
        if not self.player.alive:
            self.lives -= 1
            if self.lives <= 0:
                self.state = 'GAMEOVER'
            else:
                self.state = 'LOAD'
                self.load_timer = 120
        
        # Flag Pole Collision
        if not self.player.flag_slide and self.player.x >= self.level.flag_x and self.player.y < self.level.floor_y:
             if self.player.rect.colliderect(pygame.Rect(self.level.flag_x, 0, 10, SCREEN_H)):
                 self.player.flag_slide = True
                 self.player.x = self.level.flag_x
                 self.player.vx = 0
                 self.audio.play_music(None)
                 self.audio.play_sfx('flag')
        
        # Level Transition
        if not self.player.alive and self.level.complete:
            # Player walked off screen (win)
            self.stage += 1
            if self.stage > 4:
                self.stage = 1
                self.world += 1
            self.state = 'LOAD'
            self.load_timer = 150

        # Draw
        self.draw_play()

    def update_gameover(self):
        self.screen.fill(C_BLACK)
        t = self.font.render("GAME OVER", True, C_WHITE)
        self.screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2))
        
        if pygame.time.get_ticks() % 2000 < 1000:
            s = self.sfont.render("Press Enter to Restart", True, C_WHITE)
            self.screen.blit(s, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2 + 50))
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            self.lives = 3
            self.world = 1
            self.stage = 1
            self.score = 0
            self.state = 'TITLE'

    def draw_play(self):
        # Background
        bg_col = C_SKY
        if self.level.theme == 'underground': bg_col = C_BLACK
        elif self.level.theme == 'castle': bg_col = C_SKY_BLACK
        self.screen.fill(bg_col)
        
        cam = self.level.camera_x
        
        # Draw Scenery
        # (Simplified cloud/bush logic could go here)
        
        # Draw Tiles
        start_col = int(cam // TILE_SIZE)
        end_col = start_col + (SCREEN_W // TILE_SIZE) + 2
        
        for y in range(self.level.height):
            for x in range(start_col, end_col):
                t = self.level.get_tile(x, y)
                if t:
                    draw_x = x * TILE_SIZE - cam
                    draw_y = y * TILE_SIZE
                    Renderer.draw_block(self.screen, draw_x, draw_y, t, self.level.theme)

        # Draw Flagpole
        fx = self.level.flag_x - cam
        if -50 < fx < SCREEN_W:
            pygame.draw.rect(self.screen, C_BLOCK_USED, (fx + 6, TILE_SIZE * 2, 4, self.level.floor_y - TILE_SIZE*2))
            pygame.draw.circle(self.screen, C_BRICK, (int(fx+8), int(TILE_SIZE*2)), 8)
            # Flag
            flag_y = self.level.floor_y - TILE_SIZE*2
            if self.player.flag_slide:
                flag_y = self.player.y
            pygame.draw.polygon(self.screen, C_MARIO_RED, [(fx+10, flag_y), (fx+40, flag_y+10), (fx+10, flag_y+20)])

        # Draw Enemies
        for e in self.level.enemies:
            if e.alive and e.x - cam > -50 and e.x - cam < SCREEN_W:
                if e.type == 'goomba':
                    Renderer.draw_goomba(self.screen, e.x - cam, e.y, e.frame)
                elif e.type == 'koopa':
                    Renderer.draw_koopa(self.screen, e.x - cam, e.y, e.frame, e.facing)
                elif e.type == 'bowser':
                    Renderer.draw_bowser(self.screen, e.x - cam, e.y, e.frame, e.facing)
        
        # Draw Particles
        for p in self.level.particles:
            p.draw(self.screen, cam)

        # Draw Fireballs
        for f in self.player.fireballs:
            pygame.draw.circle(self.screen, C_FIREBAR, (int(f.x - cam), int(f.y)), 6)
            pygame.draw.circle(self.screen, C_COIN, (int(f.x - cam), int(f.y)), 3)

        # Draw Player
        if self.player.state != 'dead' and self.player.iframes % 4 < 2:
            Renderer.draw_mario(self.screen, self.player.x - cam, self.player.y, self.player.frame, self.player.facing, self.player.state, self.player.powerup)

        # HUD
        self.draw_hud()

    def draw_hud(self):
        ui_y = 20
        # MARIO
        self.screen.blit(self.font.render("MARIO", True, C_WHITE), (50, ui_y))
        self.screen.blit(self.font.render(f"{self.player.score:06d}", True, C_WHITE), (50, ui_y + 30))
        
        # COINS
        pygame.draw.circle(self.screen, C_COIN, (300, ui_y + 15), 8)
        self.screen.blit(self.font.render(f"x {self.player.coins:02d}", True, C_WHITE), (320, ui_y + 5))
        
        # WORLD
        self.screen.blit(self.font.render("WORLD", True, C_WHITE), (450, ui_y))
        self.screen.blit(self.font.render(f"{self.world}-{self.stage}", True, C_WHITE), (460, ui_y + 30))
        
        # TIME (Static for now)
        self.screen.blit(self.font.render("TIME", True, C_WHITE), (650, ui_y))
        self.screen.blit(self.font.render(" 300", True, C_WHITE), (660, ui_y + 30))

if __name__ == "__main__":
    game = Game()
    game.run()
