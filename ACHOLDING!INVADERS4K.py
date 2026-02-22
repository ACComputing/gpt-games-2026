import pygame
import sys
import math
import array

# =============================================================================
# AC'S SPACE INVADERS 0.2 - CatSDK Famicom Edition (NES Speed Update)
# =============================================================================
# /pr files = off (All assets generated in code)
# fps = 60 (Locked)
# speed = famicon (Dynamic speed ramp based on remaining enemies)
# =============================================================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AC Holdings Space Invader 0.1 #")
CLOCK = pygame.time.Clock()
FPS = 60  # Locked to standard NTSC Famicom refresh rate

# Colors (Famicom Palette approximation)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# -----------------------------------------------------------------------------
# SOUND ENGINE (Procedural Beeps n Boops)
# -----------------------------------------------------------------------------
def create_sound(frequency, duration=0.1):
    """Generates a retro 8-bit square wave sound."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    amplitude = 4096
    period = sample_rate / frequency
    for i in range(n_samples):
        # Square wave generation
        buf[i] = amplitude if (i // (period / 2)) % 2 == 0 else -amplitude
    return pygame.mixer.Sound(buffer=buf.tobytes())

# Sound Effects
snd_shoot = create_sound(880, 0.05)
snd_hit = create_sound(220, 0.15)
snd_menu_move = create_sound(440, 0.02)

# -----------------------------------------------------------------------------
# PIXEL ART ASSETS (Famicom Style)
# -----------------------------------------------------------------------------
PATTERN_PLAYER = [
    "00011000",
    "00111100",
    "01111110",
    "11111111",
    "11111111"
]

PATTERN_INVADER_1 = [  # Squid Type
    "01000100",
    "00010100",
    "01111110",
    "10011001",
    "10111101"
]

PATTERN_INVADER_2 = [  # Crab Type
    "00100100",
    "01111110",
    "11111111",
    "11011011",
    "01100110"
]

def draw_pixel_entity(surface, color, rect, pattern):
    """Renders a pixel pattern to the screen."""
    px_w = rect.width / 8
    px_h = rect.height / len(pattern)
    for y, row in enumerate(pattern):
        for x, char in enumerate(row):
            if char == "1":
                pixel_rect = pygame.Rect(
                    rect.x + x * px_w,
                    rect.y + y * px_h,
                    math.ceil(px_w),
                    math.ceil(px_h)
                )
                pygame.draw.rect(surface, color, pixel_rect)

# -----------------------------------------------------------------------------
# GAME CLASSES
# -----------------------------------------------------------------------------
class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT - 60, 50, 40)

    def draw(self, surface):
        draw_pixel_entity(surface, GREEN, self.rect, PATTERN_PLAYER)

    def update(self, mouse_x):
        self.rect.centerx = mouse_x
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH

class Bullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 2, y, 4, 12)
        self.speed = -10  # Fast bullet speed for NES feel
        self.active = True

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.active = False

    def draw(self, surface):
        pygame.draw.rect(surface, YELLOW, self.rect)

class Invader:
    def __init__(self, x, y, type_id):
        self.rect = pygame.Rect(x, y, 40, 35)
        self.type = type_id
        self.active = True
        if self.type == 0:
            self.color = CYAN
            self.pattern = PATTERN_INVADER_1
        else:
            self.color = MAGENTA
            self.pattern = PATTERN_INVADER_2

    def draw(self, surface):
        if self.active:
            draw_pixel_entity(surface, self.color, self.rect, self.pattern)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def draw_text(surface, text, size, color, x, y, center=True):
    font = pygame.font.SysFont("freesansbold.ttf", size)
    label = font.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(label, rect)

def get_nes_speed(invader_count):
    """
    Replicates the original NES/Arcade speed ramp.
    More enemies = slower. Fewer enemies = faster.
    """
    # Base speed starts very slow
    if invader_count > 25: return 1.0
    if invader_count > 20: return 1.5
    if invader_count > 15: return 2.0
    if invader_count > 10: return 2.5
    if invader_count > 5:  return 3.5
    if invader_count > 1:  return 4.5
    return 6.0  # Last alien zooms

# -----------------------------------------------------------------------------
# GAME LOOP
# -----------------------------------------------------------------------------
def game_loop():
    player = Player()
    bullets = []
    invaders = []
    
    # Create Formation
    for row in range(4):
        for col in range(8):
            type_id = row % 2
            invaders.append(Invader(100 + col * 80, 80 + row * 60, type_id))

    invader_dir = 1
    running = True
    
    while running:
        SCREEN.fill(BLACK)
        
        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                bullets.append(Bullet(player.rect.centerx, player.rect.top))
                snd_shoot.play()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- Player Logic ---
        player.update(pygame.mouse.get_pos()[0])
        player.draw(SCREEN)

        # --- Bullet Logic ---
        for b in bullets[:]:
            b.update()
            b.draw(SCREEN)
            if not b.active:
                bullets.remove(b)

        # --- Invader Logic (NES Speed Mechanics) ---
        # Calculate current speed based on enemies left
        current_speed = get_nes_speed(len(invaders))
        
        edge_hit = False
        for inv in invaders:
            inv.rect.x += current_speed * invader_dir
            if inv.rect.right >= WIDTH or inv.rect.left <= 0:
                edge_hit = True
        
        if edge_hit:
            invader_dir *= -1
            for inv in invaders:
                inv.rect.y += 20 # Drop down

        # --- Collision Detection ---
        for b in bullets[:]:
            for inv in invaders[:]:
                if b.rect.colliderect(inv.rect):
                    bullets.remove(b)
                    invaders.remove(inv)
                    snd_hit.play()
                    break

        # Draw Invaders
        for inv in invaders:
            inv.draw(SCREEN)

        # --- Win/Lose States ---
        if len(invaders) == 0:
            draw_text(SCREEN, "YOU WIN!", 60, GREEN, WIDTH//2, HEIGHT//2)
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False
            
        for inv in invaders:
            if inv.rect.bottom >= HEIGHT:
                draw_text(SCREEN, "GAME OVER", 60, RED, WIDTH//2, HEIGHT//2)
                pygame.display.flip()
                pygame.time.delay(2000)
                running = False

        pygame.display.flip()
        CLOCK.tick(FPS) # Strict 60 FPS

# -----------------------------------------------------------------------------
# MENUS
# -----------------------------------------------------------------------------
def show_screen(screen_type):
    """Displays a menu screen and waits for user input."""
    running = True
    while running:
        SCREEN.fill(BLACK)
        
        if screen_type == "main_menu":
            draw_text(SCREEN, "AC Holdings Space Invader 0.1 #", 48, GREEN, WIDTH//2, HEIGHT//4)
            draw_text(SCREEN, "M4 PORT Py Edition", 36, CYAN, WIDTH//2, HEIGHT//4 + 50)
            draw_text(SCREEN, "Click anywhere to start", 24, WHITE, WIDTH//2, HEIGHT//2 - 20)
            draw_text(SCREEN, "Press H for How to Play", 24, WHITE, WIDTH//2, HEIGHT//2 + 20)
            draw_text(SCREEN, "Press ESC to quit", 18, WHITE, WIDTH//2, HEIGHT - 60)
            
        elif screen_type == "how_to_play":
            draw_text(SCREEN, "HOW TO PLAY", 48, YELLOW, WIDTH//2, HEIGHT//4)
            draw_text(SCREEN, "Move Mouse: Aim Ship", 28, WHITE, WIDTH//2, HEIGHT//2 - 60)
            draw_text(SCREEN, "Left Click: Shoot", 28, WHITE, WIDTH//2, HEIGHT//2 - 20)
            draw_text(SCREEN, "Goal: Destroy all invaders!", 28, WHITE, WIDTH//2, HEIGHT//2 + 20)
            draw_text(SCREEN, "Warning: They speed up as they die.", 24, ORANGE, WIDTH//2, HEIGHT//2 + 70)
            draw_text(SCREEN, "Press ESC or click to return", 20, WHITE, WIDTH//2, HEIGHT - 60)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if screen_type == "main_menu":
                        pygame.quit()
                        sys.exit()
                    else:
                        return  # go back to main menu
                if screen_type == "main_menu" and event.key == pygame.K_h:
                    show_screen("how_to_play")
            if event.type == pygame.MOUSEBUTTONDOWN:
                if screen_type == "main_menu":
                    return  # start game
                elif screen_type == "how_to_play":
                    return  # go back to main menu

# -----------------------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------
def main():
    while True:
        show_screen("main_menu")      # returns when player clicks to start
        game_loop()                   # plays one game, returns to menu when done

if __name__ == "__main__":
    main()
