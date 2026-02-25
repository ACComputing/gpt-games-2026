import pygame
import sys
import random
import math
import array

# ─── CONFIG ─────────────────────────────────────────────
TITLE = "ULTRA!BREAKOUT by A.C (60 FPS Edition)"
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400          # 600x400 — 3:2
FPS = 60
BASE_BALL_SPEED = 5.0
PADDLE_SPEED = 8
BRICK_ROWS, BRICK_COLS = 6, 10
BRICK_WIDTH = SCREEN_WIDTH // BRICK_COLS         # = 60
BRICK_HEIGHT = 30

# Colors
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
RED     = (220, 50, 50)
ORANGE  = (255, 140, 0)
YELLOW  = (220, 220, 50)
GREEN   = (50, 220, 50)
CYAN    = (50, 220, 220)
BLUE    = (50, 50, 220)
MAGENTA = (220, 50, 220)

# Atari-style row colors (Top to bottom)
ROW_COLORS = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE]

# ─── INITIALIZE PYGAME ─────────────────────────────────
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
font_tiny   = pygame.font.SysFont("Courier", 12, bold=True)   # HUD / sub-labels
font_small  = pygame.font.SysFont("Courier", 14, bold=True)   # Instructions
font_medium = pygame.font.SysFont("Courier", 20, bold=True)   # Win / Game-over sub
font_big    = pygame.font.SysFont("Courier", 22, bold=True)   # Title + big headers

# ─── DYNAMIC SOUND SYSTEM ──────────────────────────────
def generate_sound(frequency, duration, wave_type='square'):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    amplitude = 12000

    for i in range(n_samples):
        t = float(i) / sample_rate
        if wave_type == 'descend':
            current_freq = frequency - (frequency * 0.7 * (i / n_samples))
            val = amplitude if math.sin(2 * math.pi * current_freq * t) > 0 else -amplitude
        elif wave_type == 'square':
            val = amplitude if math.sin(2 * math.pi * frequency * t) > 0 else -amplitude
        elif wave_type == 'noise':
            val = random.randint(-amplitude, amplitude)
        else:
            val = int(amplitude * math.sin(2 * math.pi * frequency * t))

        envelope = 1.0 - (i / n_samples)
        buf.append(int(val * envelope))

    return pygame.mixer.Sound(buffer=buf)

sounds = {
    "hit":       generate_sound(440,  0.08, 'square'),
    "brick":     generate_sound(880,  0.08, 'square'),
    "powerup":   generate_sound(1200, 0.10, 'square'),
    "lose_life": generate_sound(150,  0.40, 'descend'),
    "game_over": generate_sound(100,  1.50, 'descend'),
}

# ─── CLASSES ───────────────────────────────────────────
class Paddle:
    def __init__(self):
        self.width, self.height = 80, 20
        self.rect = pygame.Rect(
            (SCREEN_WIDTH // 2 - self.width // 2, SCREEN_HEIGHT - 40),
            (self.width, self.height)
        )

    def move_with_mouse(self, mouse_x):
        self.rect.centerx = mouse_x
        self.rect.left  = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)


class Ball:
    def __init__(self):
        self.radius = 6
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2 + 50
        self.rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )
        self.current_speed = BASE_BALL_SPEED
        self.hit_count = 0
        self.hit_orange = False
        self.hit_red    = False

        angle = math.radians(random.uniform(45, 135))
        self.vel = [self.current_speed * math.cos(angle),
                    self.current_speed * math.sin(angle)]

    def update_velocity_magnitude(self):
        angle = math.atan2(self.vel[1], self.vel[0])
        self.vel[0] = self.current_speed * math.cos(angle)
        self.vel[1] = self.current_speed * math.sin(angle)

    def update(self, paddle, bricks):
        self.x += self.vel[0]
        self.y += self.vel[1]
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        hit_bricks = []

        if self.rect.left <= 0:
            self.rect.left = 0
            self.vel[0] *= -1
            sounds["hit"].play()
        elif self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.vel[0] *= -1
            sounds["hit"].play()

        if self.rect.top <= 0:
            self.rect.top = 0
            self.vel[1] *= -1
            sounds["hit"].play()

        if self.rect.bottom >= SCREEN_HEIGHT:
            return False, hit_bricks

        if self.rect.colliderect(paddle.rect) and self.vel[1] > 0:
            offset = (self.rect.centerx - paddle.rect.centerx) / (paddle.rect.width / 2)
            offset = max(-0.85, min(0.85, offset))
            bounce_angle = math.pi / 2 - (offset * math.pi / 3)
            self.vel[0] = self.current_speed * math.cos(bounce_angle)
            self.vel[1] = -abs(self.current_speed * math.sin(bounce_angle))
            sounds["hit"].play()

        for brick_data in bricks[:]:
            rect, color, row_idx = brick_data
            if self.rect.colliderect(rect):
                dx = self.rect.centerx - rect.centerx
                dy = self.rect.centery - rect.centery
                if abs(dx) > abs(dy):
                    self.vel[0] *= -1
                else:
                    self.vel[1] *= -1

                bricks.remove(brick_data)
                sounds["brick"].play()

                self.hit_count += 1
                speed_increased = False
                if self.hit_count in (4, 12):
                    self.current_speed += 1.0
                    speed_increased = True

                if row_idx == 1 and not self.hit_orange:
                    self.current_speed += 1.5
                    self.hit_orange = True
                    speed_increased = True
                elif row_idx == 0 and not self.hit_red:
                    self.current_speed += 2.0
                    self.hit_red = True
                    speed_increased = True

                if speed_increased:
                    self.update_velocity_magnitude()

                hit_bricks.append(brick_data)
                break

        return True, hit_bricks

    def draw(self):
        pygame.draw.circle(screen, WHITE, self.rect.center, self.radius)


class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-3, 3)
        self.life  = random.randint(15, 30)
        self.size  = random.randint(2, 4)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.life -= 1

    def draw(self):
        if self.life > 0:
            pygame.draw.rect(screen, self.color,
                             (int(self.x), int(self.y), self.size, self.size))


class PowerUp:
    def __init__(self, x, y):
        self.rect  = pygame.Rect(x, y, 20, 10)
        self.type  = random.choice(['E', 'M'])
        self.color = CYAN if self.type == 'E' else MAGENTA
        self.vel_y = 3

    def update(self):
        self.rect.y += self.vel_y

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        surf = font_tiny.render(self.type, True, BLACK)
        screen.blit(surf, surf.get_rect(center=self.rect.center))


def create_bricks():
    bricks = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            rect  = pygame.Rect(col * BRICK_WIDTH, row * BRICK_HEIGHT + 50,
                                BRICK_WIDTH - 2, BRICK_HEIGHT - 2)
            color = ROW_COLORS[row]
            bricks.append((rect, color, row))
    return bricks


# ─── UI HELPERS ────────────────────────────────────────
def draw_text_center(text, font, color, y):
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))

def draw_text_center_x(text, font, color, x, y):
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(x, y)))


# ─── MENUS ─────────────────────────────────────────────
def main_menu():
    pygame.mouse.set_visible(True)
    while True:
        screen.fill(BLACK)

        # Title — two lines so it fits 600 px
        draw_text_center("ULTRA!BREAKOUT", font_big, WHITE, 80)
        draw_text_center("by A.C  (60 FPS Edition)", font_tiny, WHITE, 106)

        draw_text_center("1.  Play Game",  font_small, WHITE, 190)
        draw_text_center("2.  How to Play", font_small, WHITE, 214)
        draw_text_center("ESC  Quit",      font_tiny,  WHITE, 270)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_loop()
                elif event.key == pygame.K_2:
                    how_to_play()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
        clock.tick(FPS)


def how_to_play():
    while True:
        screen.fill(BLACK)
        draw_text_center("HOW TO PLAY", font_big, WHITE, 40)

        lines = [
            "Mouse: Move Paddle   |   ESC: Quit to Menu",
            "",
            "Bounce the ball to break all bricks!",
            "Higher bricks award more points.",
            "",
            "SPEED INCREASES:",
            "4 hits, 12 hits, hitting Orange, hitting Red!",
            "",
            "POWER-UPS (15% drop chance):",
            "[E] Cyan    = Expands paddle",
            "[M] Magenta = Extra ball!",
        ]
        y = 75
        for line in lines:
            draw_text_center(line, font_small, WHITE, y)
            y += 20

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return
        clock.tick(FPS)


# ─── MAIN GAME LOOP ────────────────────────────────────
def game_loop():
    paddle   = Paddle()
    balls    = [Ball()]
    bricks   = create_bricks()
    particles = []
    powerups  = []

    score   = 0
    lives   = 3
    running = True

    pygame.mouse.set_visible(False)

    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            pygame.mouse.set_visible(True)
            return

        mouse_x, _ = pygame.mouse.get_pos()
        paddle.move_with_mouse(mouse_x)

        # Update balls
        for ball in balls[:]:
            alive, hit_bricks = ball.update(paddle, bricks)
            for brick in hit_bricks:
                rect, color, row_idx = brick
                score += (BRICK_ROWS - row_idx) * 10
                for _ in range(8):
                    particles.append(Particle(rect.centerx, rect.centery, color))
                if random.random() < 0.15:
                    powerups.append(PowerUp(rect.centerx, rect.centery))
            if not alive:
                balls.remove(ball)

        # Life / game-over logic
        if len(balls) == 0:
            lives -= 1
            if lives > 0:
                sounds["lose_life"].play()
                paddle = Paddle()
                balls  = [Ball()]
                pygame.time.wait(1000)
            else:
                sounds["game_over"].play()
                draw_text_center("GAME OVER",          font_big,    RED,   SCREEN_HEIGHT // 2 - 16)
                draw_text_center(f"SCORE: {score}",    font_medium, WHITE, SCREEN_HEIGHT // 2 + 14)
                pygame.display.flip()
                pygame.time.wait(4000)
                running = False

        # Update power-ups
        for pu in powerups[:]:
            pu.update()
            if pu.rect.colliderect(paddle.rect):
                sounds["powerup"].play()
                if pu.type == 'E':
                    paddle.width      = min(200, paddle.rect.width + 40)
                    paddle.rect.width = paddle.width
                elif pu.type == 'M':
                    nb = Ball()
                    nb.x, nb.y = paddle.rect.centerx, paddle.rect.top - 20
                    nb.vel[1]  = -abs(nb.current_speed)
                    balls.append(nb)
                powerups.remove(pu)
            elif pu.rect.top > SCREEN_HEIGHT:
                powerups.remove(pu)

        # Update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # Draw everything
        paddle.draw()
        for ball in balls:
            ball.draw()
        for brick_data in bricks:
            pygame.draw.rect(screen, brick_data[1], brick_data[0])
        for pu in powerups:
            pu.draw()
        for p in particles:
            p.draw()

        # ── HUD — centred horizontally ──────────────────
        cx = SCREEN_WIDTH // 2
        draw_text_center_x(f"SCORE  {score}",  font_tiny, WHITE, cx - 80, 10)
        draw_text_center_x(f"LIVES  {lives}",  font_tiny, WHITE, cx + 80, 10)

        # Win condition
        if not bricks:
            draw_text_center("YOU WIN!",           font_big,    GREEN, SCREEN_HEIGHT // 2 - 16)
            draw_text_center(f"SCORE: {score}",    font_medium, WHITE, SCREEN_HEIGHT // 2 + 14)
            pygame.display.flip()
            pygame.time.wait(4000)
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mouse.set_visible(True)


# ─── START ─────────────────────────────────────────────
if __name__ == "__main__":
    main_menu()
