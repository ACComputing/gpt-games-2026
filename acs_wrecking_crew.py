import pygame
import sys
import math
import struct
import random

# --- Constants ---
SCREEN_WIDTH = 512
SCREEN_HEIGHT = 480
INTERNAL_WIDTH = 256
INTERNAL_HEIGHT = 240
FPS = 60
TILE_SIZE = 16

# NES Palette (subset of actual NES colors)
NES_PALETTE = {
    'black': (0, 0, 0),
    'dark_gray': (88, 88, 88),
    'gray': (152, 152, 152),
    'white': (252, 252, 252),
    'red': (228, 0, 88),
    'dark_red': (168, 0, 32),
    'orange': (228, 92, 16),
    'brown': (136, 52, 0),
    'tan': (228, 148, 92),
    'yellow': (252, 224, 60),
    'green': (0, 168, 0),
    'dark_green': (0, 120, 0),
    'lime': (88, 216, 84),
    'cyan': (0, 232, 216),
    'blue': (0, 120, 248),
    'dark_blue': (0, 0, 168),
    'purple': (148, 0, 132),
    'pink': (248, 120, 248),
    'skin': (252, 188, 148),
}

# Game States
STATE_MENU = 'menu'
STATE_PLAY = 'play'
STATE_HELP = 'help'
STATE_CREDITS = 'credits'
STATE_ABOUT = 'about'
STATE_GAMEOVER = 'gameover'
STATE_WIN = 'win'

# Tile Types
TYPE_EMPTY = 0
TYPE_FLOOR = 1
TYPE_WALL = 2
TYPE_LADDER = 3

# Level Map (16 cols x 15 rows for NES resolution)
LEVEL_LAYOUT = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [1,1,1,1,1,3,1,1,1,1,3,1,1,1,1,1],
    [3,0,2,2,0,3,0,2,2,0,3,0,2,2,0,3],
    [3,0,2,2,0,3,0,2,2,0,3,0,2,2,0,3],
    [1,1,1,3,1,1,1,1,1,1,1,1,3,1,1,1],
    [0,2,0,3,0,0,3,0,0,3,0,0,3,0,2,0],
    [0,2,0,3,0,0,3,0,0,3,0,0,3,0,2,0],
    [1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1],
    [3,0,0,2,0,0,0,3,0,0,0,2,0,0,0,3],
    [3,0,0,2,0,0,0,3,0,0,0,2,0,0,0,3],
    [1,1,3,1,1,1,1,1,1,1,1,1,1,3,1,1],
    [0,0,3,0,2,0,0,3,0,0,2,0,0,3,0,0],
    [0,0,3,0,2,0,0,3,0,0,2,0,0,3,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# 8x8 Font Data (simplified bitmap font)
FONT_DATA = {
    'A': [0x18,0x3C,0x66,0x7E,0x66,0x66,0x66,0x00],
    'B': [0x7C,0x66,0x7C,0x66,0x66,0x66,0x7C,0x00],
    'C': [0x3C,0x66,0x60,0x60,0x60,0x66,0x3C,0x00],
    'D': [0x78,0x6C,0x66,0x66,0x66,0x6C,0x78,0x00],
    'E': [0x7E,0x60,0x7C,0x60,0x60,0x60,0x7E,0x00],
    'F': [0x7E,0x60,0x7C,0x60,0x60,0x60,0x60,0x00],
    'G': [0x3C,0x66,0x60,0x6E,0x66,0x66,0x3C,0x00],
    'H': [0x66,0x66,0x7E,0x66,0x66,0x66,0x66,0x00],
    'I': [0x3C,0x18,0x18,0x18,0x18,0x18,0x3C,0x00],
    'J': [0x1E,0x0C,0x0C,0x0C,0x6C,0x6C,0x38,0x00],
    'K': [0x66,0x6C,0x78,0x70,0x78,0x6C,0x66,0x00],
    'L': [0x60,0x60,0x60,0x60,0x60,0x60,0x7E,0x00],
    'M': [0x63,0x77,0x7F,0x6B,0x63,0x63,0x63,0x00],
    'N': [0x66,0x76,0x7E,0x7E,0x6E,0x66,0x66,0x00],
    'O': [0x3C,0x66,0x66,0x66,0x66,0x66,0x3C,0x00],
    'P': [0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00],
    'Q': [0x3C,0x66,0x66,0x66,0x66,0x6C,0x36,0x00],
    'R': [0x7C,0x66,0x66,0x7C,0x78,0x6C,0x66,0x00],
    'S': [0x3C,0x66,0x60,0x3C,0x06,0x66,0x3C,0x00],
    'T': [0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x00],
    'U': [0x66,0x66,0x66,0x66,0x66,0x66,0x3C,0x00],
    'V': [0x66,0x66,0x66,0x66,0x66,0x3C,0x18,0x00],
    'W': [0x63,0x63,0x63,0x6B,0x7F,0x77,0x63,0x00],
    'X': [0x66,0x66,0x3C,0x18,0x3C,0x66,0x66,0x00],
    'Y': [0x66,0x66,0x66,0x3C,0x18,0x18,0x18,0x00],
    'Z': [0x7E,0x06,0x0C,0x18,0x30,0x60,0x7E,0x00],
    '0': [0x3C,0x66,0x6E,0x76,0x66,0x66,0x3C,0x00],
    '1': [0x18,0x38,0x18,0x18,0x18,0x18,0x7E,0x00],
    '2': [0x3C,0x66,0x06,0x1C,0x30,0x60,0x7E,0x00],
    '3': [0x3C,0x66,0x06,0x1C,0x06,0x66,0x3C,0x00],
    '4': [0x0C,0x1C,0x3C,0x6C,0x7E,0x0C,0x0C,0x00],
    '5': [0x7E,0x60,0x7C,0x06,0x06,0x66,0x3C,0x00],
    '6': [0x1C,0x30,0x60,0x7C,0x66,0x66,0x3C,0x00],
    '7': [0x7E,0x06,0x0C,0x18,0x30,0x30,0x30,0x00],
    '8': [0x3C,0x66,0x66,0x3C,0x66,0x66,0x3C,0x00],
    '9': [0x3C,0x66,0x66,0x3E,0x06,0x0C,0x38,0x00],
    ' ': [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
    ':': [0x00,0x18,0x18,0x00,0x18,0x18,0x00,0x00],
    '-': [0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00],
    '!': [0x18,0x18,0x18,0x18,0x18,0x00,0x18,0x00],
    '.': [0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00],
    '/': [0x06,0x0C,0x18,0x30,0x60,0xC0,0x80,0x00],
    '>': [0x60,0x30,0x18,0x0C,0x18,0x30,0x60,0x00],
    "'": [0x18,0x18,0x08,0x00,0x00,0x00,0x00,0x00],
}

class SoundEngine:
    """NES-style 2A03 sound synthesis"""
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.sounds = {}
            self.generate_sounds()
        except:
            self.enabled = False

    def generate_sounds(self):
        if not self.enabled: return
        # NES-style bleeps and bloops
        self.sounds['jump'] = self.make_nes_sound([440, 520, 600], 0.08, 'pulse')
        self.sounds['land'] = self.make_nes_sound([120], 0.03, 'noise')
        self.sounds['hammer'] = self.make_nes_sound([200, 150, 100], 0.12, 'pulse')
        self.sounds['hit'] = self.make_nes_sound([800, 600, 400, 200], 0.15, 'pulse')
        self.sounds['win'] = self.make_nes_sound([523, 659, 784, 1047], 0.4, 'triangle')
        self.sounds['die'] = self.make_nes_sound([400, 300, 200, 100, 50], 0.4, 'pulse')
        self.sounds['menu_move'] = self.make_nes_sound([1200], 0.03, 'pulse')
        self.sounds['menu_select'] = self.make_nes_sound([800, 1000], 0.08, 'pulse')

    def make_nes_sound(self, freqs, duration, wave_type='pulse'):
        sample_rate = 44100
        total_samples = int(sample_rate * duration)
        samples_per_freq = total_samples // len(freqs)
        buf = []
        
        for freq_idx, freq in enumerate(freqs):
            for i in range(samples_per_freq):
                t = i / sample_rate
                val = 0
                phase = (i * freq / sample_rate) * 2 * math.pi
                
                if wave_type == 'pulse':  # 25% duty cycle like NES
                    val = 1.0 if (phase % (2*math.pi)) < (math.pi * 0.5) else -1.0
                elif wave_type == 'triangle':
                    val = 2.0 * abs(2.0 * (phase/(2*math.pi) - math.floor(phase/(2*math.pi) + 0.5))) - 1.0
                elif wave_type == 'noise':
                    val = random.uniform(-1, 1)
                
                # Decay envelope
                progress = (freq_idx * samples_per_freq + i) / total_samples
                envelope = 1.0 - progress
                
                scaled = int(val * envelope * 12000)
                buf.append(scaled)
                buf.append(scaled)
        
        sound_bytes = struct.pack('h' * len(buf), *buf)
        return pygame.mixer.Sound(sound_bytes)

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()


class PixelRenderer:
    """NES-style pixel art renderer"""
    def __init__(self):
        self.internal_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        self.sprites = {}
        self.generate_sprites()

    def generate_sprites(self):
        # Player sprite (16x16 Mario-like worker)
        self.sprites['player_r'] = self.create_player_sprite(False)
        self.sprites['player_l'] = self.create_player_sprite(True)
        self.sprites['player_hammer_r'] = self.create_player_hammer_sprite(False)
        self.sprites['player_hammer_l'] = self.create_player_hammer_sprite(True)
        self.sprites['player_climb'] = self.create_player_climb_sprite()
        
        # Enemy sprite (16x16 Gotchawrench-style)
        self.sprites['enemy_r'] = self.create_enemy_sprite(False)
        self.sprites['enemy_l'] = self.create_enemy_sprite(True)
        
        # Tiles
        self.sprites['floor'] = self.create_floor_tile()
        self.sprites['wall'] = self.create_wall_tile()
        self.sprites['ladder'] = self.create_ladder_tile()

    def create_player_sprite(self, flip):
        """16x16 worker sprite - red overalls, hard hat"""
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        # Pixel data for worker (0=transparent, 1=skin, 2=red, 3=dark_red, 4=yellow, 5=brown)
        data = [
            "0000044440000000",
            "0000444444000000",
            "0001111110000000",
            "0011111111000000",
            "0011011011000000",
            "0011111111000000",
            "0001111110000000",
            "0000222222220000",
            "0022222222222000",
            "0022212212220000",
            "0000222222000000",
            "0000222222000000",
            "0000222222000000",
            "0000333333000000",
            "0005550055500000",
            "0055500005550000",
        ]
        colors = {
            '0': None,
            '1': NES_PALETTE['skin'],
            '2': NES_PALETTE['red'],
            '3': NES_PALETTE['dark_red'],
            '4': NES_PALETTE['yellow'],
            '5': NES_PALETTE['brown'],
        }
        for y, row in enumerate(data):
            for x, c in enumerate(row):
                if colors[c]:
                    surf.set_at((x, y), colors[c])
        if flip:
            surf = pygame.transform.flip(surf, True, False)
        return surf

    def create_player_hammer_sprite(self, flip):
        """Player swinging hammer"""
        surf = pygame.Surface((24, 16), pygame.SRCALPHA)
        # Base player
        base = self.create_player_sprite(False)
        surf.blit(base, (0, 0))
        # Hammer
        hammer_color = NES_PALETTE['gray']
        handle_color = NES_PALETTE['brown']
        if not flip:
            pygame.draw.rect(surf, handle_color, (16, 6, 6, 2))
            pygame.draw.rect(surf, hammer_color, (20, 4, 4, 6))
        else:
            surf = pygame.Surface((24, 16), pygame.SRCALPHA)
            base = pygame.transform.flip(self.create_player_sprite(False), True, False)
            surf.blit(base, (8, 0))
            pygame.draw.rect(surf, handle_color, (2, 6, 6, 2))
            pygame.draw.rect(surf, hammer_color, (0, 4, 4, 6))
        return surf

    def create_player_climb_sprite(self):
        """Player on ladder"""
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        data = [
            "0000044440000000",
            "0000444444000000",
            "0001111110000000",
            "0011111111000000",
            "0011011011000000",
            "0011111111000000",
            "0001111110000000",
            "0222222222220000",
            "0022222222220000",
            "0002222222200000",
            "0000222222000000",
            "0000222222000000",
            "0000222222000000",
            "0000333333000000",
            "0000550550000000",
            "0000550550000000",
        ]
        colors = {
            '0': None, '1': NES_PALETTE['skin'], '2': NES_PALETTE['red'],
            '3': NES_PALETTE['dark_red'], '4': NES_PALETTE['yellow'], '5': NES_PALETTE['brown'],
        }
        for y, row in enumerate(data):
            for x, c in enumerate(row):
                if colors[c]:
                    surf.set_at((x, y), colors[c])
        return surf

    def create_enemy_sprite(self, flip):
        """16x16 wrench enemy - purple/pink menace"""
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        data = [
            "0000066660000000",
            "0006666666600000",
            "0066666666660000",
            "0066077077660000",
            "0066777777660000",
            "0066677776660000",
            "0006666666600000",
            "0000666666000000",
            "0006666666600000",
            "0066666666660000",
            "0066666666660000",
            "0006666666600000",
            "0000666666000000",
            "0000066660000000",
            "0000660066000000",
            "0006600006600000",
        ]
        colors = {
            '0': None,
            '6': NES_PALETTE['purple'],
            '7': NES_PALETTE['white'],
        }
        for y, row in enumerate(data):
            for x, c in enumerate(row):
                if colors[c]:
                    surf.set_at((x, y), colors[c])
        if flip:
            surf = pygame.transform.flip(surf, True, False)
        return surf

    def create_floor_tile(self):
        """16x16 brick floor - indestructible"""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(NES_PALETTE['dark_red'])
        # Brick pattern
        pygame.draw.line(surf, NES_PALETTE['brown'], (0, 4), (16, 4), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (0, 8), (16, 8), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (0, 12), (16, 12), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (8, 0), (8, 4), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (4, 4), (4, 8), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (12, 4), (12, 8), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (8, 8), (8, 12), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (4, 12), (4, 16), 1)
        pygame.draw.line(surf, NES_PALETTE['brown'], (12, 12), (12, 16), 1)
        return surf

    def create_wall_tile(self):
        """16x16 destructible wall - gray blocks"""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(NES_PALETTE['gray'])
        pygame.draw.rect(surf, NES_PALETTE['white'], (1, 1, 14, 14), 1)
        pygame.draw.rect(surf, NES_PALETTE['dark_gray'], (2, 2, 12, 12), 1)
        pygame.draw.line(surf, NES_PALETTE['dark_gray'], (0, 8), (16, 8), 1)
        pygame.draw.line(surf, NES_PALETTE['dark_gray'], (8, 0), (8, 16), 1)
        return surf

    def create_ladder_tile(self):
        """16x16 ladder"""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Vertical rails
        pygame.draw.rect(surf, NES_PALETTE['yellow'], (3, 0, 2, 16))
        pygame.draw.rect(surf, NES_PALETTE['yellow'], (11, 0, 2, 16))
        # Rungs
        for y in [2, 6, 10, 14]:
            pygame.draw.rect(surf, NES_PALETTE['orange'], (3, y, 10, 2))
        return surf

    def draw_text(self, text, x, y, color=NES_PALETTE['white']):
        """Draw text using 8x8 bitmap font"""
        for i, char in enumerate(text.upper()):
            if char in FONT_DATA:
                self.draw_char(char, x + i * 8, y, color)

    def draw_char(self, char, x, y, color):
        """Draw single 8x8 character"""
        if char not in FONT_DATA:
            return
        data = FONT_DATA[char]
        for row_idx, row_byte in enumerate(data):
            for col in range(8):
                if row_byte & (0x80 >> col):
                    px = x + col
                    py = y + row_idx
                    if 0 <= px < INTERNAL_WIDTH and 0 <= py < INTERNAL_HEIGHT:
                        self.internal_surface.set_at((px, py), color)

    def scale_to_screen(self, screen, scanlines=True):
        """Scale internal buffer to screen with optional scanlines"""
        scaled = pygame.transform.scale(self.internal_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled, (0, 0))
        
        if scanlines:
            for y in range(0, SCREEN_HEIGHT, 4):
                pygame.draw.line(screen, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AC'S WRECKING CREW")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.sound = SoundEngine()
        self.renderer = PixelRenderer()
        
        self.state = STATE_MENU
        self.menu_options = ["START", "HELP", "CREDITS", "ABOUT"]
        self.selected_option = 0
        self.frame_count = 0
        
        self.player = None
        self.tiles = []
        self.walls = []
        self.ladders = []
        self.floors = []
        self.enemies = []
        self.score = 0
        self.phase = 1

    def reset_game(self):
        self.tiles = []
        self.walls = []
        self.ladders = []
        self.floors = []
        
        for r, row in enumerate(LEVEL_LAYOUT):
            row_tiles = []
            for c, tile_type in enumerate(row):
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                tile = {'type': tile_type, 'rect': rect, 'active': True}
                
                if tile_type == TYPE_FLOOR:
                    self.floors.append(rect)
                elif tile_type == TYPE_WALL:
                    self.walls.append(tile)
                elif tile_type == TYPE_LADDER:
                    self.ladders.append(rect)
                
                row_tiles.append(tile)
            self.tiles.append(row_tiles)

        self.player = Player(32, 200)
        self.enemies = [
            Enemy(120, 48, 0.5),
            Enemy(180, 112, -0.5),
        ]
        self.score = 0

    def get_tile_at(self, x, y):
        c = int(x // TILE_SIZE)
        r = int(y // TILE_SIZE)
        if 0 <= r < len(self.tiles) and 0 <= c < len(self.tiles[0]):
            return self.tiles[r][c]
        return None

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.sound.toggle()
                
                if self.state == STATE_MENU:
                    self.handle_menu_input(event)
                elif self.state in [STATE_HELP, STATE_CREDITS, STATE_ABOUT]:
                    if event.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_z]:
                        self.sound.play('menu_select')
                        self.state = STATE_MENU
                elif self.state in [STATE_GAMEOVER, STATE_WIN]:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = STATE_PLAY
                        self.sound.play('menu_select')
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU
                        self.sound.play('menu_select')
                elif self.state == STATE_PLAY:
                    if event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU
                        self.sound.play('menu_select')
                    if event.key in [pygame.K_SPACE, pygame.K_z, pygame.K_x]:
                        if not self.player.is_hammering:
                            self.player.hammer(self)

        if self.state == STATE_PLAY:
            self.handle_play_input(keys)

    def handle_menu_input(self, event):
        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            self.sound.play('menu_move')
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            self.sound.play('menu_move')
        elif event.key in [pygame.K_RETURN, pygame.K_z]:
            self.sound.play('menu_select')
            choice = self.menu_options[self.selected_option]
            if choice == "START":
                self.reset_game()
                self.state = STATE_PLAY
            elif choice == "HELP":
                self.state = STATE_HELP
            elif choice == "CREDITS":
                self.state = STATE_CREDITS
            elif choice == "ABOUT":
                self.state = STATE_ABOUT

    def handle_play_input(self, keys):
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT]: dx = -1
        elif keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        elif keys[pygame.K_DOWN]: dy = 1
        
        self.player.move(dx, dy, self.floors, self.ladders)

    def update(self):
        self.frame_count += 1
        
        if self.state == STATE_PLAY:
            self.player.update()
            
            for enemy in self.enemies:
                enemy.update(self.floors, self.ladders)
                if enemy.rect.colliderect(self.player.rect):
                    self.sound.play('die')
                    self.state = STATE_GAMEOVER
            
            active_walls = sum(1 for w in self.walls if w['active'])
            if active_walls == 0:
                self.sound.play('win')
                self.state = STATE_WIN

    def draw(self):
        r = self.renderer
        r.internal_surface.fill(NES_PALETTE['black'])
        
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAY:
            self.draw_game()
            self.draw_hud()
        elif self.state == STATE_GAMEOVER:
            self.draw_game()
            r.draw_text("GAME OVER", 88, 100, NES_PALETTE['red'])
            r.draw_text("PRESS R TO RETRY", 64, 120, NES_PALETTE['white'])
            r.draw_text("ESC FOR MENU", 80, 136, NES_PALETTE['gray'])
        elif self.state == STATE_WIN:
            self.draw_game()
            r.draw_text("PHASE CLEAR!", 80, 100, NES_PALETTE['lime'])
            r.draw_text("SCORE: " + str(self.score), 88, 120, NES_PALETTE['yellow'])
            r.draw_text("PRESS R", 104, 144, NES_PALETTE['white'])
        elif self.state == STATE_HELP:
            self.draw_info_screen("HOW TO PLAY", [
                "ARROWS: MOVE",
                "UP/DOWN: CLIMB",
                "Z OR SPACE: HAMMER",
                "M: SOUND ON/OFF",
                "ESC: BACK",
                "",
                "DESTROY ALL WALLS!",
                "AVOID ENEMIES!",
            ])
        elif self.state == STATE_CREDITS:
            self.draw_info_screen("CREDITS", [
                "ORIGINAL GAME:",
                "NINTENDO 1985",
                "",
                "THIS VERSION:",
                "TEAM FLAMES",
                "",
                "ENGINE: PYGAME",
            ])
        elif self.state == STATE_ABOUT:
            self.draw_info_screen("ABOUT", [
                "AC'S WRECKING CREW",
                "FAMICOM TRIBUTE",
                "",
                "AUTHENTIC NES",
                "256X240 RENDER",
                "2A03 STYLE SOUND",
            ])
        
        r.scale_to_screen(self.screen, scanlines=True)
        pygame.display.flip()

    def draw_menu(self):
        r = self.renderer
        
        # Title with flicker effect
        title_color = NES_PALETTE['red'] if (self.frame_count // 30) % 2 == 0 else NES_PALETTE['orange']
        r.draw_text("AC'S", 112, 32, NES_PALETTE['cyan'])
        r.draw_text("WRECKING CREW", 64, 48, title_color)
        
        # Menu options
        for i, option in enumerate(self.menu_options):
            color = NES_PALETTE['white'] if i == self.selected_option else NES_PALETTE['gray']
            y = 100 + i * 20
            
            if i == self.selected_option:
                # Blinking cursor
                if (self.frame_count // 15) % 2 == 0:
                    r.draw_text(">", 80, y, NES_PALETTE['yellow'])
            
            r.draw_text(option, 96, y, color)
        
        # Footer
        r.draw_text("2025 TEAM FLAMES", 72, 210, NES_PALETTE['dark_gray'])
        r.draw_text("PRESS START", 88, 224, NES_PALETTE['cyan'] if (self.frame_count // 20) % 2 == 0 else NES_PALETTE['blue'])

    def draw_game(self):
        r = self.renderer
        
        # Draw tiles
        for row in self.tiles:
            for tile in row:
                if not tile['active']:
                    continue
                
                x, y = tile['rect'].x, tile['rect'].y
                
                if tile['type'] == TYPE_FLOOR:
                    r.internal_surface.blit(r.sprites['floor'], (x, y))
                elif tile['type'] == TYPE_WALL:
                    r.internal_surface.blit(r.sprites['wall'], (x, y))
                elif tile['type'] == TYPE_LADDER:
                    r.internal_surface.blit(r.sprites['ladder'], (x, y))
        
        # Draw enemies
        for enemy in self.enemies:
            sprite_key = 'enemy_r' if enemy.speed > 0 else 'enemy_l'
            r.internal_surface.blit(r.sprites[sprite_key], (int(enemy.rect.x), int(enemy.rect.y)))
        
        # Draw player
        px, py = int(self.player.rect.x), int(self.player.rect.y)
        if self.player.on_ladder:
            r.internal_surface.blit(r.sprites['player_climb'], (px, py))
        elif self.player.is_hammering:
            sprite = r.sprites['player_hammer_r'] if self.player.facing_right else r.sprites['player_hammer_l']
            offset = 0 if self.player.facing_right else -8
            r.internal_surface.blit(sprite, (px + offset, py))
        else:
            sprite = r.sprites['player_r'] if self.player.facing_right else r.sprites['player_l']
            r.internal_surface.blit(sprite, (px, py))

    def draw_hud(self):
        r = self.renderer
        # Score
        r.draw_text("SCORE", 8, 2, NES_PALETTE['white'])
        r.draw_text(str(self.score).zfill(6), 56, 2, NES_PALETTE['yellow'])
        # Phase
        r.draw_text("PHASE", 168, 2, NES_PALETTE['white'])
        r.draw_text(str(self.phase).zfill(2), 216, 2, NES_PALETTE['cyan'])
        # Walls remaining
        active_walls = sum(1 for w in self.walls if w['active'])
        r.draw_text("WALLS:" + str(active_walls), 8, 230, NES_PALETTE['gray'])

    def draw_info_screen(self, title, lines):
        r = self.renderer
        r.draw_text(title, (INTERNAL_WIDTH - len(title) * 8) // 2, 24, NES_PALETTE['yellow'])
        
        y = 64
        for line in lines:
            x = (INTERNAL_WIDTH - len(line) * 8) // 2
            r.draw_text(line, x, y, NES_PALETTE['white'])
            y += 16
        
        r.draw_text("PRESS Z OR ESC", 72, 216, NES_PALETTE['cyan'])

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_input()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 14, 16)
        self.speed = 1.5
        self.climb_speed = 1.0
        self.vel_y = 0
        self.gravity = 0.15
        self.on_ground = False
        self.on_ladder = False
        self.facing_right = True
        self.is_hammering = False
        self.hammer_timer = 0
        self.hammer_duration = 15

    def move(self, dx, dy, floors, ladders):
        cx, cy = self.rect.centerx, self.rect.centery
        
        self.on_ladder = any(l.collidepoint(cx, cy) for l in ladders)
        
        if not self.is_hammering:
            if dx != 0:
                self.rect.x += dx * self.speed
                self.facing_right = dx > 0
            
            if self.on_ladder:
                self.vel_y = 0
                self.rect.y += dy * self.climb_speed
            else:
                self.vel_y += self.gravity
                self.rect.y += self.vel_y
        
        self.on_ground = False
        for floor in floors:
            if self.rect.colliderect(floor):
                if self.vel_y > 0 and self.rect.bottom <= floor.bottom + 4:
                    self.rect.bottom = floor.top
                    self.vel_y = 0
                    self.on_ground = True
        
        self.rect.clamp_ip(pygame.Rect(0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT))

    def hammer(self, game):
        self.is_hammering = True
        self.hammer_timer = self.hammer_duration
        game.sound.play('hammer')
        
        check_x = self.rect.centerx + (TILE_SIZE if self.facing_right else -TILE_SIZE)
        check_y = self.rect.centery
        
        target = game.get_tile_at(check_x, check_y)
        
        if target and target['type'] == TYPE_WALL and target['active']:
            target['active'] = False
            game.score += 100
            game.sound.play('hit')

    def update(self):
        if self.is_hammering:
            self.hammer_timer -= 1
            if self.hammer_timer <= 0:
                self.is_hammering = False


class Enemy:
    def __init__(self, x, y, speed):
        self.rect = pygame.Rect(x, y, 14, 16)
        self.speed = speed
        self.vel_y = 0
        self.gravity = 0.15

    def update(self, floors, ladders):
        self.rect.x += self.speed
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        
        for floor in floors:
            if self.rect.colliderect(floor):
                if self.vel_y > 0 and self.rect.bottom <= floor.bottom + 4:
                    self.rect.bottom = floor.top
                    self.vel_y = 0
        
        if self.rect.left < 0 or self.rect.right > INTERNAL_WIDTH:
            self.speed *= -1
            self.rect.clamp_ip(pygame.Rect(0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT))


if __name__ == "__main__":
    game = Game()
    game.run()
