import pygame
import random
import math
import sys
import array
import struct

# Initialize Pygame with specific audio settings for low latency
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.font.init()

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- Colors (Neon Palette) ---
BLACK = (10, 10, 15)
WHITE = (255, 255, 255)
NEON_BLUE = (0, 240, 255)
NEON_PINK = (255, 0, 150)
NEON_GREEN = (0, 255, 100)
NEON_YELLOW = (255, 220, 0)
NEON_RED = (255, 50, 50)
DARK_PURPLE = (20, 0, 30)
GRAY = (100, 100, 100)

# --- Setup Display ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("AC'S SPACE INVADERS // FAMICOM AI EDITION")
clock = pygame.time.Clock()

# --- Helper Functions for Visuals ---

def draw_bloom_circle(surface, color, center, radius, glow_radius):
    pygame.draw.circle(surface, color, center, radius)
    glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
    r, g, b = color
    pygame.draw.circle(glow_surf, (r, g, b, 50), (glow_radius, glow_radius), glow_radius)
    pygame.draw.circle(glow_surf, (r, g, b, 100), (glow_radius, glow_radius), glow_radius * 0.7)
    surface.blit(glow_surf, (center[0] - glow_radius, center[1] - glow_radius), special_flags=pygame.BLEND_ADD)

def draw_pixel_alien(surface, x, y, color, type_idx, animation_state):
    size = 4
    shapes = [
        [
            "  1     1  ", "   1   1   ", "  1111111  ", " 11 111 11 ",
            "11111111111", "1 1111111 1", "1 1     1 1",
            "   11 11   " if animation_state else "  11   11  "
        ],
        [
            "   11111   ", "  1111111  ", " 111111111 ", " 11 111 11 ",
            " 111111111 ", "   1 1 1   ", "  1 1 1 1  ",
            " 1 1   1 1 " if animation_state else "  11   11  "
        ],
        [
            "    111    ", " 111111111 ", "11111111111", "1 1111111 1",
            "11111111111", "   11 11   ", "  11   11  ",
            " 11     11 " if animation_state else "  11   11  "
        ]
    ]
    shape = shapes[type_idx % len(shapes)]
    for row_idx, row in enumerate(shape):
        for col_idx, char in enumerate(row):
            if char == '1':
                px = x + col_idx * size
                py = y + row_idx * size
                pygame.draw.rect(surface, color, (px, py, size, size))
                if random.random() < 0.05:
                    pygame.draw.rect(surface, (255, 255, 255), (px, py, size, size))

# --- FAMICOM AUDIO ENGINE AI ---

class FamicomAudioAI:
    """
    Procedural Audio Generator imitating the NES/Famicom 2A03 Chip.
    Generates Pulse Waves (Square) and Noise entirely via code.
    No external assets required.
    """
    def __init__(self):
        self.volume = 0.5
        self.sample_rate = 44100
        self.enabled = True
        
        # Audio Buffers (Cache)
        self.sounds = {
            'shoot': self._generate_pulse_sweep(800, 300, 0.15, 0.5),
            'explosion': self._generate_noise_decay(0.3),
            'ufo_high': self._generate_pulse_sweep(1000, 1500, 0.5, 0.3),
            'beat1': self._generate_square_tone(180, 0.05),
            'beat2': self._generate_square_tone(170, 0.05),
            'beat3': self._generate_square_tone(160, 0.05),
            'beat4': self._generate_square_tone(150, 0.05),
            'ui_move': self._generate_square_tone(440, 0.05),
            'ui_select': self._generate_pulse_sweep(440, 880, 0.1, 0.5)
        }
        
        # Dynamic Soundtrack State
        self.beat_sounds = ['beat1', 'beat2', 'beat3', 'beat4']
        self.beat_index = 0
        self.beat_timer = 0
        self.beat_delay = 60 # Start slow (frames)

    def _generate_square_tone(self, freq, duration):
        """Generates a static square wave (Pulse Channel)."""
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h')
        period = self.sample_rate / freq
        
        for i in range(n_samples):
            # Square wave logic: High for half period, Low for half
            val = 32000 if (i % period) < (period / 2) else -32000
            buf.append(int(val * 0.5)) # Master volume scaling
            
        return pygame.mixer.Sound(buffer=buf)

    def _generate_pulse_sweep(self, start_freq, end_freq, duration, volume_scale):
        """Generates a frequency sweep (Zap/Pew effects)."""
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h')
        
        for i in range(n_samples):
            progress = i / n_samples
            current_freq = start_freq + (end_freq - start_freq) * progress
            period = self.sample_rate / current_freq
            
            # 50% Duty Cycle Square Wave
            val = 32000 if (i % period) < (period / 2) else -32000
            
            # Linear Decay Envelope
            envelope = 1.0 - progress
            buf.append(int(val * envelope * volume_scale))
            
        return pygame.mixer.Sound(buffer=buf)

    def _generate_noise_decay(self, duration):
        """Generates 1-bit pseudo-random noise (Explosions)."""
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h')
        
        for i in range(n_samples):
            # White Noise
            val = random.choice([32000, -32000])
            envelope = 1.0 - (i / n_samples) # Linear decay
            buf.append(int(val * envelope * 0.4))
            
        return pygame.mixer.Sound(buffer=buf)

    def play(self, name):
        if self.enabled and name in self.sounds:
            s = self.sounds[name]
            s.set_volume(self.volume)
            s.play()

    def update_dynamic_music(self, enemy_count, max_enemies, game_speed):
        """
        The 'AI' conductor: Increases tempo based on remaining enemies.
        As enemies die, the heartbeat gets faster (Classic Space Invaders behavior).
        """
        if not self.enabled: return
        
        # Calculate urgency (0.0 to 1.0)
        urgency = 1.0 - (enemy_count / max(1, max_enemies))
        
        # Map urgency to delay (Slow: 60 frames -> Fast: 4 frames)
        target_delay = max(5, 60 - (urgency * 55))
        
        self.beat_timer += 1
        if self.beat_timer >= target_delay:
            self.beat_timer = 0
            self.play(self.beat_sounds[self.beat_index])
            self.beat_index = (self.beat_index + 1) % 4

# --- Standard Classes ---

class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=3, glow=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.glow = glow

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size *= 0.95

    def draw(self, surface):
        if self.life > 0:
            if self.glow:
                draw_bloom_circle(surface, self.color, (int(self.x), int(self.y)), int(self.size), int(self.size * 2))
            else:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class Star:
    def __init__(self):
        self.reset()
        self.y = random.randint(0, SCREEN_HEIGHT)

    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = -10
        self.z = random.uniform(0.5, 3.0)
        self.speed = 2 * self.z
        self.color = random.choice([(200, 200, 255), (255, 255, 255), (150, 150, 200)])

    def update(self, speed_mult):
        self.y += self.speed * speed_mult
        if self.y > SCREEN_HEIGHT:
            self.reset()

    def draw(self, surface):
        s = max(1, int(self.z))
        pygame.draw.rect(surface, self.color, (self.x, self.y, s, s))

class Player:
    def __init__(self):
        self.width = 40
        self.height = 40
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - 80
        self.speed = 6
        self.color = NEON_BLUE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.vel_x = 0
        self.hp = 100

    def update(self):
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
        
        self.x += self.vel_x
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface):
        points = [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width // 2, self.y + self.height - 10),
            (self.x + self.width, self.y + self.height)
        ]
        pygame.draw.polygon(surface, self.color, points)
        draw_bloom_circle(surface, NEON_PINK, (int(self.x + self.width//2), int(self.y + self.height)), 5, 15)

class Enemy:
    def __init__(self, x, y, type_idx):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 30
        self.type_idx = type_idx
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.anim_timer = 0
        self.anim_state = False
        
        if type_idx == 0: self.color = NEON_PINK
        elif type_idx == 1: self.color = NEON_GREEN
        else: self.color = NEON_RED

    def update(self, direction, move_down):
        self.x += direction
        if move_down:
            self.y += 20
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        self.anim_timer += 1
        if self.anim_timer > 30:
            self.anim_timer = 0
            self.anim_state = not self.anim_state

    def draw(self, surface):
        draw_pixel_alien(surface, self.x, self.y, self.color, self.type_idx, self.anim_state)

class Bullet:
    def __init__(self, x, y, speed, color):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.rect = pygame.Rect(x, y, 6, 15)

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=3)
        s = pygame.Surface((20, 30), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (10, 15), 10)
        surface.blit(s, (self.x - 7, self.y - 7), special_flags=pygame.BLEND_ADD)

# --- Game State Manager ---

class Game:
    def __init__(self):
        self.state = "MENU"
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.particles = []
        self.stars = [Star() for _ in range(80)]
        self.score = 0
        self.wave = 1
        self.initial_enemy_count = 0
        
        self.screen_shake = 0.0
        self.hit_stop = 0
        
        self.enemy_speed = 1
        self.enemy_dir = 1
        
        # Audio System
        self.audio = FamicomAudioAI()
        
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 50)
        self.font_small = pygame.font.Font(None, 36)
        
        self.menu_options = [
            "PLAY GAME", 
            "SOUND SETTINGS", 
            "HELP", 
            "ABOUT GAME", 
            "CREDITS", 
            "EXIT GAME"
        ]
        self.selected_index = 0
        
        self.settings_options = ["VOLUME", "BACK"]
        self.settings_index = 0

    def setup_level(self):
        self.enemies = []
        self.bullets = []
        self.player.x = SCREEN_WIDTH // 2 - 20
        self.player.y = SCREEN_HEIGHT - 80
        self.player.hp = 100
        rows = 4 + (self.wave // 2)
        cols = 8
        start_x = (SCREEN_WIDTH - (cols * 50)) // 2
        
        for row in range(rows):
            for col in range(cols):
                e_type = row % 3
                x = start_x + col * 50
                y = 50 + row * 40
                self.enemies.append(Enemy(x, y, e_type))
        
        self.initial_enemy_count = len(self.enemies)
        self.enemy_speed = 1.0 + (self.wave * 0.2)
        # Reset Music Tempo
        self.audio.beat_index = 0

    def add_explosion(self, x, y, color, count=10):
        self.audio.play('explosion')
        for _ in range(count):
            vx = random.uniform(-4, 4)
            vy = random.uniform(-4, 4)
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(20, 40), size=random.randint(2, 6), glow=True))

    def handle_menu_input(self, event):
        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.menu_options)
            self.audio.play('ui_move')
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.menu_options)
            self.audio.play('ui_move')
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.audio.play('ui_select')
            option = self.menu_options[self.selected_index]
            if option == "PLAY GAME":
                self.state = "PLAY"
                self.score = 0
                self.wave = 1
                self.setup_level()
            elif option == "SOUND SETTINGS":
                self.state = "SETTINGS"
                self.settings_index = 0
            elif option == "HELP":
                self.state = "HOWTO"
            elif option == "ABOUT GAME":
                self.state = "ABOUT"
            elif option == "CREDITS":
                self.state = "CREDITS"
            elif option == "EXIT GAME":
                pygame.quit()
                sys.exit()

    def handle_settings_input(self, event):
        if event.key == pygame.K_UP:
            self.settings_index = (self.settings_index - 1) % len(self.settings_options)
            self.audio.play('ui_move')
        elif event.key == pygame.K_DOWN:
            self.settings_index = (self.settings_index + 1) % len(self.settings_options)
            self.audio.play('ui_move')
        elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
             if self.settings_options[self.settings_index] == "VOLUME":
                 self.audio.play('ui_move')
                 change = 0.1 if event.key == pygame.K_RIGHT else -0.1
                 self.audio.volume = max(0.0, min(1.0, self.audio.volume + change))
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
            self.audio.play('ui_select')
            self.state = "MENU"

    def update(self):
        for star in self.stars:
            star.update(4 if self.state == "PLAY" else 0.5)

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        if self.state == "PLAY":
            if self.hit_stop > 0:
                self.hit_stop -= 1
                return

            # AI MUSIC UPDATE
            self.audio.update_dynamic_music(len(self.enemies), self.initial_enemy_count, self.enemy_speed)

            self.player.update()
            
            # Enemy Logic
            move_down = False
            hit_edge = False
            for e in self.enemies:
                if e.x <= 10 or e.x >= SCREEN_WIDTH - 50:
                    hit_edge = True
            
            if hit_edge:
                self.enemy_dir *= -1
                move_down = True
            
            for e in self.enemies:
                e.update(self.enemy_speed * self.enemy_dir, move_down)
                # Random shooting
                if random.random() < (0.001 * self.wave):
                    self.bullets.append(Bullet(e.x + 20, e.y + 30, 4, NEON_RED))
                
                # Collision with player
                if e.rect.colliderect(self.player.rect):
                    self.player.hp = 0
                    self.state = "GAMEOVER"
                    self.screen_shake = 30.0
                    self.add_explosion(self.player.x, self.player.y, NEON_BLUE, 50)

            # Bullet Logic
            for b in self.bullets[:]:
                b.update()
                
                # Player shoots Enemy
                if b.speed < 0: 
                    hit = False
                    for e in self.enemies[:]:
                        if b.rect.colliderect(e.rect):
                            self.enemies.remove(e)
                            self.score += 10 * self.wave
                            self.add_explosion(e.x + 20, e.y + 15, e.color, 15)
                            hit = True
                            self.hit_stop = 2
                            self.screen_shake = 5.0
                            break
                    if hit or b.y < 0:
                        self.bullets.remove(b)
                        
                # Enemy shoots Player
                else: 
                    if b.rect.colliderect(self.player.rect):
                        self.player.hp -= 20
                        self.bullets.remove(b)
                        self.screen_shake = 20.0
                        self.hit_stop = 5
                        self.add_explosion(self.player.x + 20, self.player.y + 20, NEON_RED, 20)
                        if self.player.hp <= 0:
                            self.state = "GAMEOVER"
                    elif b.y > SCREEN_HEIGHT:
                        self.bullets.remove(b)

            if len(self.enemies) == 0:
                self.wave += 1
                self.setup_level()
                self.screen_shake = 10.0

        if self.screen_shake > 0:
            self.screen_shake -= 1.0
            if self.screen_shake < 0:
                self.screen_shake = 0

    def draw_text_centered(self, surface, text, font, y, color):
        render = font.render(text, True, color)
        rect = render.get_rect(center=(SCREEN_WIDTH // 2, y))
        surface.blit(render, rect)

    def draw(self):
        display_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        display_surf.fill(BLACK)
        
        for star in self.stars:
            star.draw(display_surf)
        for p in self.particles:
            p.draw(display_surf)

        if self.state == "MENU":
            self.draw_text_centered(display_surf, "AC'S SPACE INVADERS", self.font_large, 80, NEON_BLUE)
            self.draw_text_centered(display_surf, "FAMICOM AI EDITION", self.font_small, 130, NEON_RED)
            
            for i, option in enumerate(self.menu_options):
                color = NEON_YELLOW if i == self.selected_index else WHITE
                if i == self.selected_index:
                    draw_bloom_circle(display_surf, NEON_YELLOW, (SCREEN_WIDTH//2 - 140, 200 + i * 50 + 10), 3, 10)
                self.draw_text_centered(display_surf, option, self.font_medium, 200 + i * 50, color)

        elif self.state == "HOWTO":
            self.draw_text_centered(display_surf, "HOW TO PLAY", self.font_large, 80, NEON_GREEN)
            instructions = [
                "LEFT / RIGHT ARROWS to Move",
                "SPACE to Shoot",
                "Listen to the Music speed up",
                "as you destroy aliens!",
                "",
                "PRESS ESC TO RETURN"
            ]
            for i, line in enumerate(instructions):
                self.draw_text_centered(display_surf, line, self.font_small, 200 + i * 40, WHITE)

        elif self.state == "CREDITS":
            self.draw_text_centered(display_surf, "CREDITS", self.font_large, 80, NEON_PINK)
            lines = [
                "PROGRAMMING & DESIGN",
                "AC's Infinite Arcade",
                "",
                "AUDIO ENGINE",
                "Famicom 2A03 Emulation",
                "",
                "VISUALS",
                "Procedural Neon Core",
                "",
                "PRESS ESC TO RETURN"
            ]
            for i, line in enumerate(lines):
                color = NEON_BLUE if i % 3 == 0 else WHITE
                self.draw_text_centered(display_surf, line, self.font_small, 180 + i * 35, color)

        elif self.state == "ABOUT":
            self.draw_text_centered(display_surf, "ABOUT GAME", self.font_large, 80, NEON_YELLOW)
            lines = [
                "A tribute to the golden age",
                "of console gaming.",
                "",
                "Featuring:",
                "- Procedural Audio Synthesis",
                "- Dynamic Music Tempo AI",
                "- Next-Gen Bloom Visuals",
                "",
                "PRESS ESC TO RETURN"
            ]
            for i, line in enumerate(lines):
                self.draw_text_centered(display_surf, line, self.font_small, 200 + i * 35, WHITE)

        elif self.state == "SETTINGS":
            self.draw_text_centered(display_surf, "SOUND SETTINGS", self.font_large, 80, NEON_RED)
            
            # Volume Control
            vol_color = NEON_YELLOW if self.settings_index == 0 else WHITE
            vol_bars = "|" * int(self.audio.volume * 10)
            vol_str = f"VOLUME: {vol_bars} {int(self.audio.volume * 100)}%"
            self.draw_text_centered(display_surf, vol_str, self.font_medium, 250, vol_color)
            
            # Back Button
            back_color = NEON_YELLOW if self.settings_index == 1 else WHITE
            self.draw_text_centered(display_surf, "BACK TO MENU", self.font_medium, 350, back_color)

            self.draw_text_centered(display_surf, "(Use Arrows to Adjust)", self.font_small, 500, GRAY)

        elif self.state == "PLAY":
            self.player.draw(display_surf)
            for e in self.enemies:
                e.draw(display_surf)
            for b in self.bullets:
                b.draw(display_surf)
            
            score_txt = self.font_small.render(f"SCORE: {self.score}", True, NEON_YELLOW)
            display_surf.blit(score_txt, (20, 20))
            hp_txt = self.font_small.render(f"HP: {self.player.hp}%", True, NEON_RED if self.player.hp < 40 else NEON_GREEN)
            display_surf.blit(hp_txt, (20, 50))

        elif self.state == "GAMEOVER":
            self.draw_text_centered(display_surf, "GAME OVER", self.font_large, 200, NEON_RED)
            self.draw_text_centered(display_surf, f"FINAL SCORE: {self.score}", self.font_small, 300, WHITE)
            self.draw_text_centered(display_surf, "PRESS 'R' TO RETURN TO MENU", self.font_small, 400, NEON_BLUE)

        # Screen Shake
        render_x, render_y = 0, 0
        if self.screen_shake > 0:
            shake_int = int(self.screen_shake)
            if shake_int > 0:
                render_x = random.randint(-shake_int, shake_int)
                render_y = random.randint(-shake_int, shake_int)
        
        screen.blit(display_surf, (render_x, render_y))
        pygame.display.flip()

# --- Main Execution ---

def main():
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game.state == "MENU":
                    game.handle_menu_input(event)
                
                elif game.state == "SETTINGS":
                    game.handle_settings_input(event)

                elif game.state in ["HOWTO", "CREDITS", "ABOUT"]:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        game.audio.play('ui_select')
                        game.state = "MENU"

                elif game.state == "PLAY":
                    if event.key == pygame.K_SPACE:
                        game.bullets.append(Bullet(game.player.x + 20 - 3, game.player.y, -12, NEON_BLUE))
                        game.add_explosion(game.player.x + 20, game.player.y + 40, NEON_BLUE, 2)
                        game.audio.play('shoot')
                    if event.key == pygame.K_ESCAPE:
                        game.audio.play('ui_select')
                        game.state = "MENU"
                
                elif game.state == "GAMEOVER":
                    if event.key == pygame.K_r or event.key == pygame.K_ESCAPE:
                        game.audio.play('ui_select')
                        game.state = "MENU"
        
        game.update()
        game.draw()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
