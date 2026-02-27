# Using pygame-ce (pygame community edition)
import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# ==========================================
# CONSTANTS
# ==========================================
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GRID_ROWS = 5
GRID_COLS = 9
CELL_SIZE = 80
SIDEBAR_WIDTH = 200
GAME_WIDTH = GRID_COLS * CELL_SIZE
GAME_HEIGHT = GRID_ROWS * CELL_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (0, 100, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
DARK_BROWN = (60, 30, 10)
CYAN = (0, 255, 255)
WATER_BLUE = (64, 164, 223)
DARK_WATER = (40, 120, 180)
ICE_BLUE = (200, 230, 255)

# Game settings
SUN_START = 50
SUN_DROP_RATE = 600          # frames between natural sun drops
ZOMBIE_SPAWN_BASE = 400
PEA_SHOOT_COOLDOWN = 90
SUNFLOWER_GEN_RATE = 600

# Plant Data
PLANT_DATA = {
    'peashooter': {'cost': 100, 'health': 100, 'cooldown': 0, 'unlock': '1-1'},
    'sunflower':  {'cost': 50,  'health': 100, 'cooldown': 0, 'unlock': '1-1'},
    'wallnut':    {'cost': 50,  'health': 800, 'cooldown': 0, 'unlock': '1-4'},
    'cherrybomb': {'cost': 150, 'health': 100, 'cooldown': 0, 'unlock': '1-2'},
    'snowpea':    {'cost': 175, 'health': 100, 'cooldown': 0, 'unlock': '1-6'},
    'repeater':   {'cost': 200, 'health': 100, 'cooldown': 0, 'unlock': '1-8'},
    'potatomine': {'cost': 25,  'health': 100, 'cooldown': 200, 'unlock': '1-5'},
    'chomper':    {'cost': 150, 'health': 100, 'cooldown': 0, 'unlock': '1-7'},
    'puffshroom': {'cost': 0,   'health': 100, 'cooldown': 0, 'unlock': '2-1'},
    'lilypad':    {'cost': 25,  'health': 100, 'cooldown': 0, 'unlock': '2-1'},
    'squash':     {'cost': 50,  'health': 100, 'cooldown': 0, 'unlock': '1-3'}
}

# Zombie Data
ZOMBIE_DATA = {
    'basic':     {'health': 100, 'speed': 0.3, 'damage': 100},
    'cone':      {'health': 200, 'speed': 0.3, 'damage': 100},
    'bucket':    {'health': 400, 'speed': 0.3, 'damage': 100},
    'flag':      {'health': 100, 'speed': 0.6, 'damage': 100},
    'newspaper': {'health': 150, 'speed': 0.3, 'damage': 100},
    'pole':      {'health': 100, 'speed': 0.8, 'damage': 100},
    'football':  {'health': 500, 'speed': 0.7, 'damage': 100},
    'ducky':     {'health': 100, 'speed': 0.3, 'damage': 100}
}

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cat's PVZ - Complete Edition")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
title_font = pygame.font.Font(None, 74)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def check_unlock(plant_name, level_str):
    """Return True if plant is unlocked at the given level."""
    unlocks = {
        'peashooter': '1-1', 'sunflower': '1-1', 'cherrybomb': '1-2',
        'squash': '1-3', 'wallnut': '1-4', 'potatomine': '1-5',
        'snowpea': '1-6', 'chomper': '1-7', 'repeater': '1-8',
        'puffshroom': '2-1', 'lilypad': '2-1'
    }
    if plant_name not in unlocks:
        return True
    # Compare level strings (e.g. "2-1" vs "1-5")
    current_world, current_level = map(int, level_str.split('-'))
    req_world, req_level = map(int, unlocks[plant_name].split('-'))
    if current_world > req_world:
        return True
    if current_world == req_world and current_level >= req_level:
        return True
    return False

# ==========================================
# MAIN MENU DRAWING FUNCTIONS (PvZ1 style)
# ==========================================
def draw_menu_background(screen, frame_count):
    """Draw a lawn grid covering the left part of the screen."""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            rect = pygame.Rect(col*CELL_SIZE, row*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            # Alternate colors like a chessboard
            base_color = LIGHT_GREEN
            alt_color = DARK_GREEN
            pygame.draw.rect(screen, base_color if (row+col)%2==0 else alt_color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
    # Fill the right sidebar area with a stone-like color
    pygame.draw.rect(screen, GRAY, (GAME_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))

def draw_menu_sidebar(screen):
    """Draw a seed bank on the right with plant slots (similar to in-game)."""
    plants = ['peashooter', 'sunflower', 'wallnut', 'cherrybomb',
              'snowpea', 'repeater', 'potatomine', 'chomper',
              'puffshroom', 'lilypad', 'squash']
    y = 50
    for i, p in enumerate(plants):
        btn = pygame.Rect(GAME_WIDTH+10, y + i*60, 180, 50)
        # Outer border (slot)
        pygame.draw.rect(screen, BLACK, btn, 3)
        # Inner background (seed packet)
        color_map = {
            'peashooter': GREEN,
            'sunflower': YELLOW,
            'wallnut': BROWN,
            'cherrybomb': RED,
            'snowpea': ICE_BLUE,
            'repeater': DARK_GREEN,
            'potatomine': BROWN,
            'chomper': PURPLE,
            'puffshroom': (200,150,255),
            'lilypad': (0,100,0),
            'squash': ORANGE
        }
        color = color_map.get(p, WHITE)
        inner_rect = btn.inflate(-10, -10)
        pygame.draw.rect(screen, color, inner_rect)
        # Plant initial
        letter = p[0].upper()
        txt = small_font.render(letter, True, BLACK)
        screen.blit(txt, (inner_rect.x + 10, inner_rect.y + 10))
        # Cost
        cost = PLANT_DATA[p]['cost']
        cost_txt = small_font.render(str(cost), True, BLACK)
        screen.blit(cost_txt, (inner_rect.x + 120, inner_rect.y + 10))

def draw_menu_sun(screen):
    """Draw a sun with a number (like the sun counter)."""
    sun_x = 70
    sun_y = 70
    # Sun glow
    pygame.draw.circle(screen, YELLOW, (sun_x, sun_y), 35)
    pygame.draw.circle(screen, ORANGE, (sun_x, sun_y), 28)
    # Sun number (fixed for menu)
    text = font.render("50", True, BLACK)
    screen.blit(text, (sun_x - 18, sun_y - 15))

def main_menu():
    """Display the PvZ1-style main menu and return the selected action."""
    frame_count = 0
    while True:
        # Draw the lawn background and seed bank
        draw_menu_background(screen, frame_count)
        draw_menu_sidebar(screen)
        draw_menu_sun(screen)

        # Draw the title (with a shadow for effect)
        title_shadow = title_font.render("Cat's PVZ", True, DARK_BROWN)
        title_text = title_font.render("Cat's PVZ", True, (255, 255, 150))  # light yellow
        screen.blit(title_shadow, (SCREEN_WIDTH//2 - 148, 52))
        screen.blit(title_text, (SCREEN_WIDTH//2 - 150, 50))

        # Draw the menu buttons (wooden plank style)
        buttons = [
            ("Adventure Mode", 200, "adventure"),
            ("Mini-Games", 270, "mini"),
            ("Survival", 340, "survival"),
            ("Zen Garden", 410, "zen"),
            ("Quit", 480, "quit")
        ]

        rects = []
        for text, y, action in buttons:
            # Wooden plank background
            rect = pygame.Rect(SCREEN_WIDTH//2 - 120, y, 240, 60)
            # Draw wood grain (simple gradient or just a brown rectangle)
            pygame.draw.rect(screen, (160, 100, 40), rect)  # base wood
            pygame.draw.rect(screen, (200, 140, 60), rect.inflate(-10, -10))  # lighter inside
            pygame.draw.rect(screen, BLACK, rect, 3)  # border

            # Text
            txt_surf = font.render(text, True, BLACK)
            screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - 15))
            rects.append((rect, action))

        pygame.display.flip()
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, action in rects:
                    if rect.collidepoint(event.pos):
                        return action
        clock.tick(60)

# ==========================================
# GAME CLASSES (unchanged, except where noted)
# ==========================================
class Plant:
    def __init__(self, x, y, plant_type, env="day"):
        self.x = x
        self.y = y
        self.type = plant_type
        self.health = PLANT_DATA.get(plant_type, {}).get('health', 100)
        self.max_health = self.health
        self.rect = pygame.Rect(x, y, CELL_SIZE-10, CELL_SIZE-10)
        self.last_shot = 0
        self.last_sun_gen = 0
        self.exploded = False
        self.arm_timer = 0
        self.is_armed = False        # Potato mine
        self.chewing = 0             # Chomper
        self.sleeping = False         # Mushrooms sleep in day
        self.watered = False
        self.fertilized = False

        if 'shroom' in plant_type and env == "day":
            self.sleeping = True

    def update(self, current_time, zombies):
        """Update plant state, return action if any."""
        if self.sleeping:
            return None

        # Sunflower generates sun
        if self.type == 'sunflower':
            if current_time - self.last_sun_gen > SUNFLOWER_GEN_RATE:
                self.last_sun_gen = current_time
                return ('sun', 25)   # (action, value)

        # Cherry bomb explodes immediately
        elif self.type == 'cherrybomb' and not self.exploded:
            self.exploded = True
            return ('explode',)

        # Potato mine arms then explodes when zombie touches it
        elif self.type == 'potatomine':
            if not self.is_armed:
                self.arm_timer += 1
                if self.arm_timer > 200:
                    self.is_armed = True
            else:
                for z in zombies:
                    if z.row == (self.y // CELL_SIZE) and z.rect.colliderect(self.rect):
                        self.health = 0
                        return ('mine_explode', self.x, self.y)

        # Chomper eats a zombie
        elif self.type == 'chomper':
            if self.chewing > 0:
                self.chewing -= 1
            else:
                for z in zombies:
                    if z.row == (self.y // CELL_SIZE) and abs(z.x - self.x) < 40:
                        if z.type not in ('football', 'bucket'):   # cannot eat these
                            self.chewing = 300
                            return ('eat_zombie', z)
        return None

    def draw(self, screen):
        # Color based on type
        color_map = {
            'peashooter': GREEN,
            'sunflower': YELLOW,
            'wallnut': BROWN,
            'cherrybomb': RED,
            'snowpea': ICE_BLUE,
            'repeater': DARK_GREEN,
            'potatomine': BROWN if not self.is_armed else ORANGE,
            'chomper': PURPLE,
            'puffshroom': (200, 150, 255),
            'lilypad': (0, 100, 0),
            'squash': ORANGE
        }
        color = color_map.get(self.type, WHITE)

        pygame.draw.rect(screen, color, self.rect)

        if self.sleeping:
            pygame.draw.circle(screen, BLACK, self.rect.center, 10)
            text = small_font.render("Zzz", True, WHITE)
            screen.blit(text, (self.x+5, self.y-20))
        elif self.type == 'chomper' and self.chewing > 0:
            # mouth closed (full)
            pygame.draw.rect(screen, RED, (self.x+20, self.y-10, 20, 10))

        # initial letter
        letter = self.type[0].upper()
        text = small_font.render(letter, True, BLACK)
        screen.blit(text, (self.rect.centerx - 5, self.rect.centery - 8))

        # health bar
        if self.health < self.max_health:
            bar_width = self.rect.width * (self.health / self.max_health)
            pygame.draw.rect(screen, RED, (self.x, self.y-10, self.rect.width, 5))
            pygame.draw.rect(screen, GREEN, (self.x, self.y-10, bar_width, 5))

class Zombie:
    def __init__(self, row, col, z_type='basic', env='day'):
        self.row = row
        self.col = col
        self.type = z_type
        data = ZOMBIE_DATA.get(z_type, ZOMBIE_DATA['basic'])
        self.health = data['health']
        self.max_health = self.health
        self.base_speed = data['speed']
        self.speed = self.base_speed

        self.x = GAME_WIDTH + random.randint(0, 200)
        self.y = row * CELL_SIZE + 10
        self.rect = pygame.Rect(self.x, self.y, CELL_SIZE-20, CELL_SIZE-20)
        self.eating = False
        self.target_plant = None

        # Specific states
        self.has_pole = (z_type == 'pole')
        self.angry = False   # newspaper zombie after losing paper
        self.slowed = 0

    def update(self, grid):
        # Slowing effect
        if self.slowed > 0:
            self.slowed -= 1
            current_speed = self.speed * 0.5
        else:
            current_speed = self.speed

        # Newspaper anger
        if self.type == 'newspaper' and self.health < 150 and not self.angry:
            self.angry = True
            self.speed = self.base_speed * 2.0

        # Pole vault jump
        if self.type == 'pole' and self.has_pole:
            for r in range(len(grid)):
                for c in range(len(grid[0])):
                    plant = grid[r][c]
                    if plant and r == self.row:
                        if plant.type not in ('lilypad', 'tallnut'):   # jumpable
                            if abs(plant.x - self.x) < 40:
                                self.x -= 100   # jump over
                                self.has_pole = False
                                return

        # Movement / eating
        if not self.eating:
            self.x -= current_speed
            self.col = max(0, int(self.x / CELL_SIZE))
            self.rect.x = self.x

        # Check for plant in front
        front_col = max(0, int((self.x + 10) // CELL_SIZE))
        if front_col < len(grid[0]):
            plant = grid[self.row][front_col]
            if plant and not self.eating:
                # Pole vault handles jump earlier, so here it's just eating
                self.eating = True
                self.target_plant = plant

            if self.eating and self.target_plant:
                self.target_plant.health -= 1
                if self.target_plant.health <= 0:
                    grid[self.row][front_col] = None
                    self.eating = False
                    self.target_plant = None

    def draw(self, screen):
        color_map = {
            'basic': BROWN,
            'cone': ORANGE,
            'bucket': GRAY,
            'flag': RED,
            'newspaper': PINK if self.angry else WHITE,
            'pole': YELLOW if not self.has_pole else ORANGE,
            'football': (50, 50, 50),
            'ducky': YELLOW
        }
        color = color_map.get(self.type, BROWN)
        pygame.draw.rect(screen, color, self.rect)

        if self.slowed > 0:
            pygame.draw.rect(screen, ICE_BLUE, self.rect, 3)

        text = small_font.render("Z", True, BLACK)
        screen.blit(text, (self.x+25, self.y+20))

        # health bar
        bar_width = self.rect.width * (self.health / self.max_health)
        pygame.draw.rect(screen, RED, (self.x, self.y-10, self.rect.width, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y-10, bar_width, 5))

class Projectile:
    def __init__(self, x, y, target_row, damage=20, p_type='pea'):
        self.x = x
        self.y = y + CELL_SIZE//2 - 5
        self.target_row = target_row
        self.speed = 6
        self.damage = damage
        self.type = p_type
        self.rect = pygame.Rect(self.x, self.y, 10, 10)

    def move(self):
        self.x += self.speed
        self.rect.x = self.x

    def draw(self, screen):
        color = GREEN if self.type == 'pea' else ICE_BLUE
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 5)

class Sun:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.rect = pygame.Rect(x-15, y-15, 30, 30)
        self.falling = True
        self.speed = 1

    def update(self):
        if self.falling:
            self.y += self.speed
            self.rect.y = self.y
            if self.y > GAME_HEIGHT - 50:
                self.falling = False

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (self.x, self.y), 15)
        text = small_font.render(str(self.value), True, BLACK)
        screen.blit(text, (self.x-8, self.y-10))

# ==========================================
# GAME MANAGER (unchanged)
# ==========================================
class Game:
    def __init__(self, level_str="1-1", mode="adventure"):
        self.mode = mode
        self.level_str = level_str
        self.world, self.sublevel = map(int, level_str.split('-'))

        # Environment setup
        if self.world == 1:
            self.env = "day"
        elif self.world == 2:
            self.env = "night"
        elif self.world == 3:
            self.env = "pool"
        else:
            self.env = "fog"

        # Grid
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.water_rows = [2, 3] if self.env in ("pool", "fog") else []

        # Objects
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.sun_points = SUN_START
        self.frame_count = 0
        self.selected_plant = None
        self.game_over = False
        self.win = False
        self.zombies_spawned = 0
        self.zombies_to_spawn = 5 + self.sublevel * 2
        self.spawn_delay = ZOMBIE_SPAWN_BASE
        self.next_spawn = 200

    def handle_click(self, pos):
        x, y = pos
        # Sidebar click
        if x > GAME_WIDTH:
            self.handle_sidebar_click(x, y)
        elif not self.game_over:
            col = x // CELL_SIZE
            row = y // CELL_SIZE
            if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                target_cell = self.grid[row][col]
                is_water = row in self.water_rows

                if self.selected_plant:
                    p_type = self.selected_plant
                    # Check water placement
                    if is_water:
                        if p_type == 'lilypad' and target_cell is None:
                            self.place_plant(row, col, 'lilypad')
                        elif target_cell and target_cell.type == 'lilypad':
                            # Replace lily pad with the selected plant (keeps water property)
                            self.place_plant(row, col, p_type)
                    else:
                        if target_cell is None:
                            self.place_plant(row, col, p_type)

    def place_plant(self, row, col, p_type):
        cost = PLANT_DATA[p_type]['cost']
        if self.sun_points >= cost:
            self.sun_points -= cost
            new_plant = Plant(col*CELL_SIZE+5, row*CELL_SIZE+5, p_type, self.env)
            self.grid[row][col] = new_plant
            self.selected_plant = None

    def handle_sidebar_click(self, x, y):
        y_index = (y - 50) // 60
        plants_available = [
            'peashooter', 'sunflower', 'wallnut', 'cherrybomb',
            'snowpea', 'repeater', 'potatomine', 'chomper',
            'puffshroom', 'lilypad', 'squash'
        ]
        if 0 <= y_index < len(plants_available):
            p = plants_available[y_index]
            if check_unlock(p, self.level_str):
                self.selected_plant = p

    def update(self):
        if self.game_over or self.win:
            return

        self.frame_count += 1

        # Natural sun drop
        if self.env == "day" and self.frame_count % SUN_DROP_RATE == 0:
            self.suns.append(Sun(random.randint(50, GAME_WIDTH-50), 0, 25))

        # Zombie spawning
        if self.zombies_spawned < self.zombies_to_spawn:
            if self.frame_count >= self.next_spawn:
                self.spawn_zombie()
                self.next_spawn = self.frame_count + self.spawn_delay - (self.sublevel * 10)
        elif len(self.zombies) == 0:
            self.win = True

        self.update_plants()
        self.update_projectiles()
        self.update_zombies()
        self.update_suns()
        self.shooting_logic()

    def spawn_zombie(self):
        row = random.randint(0, GRID_ROWS-1)
        # Choose type based on level
        r = random.random()
        if self.world == 3:   # Pool
            if row in self.water_rows:
                z_type = 'ducky'
            else:
                z_type = random.choice(['basic', 'cone', 'bucket'])
        else:
            if self.sublevel >= 5:
                if r < 0.2:
                    z_type = 'pole'
                elif r < 0.4:
                    z_type = 'newspaper'
                elif r < 0.6:
                    z_type = 'bucket'
                else:
                    z_type = 'basic'
            elif self.sublevel >= 3:
                if r < 0.3:
                    z_type = 'cone'
                else:
                    z_type = 'basic'
            else:
                z_type = 'basic'
        self.zombies.append(Zombie(row, GRID_COLS-1, z_type, self.env))
        self.zombies_spawned += 1

    def shooting_logic(self):
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                plant = self.grid[row][col]
                if plant and not plant.sleeping:
                    if plant.type in ('peashooter', 'snowpea', 'repeater', 'puffshroom'):
                        # Check for zombie in row to the right
                        has_target = False
                        for z in self.zombies:
                            if z.row == row and z.x > plant.x:
                                has_target = True
                                break
                        if has_target and self.frame_count - plant.last_shot > PEA_SHOOT_COOLDOWN:
                            plant.last_shot = self.frame_count
                            p_type = 'pea'
                            if plant.type == 'snowpea':
                                p_type = 'frozen'
                            self.projectiles.append(Projectile(plant.x+CELL_SIZE, plant.y, row, p_type=p_type))
                            if plant.type == 'repeater':
                                self.projectiles.append(Projectile(plant.x+CELL_SIZE+20, plant.y, row, p_type='pea'))

    def update_plants(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                plant = self.grid[r][c]
                if plant:
                    result = plant.update(self.frame_count, self.zombies)
                    if result is None:
                        continue
                    action = result[0]
                    if action == 'explode':
                        self.cherry_explode(r, c)
                        self.grid[r][c] = None
                    elif action == 'mine_explode':
                        _, ex, ey = result
                        for z in self.zombies[:]:
                            if z.row == r and abs(z.x - ex) < 50:
                                z.health = 0
                        self.grid[r][c] = None
                    elif action == 'eat_zombie':
                        target_z = result[1]
                        if target_z in self.zombies:
                            self.zombies.remove(target_z)
                    elif action == 'sun':
                        # Sunflower generated sun
                        _, value = result
                        self.suns.append(Sun(plant.x+CELL_SIZE//2, plant.y, value))

    def cherry_explode(self, row, col):
        for z in self.zombies[:]:
            if abs(z.row - row) <= 1 and z.col >= col-1 and z.col <= col+1:
                z.health = 0

    def update_zombies(self):
        for z in self.zombies[:]:
            z.update(self.grid)
            if z.x < -20:
                self.game_over = True
            if z.health <= 0:
                self.zombies.remove(z)

    def update_projectiles(self):
        for p in self.projectiles[:]:
            p.move()
            if p.x > GAME_WIDTH:
                self.projectiles.remove(p)
                continue
            # Check collision with zombies
            for z in self.zombies:
                if z.row == p.target_row and z.rect.colliderect(p.rect):
                    z.health -= p.damage
                    if p.type == 'frozen':
                        z.slowed = 300
                    if p in self.projectiles:
                        self.projectiles.remove(p)
                    break

    def update_suns(self):
        for s in self.suns[:]:
            s.update()
            if s.y > SCREEN_HEIGHT:
                self.suns.remove(s)

    def draw(self, screen):
        self.draw_background(screen)

        # Plants
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if self.grid[row][col]:
                    self.grid[row][col].draw(screen)

        for z in self.zombies:
            z.draw(screen)
        for p in self.projectiles:
            p.draw(screen)
        for s in self.suns:
            s.draw(screen)

        self.draw_sidebar(screen)
        self.draw_overlay(screen)

    def draw_background(self, screen):
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                rect = pygame.Rect(col*CELL_SIZE, row*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                base_color = LIGHT_GREEN
                alt_color = DARK_GREEN
                if self.env == "night":
                    base_color = (50, 80, 50)
                    alt_color = (30, 60, 30)
                elif row in self.water_rows:
                    # Animate water slightly
                    if (self.frame_count // 10) % 2 == 0:
                        base_color = WATER_BLUE
                        alt_color = DARK_WATER
                    else:
                        base_color = DARK_WATER
                        alt_color = WATER_BLUE
                pygame.draw.rect(screen, base_color if (row+col)%2==0 else alt_color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

    def draw_sidebar(self, screen):
        pygame.draw.rect(screen, GRAY, (GAME_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))

        # Sun counter
        text = font.render(f"Sun: {self.sun_points}", True, BLACK)
        screen.blit(text, (GAME_WIDTH+10, 10))

        # Plant selection buttons
        plants = ['peashooter', 'sunflower', 'wallnut', 'cherrybomb',
                  'snowpea', 'repeater', 'potatomine', 'chomper',
                  'puffshroom', 'lilypad', 'squash']
        y = 50
        for p in plants:
            btn = pygame.Rect(GAME_WIDTH+10, y, 180, 50)
            if not check_unlock(p, self.level_str):
                color = DARK_BROWN
            elif self.selected_plant == p:
                color = GREEN
            else:
                color = WHITE
            pygame.draw.rect(screen, color, btn)
            pygame.draw.rect(screen, BLACK, btn, 2)

            cost = PLANT_DATA[p]['cost']
            txt = small_font.render(f"{p[:6]}({cost})", True, BLACK)
            screen.blit(txt, (btn.x+5, btn.y+15))
            y += 60

        # Level info
        lvl_txt = font.render(f"Lvl: {self.level_str}", True, BLACK)
        screen.blit(lvl_txt, (GAME_WIDTH+10, SCREEN_HEIGHT-100))
        mode_txt = small_font.render(f"Mode: {self.mode}", True, BLACK)
        screen.blit(mode_txt, (GAME_WIDTH+10, SCREEN_HEIGHT-60))

    def draw_overlay(self, screen):
        if self.game_over:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(128)
            s.fill((0,0,0))
            screen.blit(s, (0,0))
            txt = font.render("GAME OVER", True, RED)
            screen.blit(txt, (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2))
        elif self.win:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(128)
            s.fill((0,0,0))
            screen.blit(s, (0,0))
            txt = font.render("LEVEL COMPLETE!", True, GREEN)
            screen.blit(txt, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))

# ==========================================
# GAME LOOP
# ==========================================
def run_game(level_str, mode="adventure"):
    """Run a level and return the next level string or 'menu'."""
    game = Game(level_str, mode)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(event.pos)

                # Sun collection
                for s in game.suns[:]:
                    if s.rect.collidepoint(event.pos):
                        game.sun_points += s.value
                        game.suns.remove(s)

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

        if game.win:
            # Advance to next level
            w, sl = map(int, level_str.split('-'))
            sl += 1
            if sl > 10:
                sl = 1
                w += 1
                if w > 3:  # Max world 3 for now
                    return "menu"
            next_level = f"{w}-{sl}"
            return next_level

        if game.game_over:
            # Game over: go back to menu or retry? For now, return "menu"
            return "menu"

# ==========================================
# MAIN PROGRAM
# ==========================================
def main():
    """Main program loop."""
    current_level = "1-1"
    mode = "adventure"
    while True:
        action = main_menu()
        if action == "quit":
            pygame.quit()
            sys.exit()
        elif action == "adventure":
            # Start or continue adventure mode
            result = run_game(current_level, mode)
            if result == "menu":
                continue
            elif result:
                current_level = result
        else:
            # Other modes not implemented yet; just go back to menu
            continue

if __name__ == "__main__":
    main()
