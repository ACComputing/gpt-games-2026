import pygame
import math
import sys
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500
VIEW_DISTANCE = 8000

# SM64 Physics Constants (Scaled)
MOUSE_SENS_X = 0.003
MOUSE_SENS_Y = 0.002
PITCH_MIN = -1.5
PITCH_MAX = 1.5
EYE_HEIGHT = 160  # Mario's eye height approx

# Physics
MAX_RUN_SPEED = 32.0
RUN_ACCEL = 2.0
RUN_DECEL = 1.5
AIR_ACCEL = 1.2
AIR_DECEL = 0.1
GRAVITY = 2.0
TERMINAL_VELOCITY = -75.0
JUMP_FORCE = 52.0
SWIM_SPEED = 15.0
FRICTION = 0.9

# =====================================================================
# PALETTES
# =====================================================================
# Castle
CG_GRASS = (0, 154, 0); CG_PATH = (220, 190, 140)
CG_WALL = (240, 230, 200); CG_ROOF = (220, 40, 40)
CG_WATER = (20, 100, 220)

# Levels
BOB_GRASS = (0, 168, 0); BOB_DIRT = (144, 104, 56)
WF_STONE = (184, 176, 160); WF_BRICK = (176, 152, 112)
JRB_WATER = (0, 72, 200); JRB_SAND = (224, 200, 152)
CCM_SNOW = (240, 248, 255); CCM_WOOD = (100, 60, 20)
BBH_WALL = (96, 80, 96); BBH_FLOOR = (64, 56, 64)
HMC_ROCK = (104, 88, 72); HMC_TOXIC = (100, 160, 20)
LLL_LAVA = (232, 40, 0); LLL_PLAT = (96, 80, 64)
SSL_SAND = (232, 200, 136); SSL_STONE = (200, 180, 140)
DDD_WATER = (0, 48, 160); DDD_METAL = (144, 152, 168)
SL_SNOW = (240, 248, 255); SL_ICE = (160, 200, 248)
WDW_WALL = (160, 152, 136); WDW_WATER = (48, 112, 216)
TTM_ROCK = (128, 120, 104); TTM_MUSH = (200, 40, 40)
THI_GRASS = (0, 168, 0); THI_WATER = (24, 88, 200)
TTC_WOOD = (168, 120, 56); TTC_GOLD = (200, 180, 50)
RR_CLOUD = (240, 240, 255); RR_RAINBOW = [(255,0,0),(255,165,0),(255,255,0),(0,255,0),(0,0,255),(75,0,130)]

# Universal
WHITE=(255,255,255); BLACK=(0,0,0); RED=(220,20,60); 
GREY=(128,128,128); DARK_GREY=(50,50,50); GOLD=(255,215,0)
PIPE_GREEN=(0,180,0); YELLOW=(255, 255, 0)

SM64_SKIES = {
    "default": ((80, 152, 248), (255, 255, 255)),
    "dark": ((10, 5, 20), (40, 30, 60)),
    "fire": ((60, 10, 0), (120, 40, 0)),
    "water": ((20, 40, 100), (60, 100, 180)),
}

# =====================================================================
# ENGINE
# =====================================================================
class Vector3:
    __slots__ = ['x','y','z']
    def __init__(self, x, y, z): self.x, self.y, self.z = x, y, z

class Face:
    __slots__ = ['indices','color','normal','center']
    def __init__(self, indices, color, normal):
        self.indices = indices
        self.color = color
        self.normal = normal

class Mesh:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def add_vert(self, x, y, z):
        self.vertices.append(Vector3(x, y, z))
        return len(self.vertices) - 1

    def add_face(self, idxs, color):
        # Compute normal
        v0 = self.vertices[idxs[0]]
        v1 = self.vertices[idxs[1]]
        v2 = self.vertices[idxs[2]]
        ax, ay, az = v1.x-v0.x, v1.y-v0.y, v1.z-v0.z
        bx, by, bz = v2.x-v0.x, v2.y-v0.y, v2.z-v0.z
        nx, ny, nz = ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx
        l = math.sqrt(nx*nx + ny*ny + nz*nz)
        if l == 0: l = 1
        self.faces.append(Face(idxs, color, (nx/l, ny/l, nz/l)))

    # --- Primitive Generators ---
    def add_cube(self, w, h, d, ox, oy, oz, color):
        hw, hh, hd = w/2, h/2, d/2
        # Bottom
        i0=self.add_vert(-hw+ox, -hh+oy, -hd+oz); i1=self.add_vert(hw+ox, -hh+oy, -hd+oz)
        i2=self.add_vert(hw+ox, -hh+oy, hd+oz);   i3=self.add_vert(-hw+ox, -hh+oy, hd+oz)
        # Top
        i4=self.add_vert(-hw+ox, hh+oy, -hd+oz);  i5=self.add_vert(hw+ox, hh+oy, -hd+oz)
        i6=self.add_vert(hw+ox, hh+oy, hd+oz);    i7=self.add_vert(-hw+ox, hh+oy, hd+oz)
        
        self.add_face([i0, i1, i5, i4], color) # Back
        self.add_face([i1, i2, i6, i5], color) # Right
        self.add_face([i2, i3, i7, i6], color) # Front
        self.add_face([i3, i0, i4, i7], color) # Left
        self.add_face([i4, i5, i6, i7], color) # Top
        self.add_face([i3, i2, i1, i0], color) # Bot

    def add_slope(self, w, d, h1, h2, ox, oy, oz, color):
        hw, hd = w/2, d/2
        # Bot
        i0=self.add_vert(-hw+ox, 0+oy, -hd+oz); i1=self.add_vert(hw+ox, 0+oy, -hd+oz)
        i2=self.add_vert(hw+ox, 0+oy, hd+oz);   i3=self.add_vert(-hw+ox, 0+oy, hd+oz)
        # Top
        i4=self.add_vert(-hw+ox, h2+oy, -hd+oz); i5=self.add_vert(hw+ox, h2+oy, -hd+oz)
        i6=self.add_vert(hw+ox, h1+oy, hd+oz);   i7=self.add_vert(-hw+ox, h1+oy, hd+oz)
        
        self.add_face([i4, i5, i6, i7], color) # Slope
        self.add_face([i3, i2, i6, i7], color) # Front
        self.add_face([i1, i0, i4, i5], color) # Back
        self.add_face([i0, i3, i7, i4], color) # Left
        self.add_face([i2, i1, i5, i6], color) # Right

    def add_cylinder(self, r, h, ox, oy, oz, color, seg=8):
        top_verts = []
        bot_verts = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            top_verts.append(self.add_vert(ox+math.cos(a)*r, oy+h, oz+math.sin(a)*r))
            bot_verts.append(self.add_vert(ox+math.cos(a)*r, oy, oz+math.sin(a)*r))
        
        # Sides
        for i in range(seg):
            j = (i+1)%seg
            self.add_face([bot_verts[i], bot_verts[j], top_verts[j], top_verts[i]], color)
        
        # Caps
        self.add_face(list(reversed(top_verts)), color)
        self.add_face(bot_verts, color)

    def add_cone(self, r, h, ox, oy, oz, color, seg=8):
        tip = self.add_vert(ox, oy+h, oz)
        base_verts = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            base_verts.append(self.add_vert(ox+math.cos(a)*r, oy, oz+math.sin(a)*r))
        
        for i in range(seg):
            j = (i+1)%seg
            self.add_face([base_verts[i], base_verts[j], tip], color)
        self.add_face(base_verts, color)

# =====================================================================
# 1:1 LEVEL BUILDERS
# =====================================================================

def b_castle():
    m = Mesh()
    # Grounds
    m.add_cube(3000, 20, 2000, 0, -20, 500, CG_GRASS) # Lawn
    m.add_cube(1200, 10, 500, 0, -15, -600, CG_WATER) # Moat
    m.add_cube(200, 10, 600, 0, 10, -500, CG_PATH) # Bridge
    
    # Castle Body
    cz = -1000
    m.add_cube(600, 400, 400, 0, 200, cz, CG_WALL)
    m.add_cylinder(100, 400, -300, 0, cz, CG_WALL) # Left Turret
    m.add_cylinder(100, 400, 300, 0, cz, CG_WALL) # Right Turret
    m.add_cone(120, 150, -300, 400, cz, CG_ROOF)
    m.add_cone(120, 150, 300, 400, cz, CG_ROOF)
    m.add_cylinder(250, 200, 0, 400, cz, CG_WALL) # Top tower
    m.add_cone(270, 180, 0, 600, cz, CG_ROOF)
    
    # Entrance
    m.add_cube(150, 200, 50, 0, 100, cz+225, CG_WALL)
    m.add_cube(80, 120, 60, 0, 60, cz+225, (100, 60, 20)) # Door
    return m

def b_bob():
    m = Mesh()
    # Field
    m.add_cube(4000, 20, 4000, 0, -20, 0, BOB_GRASS)
    # Path
    m.add_slope(300, 400, 50, 0, 0, 0, -1000, BOB_DIRT) # Start ramp
    m.add_cube(300, 50, 1000, 0, 25, -500, BOB_DIRT)
    # Bridge Area
    m.add_cube(200, 10, 300, -800, 30, 0, (150, 100, 50)) # Bridge 1
    m.add_cube(200, 10, 300, 800, 30, 0, (150, 100, 50)) # Bridge 2
    # Mountain
    m.add_cylinder(800, 400, 0, 0, 1500, BOB_DIRT, 12) # Base
    m.add_cylinder(600, 300, 0, 400, 1500, BOB_DIRT, 10) # Mid
    m.add_cylinder(400, 200, 0, 700, 1500, (100, 100, 100), 8) # Top
    # Spiral Path
    for i in range(10):
        a = i * 0.8
        r = 850 - i*20
        h = i * 80
        m.add_cube(150, 20, 150, math.cos(a)*r, h, 1500+math.sin(a)*r, BOB_DIRT)
    # Chain Chomp Gate
    m.add_cube(20, 150, 20, -500, 75, -500, WHITE)
    m.add_cube(20, 150, 20, -300, 75, -500, WHITE)
    return m

def b_wf():
    m = Mesh()
    # Base
    m.add_cube(2000, 50, 2000, 0, -25, 0, WF_STONE)
    # Ramp
    m.add_slope(300, 600, 200, 0, -500, 0, 800, WF_STONE)
    # Path with sliding blocks
    m.add_cube(800, 200, 300, 500, 100, 0, WF_BRICK)
    m.add_cube(100, 180, 50, 500, 100, 200, GREY) # Sliding block
    # Pool
    m.add_cube(400, 20, 400, -800, 100, 0, JRB_WATER)
    # Tower
    m.add_cylinder(300, 600, 0, 200, -800, WF_STONE, 10)
    # Plank
    m.add_cube(40, 10, 400, 200, 800, -800, (150, 100, 50))
    return m

def b_jrb():
    m = Mesh()
    # Water surface
    m.add_cube(3000, 10, 3000, 0, 0, 0, JRB_WATER)
    # Sand bed
    m.add_cube(3000, 50, 3000, 0, -800, 0, JRB_SAND)
    # Sunken Ship
    m.add_cube(400, 200, 800, 0, -700, 0, (100, 60, 30))
    m.add_slope(300, 200, 100, 0, 0, -550, 400, (100, 60, 30)) # Bow
    # Pillars
    m.add_cylinder(50, 800, -800, -800, -800, WHITE)
    m.add_cylinder(50, 800, 800, -800, -800, WHITE)
    # Cave
    m.add_cube(500, 200, 500, 0, -800, 1200, HMC_ROCK)
    return m

def b_ccm():
    m = Mesh()
    # Mountain Cone
    m.add_cone(1500, 1500, 0, -200, 0, CCM_SNOW, 16)
    # Chimney / Start
    m.add_cube(200, 200, 200, 0, 1300, 0, CCM_WOOD)
    # Slide path (External)
    for i in range(20):
        a = i * 0.5
        r = 1400 + i*10
        h = 1300 - i*60
        m.add_cube(200, 20, 200, math.cos(a)*r, h, math.sin(a)*r, CCM_SNOW)
    # Broken Bridge
    m.add_cube(100, 10, 300, 800, 800, 800, CCM_WOOD)
    m.add_cube(100, 10, 300, 800, 800, 1200, CCM_WOOD)
    # Snowman Head
    m.add_cylinder(200, 200, -800, 200, -800, WHITE)
    return m

def b_bbh():
    m = Mesh()
    # Ground
    m.add_cube(3000, 20, 3000, 0, -20, 0, BBH_FLOOR)
    # Mansion
    m.add_cube(1200, 600, 800, 0, 300, 0, BBH_WALL) # Main
    m.add_cube(400, 400, 600, -800, 200, 0, BBH_WALL) # Left Wing
    m.add_cube(400, 400, 600, 800, 200, 0, BBH_WALL) # Right Wing
    # Balcony
    m.add_cube(300, 20, 100, 0, 500, 450, DARK_GREY)
    # Shed
    m.add_cube(200, 150, 200, -1000, 75, -800, BBH_WALL)
    return m

def b_hmc():
    m = Mesh()
    # Central Hub
    m.add_cube(600, 20, 600, 0, 0, 0, HMC_ROCK)
    # Paths
    m.add_cube(200, 20, 800, 0, 0, -700, HMC_ROCK) # To Lake
    m.add_cube(200, 20, 800, 0, 0, 700, HMC_ROCK) # To Toxic
    # Underground Lake
    m.add_cube(1000, 20, 1000, 0, -200, -1500, JRB_WATER)
    m.add_cylinder(100, 50, 0, -200, -1500, (50, 150, 50)) # Dorrie-ish
    # Toxic Maze
    m.add_cube(1000, 20, 1000, 0, -100, 1500, HMC_TOXIC)
    # Walls in maze
    m.add_cube(20, 200, 800, 200, 0, 1500, HMC_ROCK)
    return m

def b_lll():
    m = Mesh()
    # Lava Ocean
    m.add_cube(4000, 20, 4000, 0, -20, 0, LLL_LAVA)
    # Volcano
    m.add_cone(600, 400, 0, 0, 0, LLL_PLAT, 12)
    # Sliding Puzzle
    m.add_cube(600, 10, 600, -1200, 10, 0, LLL_PLAT)
    # Log Area
    m.add_cylinder(50, 400, 1200, 25, 0, (100, 60, 20)) # Log (static)
    m.add_cube(300, 10, 300, 1200, 10, 400, LLL_PLAT)
    return m

def b_ssl():
    m = Mesh()
    # Desert
    m.add_cube(4000, 20, 4000, 0, -20, 0, SSL_SAND)
    # Pyramid
    m.add_pyramid(1000, 600, 0, 0, -500, SSL_STONE)
    # Pillars
    coords = [(-1200, 1200), (1200, 1200), (-1200, -1200), (1200, -1200)]
    for x, z in coords:
        m.add_cylinder(80, 400, x, 0, z, SSL_STONE)
    # Tox Box Path
    m.add_cube(800, 20, 800, -1000, 200, 0, SSL_STONE) # Quicksand maze area
    return m

def b_ddd():
    m = Mesh()
    # Water
    m.add_cube(3000, 20, 3000, 0, -20, 0, DDD_WATER)
    # Dock
    m.add_cube(600, 10, 400, 0, 0, -1000, (150, 100, 50))
    # Submarine
    m.add_cylinder(200, 600, 0, -100, 0, DDD_METAL, 12) # Hull (Vertical approximation or rotate logic needed)
    # Actually just a box for sub in this simple engine
    m.add_cube(300, 150, 800, 0, 50, 0, DDD_METAL) 
    m.add_cylinder(80, 80, 0, 200, 0, DDD_METAL) # Periscope base
    # Poles
    m.add_cylinder(10, 1000, -800, -500, 0, DDD_METAL)
    return m

def b_sl():
    m = Mesh()
    # Snow ground
    m.add_cube(3000, 20, 3000, 0, -20, 0, SL_SNOW)
    # Giant Snowman
    m.add_cylinder(600, 400, 0, 0, 0, SL_SNOW, 12) # Base
    m.add_cylinder(400, 300, 0, 400, 0, SL_SNOW, 10) # Head
    m.add_cube(800, 10, 100, 0, 300, 500, CCM_WOOD) # Walkway
    # Ice Sculpture
    m.add_cube(300, 300, 300, -1000, 150, 0, SL_ICE)
    # Igloo
    m.add_cylinder(300, 150, 1000, 0, 1000, SL_SNOW)
    return m

def b_wdw():
    m = Mesh()
    # Main Box
    m.add_cube(2000, 20, 2000, 0, -20, 0, WDW_WALL)
    # Water Level (Visual)
    m.add_cube(2000, 10, 2000, 0, 200, 0, WDW_WATER)
    # Buildings
    m.add_cube(400, 600, 400, -800, 300, -800, WDW_WALL)
    m.add_cube(400, 400, 400, 800, 200, 800, WDW_WALL)
    # Ramp
    m.add_slope(200, 800, 400, 0, 0, 0, 800, WDW_WALL)
    # Cage
    m.add_cube(200, 400, 200, 0, 200, 0, GREY)
    return m

def b_ttm():
    m = Mesh()
    # Mountain
    m.add_cylinder(1000, 1500, 0, 0, 0, TTM_ROCK, 12)
    # Mushrooms
    for i in range(5):
        m.add_cylinder(100, 20, 1200, 200 + i*200, -500 + i*200, TTM_MUSH)
        m.add_cylinder(20, 200 + i*200, 1200, 0, -500 + i*200, WHITE)
    # Waterfall
    m.add_cube(200, 1500, 20, 0, 750, -1010, JRB_WATER)
    return m

def b_thi():
    m = Mesh()
    # Ocean
    m.add_cube(4000, 20, 4000, 0, -20, 0, THI_WATER)
    # Huge Island
    m.add_cylinder(1500, 800, 0, 0, 0, THI_GRASS, 12)
    # Top Pool
    m.add_cube(500, 10, 500, 0, 800, 0, THI_WATER)
    # Pipes
    m.add_cylinder(100, 200, 1000, 0, 0, PIPE_GREEN)
    return m

def b_ttc():
    m = Mesh()
    # Floor
    m.add_cube(1000, 20, 1000, 0, -20, 0, TTC_WOOD)
    # Walls
    m.add_cube(20, 2000, 1000, 500, 1000, 0, TTC_WOOD)
    m.add_cube(20, 2000, 1000, -500, 1000, 0, TTC_WOOD)
    # Gears
    for i in range(10):
        h = i * 200
        m.add_cylinder(200, 20, 0, h, 0, TTC_GOLD)
        m.add_cube(150, 10, 400, 0, h+50, 0, TTC_GOLD) # Hands
    return m

def b_rr():
    m = Mesh()
    # Carpet Path
    for i in range(40):
        x = i * 100
        y = math.sin(i*0.2) * 200 + 500
        m.add_cube(100, 10, 50, x, y, 0, RR_RAINBOW[i%6])
    # Cruiser
    m.add_cube(600, 100, 300, 2000, 800, -1000, (150, 150, 255))
    # Big House
    m.add_cube(400, 600, 400, -1000, 300, 0, RR_CLOUD)
    return m

# Bowser Stages
def b_bitdw():
    m = Mesh()
    m.add_cube(500, 20, 500, 0, 0, 0, BDW_STONE)
    for i in range(10):
        m.add_cube(100, 20, 100, i*150, i*20, i*100, (0, 200, 200))
    return m

def b_bitfs():
    m = Mesh()
    m.add_cube(4000, 20, 4000, 0, -50, 0, LLL_LAVA)
    m.add_cube(200, 20, 2000, 0, 0, 0, BFS_METAL)
    m.add_cylinder(20, 500, 0, 0, 1000, GREY) # Pole
    return m

def b_bits():
    m = Mesh()
    m.add_slope(300, 2000, 500, 0, 0, 250, 0, WF_STONE) # Endless stairs
    m.add_cylinder(800, 20, 0, 600, -1000, (150, 50, 50)) # Final Arena
    return m

# Secrets
def b_pss():
    m = Mesh()
    m.add_cube(200, 20, 200, 0, 500, 0, CG_WALL)
    for i in range(30):
        a=i*0.3; r=150+i*20
        m.add_cube(100, 10, 100, math.cos(a)*r, 500-i*20, math.sin(a)*r, CCM_WOOD)
    return m

def b_cotmc():
    m = Mesh()
    m.add_cube(2000, 20, 2000, 0, -20, 0, HMC_ROCK)
    m.add_cube(800, 10, 800, 0, 0, 0, HMC_TOXIC) # Liquid metal
    m.add_cube(100, 20, 100, 0, 20, 0, PIPE_GREEN) # Switch
    return m

def b_totwc():
    m = Mesh()
    m.add_cylinder(300, 1000, 0, 0, 0, RR_CLOUD, 12)
    m.add_cube(100, 20, 100, 0, 1000, 0, RED)
    return m

def b_vcutm():
    m = Mesh()
    m.add_cube(200, 500, 200, 0, 0, 0, HMC_ROCK)
    m.add_cube(100, 20, 100, 500, -500, 0, SL_ICE) # Fall check
    return m

def b_wmotr():
    m = Mesh()
    for i in range(10):
        m.add_cube(200, 20, 200, i*300, i*100, 0, RR_CLOUD)
    return m

# =====================================================================
# GAME CLASS
# =====================================================================

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SM64 PC Port - Python 1:1 Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 16)
        
        self.levels = {
            pygame.K_1: ("Bob-omb Battlefield", b_bob, "default"),
            pygame.K_2: ("Whomp's Fortress", b_wf, "default"),
            pygame.K_3: ("Jolly Roger Bay", b_jrb, "water"),
            pygame.K_4: ("Cool Cool Mountain", b_ccm, "default"),
            pygame.K_5: ("Big Boo's Haunt", b_bbh, "dark"),
            pygame.K_6: ("Hazy Maze Cave", b_hmc, "dark"),
            pygame.K_7: ("Lethal Lava Land", b_lll, "fire"),
            pygame.K_8: ("Shifting Sand Land", b_ssl, "default"),
            pygame.K_9: ("Dire Dire Docks", b_ddd, "water"),
            pygame.K_0: ("Snowman's Land", b_sl, "default"),
            pygame.K_MINUS: ("Wet-Dry World", b_wdw, "default"),
            pygame.K_EQUALS: ("Tall Tall Mountain", b_ttm, "default"),
            pygame.K_q: ("Tiny-Huge Island", b_thi, "default"),
            pygame.K_w: ("Tick Tock Clock", b_ttc, "default"),
            pygame.K_e: ("Rainbow Ride", b_rr, "default"),
            pygame.K_r: ("Castle Grounds", b_castle, "default"),
            pygame.K_t: ("Bowser 1", b_bitdw, "dark"),
            pygame.K_y: ("Bowser 2", b_bitfs, "fire"),
            pygame.K_u: ("Bowser 3", b_bits, "dark"),
            pygame.K_F1: ("Princess Slide", b_pss, "default"),
            pygame.K_F2: ("Metal Cap", b_cotmc, "dark"),
            pygame.K_F3: ("Wing Cap", b_totwc, "default"),
            pygame.K_F4: ("Vanish Cap", b_vcutm, "dark"),
            pygame.K_F5: ("Wing Mario Rainbow", b_wmotr, "default")
        }
        
        self.pos = [0, 500, 1000]
        self.vel = [0, 0, 0]
        self.yaw = 0
        self.pitch = 0
        self.state = "air" # ground, air, water
        
        self.load_level(b_castle, "default")
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def load_level(self, builder, sky):
        self.mesh = builder()
        self.sky_colors = SM64_SKIES.get(sky, SM64_SKIES["default"])
        self.pos = [0, 500, 800]
        self.vel = [0, 0, 0]

    def physics(self, dt):
        keys = pygame.key.get_pressed()
        
        # Mouse
        mx, my = pygame.mouse.get_rel()
        self.yaw += mx * MOUSE_SENS_X
        self.pitch = max(PITCH_MIN, min(PITCH_MAX, self.pitch - my * MOUSE_SENS_Y))
        
        # Input Vectors
        fd, sd = 0, 0
        if keys[pygame.K_w]: fd += 1
        if keys[pygame.K_s]: fd -= 1
        if keys[pygame.K_a]: sd -= 1
        if keys[pygame.K_d]: sd += 1
        
        # Rotation
        move_x = fd * math.sin(self.yaw) + sd * math.cos(self.yaw)
        move_z = fd * math.cos(self.yaw) - sd * math.sin(self.yaw)
        
        # State Logic
        is_water = self.pos[1] < -50 and self.sky_colors == SM64_SKIES["water"] # Simple water check
        
        if is_water:
            self.state = "water"
            target_speed = SWIM_SPEED
            self.vel[0] += move_x * RUN_ACCEL * 0.5
            self.vel[2] += move_z * RUN_ACCEL * 0.5
            self.vel[0] *= 0.95
            self.vel[2] *= 0.95
            if keys[pygame.K_SPACE]: self.vel[1] += 2.0
            if keys[pygame.K_LSHIFT]: self.vel[1] -= 2.0
            self.vel[1] *= 0.9
        
        else:
            # Gravity
            self.vel[1] = max(TERMINAL_VELOCITY, self.vel[1] - GRAVITY)
            
            # Ground Movement
            if self.state == "ground":
                target_speed = MAX_RUN_SPEED
                if fd != 0 or sd != 0:
                    self.vel[0] += move_x * RUN_ACCEL
                    self.vel[2] += move_z * RUN_ACCEL
                else:
                    self.vel[0] *= RUN_DECEL
                    self.vel[2] *= RUN_DECEL
                
                # Jump
                if keys[pygame.K_SPACE]:
                    self.vel[1] = JUMP_FORCE
                    self.state = "air"
            else:
                # Air control
                self.vel[0] += move_x * AIR_ACCEL
                self.vel[2] += move_z * AIR_ACCEL
                self.vel[0] *= 0.98
                self.vel[2] *= 0.98

        # Cap horizontal speed
        h_speed = math.sqrt(self.vel[0]**2 + self.vel[2]**2)
        if h_speed > MAX_RUN_SPEED:
            scale = MAX_RUN_SPEED / h_speed
            self.vel[0] *= scale
            self.vel[2] *= scale

        # Integration
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.pos[2] += self.vel[2]
        
        # Collision (Ground)
        ground_y = -2000
        for f in self.mesh.faces:
            # Simple point-in-rect XZ check for ground
            vs = [self.mesh.vertices[i] for i in f.indices]
            min_x = min(v.x for v in vs) - 10
            max_x = max(v.x for v in vs) + 10
            min_z = min(v.z for v in vs) - 10
            max_z = max(v.z for v in vs) + 10
            
            if min_x <= self.pos[0] <= max_x and min_z <= self.pos[2] <= max_z:
                # Plane Y at X,Z
                nx, ny, nz = f.normal
                if ny > 0.3: # Walkable
                    # Plane eq: nx(x-v0x) + ny(y-v0y) + nz(z-v0z) = 0
                    # y = v0y - (nx(x-v0x) + nz(z-v0z))/ny
                    v0 = vs[0]
                    h = v0.y - (nx*(self.pos[0]-v0.x) + nz*(self.pos[2]-v0.z))/ny
                    if h > ground_y and h <= self.pos[1] + 30:
                        ground_y = h
        
        if self.pos[1] <= ground_y + EYE_HEIGHT and self.vel[1] <= 0:
            self.pos[1] = ground_y + EYE_HEIGHT
            self.vel[1] = 0
            self.state = "ground"
        elif not is_water:
            self.state = "air"
            
        if self.pos[1] < -3000: # Void
            self.pos = [0, 1000, 0]
            self.vel = [0, 0, 0]

    def render(self):
        # Sky
        c1, c2 = self.sky_colors
        for y in range(HEIGHT):
            t = y / HEIGHT
            c = (c1[0]*(1-t)+c2[0]*t, c1[1]*(1-t)+c2[1]*t, c1[2]*(1-t)+c2[2]*t)
            pygame.draw.line(self.screen, c, (0,y), (WIDTH,y))

        # 3D
        cx, cy, cz = self.pos
        cy -= 20 # Camera slightly below hitbox top
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)
        
        faces = []
        
        # Transform all verts once
        t_verts = []
        for v in self.mesh.vertices:
            dx, dy, dz = v.x - cx, v.y - cy, v.z - cz
            
            # Yaw
            rx = dx*cos_y - dz*sin_y
            rz = dx*sin_y + dz*cos_y
            
            # Pitch
            ry = dy*cos_p - rz*sin_p
            rz = dy*sin_p + rz*cos_p
            
            t_verts.append((rx, ry, rz))
            
        for f in self.mesh.faces:
            # Backface Cull
            # Use precomputed face normal? No, need view space normal
            # Approx: Check center Z
            vs = [t_verts[i] for i in f.indices]
            
            # Clipping
            if any(v[2] < 10 for v in vs): continue
            
            # Painter sort val
            avg_z = sum(v[2] for v in vs) / len(vs)
            if avg_z > VIEW_DISTANCE: continue
            
            # Normal Check (Simplified)
            v0, v1, v2 = vs[0], vs[1], vs[2]
            nx = (v1[1]-v0[1])*(v2[2]-v0[2]) - (v1[2]-v0[2])*(v2[1]-v0[1])
            ny = (v1[2]-v0[2])*(v2[0]-v0[0]) - (v1[0]-v0[0])*(v2[2]-v0[2])
            nz = (v1[0]-v0[0])*(v2[1]-v0[1]) - (v1[1]-v0[1])*(v2[0]-v0[0])
            
            # View vector is (0,0,0) -> v0, which is just v0
            if v0[0]*nx + v0[1]*ny + v0[2]*nz >= 0: continue

            # Project
            pts = []
            for vx, vy, vz in vs:
                sx = (vx/vz) * FOV + WIDTH/2
                sy = (-vy/vz) * FOV + HEIGHT/2
                pts.append((sx, sy))
                
            faces.append((avg_z, pts, f.color))
            
        faces.sort(key=lambda x: x[0], reverse=True)
        
        for _, pts, col in faces:
            # Fake lighting
            pygame.draw.polygon(self.screen, col, pts)
            pygame.draw.polygon(self.screen, tuple(max(0,c-30) for c in col), pts, 1)

        # UI
        ui_txt = f"Map: {self.current_map_name} | FPS: {int(self.clock.get_fps())}"
        self.screen.blit(self.font.render(ui_txt, True, WHITE), (10, 10))
        self.screen.blit(self.font.render("WASD=Move Space=Jump Shift=Run", True, WHITE), (10, 30))
        self.screen.blit(self.font.render("1-0, Q-U=Warps", True, YELLOW), (10, 50))
        
        pygame.display.flip()

    def run(self):
        self.current_map_name = "Castle Grounds"
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: running = False
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: running = False
                    if e.key in self.levels:
                        name, builder, sky = self.levels[e.key]
                        self.current_map_name = name
                        self.load_level(builder, sky)
            
            self.physics(1)
            self.render()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
