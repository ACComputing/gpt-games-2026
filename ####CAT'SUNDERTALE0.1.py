import pygame
import sys
import random
import math

# --- Constants & Configuration ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)       # Determination
COLOR_YELLOW = (255, 255, 0)  # Save points / Spare
COLOR_GREEN = (0, 255, 0)     # Healing
COLOR_UI_ORANGE = (255, 160, 0) 
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (50, 50, 50)
COLOR_WALL_BG = (70, 20, 70)  # Dark purple ruins walls
COLOR_WALL_BRICK = (110, 40, 110) # Lighter purple for brick details
COLOR_SEPIA = (195, 172, 133) # Intro sepia color
COLOR_FLOWERS = (255, 215, 0) # Golden flowers
COLOR_LEAVES = (180, 60, 60)  # Red leaves
COLOR_WATER = (60, 100, 200)  # Water
COLOR_TREE = (0, 0, 0)        # Black silhouette tree

# Game States
STATE_STORY = "STORY"         # The "Long ago..." intro
STATE_TITLE = "TITLE"         # The Main Menu
STATE_OVERWORLD = "OVERWORLD"
STATE_OVERWORLD_MENU = "OVERWORLD_MENU"
STATE_BATTLE = "BATTLE"
STATE_VICTORY = "VICTORY"
STATE_GAMEOVER = "GAMEOVER"
STATE_ENDING = "ENDING"       # End of Demo

# Battle Sub-States
BATTLE_MENU = "MENU"             # Selecting 4 buttons at bottom
BATTLE_SELECT_ENEMY = "SEL_ENEMY" # Choosing target
BATTLE_SELECT_ACT = "SEL_ACT"    # Choosing specific act
BATTLE_SELECT_ITEM = "SEL_ITEM"  # Choosing item
BATTLE_SELECT_MERCY = "SEL_MERCY"# Choosing Spare/Flee
BATTLE_PLAYER_ATTACK = "ATTACK"  # The timing bar
BATTLE_ENEMY_TURN = "DODGE"      # Heart dodging bullets
BATTLE_DIALOGUE = "DIALOGUE"     # Text typing out

# --- Data: Levels & Enemies ---

ENEMY_DATA = {
    "FROGGIT": {
        "hp": 30, "max_hp": 30, "atk": 4, "xp": 10, "gold": 20, 
        "lines": ["* Froggit doesn't understand what you said.", "* Froggit hops to and fro.", "* The battlefield is humid."],
        "acts": ["Check", "Compliment", "Threaten"]
    },
    "WHIMSUN": {
        "hp": 10, "max_hp": 10, "atk": 2, "xp": 2, "gold": 5, 
        "lines": ["* Whimsun is hyperventilating.", "* Whimsun looks like it's about to cry.", "* You feel bad."],
        "acts": ["Check", "Console", "Terrorize"]
    },
    "MOLDSMAL": {
        "hp": 50, "max_hp": 50, "atk": 4, "xp": 3, "gold": 3,
        "lines": ["* Moldsmal burbles quietly.", "* Slime sounds.", "* ..."],
        "acts": ["Check", "Flirt", "Imitate"]
    },
    "TORIEL": {
        "hp": 440, "max_hp": 440, "atk": 6, "xp": 0, "gold": 0,
        "lines": ["* ...", "* Prove to me you are strong enough to survive.", "* Be good, my child."],
        "acts": ["Check", "Talk"]
    }
}

# --- MAP DESIGN ---
# Adapted to fit 640x480 screens while maintaining the relative layout of Undertale's Ruins.
LEVELS = {
    # 1. The Flower Bed (Start)
    "ruins_start": {
        "walls": [(0, 0, 200, 480), (440, 0, 200, 480), (200, 400, 240, 80)],
        "portals": [((200, 0, 240, 20), "ruins_entrance", (320, 380))],
        "objects": [(280, 250, 80, 60, COLOR_FLOWERS)], # Golden Flowers
        "encounters": []
    },
    # 2. Ruins Entrance (Save Point, Archway)
    "ruins_entrance": {
        "walls": [
            (0, 0, 150, 480), (490, 0, 150, 480), # Sides
            (150, 0, 340, 100) # Top Arch
        ],
        "portals": [
            ((280, 460, 80, 20), "ruins_start", (320, 60)),
            ((280, 100, 80, 20), "ruins_switches", (320, 380)) # To Switches
        ],
        "objects": [
            (310, 200, 20, 20, COLOR_YELLOW), # Save Point
            (180, 350, 40, 20, COLOR_LEAVES), (420, 350, 40, 20, COLOR_LEAVES) # Leaves
        ],
        "encounters": []
    },
    # 3. Switch Puzzle Room
    "ruins_switches": {
        "walls": [(0, 0, 150, 480), (490, 0, 150, 480)],
        "portals": [
            ((280, 460, 80, 20), "ruins_entrance", (320, 140)),
            ((280, 0, 80, 20), "ruins_dummy", (320, 380))
        ],
        "objects": [
            (200, 100, 30, 30, COLOR_YELLOW), (410, 100, 30, 30, COLOR_YELLOW), # Switches
            (250, 200, 140, 40, COLOR_WALL_BRICK) # Sign text
        ],
        "encounters": []
    },
    # 4. Dummy Room
    "ruins_dummy": {
        "walls": [(0, 0, 150, 480), (490, 0, 150, 480)],
        "portals": [
            ((280, 460, 80, 20), "ruins_switches", (320, 40)),
            ((280, 0, 80, 20), "ruins_spike_hall", (60, 240)) # Door North leads to hallway logic
        ],
        "objects": [
            (300, 200, 40, 60, (200, 200, 180)) # The Dummy
        ],
        "encounters": []
    },
    # 5. Spike Puzzle Hallway (Transition to horizontal)
    "ruins_spike_hall": {
        "walls": [(0, 0, 640, 140), (0, 340, 640, 140)],
        "portals": [
            ((0, 140, 20, 200), "ruins_dummy", (320, 40)), # West -> Dummy (North door logic tweak)
            ((620, 140, 20, 200), "ruins_long_hall", (60, 240))
        ],
        "objects": [
            (200, 140, 240, 200, (80, 80, 80)) # Metal floor / Spikes area
        ],
        "encounters": ["FROGGIT"]
    },
    # 6. The Long Hallway (Toriel leaves)
    "ruins_long_hall": {
        "walls": [(0, 0, 640, 160), (0, 320, 640, 160)],
        "portals": [
            ((0, 160, 20, 160), "ruins_spike_hall", (600, 240)),
            ((620, 160, 20, 160), "ruins_candy", (60, 240))
        ],
        "encounters": ["WHIMSUN"]
    },
    # 7. Candy Room (Pillar view)
    "ruins_candy": {
        "walls": [(0, 0, 640, 100), (0, 380, 640, 100)],
        "portals": [
            ((0, 100, 20, 280), "ruins_long_hall", (600, 240)),
            ((620, 100, 20, 280), "ruins_rock", (60, 240))
        ],
        "objects": [
            (300, 240, 40, 40, (200, 100, 200)), # Candy Bowl
            (200, 100, 40, 280, COLOR_WALL_BG), # Pillar
            (400, 100, 40, 280, COLOR_WALL_BG)  # Pillar
        ],
        "encounters": []
    },
    # 8. Rock Pushing Room
    "ruins_rock": {
        "walls": [(0, 0, 640, 100), (0, 380, 640, 100)],
        "portals": [
            ((0, 100, 20, 280), "ruins_candy", (600, 240)),
            ((620, 100, 20, 280), "ruins_mouse", (60, 240))
        ],
        "objects": [
            (200, 200, 50, 50, (100, 100, 100)), # Rock 1
            (300, 300, 50, 50, (100, 100, 100)), # Rock 2
            (400, 150, 50, 50, (100, 100, 100))  # Rock 3
        ],
        "encounters": ["FROGGIT", "WHIMSUN"]
    },
    # 9. Mouse Hole (Squeak)
    "ruins_mouse": {
        "walls": [(0, 0, 640, 160), (0, 320, 640, 160)],
        "portals": [
            ((0, 160, 20, 160), "ruins_rock", (600, 240)),
            ((620, 160, 20, 160), "ruins_napsta", (60, 240))
        ],
        "objects": [
            (300, 310, 20, 10, (50, 50, 50)), # Mouse hole
            (320, 200, 40, 40, COLOR_YELLOW)  # Save Point
        ],
        "encounters": ["MOLDSMAL"]
    },
    # 10. Napstablook Room (Ghost area)
    "ruins_napsta": {
        "walls": [(0, 0, 640, 80), (0, 400, 640, 80)],
        "portals": [
            ((0, 80, 20, 320), "ruins_mouse", (600, 240)),
            ((620, 80, 20, 320), "ruins_bakesale", (60, 240))
        ],
        "objects": [
            (300, 220, 40, 60, (200, 200, 255)) # Napstablook (Simplified visual)
        ],
        "encounters": ["MOLDSMAL", "FROGGIT"]
    },
    # 11. Spider Bake Sale
    "ruins_bakesale": {
        "walls": [(0, 0, 640, 120), (0, 360, 640, 120)],
        "portals": [
            ((0, 120, 20, 240), "ruins_napsta", (600, 240)),
            ((620, 120, 20, 240), "ruins_view", (60, 240))
        ],
        "objects": [
            (150, 120, 100, 60, (220, 220, 220)), # Left Web
            (390, 120, 100, 60, (220, 220, 220))  # Right Web
        ],
        "encounters": []
    },
    # 12. The View (Toy Knife Balcony)
    "ruins_view": {
        "walls": [
            (0, 0, 640, 100), # Top wall
            (0, 300, 640, 180) # Balcony edge
        ],
        "portals": [
            ((0, 100, 20, 200), "ruins_bakesale", (600, 240)),
            ((620, 100, 20, 200), "ruins_home_out", (60, 240))
        ],
        "objects": [
            (0, 300, 640, 180, (20, 0, 20)) # The cityscape view (dark purple)
        ],
        "encounters": ["WHIMSUN", "MOLDSMAL"]
    },
    # 13. Toriel's Home (Outside)
    "ruins_home_out": {
        "walls": [(0, 0, 640, 80), (0, 400, 640, 80)],
        "portals": [
            ((0, 80, 20, 320), "ruins_view", (600, 240)),
            ((620, 80, 20, 320), "ruins_home_in", (320, 350)) # FIX: Spawn higher up to avoid wall collision
        ],
        "objects": [
            (220, 80, 200, 250, COLOR_TREE) # The Big Tree
        ],
        "encounters": []
    },
    # 14. Toriel's Home (Inside)
    "ruins_home_in": {
        "walls": [
            (0, 0, 100, 480), (540, 0, 100, 480), # Sides
            (100, 0, 440, 100), # Top
            (100, 420, 440, 60) # Bottom
        ],
        "portals": [
            ((280, 420, 80, 20), "ruins_home_out", (580, 240)), # Exit House
            ((280, 100, 80, 20), "ruins_basement", (320, 60)) # Stairs down
        ],
        "objects": [
            (120, 200, 60, 100, (150, 100, 50)), # Room Door
            (460, 200, 60, 100, (150, 100, 50)), # Kitchen
            (280, 250, 80, 80, (200, 150, 100))  # Carpet
        ],
        "encounters": []
    },
    # 15. Basement (The Long Walk)
    "ruins_basement": {
        "walls": [(0, 0, 220, 480), (420, 0, 220, 480)],
        "portals": [
            ((220, 0, 200, 20), "ruins_home_in", (320, 150)), # Back up
            ((220, 460, 200, 20), "boss_toriel", (320, 240)) # BOSS FIGHT TRIGGER
        ],
        "objects": [],
        "encounters": []
    }
}

STORY_LINES = [
    "Long ago, two races ruled over Earth:\nHUMANS and MONSTERS.",
    "One day, war broke out between the two races.",
    "After a long battle, the humans were victorious.",
    "They sealed the monsters underground with a magic spell.",
    "Many years later...",
    "MT. EBOTT, 201X.",
    "Legends say that those who climb the mountain never return.",
    "(Falling down...)",
    "CAT'S UNDERTALE ENGINE\n\n[PRESS Z or ENTER]"
]

# --- Setup Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cat's Undertale Engine")
clock = pygame.time.Clock()

# Fonts
def get_font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold)
    except:
        return pygame.font.SysFont("arial", size, bold)

FONT_MAIN = get_font("comicsansms", 24)        
FONT_UI = get_font("arial black", 20)          
FONT_DMG = get_font("impact", 30)              
FONT_PIXEL = get_font("couriernew", 20, bold=True) 
FONT_BATTLE_TEXT = get_font("couriernew", 26, bold=True) 
FONT_TITLE = get_font("timesnewroman", 32)
FONT_STORY = get_font("couriernew", 24)

# --- Graphics Generators (Procedural Sprites) ---

def create_frisk_sprite():
    scale = 2; w, h = 19, 30
    s = pygame.Surface((w * scale, h * scale)); s.set_colorkey((0,0,0))
    # Colors
    C_HAIR = (84, 54, 48); C_SKIN = (255, 201, 148); C_SHIRT = (40, 60, 200); C_STRIPE = (200, 40, 130)
    pixels = [
        "      .......      ", "    ...........    ", "   .............   ", "  ...............  ",
        "  .....     .....  ", "  .....ooooo.....  ", "  .....ooooo.....  ", "  .....ooooo.....  ",
        "   ...ooooooo...   ", "   xxxxxxxxxxxxx   ", "  xxxxxxxxxxxxxxx  ", "  xxxxxxxxxxxxxxx  ",
        "  xxxxxxxxxxxxxxx  ", "  ---------------  ", "  ---------------  ", "  xxxxxxxxxxxxxxx  ",
        "  xxxxxxxxxxxxxxx  ", "  ---------------  ", "  ---------------  ", "  xxxxxxxxxxxxxxx  ",
        "   .............   ", "   .....   .....   ", "   .....   .....   ", "   .....   .....   ",
        "  ......   ......  ", "  ......   ......  "
    ]
    for r, row in enumerate(pixels):
        for c, char in enumerate(row):
            color = None
            if char == '.': color = C_HAIR
            elif char == 'o': color = C_SKIN
            elif char == 'x': color = C_SHIRT
            elif char == '-': color = C_STRIPE
            if color: pygame.draw.rect(s, color, (c*scale, r*scale, scale, scale))
    return s

def create_heart_sprite():
    s = pygame.Surface((20, 20)); s.set_colorkey((0,0,0)); s.fill((0,0,0))
    points = [(10, 20), (1, 10), (1, 5), (5, 1), (10, 5), (15, 1), (19, 5), (19, 10)]
    pygame.draw.polygon(s, COLOR_RED, points)
    return s

def create_froggit_sprite():
    s = pygame.Surface((100, 100)); s.set_colorkey((0,0,0))
    pygame.draw.ellipse(s, COLOR_WHITE, (10, 40, 80, 50))
    pygame.draw.circle(s, COLOR_WHITE, (25, 35), 15); pygame.draw.circle(s, COLOR_WHITE, (75, 35), 15)
    pygame.draw.circle(s, COLOR_BLACK, (25, 35), 3); pygame.draw.circle(s, COLOR_BLACK, (75, 35), 3)
    for i in range(4): pygame.draw.polygon(s, COLOR_BLACK, [(30 + i*10, 70), (35 + i*10, 80), (40 + i*10, 70)])
    pygame.draw.ellipse(s, COLOR_WHITE, (0, 80, 30, 15)); pygame.draw.ellipse(s, COLOR_WHITE, (70, 80, 30, 15))
    return s

def create_whimsun_sprite():
    s = pygame.Surface((100, 100)); s.set_colorkey((0,0,0))
    pygame.draw.ellipse(s, (240, 240, 255), (0, 10, 40, 60)); pygame.draw.ellipse(s, (240, 240, 255), (60, 10, 40, 60))
    pygame.draw.ellipse(s, COLOR_WHITE, (40, 20, 20, 50))
    pygame.draw.line(s, COLOR_BLACK, (45, 35), (48, 38), 2); pygame.draw.line(s, COLOR_BLACK, (48, 35), (45, 38), 2)
    pygame.draw.line(s, COLOR_BLACK, (52, 35), (55, 38), 2); pygame.draw.line(s, COLOR_BLACK, (55, 35), (52, 38), 2)
    return s

def create_toriel_sprite():
    s = pygame.Surface((120, 150))
    s.set_colorkey((0,0,0))
    # Robe
    pygame.draw.polygon(s, (100, 50, 150), [(60, 20), (10, 140), (110, 140)])
    pygame.draw.rect(s, (255, 255, 255), (45, 20, 30, 120)) # White chest block
    # Delta Rune (simplified)
    pygame.draw.circle(s, (0, 0, 0), (60, 60), 5)
    # Head
    pygame.draw.rect(s, (255, 255, 255), (40, 0, 40, 40))
    # Horns
    pygame.draw.line(s, (255, 255, 255), (40, 10), (20, 5), 5)
    pygame.draw.line(s, (255, 255, 255), (80, 10), (100, 5), 5)
    return s

def draw_intro_scene(surface, index):
    rect_w, rect_h = 320, 180
    rect_x, rect_y = (SCREEN_WIDTH - rect_w) // 2, 40
    clip_rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)
    
    pygame.draw.rect(surface, COLOR_BLACK, (rect_x-4, rect_y-4, rect_w+8, rect_h+8))
    pygame.draw.rect(surface, (20, 20, 20), clip_rect)

    cx, cy = rect_x + rect_w // 2, rect_y + rect_h // 2

    if index == 0: 
        pygame.draw.circle(surface, COLOR_SEPIA, (cx - 50, cy), 20) 
        pygame.draw.rect(surface, COLOR_SEPIA, (cx - 60, cy + 20, 20, 40)) 
        mx = cx + 50
        pygame.draw.rect(surface, COLOR_SEPIA, (mx - 20, cy - 10, 40, 70)) 
        pygame.draw.circle(surface, COLOR_SEPIA, (mx, cy - 20), 15)
        pygame.draw.polygon(surface, COLOR_SEPIA, [(mx-15, cy-25), (mx-30, cy-40), (mx-5, cy-25)]) 
        pygame.draw.polygon(surface, COLOR_SEPIA, [(mx+15, cy-25), (mx+30, cy-40), (mx+5, cy-25)]) 
        pygame.draw.rect(surface, COLOR_SEPIA, (mx+20, cy, 10, 60))

    elif index == 1:
        for i in range(5):
            ox = random.randint(-40, 40)
            pygame.draw.line(surface, COLOR_SEPIA, (cx - 60 + ox, cy - 40), (cx + 20 + ox, cy + 40), 4)
            pygame.draw.line(surface, COLOR_SEPIA, (cx + 60 + ox, cy - 40), (cx - 20 + ox, cy + 40), 4)
        pygame.draw.circle(surface, (200, 100, 50), (cx, cy + 20), 30)

    elif index == 2:
        pygame.draw.rect(surface, COLOR_SEPIA, (cx - 15, cy - 20, 30, 80))
        pygame.draw.circle(surface, COLOR_SEPIA, (cx, cy - 35), 20)
        pygame.draw.line(surface, COLOR_SEPIA, (cx + 15, cy - 20), (cx + 50, cy - 60), 6)
        
    elif index == 3:
        for i in range(7):
            x_pos = rect_x + 40 + i * 40
            pygame.draw.rect(surface, COLOR_SEPIA, (x_pos, cy, 20, 80))
            pygame.draw.circle(surface, COLOR_SEPIA, (x_pos + 10, cy), 10)
    
    elif index == 4:
        # Many years later (just black/text or simple graphic)
        pass
        
    elif index == 5:
        points = [(rect_x, rect_y + rect_h), (cx, rect_y + 20), (rect_x + rect_w, rect_y + rect_h)]
        pygame.draw.polygon(surface, COLOR_SEPIA, points)
        
    elif index == 6:
        pygame.draw.circle(surface, (10, 0, 10), (cx, cy), 70) 
        pygame.draw.circle(surface, COLOR_SEPIA, (cx, cy), 70, 5) 
        pygame.draw.arc(surface, COLOR_SEPIA, (cx - 70, cy - 70, 140, 140), 0, 3.14, 2)

    elif index == 7:
        pygame.draw.rect(surface, (30, 30, 30), clip_rect) 
        pygame.draw.circle(surface, COLOR_SEPIA, (cx, cy), 10)
        pygame.draw.line(surface, COLOR_SEPIA, (cx, cy), (cx-10, cy-20), 2)
        pygame.draw.line(surface, COLOR_SEPIA, (cx, cy), (cx+10, cy-20), 2)

# --- Classes ---

class DialogueBox:
    def __init__(self, rect, font=FONT_BATTLE_TEXT):
        self.rect = rect; self.font = font
        self.full_text = ""; self.displayed_text = ""
        self.char_index = 0; self.timer = 0; self.typing_speed = 1
        self.active = False; self.finished = False

    def start(self, text):
        self.full_text = text; self.displayed_text = "*"
        self.char_index = 0; self.timer = 0; self.active = True; self.finished = False

    def update(self):
        if not self.active or self.finished: return
        self.timer += 1
        if self.timer >= self.typing_speed:
            self.timer = 0
            if self.char_index < len(self.full_text):
                self.displayed_text += self.full_text[self.char_index]
                self.char_index += 1
            else: self.finished = True

    def draw(self, surface):
        if not self.active: return
        words = self.displayed_text.split(' ')
        lines = []; current_line = ""
        for word in words:
            if self.font.size(current_line + word)[0] < self.rect.width - 40: current_line += word + " "
            else: lines.append(current_line); current_line = word + " "
        lines.append(current_line)
        y = self.rect.y + 20
        for line in lines:
            txt_surf = self.font.render(line, True, COLOR_WHITE)
            surface.blit(txt_surf, (self.rect.x + 30, y)); y += 35

class OverworldPlayer(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = create_frisk_sprite()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 4
        self.steps = 0

    def update(self, walls):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:  dx = -self.speed
        if keys[pygame.K_RIGHT]: dx = self.speed
        if keys[pygame.K_UP]:    dy = -self.speed
        if keys[pygame.K_DOWN]:  dy = self.speed

        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False):
            if dx > 0: self.rect.right = pygame.sprite.spritecollide(self, walls, False)[0].rect.left
            if dx < 0: self.rect.left = pygame.sprite.spritecollide(self, walls, False)[0].rect.right

        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False):
            if dy > 0: self.rect.bottom = pygame.sprite.spritecollide(self, walls, False)[0].rect.top
            if dy < 0: self.rect.top = pygame.sprite.spritecollide(self, walls, False)[0].rect.bottom
        self.rect.clamp_ip(screen.get_rect())
        return dx != 0 or dy != 0

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h)); self.image.fill(COLOR_WALL_BG)
        brick_w, brick_h = 30, 20
        for by in range(0, h, brick_h):
            start_x = 0 if (by // brick_h) % 2 == 0 else -15
            for bx in range(start_x, w, brick_w):
                pygame.draw.rect(self.image, COLOR_WALL_BRICK, (bx + 1, by + 1, brick_w - 2, brick_h - 2))
        self.rect = self.image.get_rect(topleft=(x, y))

class Portal(pygame.sprite.Sprite):
    def __init__(self, rect, dest_id, spawn_pos):
        super().__init__()
        self.image = pygame.Surface((rect[2], rect[3])); self.image.set_alpha(0)
        self.rect = pygame.Rect(rect); self.dest_id = dest_id; self.spawn_pos = spawn_pos

class ObjectSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class Soul(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = create_heart_sprite(); self.rect = self.image.get_rect()
        self.speed = 4; self.inv_frames = 0; self.visible = True

    def update(self, bounds):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed
        if keys[pygame.K_x] or keys[pygame.K_LSHIFT]: dx *= 0.5; dy *= 0.5
        self.rect.move_ip(dx, dy); self.rect.clamp_ip(bounds)
        if self.inv_frames > 0:
            self.inv_frames -= 1; self.visible = (self.inv_frames // 4) % 2 == 0
        else: self.visible = True

    def draw(self, surface):
        if self.visible: surface.blit(self.image, self.rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed):
        super().__init__()
        self.image = pygame.Surface((6, 6)); self.image.fill(COLOR_WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = math.cos(math.radians(angle)) * speed
        self.dy = math.sin(math.radians(angle)) * speed

    def update(self):
        self.rect.x += self.dx; self.rect.y += self.dy
        if not screen.get_rect().colliderect(self.rect): self.kill()

# --- Main Game Engine ---

class Game:
    def __init__(self):
        self.name = "FRISK"
        self.lv = 1; self.hp = 20; self.max_hp = 20
        self.xp = 0; self.gold = 0
        self.inventory = ["Butterscotch Pie", "Stick", "Bandage"]
        self.state = STATE_STORY
        self.story_index = 0
        self.title_timer = 0
        self.player = OverworldPlayer(320, 240)
        self.walls = pygame.sprite.Group()
        self.portals = pygame.sprite.Group()
        self.objects = pygame.sprite.Group()
        self.load_level("ruins_start")
        self.menu_index = 0
        self.menu_options = ["ITEM", "STAT", "CELL"]
        self.battle_dialogue = DialogueBox(pygame.Rect(50, 270, 540, 100))
        self.sprites = {
            "FROGGIT": create_froggit_sprite(), 
            "WHIMSUN": create_whimsun_sprite(),
            "MOLDSMAL": create_froggit_sprite(), # Reusing sprite for now
            "TORIEL": create_toriel_sprite()
        }
        self.sub_menu_index = 0
        self.shake = 0 # Initialize shake safely

    def load_level(self, level_id, spawn_pos=None):
        if level_id == "boss_toriel":
            self.start_battle("TORIEL")
            return
            
        self.current_level = level_id; data = LEVELS[level_id]
        self.walls.empty(); self.portals.empty(); self.objects.empty()
        for w in data.get("walls", []): self.walls.add(Wall(*w))
        for p in data.get("portals", []): self.portals.add(Portal(*p))
        for o in data.get("objects", []): self.objects.add(ObjectSprite(*o))
        if spawn_pos: self.player.rect.topleft = spawn_pos

    def start_battle(self, specific_enemy=None):
        # Determine enemy before switching state
        if specific_enemy:
            enemy_type = specific_enemy
        else:
            if not LEVELS[self.current_level]["encounters"]: return 
            enemy_type = random.choice(LEVELS[self.current_level]["encounters"])
        
        # Safe to switch state now
        self.state = STATE_BATTLE; self.battle_state = BATTLE_DIALOGUE
        self.enemy = ENEMY_DATA[enemy_type].copy(); self.enemy["name"] = enemy_type
        
        # Use fallback sprite if specific one missing
        sprite_key = enemy_type if enemy_type in self.sprites else "FROGGIT"
        self.enemy_rect = self.sprites[sprite_key].get_rect(center=(SCREEN_WIDTH//2, 160))
        self.shake = 0; self.soul = Soul(); self.battle_box = pygame.Rect(32, 250, 576, 140)
        self.soul.rect.center = self.battle_box.center
        self.bullets = pygame.sprite.Group(); self.buttons = ["FIGHT", "ACT", "ITEM", "MERCY"]
        self.btn_idx = 0; self.battle_dialogue.start(f"{enemy_type} draws near!")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m: pass
            if self.state == STATE_STORY:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    self.story_index += 1
                    if self.story_index >= len(STORY_LINES):
                        self.state = STATE_TITLE
                        
            elif self.state == STATE_TITLE:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    self.state = STATE_OVERWORLD
                    self.load_level("ruins_start")

            elif self.state == STATE_OVERWORLD:
                if event.key == pygame.K_e:
                    self.state = STATE_OVERWORLD_MENU; self.menu_index = 0
            
            elif self.state == STATE_OVERWORLD_MENU:
                if event.key == pygame.K_e or event.key == pygame.K_x: self.state = STATE_OVERWORLD
                elif event.key == pygame.K_UP: self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN: self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    if self.menu_options[self.menu_index] == "ITEM" and self.inventory:
                        print(f"Used {self.inventory.pop(0)}"); self.hp = self.max_hp
            
            elif self.state == STATE_BATTLE: self.handle_battle_input(event)
            
            elif self.state == STATE_VICTORY:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    if not self.battle_dialogue.finished:
                        self.battle_dialogue.finished = True
                        self.battle_dialogue.displayed_text = self.battle_dialogue.full_text
                    else:
                        if self.enemy["name"] == "TORIEL":
                            self.state = STATE_ENDING
                        else:
                            self.state = STATE_OVERWORLD
                            self.player.steps = 0
                            
            elif self.state == STATE_ENDING:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    # Reset game or just quit
                    pygame.quit(); sys.exit()

    def handle_battle_input(self, event):
        # 1. Dialogue Phase (Enemy appeared, etc.)
        if self.battle_state == BATTLE_DIALOGUE:
            if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                if not self.battle_dialogue.finished:
                    self.battle_dialogue.finished = True
                    self.battle_dialogue.displayed_text = self.battle_dialogue.full_text
                else:
                    self.battle_state = BATTLE_MENU
                    self.battle_box = pygame.Rect(32, 250, 576, 140)

        # 2. Main Button Menu (FIGHT, ACT, ITEM, MERCY)
        elif self.battle_state == BATTLE_MENU:
            if event.key == pygame.K_LEFT: self.btn_idx = (self.btn_idx - 1) % 4
            elif event.key == pygame.K_RIGHT: self.btn_idx = (self.btn_idx + 1) % 4
            elif event.key == pygame.K_z or event.key == pygame.K_RETURN: 
                self.sub_menu_index = 0
                selected_btn = self.buttons[self.btn_idx]
                
                if selected_btn == "FIGHT":
                    self.battle_state = BATTLE_SELECT_ENEMY
                elif selected_btn == "ACT":
                    self.battle_state = BATTLE_SELECT_ENEMY # Act also starts by selecting enemy
                elif selected_btn == "ITEM":
                    if not self.inventory:
                         self.battle_dialogue.start("You have no items.")
                         self.battle_state = BATTLE_DIALOGUE
                         self.start_enemy_turn()
                    else:
                        self.battle_state = BATTLE_SELECT_ITEM
                elif selected_btn == "MERCY":
                    self.battle_state = BATTLE_SELECT_MERCY

        # 3. Select Enemy (For FIGHT or ACT)
        elif self.battle_state == BATTLE_SELECT_ENEMY:
            # Since there is only 1 enemy, press Z to confirm, X to back
            if event.key == pygame.K_x:
                self.battle_state = BATTLE_MENU
            elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                if self.buttons[self.btn_idx] == "FIGHT":
                    self.battle_state = BATTLE_PLAYER_ATTACK
                else: # ACT
                    self.battle_state = BATTLE_SELECT_ACT
                    self.sub_menu_index = 0

        # 4. Select Action (ACT)
        elif self.battle_state == BATTLE_SELECT_ACT:
            acts = self.enemy.get("acts", [])
            if event.key == pygame.K_x:
                self.battle_state = BATTLE_SELECT_ENEMY
            elif event.key == pygame.K_UP:
                self.sub_menu_index = (self.sub_menu_index - 1) % len(acts)
            elif event.key == pygame.K_DOWN:
                self.sub_menu_index = (self.sub_menu_index + 1) % len(acts)
            elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                chosen_act = acts[self.sub_menu_index]
                self.battle_dialogue.start(f"* You {chosen_act}ed the {self.enemy['name']}.")
                self.battle_state = BATTLE_DIALOGUE
                self.start_enemy_turn()

        # 5. Select Item
        elif self.battle_state == BATTLE_SELECT_ITEM:
            if event.key == pygame.K_x:
                self.battle_state = BATTLE_MENU
            elif event.key == pygame.K_UP:
                self.sub_menu_index = (self.sub_menu_index - 1) % len(self.inventory)
            elif event.key == pygame.K_DOWN:
                self.sub_menu_index = (self.sub_menu_index + 1) % len(self.inventory)
            elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                item = self.inventory.pop(self.sub_menu_index)
                self.hp = min(self.max_hp, self.hp + 20) # Simple heal
                self.battle_dialogue.start(f"* You ate the {item}. HP maxed out.")
                self.battle_state = BATTLE_DIALOGUE
                self.start_enemy_turn()

        # 6. Mercy Menu
        elif self.battle_state == BATTLE_SELECT_MERCY:
            options = ["Spare", "Flee"]
            if event.key == pygame.K_x:
                self.battle_state = BATTLE_MENU
            elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                self.sub_menu_index = (self.sub_menu_index + 1) % 2
            elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                choice = options[self.sub_menu_index]
                if choice == "Spare":
                    self.battle_dialogue.start("* You spared the enemy.")
                    self.state = STATE_VICTORY
                else:
                    self.battle_dialogue.start("* You fled...")
                    self.state = STATE_OVERWORLD

        # 7. Player Attack Timing (simplified for now, just press Z)
        elif self.battle_state == BATTLE_PLAYER_ATTACK:
            if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                dmg = random.randint(10, 20); self.enemy["hp"] -= dmg; self.shake = 10
                self.battle_dialogue.start(f"You hit for {dmg} damage!")
                self.battle_state = BATTLE_DIALOGUE
                if self.enemy["hp"] <= 0:
                     self.battle_dialogue.start("YOU WON! You earned 10 XP and 20 Gold.")
                     self.state = STATE_VICTORY
                else: self.start_enemy_turn()

    def start_enemy_turn(self):
        self.battle_state = BATTLE_ENEMY_TURN; self.turn_timer = 180
        self.battle_box = pygame.Rect(240, 250, 160, 140)
        self.soul.rect.center = self.battle_box.center
        self.bullets.empty()

    def update(self):
        self.title_timer += 1
        if self.state == STATE_OVERWORLD:
            if self.player.update(self.walls):
                self.player.steps += 1
                if self.player.steps > 150 and random.randint(0, 100) < 2: self.start_battle()
            hits = pygame.sprite.spritecollide(self.player, self.portals, False)
            if hits: self.load_level(hits[0].dest_id, hits[0].spawn_pos)
        elif self.state == STATE_BATTLE:
            self.battle_dialogue.update()
            if self.shake > 0: self.shake = -self.shake * 0.8; 
            if abs(self.shake) < 1: self.shake = 0
            if self.battle_state == BATTLE_ENEMY_TURN:
                self.soul.update(self.battle_box); self.turn_timer -= 1
                if self.turn_timer % 12 == 0:
                    angle = random.randint(0, 360)
                    bx = self.battle_box.centerx + math.cos(math.radians(angle)) * 200
                    by = self.battle_box.centery + math.sin(math.radians(angle)) * 200
                    aim_angle = math.degrees(math.atan2(self.soul.rect.centery - by, self.soul.rect.centerx - bx))
                    self.bullets.add(Bullet(bx, by, aim_angle, 3))
                self.bullets.update()
                if self.soul.inv_frames == 0:
                    if pygame.sprite.spritecollide(self.soul, self.bullets, False):
                        self.hp -= 4; self.soul.inv_frames = 60
                        if self.hp <= 0: print("GAME OVER"); pygame.quit(); sys.exit()
                if self.turn_timer <= 0:
                    self.battle_state = BATTLE_DIALOGUE; self.battle_box = pygame.Rect(32, 250, 576, 140)
                    self.battle_dialogue.start(random.choice(self.enemy["lines"])); self.bullets.empty()
        elif self.state == STATE_VICTORY:
             self.battle_dialogue.update()

    def draw(self, surface):
        surface.fill(COLOR_BLACK)

        if self.state == STATE_STORY:
            draw_intro_scene(surface, self.story_index)
            if self.story_index < len(STORY_LINES) - 1:
                lines = STORY_LINES[self.story_index].split('\n')
                y_offset = 260 
                for line in lines:
                    txt = FONT_STORY.render(line, True, COLOR_WHITE)
                    surface.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, y_offset))
                    y_offset += 35
                hint = FONT_PIXEL.render("[Z] Next", True, COLOR_GRAY)
                surface.blit(hint, (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 40))
            else:
                self.state = STATE_TITLE

        elif self.state == STATE_TITLE:
            title_text = FONT_TITLE.render("CAT'S UNDERTALE ENGINE", True, COLOR_WHITE)
            surface.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
            if (self.title_timer // 30) % 2 == 0:
                press_text = FONT_STORY.render("[PRESS Z OR ENTER]", True, COLOR_YELLOW)
                surface.blit(press_text, (SCREEN_WIDTH//2 - press_text.get_width()//2, 300))
            pygame.draw.polygon(surface, COLOR_RED, [
                (320, 260), (300, 240), (300, 230), (310, 220), (320, 230), 
                (330, 220), (340, 230), (340, 240)
            ])
            credits = FONT_PIXEL.render("v1.5 - Python/Pygame", True, COLOR_GRAY)
            surface.blit(credits, (20, 440))

        elif self.state == STATE_OVERWORLD:
            self.walls.draw(surface)
            self.objects.draw(surface)
            surface.blit(self.player.image, self.player.rect)
            txt = FONT_PIXEL.render(self.current_level.replace("_", " ").upper(), True, COLOR_GRAY)
            surface.blit(txt, (20, 20))
            inst = FONT_PIXEL.render("[Arrows] Move  [E] Menu", True, COLOR_WHITE)
            surface.blit(inst, (20, 440))

        elif self.state == STATE_OVERWORLD_MENU:
            self.walls.draw(surface)
            self.objects.draw(surface)
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); s.set_alpha(150); s.fill((0,0,0)); surface.blit(s, (0,0))
            menu_rect = pygame.Rect(30, 30, 150, 220)
            pygame.draw.rect(surface, COLOR_WHITE, menu_rect, 2); pygame.draw.rect(surface, COLOR_BLACK, menu_rect.inflate(-4,-4))
            y = 50
            for i, opt in enumerate(self.menu_options):
                color = COLOR_YELLOW if i == self.menu_index else COLOR_WHITE
                surface.blit(FONT_PIXEL.render(("❤ " if i == self.menu_index else "  ") + opt, True, color), (40, y))
                y += 40
            stat_rect = pygame.Rect(30, 260, 150, 150)
            pygame.draw.rect(surface, COLOR_WHITE, stat_rect, 2); pygame.draw.rect(surface, COLOR_BLACK, stat_rect.inflate(-4,-4))
            for i, s in enumerate([f"NAME: {self.name}", f"LV: {self.lv}", f"HP: {self.hp}/{self.max_hp}", f"G: {self.gold}"]):
                 surface.blit(FONT_PIXEL.render(s, True, COLOR_WHITE), (40, 275 + i*30))

        elif self.state == STATE_BATTLE or self.state == STATE_VICTORY:
            shake_x = random.randint(-int(self.shake), int(self.shake)) if self.shake > 0 else 0
            en_rect = self.enemy_rect.copy(); en_rect.x += shake_x
            # Safe sprite retrieval
            sprite_key = self.enemy["name"]
            if sprite_key not in self.sprites: sprite_key = "FROGGIT"
            surface.blit(self.sprites[sprite_key], en_rect)
            
            pygame.draw.rect(surface, COLOR_WHITE, self.battle_box, 6) # Thicker border
            pygame.draw.rect(surface, COLOR_BLACK, self.battle_box.inflate(-6, -6))
            
            # Draw content inside battle box
            if self.battle_state == BATTLE_DIALOGUE or self.state == STATE_VICTORY: 
                self.battle_dialogue.draw(surface)
            elif self.battle_state == BATTLE_ENEMY_TURN: 
                self.soul.draw(surface); self.bullets.draw(surface)
            
            # Menu Drawing Logic
            elif self.battle_state == BATTLE_SELECT_ENEMY:
                # Draw enemy name
                txt = FONT_BATTLE_TEXT.render("* " + self.enemy["name"], True, COLOR_WHITE)
                surface.blit(txt, (self.battle_box.x + 60, self.battle_box.y + 30))
                # Draw Soul
                surface.blit(self.soul.image, (self.battle_box.x + 30, self.battle_box.y + 35))
            
            elif self.battle_state == BATTLE_SELECT_ACT:
                acts = self.enemy.get("acts", [])
                for i, act in enumerate(acts):
                    col = i % 2
                    row = i // 2
                    x = self.battle_box.x + 60 + col * 250
                    y = self.battle_box.y + 30 + row * 40
                    txt = FONT_BATTLE_TEXT.render("* " + act, True, COLOR_WHITE)
                    surface.blit(txt, (x, y))
                    if i == self.sub_menu_index:
                         surface.blit(self.soul.image, (x - 30, y + 5))
            
            elif self.battle_state == BATTLE_SELECT_ITEM:
                for i, item in enumerate(self.inventory):
                    col = i % 2
                    row = i // 2
                    x = self.battle_box.x + 60 + col * 250
                    y = self.battle_box.y + 30 + row * 40
                    txt = FONT_BATTLE_TEXT.render("* " + item, True, COLOR_WHITE)
                    surface.blit(txt, (x, y))
                    if i == self.sub_menu_index:
                         surface.blit(self.soul.image, (x - 30, y + 5))

            elif self.battle_state == BATTLE_SELECT_MERCY:
                options = ["Spare", "Flee"]
                for i, opt in enumerate(options):
                    x = self.battle_box.x + 60
                    y = self.battle_box.y + 30 + i * 40
                    txt = FONT_BATTLE_TEXT.render("* " + opt, True, COLOR_WHITE)
                    surface.blit(txt, (x, y))
                    if i == self.sub_menu_index:
                         surface.blit(self.soul.image, (x - 30, y + 5))

            # Bottom UI Buttons
            btn_y = 432
            for i, btn in enumerate(self.buttons):
                color = COLOR_UI_ORANGE if (i != self.btn_idx or self.battle_state != BATTLE_MENU) else COLOR_YELLOW
                pygame.draw.rect(surface, color, (32 + i * 152, btn_y, 140, 42), 2)
                img = FONT_UI.render(btn, True, color)
                surface.blit(img, (32 + i * 152 + (140 - img.get_width())//2, btn_y + 8))
                if i == self.btn_idx and self.battle_state == BATTLE_MENU:
                    surface.blit(self.soul.image, (32 + i * 152 + 10, btn_y + 12))

            name = FONT_PIXEL.render(f"{self.name}   LV {self.lv}", True, COLOR_WHITE)
            surface.blit(name, (32, 400))
            hp_label = FONT_PIXEL.render("HP", True, COLOR_WHITE); surface.blit(hp_label, (220, 400))
            pygame.draw.rect(surface, COLOR_RED, (260, 400, self.max_hp * 2, 20))
            if self.hp > 0: pygame.draw.rect(surface, COLOR_YELLOW, (260, 400, self.hp * 2, 20))
            hp_txt = FONT_PIXEL.render(f"{self.hp} / {self.max_hp}", True, COLOR_WHITE)
            surface.blit(hp_txt, (270 + self.max_hp*2, 400))
            
        elif self.state == STATE_ENDING:
            surface.blit(FONT_TITLE.render("DEMO COMPLETE", True, COLOR_YELLOW), (180, 200))
            surface.blit(FONT_STORY.render("Thank you for playing!", True, COLOR_WHITE), (180, 250))

game = Game()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        game.handle_input(event)
    game.update()
    game.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit(); sys.exit()
