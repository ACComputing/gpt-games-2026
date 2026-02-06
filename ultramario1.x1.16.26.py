import pygame
import math
import sys
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 400             # Wider FOV for first-person (N64 SM64 ~73 degree equiv)
VIEW_DISTANCE = 5000

# Game Settings
MOVE_SPEED = 12
JUMP_FORCE = 18
GRAVITY = 0.9
STAR_TOTAL = 120

# SM64 Lakitu First-Person Camera Settings
MOUSE_SENS_X = 0.003        # Horizontal mouse sensitivity
MOUSE_SENS_Y = 0.002        # Vertical mouse sensitivity
PITCH_MIN = -1.2             # Look down limit (~70 deg)
PITCH_MAX = 1.0              # Look up limit (~57 deg)
CAM_LERP_POS = 0.18         # Lakitu position smoothing (SM64 = ~0.1-0.2)
CAM_LERP_YAW = 0.25         # Lakitu yaw smoothing
CAM_LERP_PITCH = 0.25       # Lakitu pitch smoothing
EYE_HEIGHT = 38              # Mario's eye level above his Y pos
HEAD_BOB_SPEED = 10.0        # Head bob frequency when walking
HEAD_BOB_AMOUNT = 3.0        # Head bob amplitude
MOVE_ACCEL = 1.8             # SM64-style acceleration
MOVE_DECEL = 0.85            # SM64-style friction/deceleration
MAX_SPEED = 14               # Max ground speed
SPRINT_MULT = 1.6            # Sprint multiplier (shift)
# Analog-style turning when not using mouse
KEY_TURN_SPEED = 0.06        # Keyboard rotation speed (C-buttons equivalent)

# --- COLORS ---
DD_SKY_TOP = (26, 26, 77)
DD_SKY_BOT = (0, 0, 0)
DD_GAME_SKY = (20, 20, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
BLUE = (0, 0, 205)
SKIN = (255, 204, 153)
BROWN = (139, 69, 19)
MUSTACHE_BLACK = (20, 20, 20)
BUTTON_GOLD = (255, 215, 0)
EYE_BLUE = (0, 128, 255)
YELLOW = (255, 255, 0)
METAL_GREY = (160, 170, 180)
CHECKER_LIGHT = (50, 200, 50)
CHECKER_DARK = (30, 140, 30)
DARK_GREY = (80, 80, 80)
LIGHT_GREY = (200, 200, 200)
ORANGE = (255, 140, 0)
CYAN = (0, 200, 200)
MAGENTA = (200, 0, 200)
DEEP_BLUE = (0, 0, 120)
SAND = (210, 180, 120)
SNOW_WHITE = (230, 240, 255)
ICE_BLUE = (150, 200, 255)
LAVA_RED = (200, 40, 0)
LAVA_ORANGE = (255, 100, 0)
WATER_BLUE = (40, 80, 200)
WATER_LIGHT = (60, 120, 220)
DARK_BROWN = (80, 40, 10)
LIGHT_BROWN = (180, 120, 60)
STONE_GREY = (140, 140, 140)
DARK_STONE = (100, 100, 100)
PURPLE = (120, 40, 180)
DARK_PURPLE = (60, 20, 90)
DARK_GREEN = (20, 80, 20)
BRIGHT_GREEN = (80, 220, 80)
SKY_BLUE = (100, 160, 255)
PINK = (255, 150, 180)
CASTLE_WALL = (220, 200, 170)
CASTLE_ROOF = (180, 40, 40)
CASTLE_DOOR = (120, 80, 40)
PAINTING_FRAME = (160, 120, 40)
CARPET_RED = (160, 20, 30)
FLOOR_TILE = (180, 170, 150)
FLOOR_TILE_ALT = (160, 150, 130)
RAINBOW_R = (255, 50, 50)
RAINBOW_O = (255, 140, 40)
RAINBOW_Y = (255, 230, 40)
RAINBOW_G = (40, 200, 40)
RAINBOW_B = (40, 100, 255)
RAINBOW_P = (140, 40, 200)
COBWEB_GREY = (180, 180, 180)
GHOST_WHITE = (220, 220, 240)
PIPE_GREEN = (40, 160, 40)
CLOCK_GOLD = (180, 150, 40)
MOSS_GREEN = (60, 120, 40)
DOCK_WOOD = (140, 100, 60)
CLOUD_WHITE = (240, 245, 255)
TOWER_STONE = (150, 140, 130)

# --- 3D ENGINE ---

class Vector3:
    __slots__ = ['x', 'y', 'z']
    def __init__(self, x, y, z):
        self.x = x; self.y = y; self.z = z

class Face:
    __slots__ = ['indices', 'color', 'avg_z', 'normal']
    def __init__(self, indices, color):
        self.indices = indices; self.color = color; self.avg_z = 0; self.normal = None

class Mesh:
    def __init__(self, x=0, y=0, z=0):
        self.x = x; self.y = y; self.z = z
        self.vertices = []; self.faces = []; self.yaw = 0

    def add_cube(self, w, h, d, ox, oy, oz, color):
        si = len(self.vertices)
        hw, hh, hd = w/2, h/2, d/2
        corners = [
            (-hw,-hh,-hd),(hw,-hh,-hd),(hw,hh,-hd),(-hw,hh,-hd),
            (-hw,-hh,hd),(hw,-hh,hd),(hw,hh,hd),(-hw,hh,hd)
        ]
        for cx, cy, cz in corners:
            self.vertices.append(Vector3(cx+ox, cy+oy, cz+oz))
        cube_faces = [
            ([0,1,2,3],color),([5,4,7,6],color),([4,0,3,7],color),
            ([1,5,6,2],color),([3,2,6,7],color),([4,5,1,0],color)
        ]
        for fi, fc in cube_faces:
            shifted = [i+si for i in fi]
            face = Face(shifted, fc)
            v0=self.vertices[shifted[0]]; v1=self.vertices[shifted[1]]; v2=self.vertices[shifted[2]]
            ax,ay,az = v1.x-v0.x,v1.y-v0.y,v1.z-v0.z
            bx,by,bz = v2.x-v0.x,v2.y-v0.y,v2.z-v0.z
            nx=ay*bz-az*by; ny=az*bx-ax*bz; nz=ax*by-ay*bx
            l=math.sqrt(nx*nx+ny*ny+nz*nz)
            face.normal=(nx/l,ny/l,nz/l) if l!=0 else (0,0,1)
            self.faces.append(face)

    def add_ramp(self, w, h, d, ox, oy, oz, color):
        """Sloped surface - front is higher"""
        si = len(self.vertices)
        hw, hd = w/2, d/2
        # Bottom 4 verts (y=0)
        self.vertices.append(Vector3(-hw+ox, oy, -hd+oz))
        self.vertices.append(Vector3(hw+ox, oy, -hd+oz))
        self.vertices.append(Vector3(hw+ox, oy, hd+oz))
        self.vertices.append(Vector3(-hw+ox, oy, hd+oz))
        # Top 2 verts (front raised)
        self.vertices.append(Vector3(-hw+ox, oy+h, -hd+oz))
        self.vertices.append(Vector3(hw+ox, oy+h, -hd+oz))
        # Slope face
        face = Face([si+4, si+5, si+2, si+3], color)
        face.normal = (0, 0.7, -0.7)
        self.faces.append(face)
        # Front face
        face2 = Face([si, si+1, si+5, si+4], color)
        face2.normal = (0, 0, -1)
        self.faces.append(face2)

    def add_cylinder_approx(self, radius, height, ox, oy, oz, color, segments=8):
        """Approximate cylinder with segments"""
        si = len(self.vertices)
        # Bottom and top rings
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            cx = math.cos(angle) * radius + ox
            cz = math.sin(angle) * radius + oz
            self.vertices.append(Vector3(cx, oy, cz))
            self.vertices.append(Vector3(cx, oy + height, cz))
        # Side faces
        for i in range(segments):
            j = (i + 1) % segments
            b0 = si + i * 2
            t0 = si + i * 2 + 1
            b1 = si + j * 2
            t1 = si + j * 2 + 1
            face = Face([b0, b1, t1, t0], color)
            face.normal = (0, 0, 1)
            self.faces.append(face)

    def add_pyramid(self, base_w, height, ox, oy, oz, color):
        """Simple pyramid"""
        si = len(self.vertices)
        hw = base_w / 2
        self.vertices.append(Vector3(-hw+ox, oy, -hw+oz))
        self.vertices.append(Vector3(hw+ox, oy, -hw+oz))
        self.vertices.append(Vector3(hw+ox, oy, hw+oz))
        self.vertices.append(Vector3(-hw+ox, oy, hw+oz))
        self.vertices.append(Vector3(ox, oy+height, oz))  # apex
        for tri in [(0,1,4),(1,2,4),(2,3,4),(3,0,4)]:
            face = Face([si+t for t in tri], color)
            face.normal = (0, 0.7, 0.7)
            self.faces.append(face)


# ================================================================
# MARIO CHARACTER
# ================================================================
class Mario(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.dy = 0; self.is_jumping = False
        self.star_count = 0
        self.coins = 0
        self.lives = 4
        self.health = 8
        self.build_model()

    def build_model(self):
        self.add_cube(10,8,14,-6,-25,-2,BROWN)
        self.add_cube(10,8,14,6,-25,-2,BROWN)
        self.add_cube(8,12,8,-6,-15,0,BLUE)
        self.add_cube(8,12,8,6,-15,0,BLUE)
        self.add_cube(20,10,14,0,-4,0,BLUE)
        self.add_cube(22,14,14,0,8,0,RED)
        self.add_cube(2,2,1,-5,4,-8,BUTTON_GOLD)
        self.add_cube(2,2,1,5,4,-8,BUTTON_GOLD)
        self.add_cube(8,8,8,-16,12,0,RED)
        self.add_cube(6,12,6,-16,2,0,RED)
        self.add_cube(7,7,7,-16,-8,0,WHITE)
        self.add_cube(8,8,8,16,12,0,RED)
        self.add_cube(6,12,6,16,2,0,RED)
        self.add_cube(7,7,7,16,-8,0,WHITE)
        self.add_cube(18,16,18,0,22,0,SKIN)
        self.add_cube(20,6,20,0,32,0,RED)
        self.add_cube(24,2,24,0,29,-4,RED)
        self.add_cube(4,4,4,0,22,-10,SKIN)
        self.add_cube(10,3,2,0,18,-10,MUSTACHE_BLACK)
        self.add_cube(4,8,4,-9,22,-2,BROWN)
        self.add_cube(4,8,4,9,22,-2,BROWN)
        self.add_cube(18,10,6,0,22,8,BROWN)
        self.add_cube(4,4,1,-6,24,-9,WHITE)
        self.add_cube(2,2,1,-5,24,-10,EYE_BLUE)
        self.add_cube(4,4,1,6,24,-9,WHITE)
        self.add_cube(2,2,1,5,24,-10,EYE_BLUE)

    def update(self, floor_y=0):
        self.dy -= GRAVITY
        self.y += self.dy
        if self.y < floor_y:
            self.y = floor_y
            self.dy = 0
            self.is_jumping = False


# ================================================================
# COLLECTIBLE ITEMS
# ================================================================
class Star(Mesh):
    def __init__(self, x, y, z, star_id=0):
        super().__init__(x, y, z)
        self.star_id = star_id
        self.collected = False
        self.add_cube(10,40,10,0,0,0,YELLOW)
        self.add_cube(40,10,10,0,0,0,YELLOW)
        self.add_cube(10,10,40,0,0,0,YELLOW)

class Coin(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.collected = False
        self.add_cube(8,12,3,0,0,0,YELLOW)
        self.add_cube(4,8,4,0,0,0,BUTTON_GOLD)

class RedCoin(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.collected = False
        self.add_cube(8,12,3,0,0,0,RED)
        self.add_cube(4,8,4,0,0,0,ORANGE)


# ================================================================
# PAINTING / PORTAL (level entry)
# ================================================================
class Painting:
    def __init__(self, x, y, z, level_id, label, color, req_stars=0):
        self.x = x; self.y = y; self.z = z
        self.level_id = level_id
        self.label = label
        self.color = color
        self.req_stars = req_stars
        self.mesh = Mesh(x, y, z)
        # Frame
        self.mesh.add_cube(80, 80, 8, 0, 0, 0, PAINTING_FRAME)
        # Canvas
        self.mesh.add_cube(70, 70, 4, 0, 0, -3, color)


# ================================================================
# LEVEL BUILDERS
# ================================================================

def build_castle_grounds():
    """Castle Grounds - exterior courtyard, moat, bridge, castle front"""
    m = Mesh()
    # Main ground
    for x in range(-8, 8):
        for z in range(-8, 8):
            color = CHECKER_LIGHT if (x+z)%2==0 else CHECKER_DARK
            m.add_cube(200,10,200, x*200,-5, z*200, color)
    # Moat (water around castle)
    for i in range(-4, 5):
        m.add_cube(200, 6, 200, i*200, -8, -800, WATER_BLUE)
        m.add_cube(200, 6, 200, i*200, -8, 800, WATER_BLUE)
    for i in range(-4, 5):
        m.add_cube(200, 6, 200, -800, -8, i*200, WATER_BLUE)
        m.add_cube(200, 6, 200, 800, -8, i*200, WATER_BLUE)
    # Bridge
    m.add_cube(200, 20, 400, 0, 5, -600, DARK_BROWN)
    m.add_cube(20, 60, 20, -90, 30, -800, DARK_BROWN)
    m.add_cube(20, 60, 20, 90, 30, -800, DARK_BROWN)
    m.add_cube(20, 60, 20, -90, 30, -400, DARK_BROWN)
    m.add_cube(20, 60, 20, 90, 30, -400, DARK_BROWN)
    # Castle front wall
    m.add_cube(600, 400, 60, 0, 200, -1000, CASTLE_WALL)
    # Castle towers
    for tx in [-350, 350]:
        m.add_cube(120, 500, 120, tx, 250, -1000, CASTLE_WALL)
        m.add_pyramid(140, 100, tx, 500, -1000, CASTLE_ROOF)
    # Castle door
    m.add_cube(100, 150, 10, 0, 75, -968, CASTLE_DOOR)
    # Castle roof
    m.add_cube(600, 30, 200, 0, 400, -1050, CASTLE_ROOF)
    # Windows
    for wx in [-150, 150]:
        m.add_cube(50, 60, 5, wx, 280, -968, SKY_BLUE)
    # Stained glass (big center window)
    m.add_cube(80, 100, 5, 0, 320, -968, (200, 100, 255))
    # Trees around courtyard
    for tx, tz in [(-500, 200), (500, 200), (-500, -200), (500, -200),
                   (-700, 500), (700, 500), (-700, -500), (700, -500)]:
        m.add_cube(30, 80, 30, tx, 40, tz, DARK_BROWN)
        m.add_cube(80, 60, 80, tx, 100, tz, DARK_GREEN)
        m.add_cube(60, 40, 60, tx, 140, tz, BRIGHT_GREEN)
    # Cannon area
    m.add_cube(40, 20, 40, -600, 10, 600, DARK_GREY)
    m.add_cube(20, 30, 20, -600, 30, 600, METAL_GREY)
    # Waterfall
    m.add_cube(100, 200, 20, 400, 100, -1050, WATER_LIGHT)
    # Hills
    for hx, hz, hs in [(-1200, 0, 300), (1200, 0, 300), (0, 0, 1200)]:
        m.add_cube(hs*2, hs, hs*2, hx, hs/2-10, hz, DARK_GREEN)
    return m

def build_castle_interior_f1():
    """Castle Interior - First Floor / Main Hall"""
    m = Mesh()
    # Floor
    for x in range(-5, 5):
        for z in range(-5, 5):
            color = FLOOR_TILE if (x+z)%2==0 else FLOOR_TILE_ALT
            m.add_cube(200, 10, 200, x*200, -5, z*200, color)
    # Red carpet
    for z in range(-4, 4):
        m.add_cube(120, 2, 200, 0, 1, z*200, CARPET_RED)
    # Walls
    m.add_cube(2000, 400, 40, 0, 200, -1000, CASTLE_WALL)
    m.add_cube(2000, 400, 40, 0, 200, 1000, CASTLE_WALL)
    m.add_cube(40, 400, 2000, -1000, 200, 0, CASTLE_WALL)
    m.add_cube(40, 400, 2000, 1000, 200, 0, CASTLE_WALL)
    # Ceiling
    m.add_cube(2000, 20, 2000, 0, 400, 0, CASTLE_WALL)
    # Pillars
    for px, pz in [(-400,-400),(400,-400),(-400,400),(400,400)]:
        m.add_cube(60, 400, 60, px, 200, pz, WHITE)
    # Stairs to upper floor
    for i in range(8):
        m.add_cube(300, 20, 60, 0, i*25, -600-i*60, STONE_GREY)
    # Star doors
    m.add_cube(100, 200, 20, -800, 100, 0, BUTTON_GOLD)  # 1-star door
    m.add_cube(100, 200, 20, 800, 100, 0, BUTTON_GOLD)    # 3-star door
    m.add_cube(200, 200, 20, 0, 100, -980, BUTTON_GOLD)    # Upstairs door
    # Paintings (level portals)
    # Bob-omb Battlefield painting (left wall)
    m.add_cube(80, 80, 8, -978, 140, -300, BRIGHT_GREEN)
    m.add_cube(70, 70, 4, -978, 140, -300, (100, 200, 100))
    # Whomp's Fortress painting
    m.add_cube(80, 80, 8, -978, 140, -500, STONE_GREY)
    m.add_cube(70, 70, 4, -978, 140, -500, (150, 150, 140))
    # Jolly Roger Bay painting
    m.add_cube(80, 80, 8, -978, 140, -700, WATER_BLUE)
    m.add_cube(70, 70, 4, -978, 140, -700, (80, 140, 220))
    # Cool Cool Mountain painting
    m.add_cube(80, 80, 8, 978, 140, -300, SNOW_WHITE)
    m.add_cube(70, 70, 4, 978, 140, -300, (200, 220, 255))
    # Big Boo's Haunt (courtyard access)
    m.add_cube(80, 80, 8, 978, 140, -500, DARK_PURPLE)
    m.add_cube(70, 70, 4, 978, 140, -500, (80, 40, 100))
    # Basement trapdoor
    m.add_cube(150, 5, 150, 600, -2, 600, DARK_GREY)
    # Peach stained glass light
    m.add_cube(100, 100, 5, 0, 320, -998, (255, 200, 220))
    # Toad NPCs (simple cubes)
    for tx, tz in [(-200, 200), (200, -300), (-400, 0)]:
        m.add_cube(20, 30, 20, tx, 15, tz, WHITE)
        m.add_cube(24, 12, 24, tx, 38, tz, RED)
    return m

def build_castle_basement():
    """Castle Basement - dark corridors, leads to more levels"""
    m = Mesh()
    # Dark floor
    for x in range(-6, 6):
        for z in range(-6, 6):
            color = DARK_STONE if (x+z)%2==0 else DARK_GREY
            m.add_cube(200, 10, 200, x*200, -5, z*200, color)
    # Walls
    m.add_cube(2400, 300, 40, 0, 150, -1200, DARK_STONE)
    m.add_cube(2400, 300, 40, 0, 150, 1200, DARK_STONE)
    m.add_cube(40, 300, 2400, -1200, 150, 0, DARK_STONE)
    m.add_cube(40, 300, 2400, 1200, 150, 0, DARK_STONE)
    m.add_cube(2400, 20, 2400, 0, 300, 0, DARK_STONE)
    # Corridor walls (maze-like)
    m.add_cube(40, 200, 600, -400, 100, -300, DARK_STONE)
    m.add_cube(40, 200, 600, 400, 100, 300, DARK_STONE)
    m.add_cube(600, 200, 40, 0, 100, -400, DARK_STONE)
    # Lava pool area
    m.add_cube(400, 4, 400, -600, -3, -600, LAVA_RED)
    m.add_cube(400, 2, 400, -600, -1, -600, LAVA_ORANGE)
    # Metal gate
    m.add_cube(200, 200, 10, 0, 100, -600, METAL_GREY)
    m.add_cube(10, 200, 10, -80, 100, -600, DARK_GREY)
    m.add_cube(10, 200, 10, 80, 100, -600, DARK_GREY)
    # Paintings
    # Hazy Maze Cave
    m.add_cube(80, 80, 8, -1178, 100, -400, DARK_GREEN)
    # Lethal Lava Land
    m.add_cube(80, 80, 8, -1178, 100, -600, LAVA_RED)
    # Shifting Sand Land
    m.add_cube(80, 80, 8, -1178, 100, -800, SAND)
    # Dire Dire Docks
    m.add_cube(80, 80, 8, 1178, 100, -400, DEEP_BLUE)
    # Metal Cap switch room entrance (green pipe)
    m.add_cube(50, 30, 50, 800, 15, 800, PIPE_GREEN)
    # Vanish Cap entrance (blue wall)
    m.add_cube(80, 80, 10, 600, 60, -1178, CYAN)
    return m

def build_castle_upper():
    """Castle Upper Floor - Floor 2"""
    m = Mesh()
    for x in range(-4, 4):
        for z in range(-4, 4):
            color = FLOOR_TILE if (x+z)%2==0 else FLOOR_TILE_ALT
            m.add_cube(200, 10, 200, x*200, -5, z*200, color)
    m.add_cube(1600, 350, 40, 0, 175, -800, CASTLE_WALL)
    m.add_cube(1600, 350, 40, 0, 175, 800, CASTLE_WALL)
    m.add_cube(40, 350, 1600, -800, 175, 0, CASTLE_WALL)
    m.add_cube(40, 350, 1600, 800, 175, 0, CASTLE_WALL)
    m.add_cube(1600, 20, 1600, 0, 350, 0, CASTLE_WALL)
    # Mirror room (Snowman's Land + Wet-Dry World)
    m.add_cube(80, 80, 8, -778, 100, -300, ICE_BLUE)
    m.add_cube(80, 80, 8, -778, 100, -500, WATER_LIGHT)
    # Tall Tall Mountain
    m.add_cube(80, 80, 8, 778, 100, -300, DARK_GREEN)
    # Tiny-Huge Island
    m.add_cube(80, 80, 8, 778, 100, -500, BRIGHT_GREEN)
    # Stairs to top floor
    for i in range(6):
        m.add_cube(200, 20, 60, 0, i*30, -500-i*60, STONE_GREY)
    # Clock room door (Tick Tock Clock)
    m.add_cube(80, 120, 10, 0, 60, -778, CLOCK_GOLD)
    # Rainbow Ride entrance (big star door)
    m.add_cube(120, 150, 10, 0, 75, -790, BUTTON_GOLD)
    return m

def build_castle_top():
    """Castle Top Floor / Wing Cap area"""
    m = Mesh()
    # Small room
    for x in range(-2, 2):
        for z in range(-2, 2):
            m.add_cube(200, 10, 200, x*200, -5, z*200, FLOOR_TILE)
    m.add_cube(800, 300, 40, 0, 150, -400, CASTLE_WALL)
    m.add_cube(800, 300, 40, 0, 150, 400, CASTLE_WALL)
    m.add_cube(40, 300, 800, -400, 150, 0, CASTLE_WALL)
    m.add_cube(40, 300, 800, 400, 150, 0, CASTLE_WALL)
    # Sunlight beam
    m.add_cube(100, 300, 100, 0, 150, 0, (255, 255, 200))
    # Wing cap switch
    m.add_cube(60, 20, 60, 0, 10, 0, RED)
    m.add_cube(40, 40, 40, 0, 30, 0, YELLOW)
    return m


# ================================================================
# 15 MAIN COURSES
# ================================================================

def build_bob_omb_battlefield():
    """Course 1: Bob-omb Battlefield"""
    m = Mesh()
    # Green fields
    for x in range(-6, 6):
        for z in range(-6, 6):
            c = CHECKER_LIGHT if (x+z)%2==0 else CHECKER_DARK
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Mountain (center)
    m.add_cube(400,200,400, 0,100,0, DARK_BROWN)
    m.add_cube(300,150,300, 0,275,0, BROWN)
    m.add_cube(200,100,200, 0,400,0, STONE_GREY)
    m.add_pyramid(160, 80, 0, 450, 0, DARK_GREY)
    # King Bob-omb platform at top
    m.add_cube(100,10,100, 0,490,0, DARK_GREY)
    # Chain Chomp post
    m.add_cube(10,40,10, -400,20,-200, DARK_GREY)
    m.add_cube(30,30,30, -400,50,-200, BLACK)
    # Bridges
    m.add_cube(200,10,40, -200,50,-300, DARK_BROWN)
    m.add_cube(200,10,40, 200,50,300, DARK_BROWN)
    # Bob-omb buddies (cannons)
    for cx,cz in [(500,-400),(-500,400)]:
        m.add_cube(30,15,30, cx,8,cz, DARK_GREY)
        m.add_cube(15,25,15, cx,20,cz, METAL_GREY)
    # Water area
    m.add_cube(400,4,200, 400,-3,300, WATER_BLUE)
    # Gates
    m.add_cube(10,60,80, -300,30,-100, METAL_GREY)
    # Trees
    for tx,tz in [(-600,200),(600,-200),(-200,500),(300,-500)]:
        m.add_cube(20,60,20, tx,30,tz, DARK_BROWN)
        m.add_cube(60,40,60, tx,75,tz, DARK_GREEN)
    # Stars
    stars = [Star(0, 500, 0, 0), Star(500, 20, -400, 1), Star(-400, 30, 500, 2)]
    coins = [Coin(x*100, 10, z*100) for x,z in [(-2,2),(0,3),(2,2),(1,-1),(-1,-2)]]
    return m, stars, coins

def build_whomps_fortress():
    """Course 2: Whomp's Fortress"""
    m = Mesh()
    # Base platform
    m.add_cube(600,20,600, 0,-5,0, STONE_GREY)
    # Main fortress rising platforms
    for i in range(5):
        m.add_cube(500-i*80, 40, 500-i*80, 0, i*60+20, 0, TOWER_STONE)
    # Whomp at top
    m.add_cube(60,100,20, 0,320,0, STONE_GREY)
    m.add_cube(40,20,20, -30,340,0, STONE_GREY)
    m.add_cube(40,20,20, 30,340,0, STONE_GREY)
    # Ramps/slopes
    m.add_cube(80,10,200, -200,30,-100, STONE_GREY)
    m.add_cube(80,10,200, -200,70,-300, STONE_GREY)
    # Thwomps (blocks)
    m.add_cube(50,50,50, 200,80,100, DARK_GREY)
    # Rotating platforms
    m.add_cube(120,10,40, 100,120,200, DARK_BROWN)
    # Piranha plants (green tubes)
    for px,pz in [(150,-200),(-150,200)]:
        m.add_cube(30,40,30, px,20,pz, PIPE_GREEN)
    # Tower
    m.add_cube(80,200,80, -250,100,-250, TOWER_STONE)
    m.add_cube(100,20,100, -250,200,-250, CASTLE_ROOF)
    stars = [Star(0, 340, 0, 0), Star(-250, 220, -250, 1)]
    coins = [Coin(i*60-150, 40, i*40) for i in range(6)]
    return m, stars, coins

def build_jolly_roger_bay():
    """Course 3: Jolly Roger Bay"""
    m = Mesh()
    # Sandy shore
    for x in range(-4, 4):
        for z in range(-2, 2):
            m.add_cube(200,10,200, x*200,-5,z*200-600, SAND)
    # Water body (large)
    for x in range(-6, 6):
        for z in range(-6, 6):
            m.add_cube(200,6,200, x*200,-3,z*200, WATER_BLUE)
    # Underwater cave floor
    m.add_cube(400,10,400, 0,-200,0, DARK_STONE)
    # Sunken ship
    m.add_cube(100,60,300, 200,-120,200, DARK_BROWN)
    m.add_cube(80,40,200, 200,-80,200, BROWN)
    m.add_cube(10,80,10, 200,-40,200, DARK_BROWN) # mast
    # Pirate cave
    m.add_cube(200,100,200, -400,-80,-300, DARK_STONE)
    m.add_cube(180,80,180, -400,-60,-300, DARK_GREY)
    # Clam shells
    for cx,cz in [(100,-100),(-200,0),(300,100)]:
        m.add_cube(30,10,30, cx,-190,cz, LIGHT_GREY)
        m.add_cube(28,20,15, cx,-180,cz, PINK)
    # Docks
    m.add_cube(300,10,60, -200,5,-500, DOCK_WOOD)
    m.add_cube(20,30,20, -350,15,-500, DOCK_WOOD)
    m.add_cube(20,30,20, -50,15,-500, DOCK_WOOD)
    # Eels area (dark cave entrance)
    m.add_cube(80,80,40, 500,-100,400, BLACK)
    stars = [Star(200,-60,200,0), Star(-400,-40,-300,1), Star(-200,20,-500,2)]
    coins = [Coin(x*80, -180, z*80) for x,z in [(-1,0),(0,1),(1,0),(0,-1)]]
    return m, stars, coins

def build_cool_cool_mountain():
    """Course 4: Cool, Cool Mountain"""
    m = Mesh()
    # Mountain peak
    m.add_cube(200,20,200, 0,600,0, SNOW_WHITE)
    # Descending platforms/slopes
    for i in range(10):
        w = 200 + i*60
        m.add_cube(w,20,w, 0, 600-i*60, 0, SNOW_WHITE if i%2==0 else ICE_BLUE)
    # Slide entrance (chimney)
    m.add_cube(40,60,40, 0,640,0, DARK_BROWN)
    # Slide path (series of platforms)
    for i in range(15):
        angle = i * 0.4
        sx = math.cos(angle) * (200 + i*30)
        sz = math.sin(angle) * (200 + i*30)
        m.add_cube(80,10,80, sx, 550-i*35, sz, ICE_BLUE)
    # Cabin at bottom
    m.add_cube(120,80,120, -300,40,-400, DARK_BROWN)
    m.add_cube(130,10,130, -300,80,-400, CASTLE_ROOF)
    # Snowman
    m.add_cube(60,60,60, 200,30,300, SNOW_WHITE)
    m.add_cube(40,40,40, 200,80,300, SNOW_WHITE)
    m.add_cube(8,8,8, 200,90,275, BLACK)
    # Ice bridge
    m.add_cube(200,10,40, 100,100,0, ICE_BLUE)
    # Penguin
    m.add_cube(20,30,20, -50,620,50, BLACK)
    m.add_cube(20,10,20, -50,640,50, WHITE)
    # Base area
    for x in range(-4,4):
        for z in range(-4,4):
            m.add_cube(200,10,200, x*200,-5,z*200, SNOW_WHITE)
    stars = [Star(0,620,0,0), Star(-300,100,-400,1), Star(200,100,300,2)]
    coins = [Coin(math.cos(i*0.4)*(200+i*30), 560-i*35, math.sin(i*0.4)*(200+i*30)) for i in range(0,15,3)]
    return m, stars, coins

def build_big_boos_haunt():
    """Course 5: Big Boo's Haunt"""
    m = Mesh()
    # Courtyard (dark)
    for x in range(-4,4):
        for z in range(-4,4):
            c = DARK_GREY if (x+z)%2==0 else BLACK
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Haunted mansion
    m.add_cube(400,300,400, 0,150,0, DARK_PURPLE)
    # Roof
    m.add_pyramid(450, 150, 0, 300, 0, DARK_GREY)
    # Windows (eerie glow)
    for wx,wy in [(-120,200),(120,200),(-120,100),(120,100)]:
        m.add_cube(50,40,5, wx,wy,-200, (100,255,100))
    # Door
    m.add_cube(60,120,5, 0,60,-200, DARK_BROWN)
    # Interior rooms (visible through door)
    m.add_cube(350,10,350, 0,-2,0, DARK_STONE)
    # Graveyard (outside)
    for gx,gz in [(-500,-200),(-500,-400),(-600,-300),(500,200),(500,400)]:
        m.add_cube(30,40,10, gx,20,gz, STONE_GREY)
        m.add_cube(40,5,15, gx,-2,gz, DARK_BROWN)
    # Boo (ghost block)
    m.add_cube(40,40,40, 100,100,300, GHOST_WHITE)
    m.add_cube(8,8,4, 86,108,282, BLACK)
    m.add_cube(8,8,4, 114,108,282, BLACK)
    # Cobwebs
    m.add_cube(80,2,80, -100,250,0, COBWEB_GREY)
    m.add_cube(60,2,60, 100,250,100, COBWEB_GREY)
    # Balcony
    m.add_cube(200,10,60, 0,200,-230, DARK_STONE)
    # Secret library bookshelf
    m.add_cube(20,100,60, -180,50,150, DARK_BROWN)
    m.add_cube(20,100,60, -180,50,100, BROWN)
    # Merry-go-round area (basement)
    m.add_cube(200,5,200, 0,-100,300, DARK_STONE)
    m.add_cube(100,30,100, 0,-85,300, DARK_BROWN)
    stars = [Star(0,310,0,0), Star(100,120,300,1), Star(0,-70,300,2)]
    coins = [Coin(gx,30,gz) for gx,gz in [(-500,-200),(500,200),(-200,0),(200,0)]]
    return m, stars, coins

def build_hazy_maze_cave():
    """Course 6: Hazy Maze Cave"""
    m = Mesh()
    # Cave floor (dark)
    for x in range(-6,6):
        for z in range(-6,6):
            c = DARK_STONE if (x+z)%2==0 else DARK_BROWN
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Cave ceiling
    m.add_cube(2400,20,2400, 0,300,0, DARK_STONE)
    # Maze walls
    walls = [(-400,0,800,40),(-400,0,40,800),(400,0,800,40),(400,0,40,800),
             (0,-400,40,400),(0,400,40,400),(200,200,400,40),(-200,-200,400,40)]
    for wx,wz,ww,wd in walls:
        m.add_cube(ww,200,wd, wx,100,wz, DARK_STONE)
    # Toxic maze (green haze area)
    m.add_cube(600,4,600, -400,-3,-400, (40,80,20))
    # Metal cap area
    m.add_cube(200,10,200, 500,-2,500, METAL_GREY)
    m.add_cube(40,40,40, 500,20,500, BUTTON_GOLD) # Switch
    # Underground lake (Dorrie)
    m.add_cube(500,6,500, 0,-3,0, WATER_BLUE)
    # Dorrie (big green dino)
    m.add_cube(80,40,120, 0,20,0, BRIGHT_GREEN)
    m.add_cube(30,30,40, 0,55,50, BRIGHT_GREEN)
    # Elevator platforms
    m.add_cube(80,10,80, -600,50,-600, METAL_GREY)
    m.add_cube(80,10,80, -600,150,-600, METAL_GREY)
    # Stalactites
    for sx,sz in [(100,200),(-200,100),(300,-100),(-100,-300)]:
        m.add_cube(20,60,20, sx,270,sz, DARK_STONE)
    # Rolling rocks area
    m.add_cube(300,10,100, 400,10,-300, STONE_GREY)
    m.add_cube(40,40,40, 400,30,-300, DARK_GREY) # Rock
    stars = [Star(500,40,500,0), Star(0,60,0,1), Star(-600,170,-600,2)]
    coins = [Coin(x*150, 10, z*150) for x,z in [(0,0),(1,1),(-1,-1),(2,0)]]
    return m, stars, coins

def build_lethal_lava_land():
    """Course 7: Lethal Lava Land"""
    m = Mesh()
    # Lava floor
    for x in range(-6,6):
        for z in range(-6,6):
            c = LAVA_RED if (x+z)%2==0 else LAVA_ORANGE
            m.add_cube(200,6,200, x*200,-3,z*200, c)
    # Stone platforms over lava
    platforms = [(0,0,200),(300,0,150),(-300,0,150),(0,0,400),(500,0,100),
                 (-500,0,100),(200,0,300),(-200,0,300),(0,0,-200),(0,0,-500)]
    for px,py,ps in platforms:
        m.add_cube(ps,20,ps, px,10+py,py, DARK_STONE)
    # Volcano
    m.add_cube(300,200,300, 0,100,0, DARK_BROWN)
    m.add_cube(200,100,200, 0,250,0, DARK_GREY)
    m.add_cube(100,10,100, 0,300,0, LAVA_ORANGE) # Lava top
    # Volcano interior platforms
    m.add_cube(80,10,80, 0,150,0, DARK_STONE)
    m.add_cube(60,10,60, 50,200,0, DARK_STONE)
    # Rolling log
    m.add_cube(20,20,200, -200,20,-100, DARK_BROWN)
    # Puzzle platforms (tilting)
    m.add_cube(100,10,100, 400,20,400, METAL_GREY)
    m.add_cube(100,10,100, -400,20,-400, METAL_GREY)
    # Wing cap block
    m.add_cube(30,30,30, -500,40,-300, RED)
    # Fire jets
    for fx,fz in [(150,150),(-150,-150),(300,-200)]:
        m.add_cube(20,40,20, fx,30,fz, ORANGE)
    stars = [Star(0,310,0,0), Star(-400,40,-400,1), Star(500,30,0,2)]
    coins = [Coin(px,30,py) for px,py,ps in platforms[:5]]
    return m, stars, coins

def build_shifting_sand_land():
    """Course 8: Shifting Sand Land"""
    m = Mesh()
    # Sand floor
    for x in range(-6,6):
        for z in range(-6,6):
            c = SAND if (x+z)%2==0 else (190,160,100)
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Pyramid (main structure)
    m.add_cube(400,300,400, 0,150,0, SAND)
    m.add_pyramid(420, 100, 0, 300, 0, (200,170,100))
    # Pyramid interior
    m.add_cube(300,200,300, 0,100,0, DARK_BROWN)
    m.add_cube(80,10,80, 0,200,0, DARK_STONE) # Top platform inside
    # Quicksand pit
    m.add_cube(300,4,300, -500,-3,-500, (180,150,80))
    # Oasis
    m.add_cube(200,4,200, 500,-1,500, WATER_BLUE)
    m.add_cube(20,60,20, 520,30,520, DARK_BROWN) # Palm tree
    m.add_cube(60,10,60, 520,60,520, DARK_GREEN)
    # Pillars
    for px,pz in [(-300,300),(300,-300),(-300,-300),(300,300)]:
        m.add_cube(40,120,40, px,60,pz, SAND)
    # Tox boxes (moving cubes)
    m.add_cube(60,60,60, 200,30,-200, DARK_GREY)
    m.add_cube(60,60,60, -200,30,200, DARK_GREY)
    # Klepto (bird perch)
    m.add_cube(20,80,20, -500,40,200, DARK_BROWN)
    m.add_cube(30,10,50, -500,80,200, BROWN) # bird wings
    # Wing cap block
    m.add_cube(30,30,30, 400,20,-400, RED)
    stars = [Star(0,410,0,0), Star(500,20,500,1), Star(-500,10,-500,2)]
    coins = [Coin(x*200, 10, z*200) for x,z in [(1,1),(-1,-1),(2,-2),(-2,2)]]
    return m, stars, coins

def build_dire_dire_docks():
    """Course 9: Dire, Dire Docks"""
    m = Mesh()
    # Dock platforms
    for x in range(-3,3):
        m.add_cube(200,10,200, x*200,-5,-600, DOCK_WOOD)
    # Water (massive pool)
    for x in range(-6,6):
        for z in range(-4,6):
            m.add_cube(200,6,200, x*200,-3,z*200, DEEP_BLUE)
    # Underwater floor
    for x in range(-6,6):
        for z in range(-4,6):
            m.add_cube(200,10,200, x*200,-200,z*200, DARK_STONE)
    # Bowser's submarine
    m.add_cube(120,60,400, 0,-60,200, METAL_GREY)
    m.add_cube(80,40,100, 0,-30,400, DARK_GREY) # Conning tower
    m.add_cube(10,60,10, 0,0,400, METAL_GREY) # Periscope
    # Cage/gate to Bowser
    m.add_cube(200,200,20, 0,100,800, METAL_GREY)
    m.add_cube(10,200,10, -80,100,800, DARK_GREY)
    m.add_cube(10,200,10, 80,100,800, DARK_GREY)
    # Whirlpool area
    m.add_cube(100,4,100, -400,-1,400, (40,60,180))
    # Poles
    for px,pz in [(300,0),(-300,0),(0,600)]:
        m.add_cube(10,150,10, px,-120,pz, METAL_GREY)
    # Manta ray
    m.add_cube(80,8,120, 200,-80,300, (60,60,120))
    # Clam
    m.add_cube(40,15,40, -200,-185,200, LIGHT_GREY)
    stars = [Star(0,-20,200,0), Star(0,10,800,1), Star(-400,10,400,2)]
    coins = [Coin(x*100,-80,z*100) for x,z in [(0,0),(1,2),(-1,3),(2,1)]]
    return m, stars, coins

def build_snowmans_land():
    """Course 10: Snowman's Land"""
    m = Mesh()
    # Snow floor
    for x in range(-6,6):
        for z in range(-6,6):
            c = SNOW_WHITE if (x+z)%2==0 else ICE_BLUE
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Giant snowman mountain
    m.add_cube(300,200,300, 0,100,0, SNOW_WHITE)
    m.add_cube(200,150,200, 0,275,0, SNOW_WHITE)
    m.add_cube(100,100,100, 0,400,0, SNOW_WHITE)
    # Snowman head
    m.add_cube(80,80,80, 0,490,0, SNOW_WHITE)
    m.add_cube(20,20,20, 0,500,-40, ORANGE) # Carrot nose
    m.add_cube(10,10,5, -15,510,-38, BLACK) # Eye
    m.add_cube(10,10,5, 15,510,-38, BLACK) # Eye
    # Ice bridge
    m.add_cube(200,8,40, -200,150,0, ICE_BLUE)
    # Igloo
    m.add_cube(100,60,100, -400,30,-300, SNOW_WHITE)
    m.add_cube(40,40,10, -400,20,-350, DARK_BROWN) # Door
    # Frozen pond
    m.add_cube(300,4,300, 400,-1,400, ICE_BLUE)
    # Bully (ice)
    m.add_cube(30,30,30, 200,20,400, BLACK)
    m.add_cube(8,20,8, 200,45,400, METAL_GREY) # Horns
    # Chill Bully platform
    m.add_cube(150,10,150, 0,100,500, ICE_BLUE)
    # Trees (frozen)
    for tx,tz in [(-500,200),(500,-200),(-200,500)]:
        m.add_cube(20,60,20, tx,30,tz, DARK_BROWN)
        m.add_cube(60,40,60, tx,75,tz, ICE_BLUE)
    stars = [Star(0,540,0,0), Star(-400,60,-300,1), Star(0,120,500,2)]
    coins = [Coin(x*120, 10, z*120) for x,z in [(2,2),(-2,-2),(3,0),(0,3)]]
    return m, stars, coins

def build_wet_dry_world():
    """Course 11: Wet-Dry World"""
    m = Mesh()
    # Base floor
    for x in range(-4,4):
        for z in range(-4,4):
            c = FLOOR_TILE if (x+z)%2==0 else FLOOR_TILE_ALT
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Water (variable height platforms indicated)
    m.add_cube(1600,4,1600, 0,50,0, WATER_LIGHT)
    # City structures
    m.add_cube(200,300,200, -300,150,0, CASTLE_WALL)
    m.add_cube(200,200,200, 300,100,-200, CASTLE_WALL)
    m.add_cube(150,250,150, 0,125,300, STONE_GREY)
    # Crystal switches (water level controls)
    for sx,sz in [(-300,300),(300,-300),(0,0)]:
        m.add_cube(30,30,30, sx,20,sz, PURPLE)
    # Push blocks
    m.add_cube(60,60,60, -100,30,-200, METAL_GREY)
    m.add_cube(60,60,60, 200,30,200, METAL_GREY)
    # Cage area
    m.add_cube(100,100,100, -500,50,-400, METAL_GREY)
    m.add_cube(10,100,10, -550,50,-450, DARK_GREY)
    m.add_cube(10,100,10, -450,50,-350, DARK_GREY)
    # Downtown area (lower)
    m.add_cube(600,10,400, 0,-100,-500, DARK_STONE)
    m.add_cube(100,80,100, -200,-60,-500, CASTLE_WALL)
    m.add_cube(100,80,100, 200,-60,-500, CASTLE_WALL)
    # Heave-ho
    m.add_cube(30,20,30, 100,10,100, RED)
    stars = [Star(-300,310,0,0), Star(0,280,300,1), Star(-200,-50,-500,2)]
    coins = [Coin(x*100,60,z*100) for x,z in [(0,0),(1,1),(-1,-1),(2,-2)]]
    return m, stars, coins

def build_tall_tall_mountain():
    """Course 12: Tall, Tall Mountain"""
    m = Mesh()
    # Base
    for x in range(-4,4):
        for z in range(-4,4):
            c = CHECKER_LIGHT if (x+z)%2==0 else CHECKER_DARK
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Mountain (tall!)
    m.add_cube(500,300,500, 0,150,0, BROWN)
    m.add_cube(400,250,400, 0,425,0, DARK_BROWN)
    m.add_cube(300,200,300, 0,675,0, STONE_GREY)
    m.add_cube(200,150,200, 0,875,0, DARK_GREY)
    m.add_cube(100,100,100, 0,1025,0, DARK_GREY)
    m.add_pyramid(120, 60, 0, 1075, 0, DARK_STONE)
    # Spiral path (platforms going up)
    for i in range(20):
        angle = i * 0.35
        r = 300 + 50 * math.sin(i*0.5)
        px = math.cos(angle) * r
        pz = math.sin(angle) * r
        m.add_cube(80,10,80, px, i*50+20, pz, STONE_GREY)
    # Waterfall
    m.add_cube(60,400,20, -250,200,-200, WATER_LIGHT)
    # Monkey area
    m.add_cube(100,10,100, 200,400,-200, BRIGHT_GREEN)
    # Mushroom platforms
    for mx,mz,mh in [(400,200,60),(400,300,100),(-400,-200,80)]:
        m.add_cube(20,mh,20, mx,mh/2,mz, LIGHT_BROWN)
        m.add_cube(60,15,60, mx,mh,mz, RED)
    # Slide entrance
    m.add_cube(40,40,40, 0,1080,0, DARK_BROWN)
    stars = [Star(0,1100,0,0), Star(200,420,-200,1), Star(-400,100,-200,2)]
    coins = [Coin(math.cos(i*0.35)*300, i*50+30, math.sin(i*0.35)*300) for i in range(0,20,4)]
    return m, stars, coins

def build_tiny_huge_island():
    """Course 13: Tiny-Huge Island"""
    m = Mesh()
    # Island terrain
    for x in range(-5,5):
        for z in range(-5,5):
            dist = math.sqrt(x*x+z*z)
            if dist < 5:
                c = CHECKER_LIGHT if (x+z)%2==0 else CHECKER_DARK
                h = max(0, 40 - dist*8)
                m.add_cube(200,10+h,200, x*200,h/2,z*200, c)
    # Water around island
    for x in range(-6,6):
        for z in range(-6,6):
            dist = math.sqrt(x*x+z*z)
            if dist >= 4:
                m.add_cube(200,6,200, x*200,-3,z*200, WATER_BLUE)
    # Mountain on island
    m.add_cube(300,200,300, 0,100,0, DARK_BROWN)
    m.add_cube(200,100,200, 0,250,0, BROWN)
    # Tiny/Huge pipes
    m.add_cube(40,30,40, -300,50,-300, PIPE_GREEN) # Tiny pipe
    m.add_cube(80,60,80, 300,60,300, PIPE_GREEN) # Huge pipe
    # Windmill
    m.add_cube(60,120,60, -200,60,200, STONE_GREY)
    m.add_cube(10,80,10, -200,140,170, DARK_BROWN) # Blade
    m.add_cube(80,10,10, -200,180,168, DARK_BROWN) # Blade
    # Koopa beach
    m.add_cube(300,6,100, 0,-2,-500, SAND)
    # Piranhas
    for px,pz in [(100,100),(-100,-100),(200,-200)]:
        m.add_cube(20,30,20, px,50,pz, PIPE_GREEN)
    # Wiggler cave entrance
    m.add_cube(60,60,20, 0,250,-100, BLACK)
    stars = [Star(0,310,0,0), Star(-200,140,200,1), Star(0,10,-500,2)]
    coins = [Coin(x*100,50,z*100) for x,z in [(0,1),(1,0),(-1,0),(0,-1),(1,1)]]
    return m, stars, coins

def build_tick_tock_clock():
    """Course 14: Tick Tock Clock"""
    m = Mesh()
    # Inside the clock - vertical level!
    # Base platform
    m.add_cube(300,20,300, 0,-5,0, CLOCK_GOLD)
    # Clock interior walls (cylindrical approximated)
    m.add_cube(40,1200,600, -300,600,0, DARK_BROWN)
    m.add_cube(40,1200,600, 300,600,0, DARK_BROWN)
    m.add_cube(600,1200,40, 0,600,-300, DARK_BROWN)
    m.add_cube(600,1200,40, 0,600,300, DARK_BROWN)
    # Rotating platforms at various heights
    heights = [80,180,300,420,540,660,780,900,1020,1140]
    for i,h in enumerate(heights):
        angle = i * 0.7
        px = math.cos(angle)*100
        pz = math.sin(angle)*100
        w = 100 if i%2==0 else 80
        m.add_cube(w,10,w, px,h,pz, METAL_GREY)
    # Clock hands (pendulums)
    m.add_cube(10,200,10, -100,500,0, DARK_GREY)
    m.add_cube(10,300,10, 100,600,0, DARK_GREY)
    # Gears
    for gh in [200,500,800]:
        m.add_cube(80,10,80, -200,gh,100, CLOCK_GOLD)
        m.add_cube(60,10,60, 200,gh,-100, CLOCK_GOLD)
    # Thwomps
    m.add_cube(50,50,50, 0,400,0, DARK_GREY)
    # Conveyor belts (just colored platforms)
    m.add_cube(200,8,40, 0,700,0, YELLOW)
    m.add_cube(200,8,40, 0,850,0, YELLOW)
    # Top platform
    m.add_cube(200,20,200, 0,1200,0, BUTTON_GOLD)
    stars = [Star(0,1220,0,0), Star(-200,520,100,1), Star(0,710,0,2)]
    coins = [Coin(math.cos(i*0.7)*100,heights[i]+15,math.sin(i*0.7)*100) for i in range(0,10,2)]
    return m, stars, coins

def build_rainbow_ride():
    """Course 15: Rainbow Ride"""
    m = Mesh()
    # No ground - sky level!
    # Starting platform
    m.add_cube(200,20,200, 0,-5,0, CLOUD_WHITE)
    # Rainbow bridge segments
    colors = [RAINBOW_R,RAINBOW_O,RAINBOW_Y,RAINBOW_G,RAINBOW_B,RAINBOW_P]
    for i in range(30):
        c = colors[i%6]
        angle = i * 0.15
        px = i * 80
        pz = math.sin(angle) * 200
        py = i * 20
        m.add_cube(60,8,60, px,py,pz, c)
    # Flying carpet start
    m.add_cube(80,6,80, -200,100,-200, PURPLE)
    # Carpet path platforms
    for i in range(10):
        m.add_cube(60,8,60, -200-i*100, 100+i*30, -200-i*80, PURPLE)
    # House in the sky
    m.add_cube(200,120,200, 800,200,0, CASTLE_WALL)
    m.add_cube(220,10,220, 800,260,0, CASTLE_ROOF)
    m.add_cube(40,80,10, 800,200,-100, CASTLE_DOOR)
    # Maze platforms
    for i in range(5):
        for j in range(3):
            m.add_cube(80,8,80, 400+i*100, 300+j*60, -300+j*100, CLOUD_WHITE)
    # Swinging platforms
    for sx in range(-100,400,150):
        m.add_cube(60,8,60, sx,80,-400, METAL_GREY)
    # Donut lifts
    m.add_cube(50,8,50, 500,100,300, ORANGE)
    m.add_cube(50,8,50, 600,130,350, ORANGE)
    # Pole
    m.add_cube(10,200,10, 1000,300,0, METAL_GREY)
    # Tricky triangles
    for i in range(4):
        m.add_cube(100,8,100, -400+i*60, 200+i*40, 300+i*60, RAINBOW_R)
    # Cloud platforms
    for cx,cz in [(1200,200),(1200,-200),(1400,0)]:
        m.add_cube(100,20,100, cx,400,cz, CLOUD_WHITE)
    # Final star platform
    m.add_cube(120,20,120, 1400,420,0, BUTTON_GOLD)
    stars = [Star(1400,440,0,0), Star(800,280,0,1), Star(-200-9*100,130+9*30,-200-9*80,2)]
    coins = [Coin(i*80,i*20+10,math.sin(i*0.15)*200) for i in range(0,30,5)]
    return m, stars, coins


# ================================================================
# SECRET LEVELS
# ================================================================

def build_princess_secret_slide():
    """Secret: The Princess's Secret Slide"""
    m = Mesh()
    m.add_cube(200,20,200, 0,600,0, CASTLE_WALL)
    for i in range(25):
        angle = i * 0.3
        r = 100 + i * 15
        px = math.cos(angle) * r
        pz = math.sin(angle) * r
        m.add_cube(60,8,60, px, 580-i*22, pz, ICE_BLUE)
    m.add_cube(200,20,200, math.cos(24*0.3)*(100+24*15), 50, math.sin(24*0.3)*(100+24*15), CASTLE_WALL)
    stars = [Star(math.cos(24*0.3)*(100+24*15), 70, math.sin(24*0.3)*(100+24*15), 0)]
    return m, stars, []

def build_wing_mario_rainbow():
    """Secret: Wing Mario Over the Rainbow"""
    m = Mesh()
    colors = [RAINBOW_R,RAINBOW_O,RAINBOW_Y,RAINBOW_G,RAINBOW_B,RAINBOW_P]
    m.add_cube(150,20,150, 0,-5,0, CLOUD_WHITE)
    for i in range(20):
        c = colors[i%6]
        angle = i * 0.3
        r = 200 + i*40
        m.add_cube(80,8,80, math.cos(angle)*r, i*30+10, math.sin(angle)*r, c)
    for cx,cz in [(600,300),(-400,500),(200,-400)]:
        m.add_cube(120,20,120, cx,200,cz, CLOUD_WHITE)
    m.add_cube(40,40,40, 0,10,0, RED) # Wing cap box
    stars = [Star(600,220,300,0)]
    coins = [Coin(math.cos(i*0.3)*(200+i*40), i*30+20, math.sin(i*0.3)*(200+i*40)) for i in range(0,20,4)]
    return m, stars, coins

def build_metal_cap_cavern():
    """Secret: Cavern of the Metal Cap"""
    m = Mesh()
    for x in range(-4,4):
        for z in range(-4,4):
            c = DARK_STONE if (x+z)%2==0 else DARK_GREY
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(1600,20,1600, 0,250,0, DARK_STONE)
    m.add_cube(800,4,800, 0,-1,0, WATER_BLUE)
    # Metal cap switch
    m.add_cube(60,20,60, 0,10,0, PIPE_GREEN)
    m.add_cube(40,40,40, 0,30,0, METAL_GREY)
    # Waterfall
    m.add_cube(100,200,20, 300,100,-400, WATER_LIGHT)
    # Platforms
    for i in range(5):
        m.add_cube(80,10,80, -200+i*100, 5, 200-i*80, DARK_STONE)
    stars = [Star(0,50,0,0)]
    return m, stars, []

def build_vanish_cap():
    """Secret: Vanish Cap Under the Moat"""
    m = Mesh()
    m.add_cube(200,20,200, 0,200,0, DARK_STONE)
    # Slope down
    for i in range(15):
        m.add_cube(100,10,100, i*80, 180-i*12, 0, ICE_BLUE if i%2==0 else CYAN)
    # Vanish cap switch
    m.add_cube(60,20,60, 1200,10,0, CYAN)
    m.add_cube(40,40,40, 1200,30,0, BLUE)
    # Platforms
    for i in range(8):
        m.add_cube(60,10,60, 600+i*80, 60+i*10, i*40-160, DARK_STONE)
    # Elevator
    m.add_cube(80,10,80, 400,100,200, METAL_GREY)
    stars = [Star(1200,50,0,0)]
    return m, stars, []

def build_tower_wing_cap():
    """Secret: Tower of the Wing Cap"""
    m = Mesh()
    m.add_cube(300,20,300, 0,-5,0, CLOUD_WHITE)
    # Tower
    m.add_cube(60,400,60, 0,200,0, TOWER_STONE)
    # Wing cap switch at top
    m.add_cube(100,20,100, 0,400,0, CLOUD_WHITE)
    m.add_cube(40,40,40, 0,420,0, RED)
    # Floating coins in rings
    for i in range(8):
        angle = i * math.pi / 4
        m.add_cube(100,10,100, math.cos(angle)*400, 200, math.sin(angle)*400, CLOUD_WHITE)
    stars = [Star(0,440,0,0)]
    coins = [Coin(math.cos(i*math.pi/4)*400, 220, math.sin(i*math.pi/4)*400) for i in range(8)]
    return m, stars, coins


# ================================================================
# BOWSER LEVELS
# ================================================================

def build_bowser_dark_world():
    """Bowser in the Dark World"""
    m = Mesh()
    # Dark floating platforms
    m.add_cube(200,20,200, 0,-5,0, DARK_STONE)
    path = [(200,0),(400,40),(600,80),(600,160),(400,240),(200,240),
            (0,320),(200,400),(400,400),(600,480),(800,480),(1000,400)]
    for px,pz in path:
        m.add_cube(120,20,120, px,10,pz, DARK_PURPLE)
    # Flame bars
    for fx,fz in [(400,40),(600,160),(200,240)]:
        m.add_cube(10,10,80, fx,30,fz, ORANGE)
    # Bowser arena
    m.add_cube(400,20,400, 1000,10,400, DARK_STONE)
    m.add_cube(420,4,420, 1000,20,400, LAVA_RED)
    # Bowser
    m.add_cube(60,80,60, 1000,60,400, DARK_GREEN)
    m.add_cube(40,40,40, 1000,120,400, BRIGHT_GREEN) # Head
    m.add_cube(20,20,10, 1000,140,370, RED) # Eyes
    # Bombs around edge
    for i in range(8):
        angle = i*math.pi/4
        bx = 1000+math.cos(angle)*180
        bz = 400+math.sin(angle)*180
        m.add_cube(20,20,20, bx,30,bz, BLACK)
    # Key
    stars = [Star(1000,120,400,0)]
    return m, stars, []

def build_bowser_fire_sea():
    """Bowser in the Fire Sea"""
    m = Mesh()
    # Lava everywhere
    for x in range(-6,6):
        for z in range(-6,6):
            c = LAVA_RED if (x+z)%2==0 else LAVA_ORANGE
            m.add_cube(200,6,200, x*200,-3,z*200, c)
    # Platforms
    m.add_cube(200,20,200, 0,10,0, DARK_STONE)
    # Moving mesh platforms
    platform_path = [(0,0),(150,200),(300,400),(150,600),(0,800),
                     (-200,1000),(-400,1000),(-400,800),(-200,600),(0,400)]
    for i,(px,pz) in enumerate(platform_path):
        m.add_cube(100,20,100, px,10+i*5,pz, METAL_GREY)
    # Tilting bridges
    m.add_cube(200,8,40, 200,20,200, DARK_BROWN)
    m.add_cube(200,8,40, -200,20,800, DARK_BROWN)
    # Pole
    m.add_cube(10,200,10, -400,100,1000, METAL_GREY)
    # Fire jets
    for i in range(0,len(platform_path),2):
        px,pz = platform_path[i]
        m.add_cube(15,30,15, px+50,30+i*5,pz, ORANGE)
    # Bowser arena
    m.add_cube(500,20,500, 0,60,1200, DARK_STONE)
    # Bowser
    m.add_cube(80,100,80, 0,110,1200, DARK_GREEN)
    m.add_cube(50,50,50, 0,180,1200, BRIGHT_GREEN)
    m.add_cube(30,20,10, 0,200,1160, RED)
    # Spiky shell
    m.add_cube(90,30,90, 0,80,1200, DARK_BROWN)
    stars = [Star(0,180,1200,0)]
    return m, stars, []

def build_bowser_sky():
    """Bowser in the Sky"""
    m = Mesh()
    # Sky level - no floor, platforms only
    m.add_cube(200,20,200, 0,-5,0, DARK_STONE)
    # Ascending path
    sky_path = []
    for i in range(25):
        angle = i * 0.25
        r = 200 + i*20
        px = math.cos(angle)*r
        pz = math.sin(angle)*r
        py = i*40
        sky_path.append((px,py,pz))
        c = [DARK_STONE,DARK_PURPLE,DARK_GREY,METAL_GREY][i%4]
        m.add_cube(100,15,100, px,py,pz, c)
    # Obstacles along path
    for i in range(0,25,3):
        px,py,pz = sky_path[i]
        m.add_cube(10,10,60, px+40,py+20,pz, ORANGE) # Flame bar
    # Bowser arena (top)
    last = sky_path[-1]
    arena_x, arena_y, arena_z = last[0], last[1]+40, last[2]
    m.add_cube(600,20,600, arena_x, arena_y, arena_z, DARK_STONE)
    # Arena edge bombs
    for i in range(12):
        angle = i*math.pi/6
        bx = arena_x+math.cos(angle)*280
        bz = arena_z+math.sin(angle)*280
        m.add_cube(20,20,20, bx,arena_y+20,bz, BLACK)
    # Final Bowser
    m.add_cube(100,120,100, arena_x,arena_y+80,arena_z, DARK_GREEN)
    m.add_cube(60,60,60, arena_x,arena_y+180,arena_z, BRIGHT_GREEN)
    m.add_cube(40,30,10, arena_x,arena_y+200,arena_z-50, RED)
    # Spikes on shell
    for sx,sz in [(-30,0),(30,0),(0,-30),(0,30)]:
        m.add_cube(15,25,15, arena_x+sx,arena_y+130,arena_z+sz, DARK_BROWN)
    # Grand star
    stars = [Star(arena_x,arena_y+220,arena_z,0)]
    return m, stars, []


# ================================================================
# LEVEL REGISTRY
# ================================================================
LEVELS = {
    "castle_grounds": {"name": "Castle Grounds", "builder": build_castle_grounds, "sky": (100,160,255), "stars": 0, "req": 0},
    "castle_f1": {"name": "Castle Interior", "builder": build_castle_interior_f1, "sky": (60,50,40), "stars": 0, "req": 0},
    "castle_basement": {"name": "Castle Basement", "builder": build_castle_basement, "sky": (20,15,10), "stars": 0, "req": 8},
    "castle_upper": {"name": "Castle Upper Floor", "builder": build_castle_upper, "sky": (60,50,40), "stars": 0, "req": 30},
    "castle_top": {"name": "Castle Top", "builder": build_castle_top, "sky": (200,220,255), "stars": 0, "req": 50},

    # 15 Main Courses
    "c01_bob": {"name": "Bob-omb Battlefield", "builder": build_bob_omb_battlefield, "sky": (100,180,255), "stars": 7, "req": 0},
    "c02_whomp": {"name": "Whomp's Fortress", "builder": build_whomps_fortress, "sky": (130,170,240), "stars": 7, "req": 1},
    "c03_jolly": {"name": "Jolly Roger Bay", "builder": build_jolly_roger_bay, "sky": (60,100,180), "stars": 7, "req": 3},
    "c04_cool": {"name": "Cool, Cool Mountain", "builder": build_cool_cool_mountain, "sky": (180,210,255), "stars": 7, "req": 3},
    "c05_boo": {"name": "Big Boo's Haunt", "builder": build_big_boos_haunt, "sky": (15,10,25), "stars": 7, "req": 12},
    "c06_hazy": {"name": "Hazy Maze Cave", "builder": build_hazy_maze_cave, "sky": (20,20,20), "stars": 7, "req": 8},
    "c07_lava": {"name": "Lethal Lava Land", "builder": build_lethal_lava_land, "sky": (40,10,0), "stars": 7, "req": 8},
    "c08_sand": {"name": "Shifting Sand Land", "builder": build_shifting_sand_land, "sky": (200,180,140), "stars": 7, "req": 8},
    "c09_dock": {"name": "Dire, Dire Docks", "builder": build_dire_dire_docks, "sky": (20,40,100), "stars": 7, "req": 30},
    "c10_snow": {"name": "Snowman's Land", "builder": build_snowmans_land, "sky": (180,200,240), "stars": 7, "req": 30},
    "c11_wet": {"name": "Wet-Dry World", "builder": build_wet_dry_world, "sky": (150,180,220), "stars": 7, "req": 30},
    "c12_tall": {"name": "Tall, Tall Mountain", "builder": build_tall_tall_mountain, "sky": (120,180,240), "stars": 7, "req": 30},
    "c13_tiny": {"name": "Tiny-Huge Island", "builder": build_tiny_huge_island, "sky": (100,180,255), "stars": 7, "req": 30},
    "c14_clock": {"name": "Tick Tock Clock", "builder": build_tick_tock_clock, "sky": (40,30,20), "stars": 7, "req": 50},
    "c15_rainbow": {"name": "Rainbow Ride", "builder": build_rainbow_ride, "sky": (100,140,255), "stars": 7, "req": 50},

    # Secret Levels
    "s_slide": {"name": "Princess's Secret Slide", "builder": build_princess_secret_slide, "sky": (60,50,40), "stars": 2, "req": 1},
    "s_wing": {"name": "Wing Mario Over Rainbow", "builder": build_wing_mario_rainbow, "sky": (140,180,255), "stars": 1, "req": 10},
    "s_metal": {"name": "Metal Cap Cavern", "builder": build_metal_cap_cavern, "sky": (10,10,10), "stars": 1, "req": 8},
    "s_vanish": {"name": "Vanish Cap Moat", "builder": build_vanish_cap, "sky": (20,30,60), "stars": 1, "req": 8},
    "s_tower": {"name": "Tower of Wing Cap", "builder": build_tower_wing_cap, "sky": (200,220,255), "stars": 1, "req": 10},

    # Bowser Levels
    "b1_dark": {"name": "Bowser Dark World", "builder": build_bowser_dark_world, "sky": (10,0,20), "stars": 1, "req": 8},
    "b2_fire": {"name": "Bowser Fire Sea", "builder": build_bowser_fire_sea, "sky": (30,5,0), "stars": 1, "req": 30},
    "b3_sky": {"name": "Bowser in the Sky", "builder": build_bowser_sky, "sky": (60,40,80), "stars": 1, "req": 70},
}


# ================================================================
# LEVEL SELECT PAINTING DATA (for interior paintings)
# ================================================================
CASTLE_F1_PAINTINGS = [
    {"pos": (-978, 140, -300), "level": "c01_bob", "color": BRIGHT_GREEN, "label": "Bob-omb Battlefield"},
    {"pos": (-978, 140, -500), "level": "c02_whomp", "color": STONE_GREY, "label": "Whomp's Fortress"},
    {"pos": (-978, 140, -700), "level": "c03_jolly", "color": WATER_BLUE, "label": "Jolly Roger Bay"},
    {"pos": (978, 140, -300), "level": "c04_cool", "color": SNOW_WHITE, "label": "Cool Cool Mountain"},
    {"pos": (978, 140, -500), "level": "c05_boo", "color": DARK_PURPLE, "label": "Big Boo's Haunt"},
]

BASEMENT_PAINTINGS = [
    {"pos": (-1178, 100, -400), "level": "c06_hazy", "color": DARK_GREEN, "label": "Hazy Maze Cave"},
    {"pos": (-1178, 100, -600), "level": "c07_lava", "color": LAVA_RED, "label": "Lethal Lava Land"},
    {"pos": (-1178, 100, -800), "level": "c08_sand", "color": SAND, "label": "Shifting Sand Land"},
    {"pos": (1178, 100, -400), "level": "c09_dock", "color": DEEP_BLUE, "label": "Dire Dire Docks"},
]

UPPER_PAINTINGS = [
    {"pos": (-778, 100, -300), "level": "c10_snow", "color": ICE_BLUE, "label": "Snowman's Land"},
    {"pos": (-778, 100, -500), "level": "c11_wet", "color": WATER_LIGHT, "label": "Wet-Dry World"},
    {"pos": (778, 100, -300), "level": "c12_tall", "color": DARK_GREEN, "label": "Tall Tall Mountain"},
    {"pos": (778, 100, -500), "level": "c13_tiny", "color": BRIGHT_GREEN, "label": "Tiny-Huge Island"},
    {"pos": (0, 60, -778), "level": "c14_clock", "color": CLOCK_GOLD, "label": "Tick Tock Clock"},
    {"pos": (0, 75, -790), "level": "c15_rainbow", "color": RAINBOW_R, "label": "Rainbow Ride"},
]


# ================================================================
# RENDERER - Full FPS Camera with Pitch + Yaw + N64 Vertex Jitter
# ================================================================
# N64 fixed-point vertex snapping grid (Super FX style jitter)
N64_SNAP = 2  # Snap vertices to this grid to emulate N64 fixed-point

def render_mesh(screen, mesh, cam_x, cam_y, cam_z, cam_yaw, cam_pitch, cx, cy, is_menu=False):
    render_list = []
    # Camera yaw rotation
    c_cos = math.cos(-cam_yaw)
    c_sin = math.sin(-cam_yaw)
    # Camera pitch rotation
    p_cos = math.cos(-cam_pitch)
    p_sin = math.sin(-cam_pitch)
    # Mesh object rotation
    m_cos = math.cos(mesh.yaw)
    m_sin = math.sin(mesh.yaw)
    menu_tilt = 0.2
    wiggle = math.sin(pygame.time.get_ticks()/500.0)*10 if is_menu else 0

    for face in mesh.faces:
        transformed_verts = []
        avg_z = 0
        valid = True
        for i in face.indices:
            v = mesh.vertices[i]
            # 1. Object-space rotation (mesh.yaw)
            rx = v.x*m_cos - v.z*m_sin
            rz = v.x*m_sin + v.z*m_cos
            ry = v.y
            if is_menu:
                ry_t = ry*math.cos(menu_tilt) - rz*math.sin(menu_tilt)
                rz = ry*math.sin(menu_tilt) + rz*math.cos(menu_tilt)
                ry = ry_t + wiggle
            # 2. World translate
            wx = rx + mesh.x
            wy = ry + mesh.y
            wz = rz + mesh.z
            # 3. Camera translate
            dcx = wx - cam_x
            dcy = wy - cam_y
            dcz = wz - cam_z
            if not is_menu:
                # 4a. Camera yaw rotation (Y-axis)
                xx = dcx*c_cos - dcz*c_sin
                zz = dcx*c_sin + dcz*c_cos
                yy = dcy
                # 4b. Camera pitch rotation (X-axis) - FPS look up/down
                yy2 = yy*p_cos - zz*p_sin
                zz2 = yy*p_sin + zz*p_cos
                xx, yy, zz = xx, yy2, zz2
            else:
                xx = dcx; yy = dcy; zz = dcz
            # Near clip
            if zz < 5:
                valid = False; break
            transformed_verts.append((xx, yy, zz))
            avg_z += zz
        if not valid:
            continue
        # 5. Project to screen with N64 vertex snapping
        screen_points = []
        for xx, yy, zz in transformed_verts:
            scale = FOV / zz
            sx = xx * scale + cx
            sy = -yy * scale + cy
            # N64 fixed-point vertex jitter (Super FX snap)
            if not is_menu:
                sx = int(sx / N64_SNAP) * N64_SNAP
                sy = int(sy / N64_SNAP) * N64_SNAP
            else:
                sx = int(sx)
                sy = int(sy)
            screen_points.append((sx, sy))
        # 6. Backface culling (shoelace area)
        if len(screen_points) >= 3:
            area = 0
            for i in range(len(screen_points)):
                j = (i+1) % len(screen_points)
                area += (screen_points[j][0]-screen_points[i][0]) * (screen_points[j][1]+screen_points[i][1])
            if area > 0:
                render_list.append({
                    'poly': screen_points,
                    'depth': avg_z / len(transformed_verts),
                    'color': face.color
                })
    return render_list


# ================================================================
# MENU HEAD
# ================================================================
def create_menu_head():
    m = Mesh()
    m.add_cube(40,36,40,0,0,0,SKIN)
    m.add_cube(44,12,44,0,20,0,RED)
    m.add_cube(52,4,52,0,15,10,RED)
    m.add_cube(10,10,10,0,-2,22,SKIN)
    m.add_cube(24,6,4,0,-10,21,MUSTACHE_BLACK)
    m.add_cube(10,12,2,-12,6,20,WHITE)
    m.add_cube(10,12,2,12,6,20,WHITE)
    m.add_cube(4,6,3,-12,6,21,EYE_BLUE)
    m.add_cube(4,6,3,12,6,21,EYE_BLUE)
    m.add_cube(42,24,10,0,0,-18,BROWN)
    return m


# ================================================================
# MAIN
# ================================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ULTRA MARIO 64 - N64DD SUPER FX EDITION")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.Font(None, 72)
        font_menu = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 22)
        font_hud = pygame.font.SysFont('Arial', 20, bold=True)
        font_big = pygame.font.Font(None, 48)
    except:
        font_title = pygame.font.SysFont('Arial',54,bold=True)
        font_menu = pygame.font.SysFont('Arial',28,bold=True)
        font_small = pygame.font.SysFont('Arial',16)
        font_hud = font_small
        font_big = font_menu

    # States
    STATE_MENU = 0
    STATE_GAME = 1
    STATE_LEVEL_SELECT = 2
    STATE_PAUSE = 3
    current_state = STATE_MENU

    # Menu
    menu_head = create_menu_head()
    menu_items = ["PLAY GAME", "LEVEL SELECT", "HOW TO PLAY", "CREDITS", "EXIT GAME"]
    selected_index = 0
    active_overlay = None

    # Level select
    level_keys = list(LEVELS.keys())
    level_select_idx = 0
    level_select_scroll = 0

    # Game
    mario = None
    current_level_mesh = None
    current_level_stars = []
    current_level_coins = []
    current_level_id = None
    cam_x, cam_y, cam_z = 0,0,0
    cam_yaw = 0
    cam_pitch = 0              # Vertical look angle
    # Lakitu smooth targets (actual camera lerps toward these)
    cam_target_x, cam_target_y, cam_target_z = 0.0, 0.0, 0.0
    cam_target_yaw = 0.0
    cam_target_pitch = 0.0
    # SM64-style velocity-based movement
    vel_x, vel_z = 0.0, 0.0   # World-space velocity
    head_bob_phase = 0.0       # Head bob cycle
    bob_x, bob_y = 0.0, 0.0   # Current head bob offsets
    mouse_captured = False     # Mouse lock state
    cx, cy = WIDTH//2, HEIGHT//2
    collected_stars = set()
    total_coins = 0

    # HUD animation
    star_flash = 0
    coin_flash = 0
    level_name_timer = 0
    level_display_name = ""

    def load_level(level_id):
        nonlocal mario, current_level_mesh, current_level_stars, current_level_coins
        nonlocal current_level_id, cam_x, cam_y, cam_z, cam_yaw, cam_pitch
        nonlocal cam_target_x, cam_target_y, cam_target_z, cam_target_yaw, cam_target_pitch
        nonlocal vel_x, vel_z, head_bob_phase, bob_x, bob_y, mouse_captured
        nonlocal level_name_timer, level_display_name

        info = LEVELS[level_id]
        current_level_id = level_id
        level_display_name = info["name"]
        level_name_timer = 180  # 3 seconds display

        result = info["builder"]()
        if isinstance(result, tuple):
            if len(result) == 3:
                current_level_mesh, current_level_stars, current_level_coins = result
            elif len(result) == 2:
                current_level_mesh, current_level_stars = result
                current_level_coins = []
            else:
                current_level_mesh = result[0]
                current_level_stars = []
                current_level_coins = []
        else:
            current_level_mesh = result
            current_level_stars = []
            current_level_coins = []

        mario = Mario(0, 50, 400)
        # First-person: camera IS Mario's eyes
        cam_yaw = math.pi       # Face into the level (toward -Z)
        cam_pitch = 0.0
        cam_target_yaw = cam_yaw
        cam_target_pitch = cam_pitch
        cam_x = mario.x
        cam_y = mario.y + EYE_HEIGHT
        cam_z = mario.z
        cam_target_x = cam_x
        cam_target_y = cam_y
        cam_target_z = cam_z
        vel_x, vel_z = 0.0, 0.0
        head_bob_phase = 0.0
        bob_x, bob_y = 0.0, 0.0
        # Capture mouse for FPS look
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        mouse_captured = True

    def draw_sky_gradient(sky_color):
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(sky_color[0] * (1-ratio) + 0 * ratio)
            g = int(sky_color[1] * (1-ratio) + 0 * ratio)
            b = int(sky_color[2] * (1-ratio) + 0 * ratio)
            pygame.draw.line(screen, (max(0,r),max(0,g),max(0,b)), (0,y), (WIDTH,y))

    def draw_hud():
        nonlocal star_flash, coin_flash
        # Bottom bar
        pygame.draw.rect(screen, (0,0,0,200), (0, HEIGHT-55, WIDTH, 55))
        pygame.draw.line(screen, METAL_GREY, (0,HEIGHT-55), (WIDTH,HEIGHT-55), 2)

        # Stars
        star_color = YELLOW if star_flash <= 0 else WHITE
        star_txt = font_hud.render(f"★ {len(collected_stars)}", True, star_color)
        screen.blit(star_txt, (20, HEIGHT-42))

        # Coins
        coin_color = YELLOW if coin_flash <= 0 else WHITE
        coin_txt = font_hud.render(f"● {total_coins}", True, coin_color)
        screen.blit(coin_txt, (120, HEIGHT-42))

        # Lives
        life_txt = font_hud.render(f"♥ x{mario.lives}", True, RED)
        screen.blit(life_txt, (220, HEIGHT-42))

        # Health
        for i in range(8):
            color = RED if i < mario.health else DARK_GREY
            pygame.draw.rect(screen, color, (320+i*20, HEIGHT-42, 16, 16))

        # FPS
        fps_txt = font_hud.render(f"FPS:{int(clock.get_fps())}", True, CHECKER_LIGHT)
        screen.blit(fps_txt, (WIDTH-100, HEIGHT-42))

        # Level name
        if current_level_id:
            name = LEVELS[current_level_id]["name"]
            n_txt = font_small.render(name, True, WHITE)
            screen.blit(n_txt, (WIDTH//2 - n_txt.get_width()//2, HEIGHT-42))

        star_flash = max(0, star_flash - 1)
        coin_flash = max(0, coin_flash - 1)

    def draw_level_intro():
        nonlocal level_name_timer
        if level_name_timer > 0:
            alpha = min(255, level_name_timer * 3)
            overlay = pygame.Surface((WIDTH, 80))
            overlay.set_alpha(alpha)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, HEIGHT//2-40))

            txt = font_big.render(level_display_name, True, YELLOW)
            screen.blit(txt, (WIDTH//2-txt.get_width()//2, HEIGHT//2-20))
            level_name_timer -= 1

    running = True
    while running:
        dt = clock.tick(FPS)
        time_sec = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if current_state == STATE_MENU:
                if event.type == pygame.KEYDOWN:
                    if active_overlay:
                        if event.key in (pygame.K_ESCAPE, pygame.K_b, pygame.K_RETURN):
                            active_overlay = None
                    else:
                        if event.key == pygame.K_UP:
                            selected_index = (selected_index-1) % len(menu_items)
                        elif event.key == pygame.K_DOWN:
                            selected_index = (selected_index+1) % len(menu_items)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            choice = menu_items[selected_index]
                            if choice == "EXIT GAME":
                                running = False
                            elif choice == "PLAY GAME":
                                current_state = STATE_GAME
                                load_level("castle_grounds")
                            elif choice == "LEVEL SELECT":
                                current_state = STATE_LEVEL_SELECT
                                level_select_idx = 0
                            elif choice == "HOW TO PLAY":
                                active_overlay = "how"
                            elif choice == "CREDITS":
                                active_overlay = "credits"

            elif current_state == STATE_LEVEL_SELECT:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_state = STATE_MENU
                    elif event.key == pygame.K_UP:
                        level_select_idx = (level_select_idx-1) % len(level_keys)
                    elif event.key == pygame.K_DOWN:
                        level_select_idx = (level_select_idx+1) % len(level_keys)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        key = level_keys[level_select_idx]
                        current_state = STATE_GAME
                        load_level(key)

            elif current_state == STATE_GAME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_state = STATE_PAUSE
                        # Release mouse on pause
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                        mouse_captured = False
                    elif event.key == pygame.K_SPACE and mario and not mario.is_jumping:
                        mario.dy = JUMP_FORCE
                        mario.is_jumping = True
                    # Level transitions (E to enter)
                    elif event.key == pygame.K_e:
                        # Check proximity to painting portals or doors
                        if current_level_id == "castle_grounds":
                            if abs(mario.x) < 100 and mario.z < -900:
                                load_level("castle_f1")
                        elif current_level_id == "castle_f1":
                            # Check paintings
                            for p in CASTLE_F1_PAINTINGS:
                                dx = mario.x - p["pos"][0]
                                dz = mario.z - p["pos"][2]
                                if abs(dx)<150 and abs(dz)<150:
                                    load_level(p["level"])
                                    break
                            else:
                                # Basement access
                                if abs(mario.x-600)<100 and abs(mario.z-600)<100:
                                    load_level("castle_basement")
                                # Upper floor
                                elif abs(mario.x)<200 and mario.z < -800:
                                    load_level("castle_upper")
                                # Exit to grounds
                                elif abs(mario.x)<200 and mario.z > 800:
                                    load_level("castle_grounds")
                                # Princess slide
                                elif abs(mario.x)<100 and abs(mario.z)<100 and mario.y > 50:
                                    load_level("s_slide")
                        elif current_level_id == "castle_basement":
                            for p in BASEMENT_PAINTINGS:
                                dx = mario.x - p["pos"][0]
                                dz = mario.z - p["pos"][2]
                                if abs(dx)<150 and abs(dz)<150:
                                    load_level(p["level"])
                                    break
                            else:
                                if abs(mario.x-800)<100 and abs(mario.z-800)<100:
                                    load_level("s_metal")
                                elif abs(mario.x-600)<100 and abs(mario.z+1178)<100:
                                    load_level("s_vanish")
                                elif abs(mario.x)<200 and mario.z > 1000:
                                    load_level("castle_f1")
                                # Bowser 1 access
                                elif abs(mario.x)<100 and abs(mario.z+600)<100:
                                    load_level("b1_dark")
                        elif current_level_id == "castle_upper":
                            for p in UPPER_PAINTINGS:
                                dx = mario.x - p["pos"][0]
                                dz = mario.z - p["pos"][2]
                                if abs(dx)<150 and abs(dz)<150:
                                    load_level(p["level"])
                                    break
                            else:
                                if abs(mario.x)<200 and mario.z < -600:
                                    load_level("castle_top")
                                elif abs(mario.x)<200 and mario.z > 600:
                                    load_level("castle_f1")
                                # Bowser 2
                                elif abs(mario.x-600)<200 and abs(mario.z)<200:
                                    load_level("b2_fire")
                        elif current_level_id == "castle_top":
                            if abs(mario.x)<100 and abs(mario.z)<100:
                                load_level("s_tower")
                            elif abs(mario.x)<200 and mario.z > 300:
                                load_level("castle_upper")
                            # Bowser 3
                            elif mario.y > 100:
                                load_level("b3_sky")
                        # Return from any course level
                        elif current_level_id and current_level_id.startswith("c"):
                            load_level("castle_f1")
                        elif current_level_id and current_level_id.startswith("s"):
                            load_level("castle_f1")
                        elif current_level_id and current_level_id.startswith("b"):
                            load_level("castle_f1")

            elif current_state == STATE_PAUSE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_state = STATE_GAME
                        # Re-capture mouse on resume
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        mouse_captured = True
                    elif event.key == pygame.K_q:
                        current_state = STATE_MENU
                        # Release mouse
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                        mouse_captured = False
                    elif event.key == pygame.K_r:
                        if current_level_id:
                            load_level(current_level_id)
                            current_state = STATE_GAME

        # ========== RENDER ==========

        if current_state == STATE_MENU:
            # Gradient bg
            for y in range(HEIGHT):
                ratio = y/HEIGHT
                r = int(DD_SKY_TOP[0]*(1-ratio))
                g = int(DD_SKY_TOP[1]*(1-ratio))
                b = int(DD_SKY_TOP[2]*(1-ratio))
                pygame.draw.line(screen, (r,g,b), (0,y), (WIDTH,y))

            menu_head.yaw += 0.02
            polys = render_mesh(screen, menu_head, 0, 0, 200, 0, 0, cx, cy, is_menu=True)
            polys.sort(key=lambda x: x['depth'], reverse=True)
            for p in polys:
                pygame.draw.polygon(screen, p['color'], p['poly'])
                pygame.draw.polygon(screen, BLACK, p['poly'], 1)

            # Title with shadow
            logo_y = 40 + math.sin(time_sec)*5
            t_surf = font_title.render("ULTRA MARIO 64", True, WHITE)
            t_shad = font_title.render("ULTRA MARIO 64", True, RED)
            screen.blit(t_shad, (WIDTH//2-t_surf.get_width()//2+3, logo_y+3))
            screen.blit(t_surf, (WIDTH//2-t_surf.get_width()//2, logo_y))

            sub = font_small.render("N64DD SUPER FX EDITION - FIRST PERSON - 60FPS", True, YELLOW)
            screen.blit(sub, (WIDTH//2-sub.get_width()//2, logo_y+55))

            # Menu items
            menu_y = HEIGHT - 220
            for i, item in enumerate(menu_items):
                color = YELLOW if i==selected_index else WHITE
                label = font_menu.render(item, True, color)
                x_off = 20 if i==selected_index else 0
                screen.blit(label, (50+x_off, menu_y+i*38))
                if i==selected_index:
                    pygame.draw.polygon(screen, RED, [
                        (32, menu_y+i*38+8), (44, menu_y+i*38+14), (32, menu_y+i*38+20)])

            # Star count
            sc_txt = font_small.render(f"Stars: {len(collected_stars)}/{STAR_TOTAL}", True, YELLOW)
            screen.blit(sc_txt, (WIDTH-150, HEIGHT-30))

            # Overlay
            if active_overlay == "how":
                overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(230); overlay.fill(BLACK)
                screen.blit(overlay, (0,0))
                pygame.draw.rect(screen, RED, (60,60,WIDTH-120,HEIGHT-120), 3)
                lines = [
                    "CONTROLS (FIRST-PERSON):",
                    "MOUSE - Look Around (Lakitu Camera)",
                    "WASD - Move Forward/Back/Strafe",
                    "SHIFT - Sprint (SM64 Run Speed)",
                    "ARROW KEYS - Camera Rotate (C-Buttons)",
                    "SPACE - Jump",
                    "E - Enter Door / Painting / Exit Level",
                    "ESC - Pause Menu",
                    "",
                    "EXPLORE Peach's Castle in First-Person!",
                    "N64DD 60fps | Super FX Rendering",
                    "",
                    "Press ENTER to close"
                ]
                for i,line in enumerate(lines):
                    c = YELLOW if i==0 else WHITE
                    t = font_menu.render(line, True, c) if i==0 else font_small.render(line, True, c)
                    screen.blit(t, (100, 100+i*35))

            elif active_overlay == "credits":
                overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(230); overlay.fill(BLACK)
                screen.blit(overlay, (0,0))
                pygame.draw.rect(screen, BUTTON_GOLD, (60,60,WIDTH-120,HEIGHT-120), 3)
                lines = [
                    "ULTRA MARIO 64 - N64DD SUPER FX EDITION",
                    "",
                    "Engine: Pure Pygame 3D + Super FX Pipeline",
                    "Camera: SM64 Lakitu First-Person",
                    "Levels: All 15 Courses + Castle Hub",
                    "Secret Levels: 5 | Bowser Levels: 3",
                    "Total Stars: 120",
                    "Rendering: N64 15-bit Color, Vertex Jitter",
                    "Post-FX: CRT Scanlines, Vignette, Fog",
                    "",
                    f"Programming: Team Flames / Samsoft",
                    "Inspired by: Super Mario 64 (N64DD, 1996)",
                    "",
                    "Press ENTER to close"
                ]
                for i,line in enumerate(lines):
                    c = YELLOW if i==0 else WHITE
                    t = font_menu.render(line, True, c) if i==0 else font_small.render(line, True, c)
                    screen.blit(t, (100, 90+i*35))

        elif current_state == STATE_LEVEL_SELECT:
            screen.fill((10,10,30))
            title = font_big.render("LEVEL SELECT", True, YELLOW)
            screen.blit(title, (WIDTH//2-title.get_width()//2, 20))

            # Categories
            cats = {"Castle": [], "Courses": [], "Secret": [], "Bowser": []}
            for k in level_keys:
                if k.startswith("castle"): cats["Castle"].append(k)
                elif k.startswith("c"): cats["Courses"].append(k)
                elif k.startswith("s"): cats["Secret"].append(k)
                elif k.startswith("b"): cats["Bowser"].append(k)

            visible_start = max(0, level_select_idx - 12)
            visible_end = min(len(level_keys), visible_start + 18)

            y = 70
            for i in range(visible_start, visible_end):
                k = level_keys[i]
                info = LEVELS[k]
                selected = i == level_select_idx
                color = YELLOW if selected else WHITE
                prefix = "► " if selected else "  "

                # Category header color
                if k.startswith("castle"): cat_color = CASTLE_WALL
                elif k.startswith("c"): cat_color = BRIGHT_GREEN
                elif k.startswith("s"): cat_color = CYAN
                else: cat_color = LAVA_RED

                # Name
                txt = font_menu.render(f"{prefix}{info['name']}", True, color)
                screen.blit(txt, (40, y))

                # Stars available
                if info["stars"] > 0:
                    st = font_small.render(f"★{info['stars']}", True, YELLOW)
                    screen.blit(st, (500, y+5))

                # Required stars
                req = font_small.render(f"Req: {info['req']}★", True, cat_color)
                screen.blit(req, (600, y+5))

                # Category dot
                pygame.draw.circle(screen, cat_color, (25, y+12), 6)

                y += 28

            # Instructions
            inst = font_small.render("UP/DOWN: Navigate | ENTER: Play | ESC: Back", True, METAL_GREY)
            screen.blit(inst, (WIDTH//2-inst.get_width()//2, HEIGHT-30))

            # Scroll indicator
            if visible_start > 0:
                arr = font_menu.render("▲", True, WHITE)
                screen.blit(arr, (WIDTH-40, 70))
            if visible_end < len(level_keys):
                arr = font_menu.render("▼", True, WHITE)
                screen.blit(arr, (WIDTH-40, HEIGHT-60))

        elif current_state == STATE_GAME:
            sky = LEVELS[current_level_id]["sky"] if current_level_id else DD_GAME_SKY
            draw_sky_gradient(sky)
            # Ground horizon fog
            fog_color = (sky[0]//3, sky[1]//3, sky[2]//3)
            pygame.draw.rect(screen, fog_color, (0, cy, WIDTH, cy))

            # ============================================================
            # SM64 FIRST-PERSON INPUT + LAKITU CAMERA SYSTEM
            # ============================================================
            keys = pygame.key.get_pressed()

            # --- MOUSE LOOK (Lakitu orbital camera as first-person) ---
            if mouse_captured:
                mdx, mdy = pygame.mouse.get_rel()
                cam_target_yaw += mdx * MOUSE_SENS_X
                cam_target_pitch -= mdy * MOUSE_SENS_Y
                cam_target_pitch = max(PITCH_MIN, min(PITCH_MAX, cam_target_pitch))
            else:
                # Fallback: arrow keys / C-button style rotation
                pygame.mouse.get_rel()  # flush

            # Keyboard camera rotation (C-buttons / right-stick feel)
            if keys[pygame.K_LEFT]: cam_target_yaw -= KEY_TURN_SPEED
            if keys[pygame.K_RIGHT]: cam_target_yaw += KEY_TURN_SPEED
            if keys[pygame.K_UP]: cam_target_pitch = min(PITCH_MAX, cam_target_pitch + KEY_TURN_SPEED * 0.6)
            if keys[pygame.K_DOWN]: cam_target_pitch = max(PITCH_MIN, cam_target_pitch - KEY_TURN_SPEED * 0.6)

            # Smooth Lakitu camera interpolation (the classic SM64 lag feel)
            cam_yaw += (cam_target_yaw - cam_yaw) * CAM_LERP_YAW
            cam_pitch += (cam_target_pitch - cam_pitch) * CAM_LERP_PITCH

            # --- SM64 ANALOG STICK MOVEMENT ---
            # WASD moves Mario relative to camera facing direction
            input_fwd = 0.0  # Forward/back input (-1 to 1)
            input_strafe = 0.0  # Left/right input (-1 to 1)
            if keys[pygame.K_w]: input_fwd = -1.0
            if keys[pygame.K_s]: input_fwd = 1.0
            if keys[pygame.K_a]: input_strafe = -1.0
            if keys[pygame.K_d]: input_strafe = 1.0

            # Normalize diagonal
            input_mag = math.sqrt(input_fwd*input_fwd + input_strafe*input_strafe)
            if input_mag > 1.0:
                input_fwd /= input_mag
                input_strafe /= input_mag

            moving = abs(input_fwd) > 0.01 or abs(input_strafe) > 0.01

            # Sprint (shift = SM64 running speed)
            speed_mult = SPRINT_MULT if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1.0
            target_speed = MAX_SPEED * speed_mult

            if moving and mario:
                # World-space desired velocity from camera-relative input
                sin_yaw = math.sin(cam_yaw)
                cos_yaw = math.cos(cam_yaw)
                # Forward is -Z in camera space
                desired_vx = (input_strafe * cos_yaw + input_fwd * sin_yaw) * target_speed
                desired_vz = (-input_strafe * sin_yaw + input_fwd * cos_yaw) * target_speed
                # SM64-style acceleration (not instant — ramps up)
                vel_x += (desired_vx - vel_x) * (MOVE_ACCEL / target_speed)
                vel_z += (desired_vz - vel_z) * (MOVE_ACCEL / target_speed)
            else:
                # SM64-style deceleration (slide to stop)
                vel_x *= MOVE_DECEL
                vel_z *= MOVE_DECEL
                if abs(vel_x) < 0.1: vel_x = 0
                if abs(vel_z) < 0.1: vel_z = 0

            if mario:
                # Apply velocity to Mario position
                mario.x += vel_x
                mario.z += vel_z
                mario.yaw = cam_yaw  # Face camera direction

                # Update physics (gravity, jump, floor)
                mario.update()

                # --- HEAD BOB (authentic FPS feel when walking) ---
                ground_speed = math.sqrt(vel_x*vel_x + vel_z*vel_z)
                if ground_speed > 1.0 and not mario.is_jumping:
                    head_bob_phase += ground_speed * 0.02 * HEAD_BOB_SPEED
                    bob_y = math.sin(head_bob_phase) * HEAD_BOB_AMOUNT
                    bob_x = math.cos(head_bob_phase * 0.5) * HEAD_BOB_AMOUNT * 0.5
                else:
                    # Smoothly return to neutral
                    bob_y *= 0.85
                    bob_x *= 0.85
                    head_bob_phase *= 0.9

                # --- LAKITU POSITION SMOOTHING ---
                # Camera target = Mario's eye position
                cam_target_x = mario.x
                cam_target_y = mario.y + EYE_HEIGHT + bob_y
                cam_target_z = mario.z

                # Smooth lerp (the signature SM64 Lakitu lag)
                cam_x += (cam_target_x - cam_x) * CAM_LERP_POS
                cam_y += (cam_target_y - cam_y) * CAM_LERP_POS
                cam_z += (cam_target_z - cam_z) * CAM_LERP_POS

                # --- STAR COLLECTION ---
                for star in current_level_stars:
                    if not star.collected:
                        star.yaw += 0.05
                        dx = mario.x - star.x
                        dy = mario.y - star.y
                        dz = mario.z - star.z
                        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                        if dist < 60:
                            star.collected = True
                            sid = f"{current_level_id}_{star.star_id}"
                            collected_stars.add(sid)
                            star_flash = 30

                # --- COIN COLLECTION ---
                for coin in current_level_coins:
                    if not coin.collected:
                        coin.yaw += 0.08
                        dx = mario.x - coin.x
                        dy = mario.y - coin.y
                        dz = mario.z - coin.z
                        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                        if dist < 40:
                            coin.collected = True
                            total_coins += 1
                            coin_flash = 15
                            if total_coins % 50 == 0:
                                mario.lives += 1

            # ============================================================
            # RENDER WORLD (First-Person — no Mario model rendered)
            # ============================================================
            all_polys = []
            if current_level_mesh:
                all_polys.extend(render_mesh(screen, current_level_mesh,
                    cam_x, cam_y, cam_z, cam_yaw, cam_pitch, cx, cy))
            # Render stars
            for star in current_level_stars:
                if not star.collected:
                    all_polys.extend(render_mesh(screen, star,
                        cam_x, cam_y, cam_z, cam_yaw, cam_pitch, cx, cy))
            # Render coins
            for coin in current_level_coins:
                if not coin.collected:
                    all_polys.extend(render_mesh(screen, coin,
                        cam_x, cam_y, cam_z, cam_yaw, cam_pitch, cx, cy))
            # NOTE: Mario is NOT rendered — first-person view

            # Depth sort (painter's algorithm)
            all_polys.sort(key=lambda x: x['depth'], reverse=True)

            # ============================================================
            # SUPER FX RENDERING PIPELINE
            # ============================================================
            for item in all_polys:
                depth = item['depth']
                # N64 distance fog
                fog = min(1.0, depth / VIEW_DISTANCE)
                r, g, b = item['color']
                sr, sg, sb = sky
                # Fog blend
                fr = int(r + (sr - r) * fog)
                fg = int(g + (sg - g) * fog)
                fb = int(b + (sb - b) * fog)
                # N64 color depth reduction (Super FX 15-bit color)
                fr = (fr >> 3) << 3  # 5-bit per channel
                fg = (fg >> 3) << 3
                fb = (fb >> 3) << 3
                fr = max(0, min(255, fr))
                fg = max(0, min(255, fg))
                fb = max(0, min(255, fb))
                pygame.draw.polygon(screen, (fr, fg, fb), item['poly'])

            # ============================================================
            # FIRST-PERSON HUD OVERLAY
            # ============================================================

            # --- Mario's Gloved Hands (FPS arms) ---
            bob_offset = math.sin(head_bob_phase) * 4 if mario and not mario.is_jumping else 0
            hand_y = int(HEIGHT - 80 + bob_offset)
            # Left glove
            pygame.draw.ellipse(screen, WHITE,
                (30, hand_y, 70, 50))
            pygame.draw.ellipse(screen, (230, 230, 230),
                (35, hand_y + 5, 60, 40))
            # Left arm (red sleeve)
            pygame.draw.rect(screen, RED,
                (-10, hand_y + 20, 60, 80))
            # Right glove
            pygame.draw.ellipse(screen, WHITE,
                (WIDTH - 100, hand_y, 70, 50))
            pygame.draw.ellipse(screen, (230, 230, 230),
                (WIDTH - 95, hand_y + 5, 60, 40))
            # Right arm (red sleeve)
            pygame.draw.rect(screen, RED,
                (WIDTH - 50, hand_y + 20, 60, 80))

            # --- Crosshair (subtle SM64DD target) ---
            ch_size = 8
            ch_color = (255, 255, 255, 128)
            # Horizontal line
            pygame.draw.line(screen, WHITE, (cx - ch_size, cy), (cx - 3, cy), 1)
            pygame.draw.line(screen, WHITE, (cx + 3, cy), (cx + ch_size, cy), 1)
            # Vertical line
            pygame.draw.line(screen, WHITE, (cx, cy - ch_size), (cx, cy - 3), 1)
            pygame.draw.line(screen, WHITE, (cx, cy + 3), (cx, cy + ch_size), 1)
            # Center dot
            pygame.draw.circle(screen, YELLOW, (cx, cy), 1)

            # --- Speed indicator (N64 debug style) ---
            if mario:
                spd = math.sqrt(vel_x*vel_x + vel_z*vel_z)
                spd_w = int(min(spd / MAX_SPEED, 1.0) * 80)
                pygame.draw.rect(screen, DARK_GREY, (10, 10, 82, 8))
                spd_color = BRIGHT_GREEN if spd < MAX_SPEED * 0.7 else YELLOW if spd < MAX_SPEED else RED
                pygame.draw.rect(screen, spd_color, (11, 11, spd_w, 6))

            draw_hud()
            draw_level_intro()

            # Navigation hints
            hint = ""
            if current_level_id and "castle" in current_level_id:
                hint = "E: Enter Door/Painting"
            elif current_level_id:
                hint = "E: Exit Level"
            if hint:
                ht = font_small.render(hint, True, YELLOW)
                screen.blit(ht, (WIDTH//2 - ht.get_width()//2, 25))

        elif current_state == STATE_PAUSE:
            # Dim game behind
            overlay = pygame.Surface((WIDTH,HEIGHT)); overlay.set_alpha(180); overlay.fill(BLACK)
            screen.blit(overlay, (0,0))

            ptitle = font_big.render("PAUSED", True, YELLOW)
            screen.blit(ptitle, (WIDTH//2-ptitle.get_width()//2, 150))

            pause_items = [
                ("ESC - Resume", WHITE),
                ("R - Restart Level", WHITE),
                ("Q - Quit to Menu", WHITE),
                ("", WHITE),
                (f"Stars: {len(collected_stars)}/{STAR_TOTAL}", YELLOW),
                (f"Coins: {total_coins}", YELLOW),
                (f"Lives: {mario.lives if mario else 4}", RED),
            ]
            for i,(txt,col) in enumerate(pause_items):
                if txt:
                    t = font_menu.render(txt, True, col)
                    screen.blit(t, (WIDTH//2-t.get_width()//2, 220+i*35))

        # ============================================================
        # N64DD SUPER FX POST-PROCESSING PIPELINE
        # ============================================================
        # 1. CRT Scanlines (authentic N64 composite output)
        scanline_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(scanline_surf, (0, 0, 0, 40), (0, y), (WIDTH, y), 1)
        screen.blit(scanline_surf, (0, 0))

        # 2. N64DD vignette (CRT edge darkening)
        if current_state == STATE_GAME:
            vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Top/bottom edge darken
            for i in range(30):
                alpha = int(60 * (1 - i/30))
                pygame.draw.line(vignette, (0, 0, 0, alpha), (0, i), (WIDTH, i), 1)
                pygame.draw.line(vignette, (0, 0, 0, alpha), (0, HEIGHT-1-i), (WIDTH, HEIGHT-1-i), 1)
            # Left/right edge darken
            for i in range(20):
                alpha = int(40 * (1 - i/20))
                pygame.draw.line(vignette, (0, 0, 0, alpha), (i, 0), (i, HEIGHT), 1)
                pygame.draw.line(vignette, (0, 0, 0, alpha), (WIDTH-1-i, 0), (WIDTH-1-i, HEIGHT), 1)
            screen.blit(vignette, (0, 0))

        # 3. N64 frame counter / timing debug (top right)
        if current_state == STATE_GAME:
            fps_actual = clock.get_fps()
            fps_color = BRIGHT_GREEN if fps_actual >= 58 else YELLOW if fps_actual >= 30 else RED
            frame_txt = font_small.render(f"N64DD {int(fps_actual)}fps", True, fps_color)
            screen.blit(frame_txt, (WIDTH - 110, 3))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
