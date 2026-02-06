import pygame
import math
import sys
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500
VIEW_DISTANCE = 6000

# SM64 PC Port Camera (First-Person Lakitu)
MOUSE_SENS_X = 0.003
MOUSE_SENS_Y = 0.002
PITCH_MIN = -1.2
PITCH_MAX = 1.0
CAM_LERP = 0.18
EYE_HEIGHT = 38
HEAD_BOB_SPEED = 10.0
HEAD_BOB_AMT = 3.0

# Movement (SM64-style analog)
MOVE_ACCEL = 1.8
MOVE_DECEL = 0.85
MAX_SPEED = 14
SPRINT_MULT = 1.6
JUMP_FORCE = 18
GRAVITY = 0.9
KEY_TURN = 0.06
STAR_TOTAL = 120

# =====================================================================
# SM64 PC PORT COLOR PALETTES (sourced from actual texture/vertex data)
# =====================================================================
# Castle Grounds
CG_GRASS_1 = (0, 154, 0)
CG_GRASS_2 = (0, 120, 0)
CG_PATH = (200, 176, 128)
CG_STONE = (168, 168, 152)
CG_MOAT = (0, 80, 180)
CG_MOAT_DEEP = (0, 50, 140)
CG_CASTLE_WALL = (232, 216, 176)
CG_CASTLE_ROOF = (200, 48, 48)
CG_CASTLE_TRIM = (248, 232, 176)
CG_TREE_TRUNK = (104, 64, 24)
CG_TREE_TOP = (0, 120, 24)
CG_TREE_TOP2 = (0, 88, 8)
CG_BRIDGE = (136, 96, 48)
CG_TOWER = (232, 208, 168)

# Bob-omb Battlefield
BOB_GRASS_1 = (0, 168, 0)
BOB_GRASS_2 = (0, 128, 0)
BOB_DIRT = (184, 136, 72)
BOB_PATH = (200, 176, 120)
BOB_MTN_LOW = (144, 104, 56)
BOB_MTN_MID = (128, 96, 48)
BOB_MTN_TOP = (152, 144, 128)
BOB_WATER = (24, 88, 200)
BOB_FENCE = (168, 136, 80)
BOB_SKY_TOP = (80, 144, 248)
BOB_SKY_BOT = (184, 216, 248)

# Whomp's Fortress
WF_STONE_1 = (184, 176, 160)
WF_STONE_2 = (152, 144, 128)
WF_GRASS = (0, 136, 0)
WF_BRICK = (176, 152, 112)
WF_DIRT = (160, 120, 64)

# Jolly Roger Bay
JRB_WATER = (0, 72, 200)
JRB_WATER_DEEP = (0, 40, 140)
JRB_SAND = (224, 200, 152)
JRB_CAVE = (80, 72, 64)
JRB_SHIP = (120, 80, 40)
JRB_CORAL = (200, 100, 120)
JRB_DOCK = (144, 104, 56)

# Cool Cool Mountain
CCM_SNOW_1 = (240, 248, 255)
CCM_SNOW_2 = (208, 224, 240)
CCM_ICE = (160, 200, 248)
CCM_ROCK = (136, 128, 120)
CCM_CABIN = (120, 72, 32)
CCM_SLIDE = (176, 208, 248)

# Big Boo's Haunt
BBH_WALL = (96, 80, 96)
BBH_FLOOR = (64, 56, 64)
BBH_ROOF = (72, 64, 72)
BBH_BRICK = (112, 96, 80)
BBH_GHOST = (216, 216, 232)
BBH_FENCE = (80, 72, 64)
BBH_GRAVE = (128, 120, 112)
BBH_WINDOW = (120, 168, 80)

# Hazy Maze Cave
HMC_ROCK_1 = (104, 88, 72)
HMC_ROCK_2 = (80, 64, 48)
HMC_TOXIC = (72, 120, 24)
HMC_METAL = (160, 168, 176)
HMC_WATER = (32, 64, 160)

# Lethal Lava Land
LLL_LAVA_1 = (232, 80, 0)
LLL_LAVA_2 = (248, 136, 0)
LLL_STONE = (96, 80, 64)
LLL_METAL = (136, 128, 120)
LLL_VOLCANO = (80, 56, 32)

# Shifting Sand Land
SSL_SAND_1 = (232, 200, 136)
SSL_SAND_2 = (208, 176, 112)
SSL_PYRAMID = (216, 184, 120)
SSL_BRICK = (184, 152, 96)
SSL_QUICKSAND = (192, 160, 88)
SSL_OASIS = (32, 96, 200)
SSL_PALM = (80, 144, 24)

# Dire Dire Docks
DDD_WATER = (0, 48, 160)
DDD_WATER_DEEP = (0, 24, 100)
DDD_DOCK = (144, 104, 56)
DDD_METAL = (144, 152, 168)
DDD_SUB = (112, 120, 128)
DDD_FLOOR = (72, 64, 56)

# Snowman's Land
SL_SNOW_1 = (240, 248, 255)
SL_SNOW_2 = (200, 216, 232)
SL_ICE = (144, 192, 248)
SL_IGLOO = (232, 240, 248)

# Wet-Dry World
WDW_BRICK = (184, 168, 144)
WDW_WATER = (48, 112, 216)
WDW_STONE = (160, 152, 136)
WDW_SWITCH = (168, 48, 200)

# Tall Tall Mountain
TTM_GRASS = (0, 152, 0)
TTM_DIRT = (152, 112, 56)
TTM_ROCK = (128, 120, 104)
TTM_SLIDE = (144, 104, 56)
TTM_WATER = (48, 120, 224)
TTM_MUSH_TOP = (216, 48, 48)
TTM_MUSH_STEM = (232, 216, 176)

# Tiny-Huge Island
THI_GRASS_1 = (0, 168, 0)
THI_GRASS_2 = (0, 120, 16)
THI_WATER = (24, 88, 200)
THI_BEACH = (216, 192, 144)
THI_PIPE = (0, 176, 0)

# Tick Tock Clock
TTC_WOOD = (168, 120, 56)
TTC_GEAR = (200, 176, 56)
TTC_METAL = (176, 184, 192)
TTC_HAND = (80, 72, 64)

# Rainbow Ride
RR_RAINBOW = [(248,56,56),(248,152,40),(248,232,40),(48,200,48),(56,104,248),(152,48,200)]
RR_CLOUD = (248, 248, 255)
RR_CARPET = (152, 48, 200)
RR_HOUSE = (232, 216, 176)

# Bowser levels
BDW_STONE = (80, 64, 80)
BDW_LAVA = (232, 80, 0)
BFS_METAL = (128, 136, 144)
BITS_STONE = (96, 80, 96)

# Universal
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
ORANGE = (255, 140, 0)
DARK_GREEN = (20, 80, 20)
DARK_GREY = (80, 80, 80)
LIGHT_GREY = (200, 200, 200)
DARK_BROWN = (80, 40, 10)
DARK_STONE = (100, 100, 100)
PURPLE = (120, 40, 180)
PIPE_GREEN = (0, 176, 0)
CARPET_RED = (160, 20, 30)


# =====================================================================
# SM64 SKY DEFINITIONS (top gradient, bottom gradient, fog color)
# =====================================================================
SM64_SKIES = {
    "castle_grounds": ((80, 152, 248), (184, 224, 248), (200, 220, 248)),
    "castle_f1":      ((48, 40, 32), (80, 72, 56), (60, 52, 40)),
    "castle_basement":((16, 12, 8), (32, 24, 16), (20, 16, 8)),
    "castle_upper":   ((56, 48, 40), (88, 80, 64), (64, 56, 44)),
    "castle_top":     ((160, 192, 248), (224, 236, 248), (200, 220, 248)),
    "c01_bob":        ((80, 144, 248), (184, 216, 248), (160, 200, 240)),
    "c02_whomp":      ((88, 152, 240), (176, 208, 240), (152, 192, 232)),
    "c03_jolly":      ((32, 72, 168), (80, 128, 200), (56, 96, 176)),
    "c04_cool":       ((128, 176, 248), (216, 232, 248), (192, 216, 248)),
    "c05_boo":        ((8, 4, 16), (24, 16, 32), (16, 8, 24)),
    "c06_hazy":       ((16, 16, 16), (32, 28, 24), (24, 20, 16)),
    "c07_lava":       ((40, 8, 0), (80, 24, 0), (56, 16, 0)),
    "c08_sand":       ((168, 152, 112), (216, 200, 160), (192, 176, 136)),
    "c09_dock":       ((16, 32, 96), (48, 72, 144), (32, 48, 120)),
    "c10_snow":       ((128, 176, 240), (208, 224, 248), (176, 200, 240)),
    "c11_wet":        ((104, 144, 200), (176, 200, 232), (144, 176, 216)),
    "c12_tall":       ((72, 136, 240), (168, 208, 248), (128, 176, 240)),
    "c13_tiny":       ((80, 152, 248), (184, 216, 248), (144, 192, 240)),
    "c14_clock":      ((32, 24, 16), (64, 48, 32), (48, 36, 24)),
    "c15_rainbow":    ((72, 112, 248), (160, 192, 248), (120, 152, 248)),
    "s_slide":        ((48, 40, 32), (80, 72, 56), (60, 52, 40)),
    "s_wing":         ((96, 144, 248), (192, 216, 248), (152, 184, 248)),
    "s_metal":        ((8, 8, 8), (24, 20, 16), (16, 12, 8)),
    "s_vanish":       ((16, 24, 48), (40, 56, 96), (28, 40, 72)),
    "s_tower":        ((128, 176, 248), (224, 240, 248), (192, 216, 248)),
    "b1_dark":        ((8, 0, 16), (24, 8, 32), (16, 4, 24)),
    "b2_fire":        ((32, 4, 0), (72, 16, 0), (48, 8, 0)),
    "b3_sky":         ((48, 32, 72), (96, 72, 128), (72, 48, 96)),
}


# =====================================================================
# 3D ENGINE
# =====================================================================
class Vector3:
    __slots__ = ['x','y','z']
    def __init__(self, x, y, z):
        self.x=x; self.y=y; self.z=z

class Face:
    __slots__ = ['indices','color','avg_z','normal']
    def __init__(self, indices, color):
        self.indices=indices; self.color=color; self.avg_z=0; self.normal=None

class Mesh:
    def __init__(self, x=0, y=0, z=0):
        self.x=x; self.y=y; self.z=z
        self.vertices=[]; self.faces=[]; self.yaw=0

    def add_cube(self, w, h, d, ox, oy, oz, color):
        si = len(self.vertices)
        hw,hh,hd = w/2,h/2,d/2
        for cx,cy,cz in [(-hw,-hh,-hd),(hw,-hh,-hd),(hw,hh,-hd),(-hw,hh,-hd),
                          (-hw,-hh,hd),(hw,-hh,hd),(hw,hh,hd),(-hw,hh,hd)]:
            self.vertices.append(Vector3(cx+ox,cy+oy,cz+oz))
        for fi,fc in [([0,1,2,3],color),([5,4,7,6],color),([4,0,3,7],color),
                       ([1,5,6,2],color),([3,2,6,7],color),([4,5,1,0],color)]:
            shifted=[i+si for i in fi]; face=Face(shifted,fc)
            v0,v1,v2=self.vertices[shifted[0]],self.vertices[shifted[1]],self.vertices[shifted[2]]
            ax,ay,az=v1.x-v0.x,v1.y-v0.y,v1.z-v0.z
            bx,by,bz=v2.x-v0.x,v2.y-v0.y,v2.z-v0.z
            nx,ny,nz=ay*bz-az*by,az*bx-ax*bz,ax*by-ay*bx
            l=math.sqrt(nx*nx+ny*ny+nz*nz)
            face.normal=(nx/l,ny/l,nz/l) if l!=0 else (0,0,1)
            self.faces.append(face)

    def add_pyramid(self, bw, height, ox, oy, oz, color):
        si=len(self.vertices); hw=bw/2
        for cx,cz in [(-hw,-hw),(hw,-hw),(hw,hw),(-hw,hw)]:
            self.vertices.append(Vector3(cx+ox,oy,cz+oz))
        self.vertices.append(Vector3(ox,oy+height,oz))
        for tri in [(0,1,4),(1,2,4),(2,3,4),(3,0,4)]:
            f=Face([si+t for t in tri],color); f.normal=(0,0.7,0.7); self.faces.append(f)

    def add_slope(self, w, d, h_front, h_back, ox, oy, oz, color):
        """SM64-style slope — variable height front/back"""
        si=len(self.vertices); hw,hd=w/2,d/2
        # 4 bottom + 4 top
        self.vertices.append(Vector3(-hw+ox,oy,        -hd+oz))  # 0 back-left bot
        self.vertices.append(Vector3( hw+ox,oy,        -hd+oz))  # 1 back-right bot
        self.vertices.append(Vector3( hw+ox,oy,         hd+oz))  # 2 front-right bot
        self.vertices.append(Vector3(-hw+ox,oy,         hd+oz))  # 3 front-left bot
        self.vertices.append(Vector3(-hw+ox,oy+h_back, -hd+oz))  # 4 back-left top
        self.vertices.append(Vector3( hw+ox,oy+h_back, -hd+oz))  # 5 back-right top
        self.vertices.append(Vector3( hw+ox,oy+h_front, hd+oz))  # 6 front-right top
        self.vertices.append(Vector3(-hw+ox,oy+h_front, hd+oz))  # 7 front-left top
        # Top slope face
        f=Face([si+4,si+5,si+6,si+7],color); f.normal=(0,1,0); self.faces.append(f)
        # Front
        f=Face([si+3,si+2,si+6,si+7],color); f.normal=(0,0,1); self.faces.append(f)
        # Back
        f=Face([si+1,si+0,si+4,si+5],color); f.normal=(0,0,-1); self.faces.append(f)
        # Left
        f=Face([si+0,si+3,si+7,si+4],color); f.normal=(-1,0,0); self.faces.append(f)
        # Right
        f=Face([si+2,si+1,si+5,si+6],color); f.normal=(1,0,0); self.faces.append(f)

    def add_hill(self, radius, height, ox, oy, oz, color, color2=None, segments=8):
        """SM64-style rolling hill approximation"""
        if color2 is None: color2 = color
        si = len(self.vertices)
        # Center top
        self.vertices.append(Vector3(ox, oy+height, oz))
        # Ring at base
        for i in range(segments):
            a = 2*math.pi*i/segments
            self.vertices.append(Vector3(ox+math.cos(a)*radius, oy, oz+math.sin(a)*radius))
        # Mid ring (halfway up, 60% radius)
        for i in range(segments):
            a = 2*math.pi*i/segments
            self.vertices.append(Vector3(ox+math.cos(a)*radius*0.6, oy+height*0.7, oz+math.sin(a)*radius*0.6))
        # Top triangles (mid ring -> apex)
        for i in range(segments):
            j=(i+1)%segments
            f=Face([si, si+1+segments+i, si+1+segments+j], color)
            f.normal=(0,1,0); self.faces.append(f)
        # Mid band (base ring -> mid ring)
        for i in range(segments):
            j=(i+1)%segments
            f=Face([si+1+i, si+1+j, si+1+segments+j, si+1+segments+i], color2)
            f.normal=(0,0.5,0.5); self.faces.append(f)


# =====================================================================
# MARIO CHARACTER
# =====================================================================
class Mario(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x,y,z)
        self.dy=0; self.is_jumping=False
        self.star_count=0; self.coins=0; self.lives=4; self.health=8
        # No visible model in first-person — just collision box

    def update(self, floor_y=0):
        self.dy -= GRAVITY
        self.y += self.dy
        if self.y < floor_y:
            self.y = floor_y; self.dy = 0; self.is_jumping = False


# =====================================================================
# COLLECTIBLES
# =====================================================================
class Star(Mesh):
    def __init__(self, x, y, z, sid=0):
        super().__init__(x,y,z); self.star_id=sid; self.collected=False
        self.add_cube(10,40,10,0,0,0,YELLOW)
        self.add_cube(40,10,10,0,0,0,YELLOW)
        self.add_cube(10,10,40,0,0,0,YELLOW)

class Coin(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x,y,z); self.collected=False
        self.add_cube(8,12,3,0,0,0,YELLOW)
        self.add_cube(4,8,4,0,0,0,BUTTON_GOLD)


# =====================================================================
# SM64 PC PORT LEVEL BUILDERS — AUTHENTIC OUTDOOR GEOMETRY
# =====================================================================

def build_castle_grounds():
    """Castle Grounds — SM64 PC port authentic layout"""
    m = Mesh()
    # === TERRAIN: Rolling green hills ===
    tile = 240
    for x in range(-8,8):
        for z in range(-8,8):
            # SM64 vertex-colored grass with subtle variation
            c = CG_GRASS_1 if (x+z)%2==0 else CG_GRASS_2
            # Slight terrain undulation
            h = math.sin(x*0.5)*4 + math.cos(z*0.7)*3
            m.add_cube(tile,12,tile, x*tile, -6+h, z*tile, c)
    # Dirt path to castle
    for z in range(-6,0):
        m.add_cube(160,4,tile, 0,0,z*tile, CG_PATH)
    # === MOAT ===
    moat_positions = []
    for i in range(-4,5):
        for side in [-1,1]:
            m.add_cube(tile,8,tile, i*tile,-4, side*900, CG_MOAT)
            m.add_cube(tile,8,tile, side*900,-4, i*tile, CG_MOAT)
    # Moat deeper center
    m.add_cube(400,4,400, 0,-8, -900, CG_MOAT_DEEP)
    # === BRIDGE ===
    m.add_cube(180,16,480, 0,4,-640, CG_BRIDGE)
    # Bridge rails
    for side in [-80,80]:
        for z in range(-3,3):
            m.add_cube(12,40,12, side,24,-640+z*80, CG_BRIDGE)
        m.add_cube(12,8,480, side,44,-640, CG_BRIDGE)
    # === CASTLE ===
    # Main building
    m.add_cube(640,360,80, 0,180,-1050, CG_CASTLE_WALL)
    # Towers
    for tx in [-380,380]:
        m.add_cube(120,480,120, tx,240,-1050, CG_TOWER)
        m.add_pyramid(140,100, tx,480,-1050, CG_CASTLE_ROOF)
        # Tower windows
        m.add_cube(30,40,5, tx,360,-988, (120,180,248))
        m.add_cube(30,40,5, tx,280,-988, (120,180,248))
    # Center tower (taller)
    m.add_cube(160,520,120, 0,260,-1100, CG_CASTLE_WALL)
    m.add_pyramid(180,120, 0,520,-1100, CG_CASTLE_ROOF)
    # Main door
    m.add_cube(100,160,8, 0,80,-1008, (104,72,32))
    # Door arch
    m.add_cube(120,20,12, 0,160,-1008, CG_CASTLE_TRIM)
    # Peach stained glass
    m.add_cube(80,96,5, 0,320,-1008, (248,180,200))
    # Side windows
    for wx in [-160,160]:
        m.add_cube(48,56,5, wx,280,-1008, (120,180,248))
    # Roof
    m.add_cube(640,20,200, 0,360,-1090, CG_CASTLE_ROOF)
    # Castle base trim
    m.add_cube(680,20,100, 0,10,-1050, CG_STONE)
    # === HILLS (SM64 rolling green hills) ===
    m.add_hill(400,180, -1200,0,200, CG_GRASS_1, CG_GRASS_2)
    m.add_hill(500,220, 1200,0,200, CG_GRASS_2, CG_GRASS_1)
    m.add_hill(600,160, 0,0,1400, CG_GRASS_1, CG_GRASS_2)
    m.add_hill(350,140, -800,0,-400, CG_GRASS_2, CG_GRASS_1)
    m.add_hill(300,120, 900,0,-300, CG_GRASS_1, CG_GRASS_2)
    # === TREES (SM64 style — trunk + two-tier canopy) ===
    tree_pos = [(-500,200),(500,200),(-500,-200),(500,-200),
                (-700,600),(700,600),(-300,800),(300,800),
                (-900,100),(900,100),(-600,-500),(600,-500)]
    for tx,tz in tree_pos:
        m.add_cube(24,80,24, tx,40,tz, CG_TREE_TRUNK)
        m.add_hill(56,40, tx,80,tz, CG_TREE_TOP, CG_TREE_TOP2, 6)
    # === CANNON HOLE ===
    m.add_cube(32,8,32, -600,4,700, DARK_GREY)
    m.add_cube(24,24,24, -600,16,700, METAL_GREY)
    # === WATERFALL (side of castle) ===
    m.add_cube(80,200,16, 420,100,-1060, (120,180,248))
    m.add_cube(100,8,60, 420,0,-1060, CG_MOAT)
    # === CHAIN CHOMP AREA (hidden) ===
    m.add_cube(8,36,8, -800,18,-600, DARK_GREY)
    m.add_cube(28,28,28, -800,48,-600, (32,32,32))
    # === Star on top of castle ===
    stars = [Star(0, 540, -1100, 0)]
    coins = [Coin(x*120,10,z*120) for x,z in [(-1,1),(1,1),(0,2),(-2,0),(2,0)]]
    return m, stars, coins

def build_castle_interior_f1():
    """Castle Interior — First Floor / Main Hall"""
    m = Mesh()
    tile = 200
    for x in range(-5,5):
        for z in range(-5,5):
            c = (180,170,150) if (x+z)%2==0 else (160,150,130)
            m.add_cube(tile,10,tile, x*tile,-5, z*tile, c)
    # Red carpet
    for z in range(-4,4):
        m.add_cube(120,2,tile, 0,1, z*tile, CARPET_RED)
    # Walls
    for w_z in [-1000,1000]:
        m.add_cube(2000,400,40, 0,200,w_z, CG_CASTLE_WALL)
    for w_x in [-1000,1000]:
        m.add_cube(40,400,2000, w_x,200,0, CG_CASTLE_WALL)
    m.add_cube(2000,20,2000, 0,400,0, CG_CASTLE_WALL)
    # Pillars
    for px,pz in [(-400,-400),(400,-400),(-400,400),(400,400)]:
        m.add_cube(56,400,56, px,200,pz, WHITE)
        m.add_cube(72,24,72, px,400,pz, CG_CASTLE_TRIM)
    # Stairs
    for i in range(8):
        m.add_cube(300,20,60, 0,i*25,-600-i*60, CG_STONE)
    # Star doors
    m.add_cube(100,200,20, -800,100,0, BUTTON_GOLD)
    m.add_cube(100,200,20, 800,100,0, BUTTON_GOLD)
    m.add_cube(200,200,20, 0,100,-980, BUTTON_GOLD)
    # Painting frames + canvases
    for px,py,pz,c in [(-978,140,-300,BOB_GRASS_1),(-978,140,-500,WF_STONE_1),
                        (-978,140,-700,JRB_WATER),(978,140,-300,CCM_SNOW_1),(978,140,-500,BBH_WALL)]:
        m.add_cube(80,80,8, px,py,pz, (160,120,40))
        m.add_cube(70,70,4, px,py,pz-3 if px<0 else pz+3, c)
    # Basement trapdoor
    m.add_cube(150,5,150, 600,-2,600, DARK_GREY)
    # Peach window
    m.add_cube(100,100,5, 0,320,-998, (248,180,200))
    # Toads
    for tx,tz in [(-200,200),(200,-300),(-400,0)]:
        m.add_cube(20,30,20, tx,15,tz, WHITE)
        m.add_cube(24,12,24, tx,38,tz, RED)
    return m, [], []

def build_castle_basement():
    """Castle Basement"""
    m = Mesh()
    for x in range(-6,6):
        for z in range(-6,6):
            c = (72,64,56) if (x+z)%2==0 else (56,48,40)
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(2400,300,40, 0,150,-1200, HMC_ROCK_2)
    m.add_cube(2400,300,40, 0,150,1200, HMC_ROCK_2)
    m.add_cube(40,300,2400, -1200,150,0, HMC_ROCK_2)
    m.add_cube(40,300,2400, 1200,150,0, HMC_ROCK_2)
    m.add_cube(2400,20,2400, 0,300,0, HMC_ROCK_2)
    # Maze corridors
    m.add_cube(40,200,600, -400,100,-300, HMC_ROCK_1)
    m.add_cube(40,200,600, 400,100,300, HMC_ROCK_1)
    m.add_cube(600,200,40, 0,100,-400, HMC_ROCK_1)
    # Lava pool
    m.add_cube(400,4,400, -600,-3,-600, LLL_LAVA_1)
    m.add_cube(400,2,400, -600,-1,-600, LLL_LAVA_2)
    # Paintings
    for px,py,pz,c in [(-1178,100,-400,HMC_ROCK_1),(-1178,100,-600,LLL_LAVA_1),
                        (-1178,100,-800,SSL_SAND_1),(1178,100,-400,DDD_WATER)]:
        m.add_cube(80,80,8, px,py,pz, (160,120,40))
        m.add_cube(70,70,4, px,py,pz, c)
    m.add_cube(50,30,50, 800,15,800, PIPE_GREEN)
    m.add_cube(80,80,10, 600,60,-1178, (0,200,200))
    return m, [], []

def build_castle_upper():
    """Castle Upper Floor"""
    m = Mesh()
    for x in range(-4,4):
        for z in range(-4,4):
            c = (180,170,150) if (x+z)%2==0 else (160,150,130)
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(1600,350,40, 0,175,-800, CG_CASTLE_WALL)
    m.add_cube(1600,350,40, 0,175,800, CG_CASTLE_WALL)
    m.add_cube(40,350,1600, -800,175,0, CG_CASTLE_WALL)
    m.add_cube(40,350,1600, 800,175,0, CG_CASTLE_WALL)
    m.add_cube(1600,20,1600, 0,350,0, CG_CASTLE_WALL)
    for px,py,pz,c in [(-778,100,-300,SL_ICE),(-778,100,-500,WDW_WATER),
                        (778,100,-300,TTM_GRASS),(778,100,-500,THI_GRASS_1),
                        (0,60,-778,TTC_GEAR),(0,75,-790,(248,56,56))]:
        m.add_cube(80,80,8, px,py,pz, (160,120,40))
        m.add_cube(70,70,4, px,py,pz, c)
    for i in range(6):
        m.add_cube(200,20,60, 0,i*30,-500-i*60, CG_STONE)
    return m, [], []

def build_castle_top():
    """Castle Top / Wing Cap"""
    m = Mesh()
    for x in range(-2,2):
        for z in range(-2,2):
            m.add_cube(200,10,200, x*200,-5,z*200, (180,170,150))
    m.add_cube(800,300,40, 0,150,-400, CG_CASTLE_WALL)
    m.add_cube(800,300,40, 0,150,400, CG_CASTLE_WALL)
    m.add_cube(40,300,800, -400,150,0, CG_CASTLE_WALL)
    m.add_cube(40,300,800, 400,150,0, CG_CASTLE_WALL)
    m.add_cube(100,300,100, 0,150,0, (255,255,200))
    m.add_cube(60,20,60, 0,10,0, RED)
    m.add_cube(40,40,40, 0,30,0, YELLOW)
    return m, [], []


# === 15 MAIN COURSES (SM64 PC Port Authentic) ===

def build_bob_omb_battlefield():
    """Course 1: Bob-omb Battlefield — SM64 PC port terrain"""
    m = Mesh()
    # Rolling green terrain
    for x in range(-7,7):
        for z in range(-7,7):
            c = BOB_GRASS_1 if (x+z)%2==0 else BOB_GRASS_2
            h = math.sin(x*0.4)*8 + math.cos(z*0.5)*6
            m.add_cube(200,14,200, x*200,-7+h,z*200, c)
    # Dirt path winding up
    path_pts = [(0,-400),(100,-200),(200,0),(100,200),(0,400),(-100,200)]
    for px,pz in path_pts:
        m.add_cube(100,4,200, px,2,pz, BOB_PATH)
    # Mountain (multi-tier SM64 style)
    m.add_cube(480,160,480, 0,80,0, BOB_MTN_LOW)
    m.add_cube(360,120,360, 0,240,0, BOB_MTN_MID)
    m.add_cube(240,80,240, 0,360,0, BOB_MTN_MID)
    m.add_cube(140,60,140, 0,440,0, BOB_MTN_TOP)
    m.add_cube(100,12,100, 0,480,0, BOB_MTN_TOP)
    # Slopes between tiers
    m.add_slope(200,200, 80,40, -240,80,0, BOB_DIRT)
    m.add_slope(160,200, 60,30, 0,240,-180, BOB_DIRT)
    # King Bob-omb platform
    m.add_cube(120,10,120, 0,492,0, DARK_GREY)
    # Chain chomp post + ball
    m.add_cube(8,40,8, -440,20,-240, DARK_GREY)
    m.add_cube(32,32,32, -440,52,-240, (24,24,24))
    # Chain
    m.add_cube(4,4,60, -440,36,-210, DARK_GREY)
    # Bridges
    m.add_cube(240,10,36, -200,48,-320, BOB_FENCE)
    m.add_cube(240,10,36, 200,48,320, BOB_FENCE)
    # Bridge rails
    for bx,bz in [(-200,-320),(200,320)]:
        for side in [-16,16]:
            m.add_cube(4,20,36, bx+side,60,bz, BOB_FENCE)
    # Cannons
    for cx,cz in [(560,-440),(-560,440)]:
        m.add_cube(28,12,28, cx,6,cz, DARK_GREY)
        m.add_cube(12,24,12, cx,18,cz, METAL_GREY)
    # Water area
    m.add_cube(400,6,240, 440,-3,320, BOB_WATER)
    m.add_cube(280,6,160, 440,-3,200, BOB_WATER)
    # Gates / fences
    m.add_cube(8,56,80, -320,28,-120, BOB_FENCE)
    m.add_cube(8,56,80, 320,28,120, BOB_FENCE)
    # Trees (SM64 trunk + round top)
    for tx,tz in [(-640,240),(640,-240),(-240,560),(320,-560),(-480,-480),(480,480)]:
        m.add_cube(20,64,20, tx,32,tz, CG_TREE_TRUNK)
        m.add_hill(48,32, tx,64,tz, CG_TREE_TOP, CG_TREE_TOP2, 6)
    # Hills in background
    m.add_hill(360,140, -1000,0,-600, BOB_GRASS_1, BOB_GRASS_2)
    m.add_hill(440,180, 1000,0,600, BOB_GRASS_2, BOB_GRASS_1)
    m.add_hill(300,100, -800,0,800, BOB_GRASS_1, BOB_GRASS_2)
    # Bob-ombs (small black balls)
    for bx,bz in [(200,-200),(-300,100),(400,200)]:
        m.add_cube(16,16,16, bx,10,bz, BLACK)
        m.add_cube(6,10,6, bx,22,bz, (180,180,180))  # fuse
    stars = [Star(0,502,0,0), Star(560,20,-440,1), Star(-440,60,-240,2),
             Star(-640,40,240,3), Star(440,10,320,4)]
    coins = [Coin(px,10,pz) for px,pz in path_pts]
    coins += [Coin(x*80,10,z*80) for x,z in [(-3,3),(3,3),(-3,-3),(3,-3),(0,5)]]
    return m, stars, coins

def build_whomps_fortress():
    """Course 2: Whomp's Fortress — SM64 authentic stone fortress"""
    m = Mesh()
    # Base floating platform
    m.add_cube(640,24,640, 0,-8,0, WF_STONE_1)
    m.add_cube(600,4,600, 0,4,0, WF_GRASS)
    # Rising fortress tiers
    for i in range(6):
        w = 540-i*72
        m.add_cube(w,36,w, 0,i*56+20,0, WF_STONE_2 if i%2==0 else WF_BRICK)
    # Ramps between tiers
    m.add_slope(80,200, 56,0, -200,20,-100, WF_STONE_1)
    m.add_slope(80,200, 56,0, 200,76,100, WF_STONE_1)
    # Whomp at top
    m.add_cube(56,96,20, 0,360,0, WF_STONE_2)
    m.add_cube(36,20,20, -28,380,0, WF_STONE_2)
    m.add_cube(36,20,20, 28,380,0, WF_STONE_2)
    m.add_cube(12,12,4, -16,400,-8, BLACK)
    m.add_cube(12,12,4, 16,400,-8, BLACK)
    # Thwomps
    m.add_cube(48,48,48, 200,80,100, DARK_GREY)
    m.add_cube(8,8,4, 186,100,78, RED)
    m.add_cube(8,8,4, 214,100,78, RED)
    # Rotating platform
    m.add_cube(120,8,36, 100,120,200, WF_DIRT)
    # Piranha plants
    for px,pz in [(160,-200),(-160,200)]:
        m.add_cube(28,36,28, px,18,pz, PIPE_GREEN)
        m.add_cube(20,12,20, px,42,pz, RED)
    # Tower
    m.add_cube(80,200,80, -260,100,-260, WF_STONE_1)
    m.add_cube(100,16,100, -260,200,-260, CG_CASTLE_ROOF)
    # Bullet Bill cannons
    m.add_cube(24,16,24, 300,-4,300, DARK_GREY)
    m.add_cube(16,20,16, 300,12,300, (32,32,32))
    # Background hills visible in distance
    m.add_hill(500,200, -1200,0,800, WF_GRASS, (0,104,0))
    m.add_hill(400,160, 1200,0,-800, WF_GRASS, (0,104,0))
    stars = [Star(0,380,0,0), Star(-260,220,-260,1), Star(300,20,300,2)]
    coins = [Coin(i*56-140,40+i*10,i*36) for i in range(6)]
    return m, stars, coins

def build_jolly_roger_bay():
    """Course 3: Jolly Roger Bay"""
    m = Mesh()
    # Sandy shore
    for x in range(-4,4):
        for z in range(-2,2):
            m.add_cube(200,10,200, x*200,-5,z*200-600, JRB_SAND)
    # Water surface
    for x in range(-6,6):
        for z in range(-4,6):
            m.add_cube(200,6,200, x*200,-3,z*200, JRB_WATER)
    # Underwater floor
    for x in range(-6,6):
        for z in range(-4,6):
            m.add_cube(200,10,200, x*200,-200,z*200, JRB_CAVE)
    # Sunken ship
    m.add_cube(100,56,280, 200,-120,200, JRB_SHIP)
    m.add_cube(80,36,200, 200,-84,200, (96,64,32))
    m.add_cube(8,80,8, 200,-40,200, JRB_SHIP)
    # Cave
    m.add_cube(200,100,200, -400,-80,-300, JRB_CAVE)
    m.add_cube(180,80,180, -400,-60,-300, (64,56,48))
    # Clam shells
    for cx,cz in [(100,-100),(-200,0),(300,100)]:
        m.add_cube(28,8,28, cx,-192,cz, LIGHT_GREY)
        m.add_cube(24,16,12, cx,-182,cz, JRB_CORAL)
    # Docks
    m.add_cube(280,10,56, -200,5,-520, JRB_DOCK)
    m.add_cube(16,28,16, -340,18,-520, JRB_DOCK)
    m.add_cube(16,28,16, -60,18,-520, JRB_DOCK)
    # Eel cave
    m.add_cube(80,80,40, 500,-100,400, BLACK)
    # Shore hills
    m.add_hill(300,80, -600,0,-700, JRB_SAND, (200,176,128))
    m.add_hill(250,60, 600,0,-700, JRB_SAND, (200,176,128))
    stars = [Star(200,-60,200,0), Star(-400,-40,-300,1), Star(-200,20,-520,2)]
    coins = [Coin(x*80,-180,z*80) for x,z in [(-1,0),(0,1),(1,0),(0,-1),(1,1)]]
    return m, stars, coins

def build_cool_cool_mountain():
    """Course 4: Cool, Cool Mountain — SM64 snowy peak"""
    m = Mesh()
    # Base snow field
    for x in range(-5,5):
        for z in range(-5,5):
            c = CCM_SNOW_1 if (x+z)%2==0 else CCM_SNOW_2
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Mountain tiers
    for i in range(10):
        w = 220+i*56
        c = CCM_SNOW_1 if i%2==0 else CCM_SNOW_2
        m.add_cube(w,20,w, 0,600-i*56,0, c)
    # Rocky crags
    m.add_cube(100,40,100, -80,640,0, CCM_ROCK)
    # Chimney / slide entrance
    m.add_cube(36,56,36, 0,660,0, (96,64,24))
    # Penguin slide path
    for i in range(18):
        a = i*0.38
        r = 180+i*28
        sx = math.cos(a)*r; sz = math.sin(a)*r
        m.add_cube(72,8,72, sx,560-i*30,sz, CCM_SLIDE)
    # Cabin at bottom
    m.add_cube(120,72,120, -300,36,-400, CCM_CABIN)
    m.add_cube(132,8,132, -300,72,-400, CG_CASTLE_ROOF)
    m.add_cube(40,56,4, -300,28,-338, (72,48,16))  # door
    m.add_cube(24,24,4, -260,48,-338, (120,180,248))  # window
    # Snowman
    m.add_cube(56,56,56, 200,28,300, CCM_SNOW_1)
    m.add_cube(40,40,40, 200,72,300, CCM_SNOW_1)
    m.add_cube(16,8,16, 200,88,272, ORANGE)  # nose
    m.add_cube(8,8,4, 188,96,270, BLACK)
    m.add_cube(8,8,4, 212,96,270, BLACK)
    # Ice bridge
    m.add_cube(200,8,36, -200,150,0, CCM_ICE)
    # Penguin at top
    m.add_cube(16,28,16, -48,628,48, BLACK)
    m.add_cube(16,8,16, -48,640,48, WHITE)
    # Background mountains
    m.add_hill(600,300, -1200,0,800, CCM_SNOW_2, CCM_ROCK)
    m.add_hill(500,240, 1200,0,-600, CCM_SNOW_1, CCM_ROCK)
    stars = [Star(0,680,0,0), Star(-300,88,-400,1), Star(200,100,300,2)]
    coins = [Coin(math.cos(i*0.38)*(180+i*28),570-i*30,math.sin(i*0.38)*(180+i*28)) for i in range(0,18,3)]
    return m, stars, coins

def build_big_boos_haunt():
    """Course 5: Big Boo's Haunt"""
    m = Mesh()
    for x in range(-4,4):
        for z in range(-4,4):
            c = BBH_FLOOR if (x+z)%2==0 else (48,40,48)
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Mansion
    m.add_cube(400,280,400, 0,140,0, BBH_WALL)
    m.add_pyramid(450,140, 0,280,0, BBH_ROOF)
    for wx,wy in [(-120,200),(120,200),(-120,100),(120,100)]:
        m.add_cube(48,36,4, wx,wy,-200, BBH_WINDOW)
    m.add_cube(56,112,4, 0,56,-200, (80,56,32))
    m.add_cube(350,10,350, 0,-2,0, BBH_FLOOR)
    for gx,gz in [(-500,-200),(-500,-400),(-600,-300),(500,200),(500,400)]:
        m.add_cube(28,40,8, gx,20,gz, BBH_GRAVE)
        m.add_cube(36,4,12, gx,-2,gz, (72,64,48))
    # Ghost
    m.add_cube(36,36,36, 100,100,300, BBH_GHOST)
    m.add_cube(8,6,4, 86,106,282, BLACK)
    m.add_cube(8,6,4, 114,106,282, BLACK)
    m.add_cube(80,2,80, -100,240,0, (180,180,180))
    m.add_cube(200,10,56, 0,200,-230, BBH_FLOOR)
    m.add_cube(200,5,200, 0,-100,300, BBH_FLOOR)
    m.add_cube(100,28,100, 0,-86,300, (80,56,32))
    # Dead trees
    for tx,tz in [(-600,0),(600,0),(0,600)]:
        m.add_cube(16,80,16, tx,40,tz, (64,48,32))
        m.add_cube(8,24,48, tx,80,tz, (80,64,48))
    stars = [Star(0,300,0,0), Star(100,120,300,1), Star(0,-72,300,2)]
    coins = [Coin(gx,30,gz) for gx,gz in [(-500,-200),(500,200),(-200,0),(200,0)]]
    return m, stars, coins

def build_hazy_maze_cave():
    """Course 6: Hazy Maze Cave"""
    m = Mesh()
    for x in range(-6,6):
        for z in range(-6,6):
            c = HMC_ROCK_1 if (x+z)%2==0 else HMC_ROCK_2
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(2400,20,2400, 0,280,0, HMC_ROCK_2)
    walls = [(-400,0,800,40),(-400,0,40,800),(400,0,800,40),(400,0,40,800),
             (0,-400,40,400),(0,400,40,400),(200,200,400,40),(-200,-200,400,40)]
    for wx,wz,ww,wd in walls:
        m.add_cube(ww,200,wd, wx,100,wz, HMC_ROCK_1)
    m.add_cube(600,4,600, -400,-3,-400, HMC_TOXIC)
    m.add_cube(200,10,200, 500,-2,500, HMC_METAL)
    m.add_cube(40,40,40, 500,20,500, BUTTON_GOLD)
    m.add_cube(500,6,500, 0,-3,0, HMC_WATER)
    # Dorrie
    m.add_cube(80,36,120, 0,18,0, (0,152,0))
    m.add_cube(28,28,36, 0,48,48, (0,136,0))
    for sx,sz in [(100,200),(-200,100),(300,-100),(-100,-300)]:
        m.add_cube(20,56,20, sx,252,sz, HMC_ROCK_2)
    stars = [Star(500,40,500,0), Star(0,56,0,1), Star(-400,10,-400,2)]
    coins = [Coin(x*150,10,z*150) for x,z in [(0,0),(1,1),(-1,-1),(2,0)]]
    return m, stars, coins

def build_lethal_lava_land():
    """Course 7: Lethal Lava Land"""
    m = Mesh()
    for x in range(-6,6):
        for z in range(-6,6):
            c = LLL_LAVA_1 if (x+z)%2==0 else LLL_LAVA_2
            m.add_cube(200,6,200, x*200,-3,z*200, c)
    platforms = [(0,0,200),(300,0,140),(-300,0,140),(0,0,400),(500,0,96),
                 (-500,0,96),(200,0,280),(-200,0,280),(0,0,-200),(0,0,-480)]
    for px,py,ps in platforms:
        m.add_cube(ps,20,ps, px,10+py,py, LLL_STONE)
    m.add_cube(300,200,300, 0,100,0, LLL_VOLCANO)
    m.add_cube(200,100,200, 0,250,0, DARK_GREY)
    m.add_cube(100,8,100, 0,300,0, LLL_LAVA_2)
    m.add_cube(80,8,80, 0,148,0, LLL_STONE)
    m.add_cube(56,8,56, 48,196,0, LLL_STONE)
    m.add_cube(16,16,200, -200,18,-100, (96,64,24))
    m.add_cube(100,8,100, 400,18,400, LLL_METAL)
    m.add_cube(100,8,100, -400,18,-400, LLL_METAL)
    for fx,fz in [(150,150),(-150,-150),(300,-200)]:
        m.add_cube(16,36,16, fx,28,fz, ORANGE)
        m.add_cube(24,8,24, fx,48,fz, (248,200,0))
    stars = [Star(0,310,0,0), Star(-400,36,-400,1), Star(500,28,0,2)]
    coins = [Coin(px,28,py) for px,py,ps in platforms[:5]]
    return m, stars, coins

def build_shifting_sand_land():
    """Course 8: Shifting Sand Land — SM64 desert"""
    m = Mesh()
    for x in range(-7,7):
        for z in range(-7,7):
            c = SSL_SAND_1 if (x+z)%2==0 else SSL_SAND_2
            h = math.sin(x*0.6)*6 + math.cos(z*0.4)*4  # sand dunes
            m.add_cube(200,12,200, x*200,-6+h,z*200, c)
    # Pyramid
    m.add_cube(400,280,400, 0,140,0, SSL_PYRAMID)
    m.add_pyramid(420,100, 0,280,0, SSL_BRICK)
    m.add_cube(300,200,300, 0,100,0, (120,88,48))
    m.add_cube(80,8,80, 0,200,0, (88,72,40))
    # Quicksand
    m.add_cube(300,4,300, -500,-3,-500, SSL_QUICKSAND)
    # Oasis
    m.add_cube(200,4,200, 500,-1,500, SSL_OASIS)
    m.add_cube(20,56,20, 520,28,520, CG_TREE_TRUNK)
    m.add_cube(56,8,56, 520,56,520, SSL_PALM)
    m.add_cube(48,6,48, 520,50,520, (0,120,0))
    # Pillars
    for px,pz in [(-300,300),(300,-300),(-300,-300),(300,300)]:
        m.add_cube(36,120,36, px,60,pz, SSL_SAND_1)
        m.add_cube(48,12,48, px,120,pz, SSL_BRICK)
    # Tox boxes
    m.add_cube(56,56,56, 200,28,-200, DARK_GREY)
    m.add_cube(56,56,56, -200,28,200, DARK_GREY)
    # Klepto
    m.add_cube(20,72,20, -500,36,200, CG_TREE_TRUNK)
    m.add_cube(28,8,48, -500,76,200, (96,72,24))
    # Background dunes
    m.add_hill(500,100, -1200,0,0, SSL_SAND_2, SSL_SAND_1)
    m.add_hill(600,120, 1200,0,0, SSL_SAND_1, SSL_SAND_2)
    m.add_hill(400,80, 0,0,1400, SSL_SAND_2, SSL_SAND_1)
    stars = [Star(0,390,0,0), Star(500,16,500,1), Star(-500,8,-500,2)]
    coins = [Coin(x*200,10,z*200) for x,z in [(1,1),(-1,-1),(2,-2),(-2,2),(0,3)]]
    return m, stars, coins

def build_dire_dire_docks():
    """Course 9: Dire, Dire Docks"""
    m = Mesh()
    for x in range(-3,3):
        m.add_cube(200,10,200, x*200,-5,-600, DDD_DOCK)
    for x in range(-6,6):
        for z in range(-4,6):
            m.add_cube(200,6,200, x*200,-3,z*200, DDD_WATER)
    for x in range(-6,6):
        for z in range(-4,6):
            m.add_cube(200,10,200, x*200,-200,z*200, DDD_FLOOR)
    # Submarine
    m.add_cube(120,56,380, 0,-60,200, DDD_SUB)
    m.add_cube(80,36,96, 0,-28,380, DDD_METAL)
    m.add_cube(8,56,8, 0,0,380, DDD_METAL)
    # Bowser gate
    m.add_cube(200,200,16, 0,100,800, DDD_METAL)
    m.add_cube(8,200,8, -88,100,800, DARK_GREY)
    m.add_cube(8,200,8, 88,100,800, DARK_GREY)
    m.add_cube(96,4,96, -400,-1,400, (32,48,144))
    for px,pz in [(300,0),(-300,0),(0,600)]:
        m.add_cube(8,140,8, px,-120,pz, DDD_METAL)
    m.add_cube(80,6,120, 200,-80,300, (48,48,96))
    stars = [Star(0,-20,200,0), Star(0,10,800,1), Star(-400,10,400,2)]
    coins = [Coin(x*96,-80,z*96) for x,z in [(0,0),(1,2),(-1,3),(2,1)]]
    return m, stars, coins

def build_snowmans_land():
    """Course 10: Snowman's Land"""
    m = Mesh()
    for x in range(-6,6):
        for z in range(-6,6):
            c = SL_SNOW_1 if (x+z)%2==0 else SL_SNOW_2
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(300,200,300, 0,100,0, SL_SNOW_1)
    m.add_cube(200,140,200, 0,270,0, SL_SNOW_2)
    m.add_cube(120,96,120, 0,388,0, SL_SNOW_1)
    m.add_cube(80,72,80, 0,472,0, SL_SNOW_1)
    m.add_cube(16,16,16, 0,484,-36, ORANGE)
    m.add_cube(8,8,4, -12,496,-34, BLACK)
    m.add_cube(8,8,4, 12,496,-34, BLACK)
    m.add_cube(200,6,36, -200,148,0, SL_ICE)
    m.add_cube(100,56,100, -400,28,-300, SL_IGLOO)
    m.add_cube(36,36,8, -400,18,-348, (80,56,24))
    m.add_cube(300,4,300, 400,-1,400, SL_ICE)
    m.add_cube(28,28,28, 200,18,400, BLACK)
    m.add_cube(6,16,6, 200,40,400, METAL_GREY)
    m.add_cube(140,8,140, 0,96,500, SL_ICE)
    for tx,tz in [(-500,200),(500,-200),(-200,500)]:
        m.add_cube(16,56,16, tx,28,tz, CG_TREE_TRUNK)
        m.add_hill(44,28, tx,56,tz, SL_ICE, SL_SNOW_2, 6)
    # Bg mountains
    m.add_hill(500,200, -1200,0,600, SL_SNOW_2, CCM_ROCK)
    m.add_hill(600,260, 1200,0,-400, SL_SNOW_1, CCM_ROCK)
    stars = [Star(0,520,0,0), Star(-400,56,-300,1), Star(0,112,500,2)]
    coins = [Coin(x*120,10,z*120) for x,z in [(2,2),(-2,-2),(3,0),(0,3)]]
    return m, stars, coins

def build_wet_dry_world():
    """Course 11: Wet-Dry World"""
    m = Mesh()
    for x in range(-4,4):
        for z in range(-4,4):
            c = WDW_BRICK if (x+z)%2==0 else WDW_STONE
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(1600,4,1600, 0,48,0, WDW_WATER)
    m.add_cube(200,280,200, -300,140,0, WDW_BRICK)
    m.add_cube(200,200,200, 300,100,-200, WDW_BRICK)
    m.add_cube(150,240,150, 0,120,300, WDW_STONE)
    for sx,sz in [(-300,300),(300,-300),(0,0)]:
        m.add_cube(28,28,28, sx,18,sz, WDW_SWITCH)
    m.add_cube(56,56,56, -100,28,-200, METAL_GREY)
    m.add_cube(56,56,56, 200,28,200, METAL_GREY)
    m.add_cube(100,96,100, -500,48,-400, METAL_GREY)
    m.add_cube(600,8,400, 0,-100,-500, (56,48,40))
    m.add_cube(100,72,100, -200,-64,-500, WDW_BRICK)
    m.add_cube(100,72,100, 200,-64,-500, WDW_BRICK)
    stars = [Star(-300,290,0,0), Star(0,260,300,1), Star(-200,-50,-500,2)]
    coins = [Coin(x*96,56,z*96) for x,z in [(0,0),(1,1),(-1,-1),(2,-2)]]
    return m, stars, coins

def build_tall_tall_mountain():
    """Course 12: Tall, Tall Mountain — SM64 authentic spiral mountain"""
    m = Mesh()
    # Base grass
    for x in range(-5,5):
        for z in range(-5,5):
            c = TTM_GRASS if (x+z)%2==0 else (0,120,0)
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    # Mountain tiers (chunky SM64 style)
    m.add_cube(500,280,500, 0,140,0, TTM_DIRT)
    m.add_cube(400,240,400, 0,400,0, TTM_ROCK)
    m.add_cube(300,200,300, 0,640,0, DARK_GREY)
    m.add_cube(200,140,200, 0,840,0, (96,88,80))
    m.add_cube(120,80,120, 0,980,0, (80,72,64))
    m.add_pyramid(140,56, 0,1020,0, DARK_STONE)
    # Spiral path
    for i in range(22):
        a = i*0.32
        r = 280+48*math.sin(i*0.5)
        px = math.cos(a)*r; pz = math.sin(a)*r
        m.add_cube(72,8,72, px,i*44+16,pz, TTM_ROCK)
    # Waterfall
    m.add_cube(56,380,16, -260,190,-200, TTM_WATER)
    m.add_cube(80,8,48, -260,4,-200, TTM_WATER)
    # Mushroom platforms
    for mx,mz,mh in [(400,200,56),(400,300,96),(-400,-200,72)]:
        m.add_cube(16,mh,16, mx,mh/2,mz, TTM_MUSH_STEM)
        m.add_cube(52,12,52, mx,mh,mz, TTM_MUSH_TOP)
    # Monkey area
    m.add_cube(96,8,96, 200,380,-200, TTM_GRASS)
    # Slide entrance
    m.add_cube(36,36,36, 0,1052,0, (96,64,24))
    # Background hills
    m.add_hill(500,200, -1200,0,800, TTM_GRASS, (0,104,0))
    m.add_hill(600,280, 1200,0,-600, TTM_GRASS, (0,88,0))
    stars = [Star(0,1060,0,0), Star(200,400,-200,1), Star(-400,88,-200,2)]
    coins = [Coin(math.cos(i*0.32)*280,i*44+24,math.sin(i*0.32)*280) for i in range(0,22,4)]
    return m, stars, coins

def build_tiny_huge_island():
    """Course 13: Tiny-Huge Island"""
    m = Mesh()
    for x in range(-5,5):
        for z in range(-5,5):
            dist = math.sqrt(x*x+z*z)
            if dist < 5:
                c = THI_GRASS_1 if (x+z)%2==0 else THI_GRASS_2
                h = max(0,36-dist*7)
                m.add_cube(200,10+h,200, x*200,h/2,z*200, c)
    for x in range(-6,6):
        for z in range(-6,6):
            if math.sqrt(x*x+z*z)>=4:
                m.add_cube(200,6,200, x*200,-3,z*200, THI_WATER)
    m.add_cube(300,200,300, 0,100,0, TTM_DIRT)
    m.add_cube(200,100,200, 0,250,0, TTM_ROCK)
    m.add_cube(36,28,36, -300,48,-300, THI_PIPE)
    m.add_cube(72,56,72, 300,56,300, THI_PIPE)
    m.add_cube(56,112,56, -200,56,200, (144,136,120))
    m.add_cube(8,72,8, -200,128,168, (96,64,24))
    m.add_cube(72,8,8, -200,168,166, (96,64,24))
    m.add_cube(280,6,96, 0,-2,-500, THI_BEACH)
    for px,pz in [(100,100),(-100,-100),(200,-200)]:
        m.add_cube(20,28,20, px,46,pz, THI_PIPE)
        m.add_cube(16,10,16, px,62,pz, RED)
    m.add_cube(56,56,16, 0,240,-96, BLACK)
    # Background hills
    m.add_hill(500,160, -1200,0,400, THI_GRASS_1, THI_GRASS_2)
    m.add_hill(400,120, 1000,0,-600, THI_GRASS_2, THI_GRASS_1)
    stars = [Star(0,300,0,0), Star(-200,128,200,1), Star(0,10,-500,2)]
    coins = [Coin(x*96,48,z*96) for x,z in [(0,1),(1,0),(-1,0),(0,-1),(1,1)]]
    return m, stars, coins

def build_tick_tock_clock():
    """Course 14: Tick Tock Clock"""
    m = Mesh()
    m.add_cube(300,20,300, 0,-5,0, TTC_WOOD)
    m.add_cube(40,1200,600, -300,600,0, TTC_WOOD)
    m.add_cube(40,1200,600, 300,600,0, TTC_WOOD)
    m.add_cube(600,1200,40, 0,600,-300, TTC_WOOD)
    m.add_cube(600,1200,40, 0,600,300, TTC_WOOD)
    heights = [72,168,280,400,520,640,760,880,1000,1120]
    for i,h in enumerate(heights):
        a = i*0.7; px=math.cos(a)*96; pz=math.sin(a)*96
        w = 96 if i%2==0 else 72
        m.add_cube(w,8,w, px,h,pz, TTC_METAL)
    m.add_cube(8,200,8, -96,500,0, TTC_HAND)
    m.add_cube(8,280,8, 96,600,0, TTC_HAND)
    for gh in [200,480,760]:
        m.add_cube(72,8,72, -200,gh,96, TTC_GEAR)
        m.add_cube(56,8,56, 200,gh,-96, TTC_GEAR)
    m.add_cube(48,48,48, 0,380,0, DARK_GREY)
    m.add_cube(200,6,36, 0,680,0, TTC_GEAR)
    m.add_cube(200,6,36, 0,840,0, TTC_GEAR)
    m.add_cube(200,16,200, 0,1180,0, BUTTON_GOLD)
    stars = [Star(0,1200,0,0), Star(-200,500,96,1), Star(0,690,0,2)]
    coins = [Coin(math.cos(i*0.7)*96,heights[i]+12,math.sin(i*0.7)*96) for i in range(0,10,2)]
    return m, stars, coins

def build_rainbow_ride():
    """Course 15: Rainbow Ride"""
    m = Mesh()
    m.add_cube(200,16,200, 0,-5,0, RR_CLOUD)
    for i in range(32):
        c = RR_RAINBOW[i%6]
        a = i*0.14; px=i*76; pz=math.sin(a)*200; py=i*18
        m.add_cube(56,6,56, px,py,pz, c)
    m.add_cube(72,4,72, -200,96,-200, RR_CARPET)
    for i in range(12):
        m.add_cube(56,6,56, -200-i*96,96+i*28,-200-i*76, RR_CARPET)
    m.add_cube(200,112,200, 800,192,0, RR_HOUSE)
    m.add_cube(220,8,220, 800,248,0, CG_CASTLE_ROOF)
    m.add_cube(36,72,8, 800,192,-96, (104,72,32))
    for i in range(5):
        for j in range(3):
            m.add_cube(72,6,72, 400+i*96,280+j*56,-280+j*96, RR_CLOUD)
    for sx in range(-96,400,140):
        m.add_cube(56,6,56, sx,72,-400, METAL_GREY)
    m.add_cube(48,6,48, 500,96,280, ORANGE)
    m.add_cube(48,6,48, 600,120,340, ORANGE)
    m.add_cube(8,200,8, 1000,280,0, METAL_GREY)
    for i in range(4):
        m.add_cube(96,6,96, -400+i*56,192+i*36,280+i*56, RR_RAINBOW[0])
    for cx,cz in [(1200,200),(1200,-200),(1400,0)]:
        m.add_cube(96,16,96, cx,384,cz, RR_CLOUD)
    m.add_cube(120,16,120, 1400,400,0, BUTTON_GOLD)
    stars = [Star(1400,420,0,0), Star(800,264,0,1), Star(-200-11*96,96+11*28,-200-11*76,2)]
    coins = [Coin(i*76,i*18+8,math.sin(i*0.14)*200) for i in range(0,32,5)]
    return m, stars, coins


# === SECRET LEVELS ===

def build_princess_secret_slide():
    m = Mesh()
    m.add_cube(200,16,200, 0,580,0, CG_CASTLE_WALL)
    for i in range(25):
        a=i*0.3; r=96+i*14; px=math.cos(a)*r; pz=math.sin(a)*r
        m.add_cube(56,6,56, px,560-i*20,pz, CCM_SLIDE)
    ep = (math.cos(24*0.3)*(96+24*14), math.sin(24*0.3)*(96+24*14))
    m.add_cube(200,16,200, ep[0],40,ep[1], CG_CASTLE_WALL)
    stars = [Star(ep[0],60,ep[1],0)]
    return m, stars, []

def build_wing_mario_rainbow():
    m = Mesh()
    m.add_cube(140,16,140, 0,-5,0, RR_CLOUD)
    for i in range(20):
        c=RR_RAINBOW[i%6]; a=i*0.3; r=200+i*36
        m.add_cube(72,6,72, math.cos(a)*r,i*28+8,math.sin(a)*r, c)
    for cx,cz in [(600,300),(-400,500),(200,-400)]:
        m.add_cube(112,16,112, cx,192,cz, RR_CLOUD)
    m.add_cube(36,36,36, 0,8,0, RED)
    stars = [Star(600,212,300,0)]
    coins = [Coin(math.cos(i*0.3)*(200+i*36),i*28+16,math.sin(i*0.3)*(200+i*36)) for i in range(0,20,4)]
    return m, stars, coins

def build_metal_cap_cavern():
    m = Mesh()
    for x in range(-4,4):
        for z in range(-4,4):
            c = HMC_ROCK_1 if (x+z)%2==0 else HMC_ROCK_2
            m.add_cube(200,10,200, x*200,-5,z*200, c)
    m.add_cube(1600,20,1600, 0,240,0, HMC_ROCK_2)
    m.add_cube(800,4,800, 0,-1,0, HMC_WATER)
    m.add_cube(56,16,56, 0,8,0, PIPE_GREEN)
    m.add_cube(36,36,36, 0,24,0, METAL_GREY)
    m.add_cube(96,192,16, 300,96,-400, (48,96,192))
    for i in range(5):
        m.add_cube(72,8,72, -200+i*96,4,200-i*72, HMC_ROCK_1)
    stars = [Star(0,44,0,0)]
    return m, stars, []

def build_vanish_cap():
    m = Mesh()
    m.add_cube(200,16,200, 0,192,0, HMC_ROCK_1)
    for i in range(15):
        m.add_cube(96,8,96, i*76,176-i*11,0, SL_ICE if i%2==0 else (0,184,184))
    m.add_cube(56,16,56, 1140,8,0, (0,184,184))
    m.add_cube(36,36,36, 1140,24,0, BLUE)
    for i in range(8):
        m.add_cube(56,8,56, 600+i*72,56+i*8,i*36-140, HMC_ROCK_1)
    stars = [Star(1140,44,0,0)]
    return m, stars, []

def build_tower_wing_cap():
    m = Mesh()
    m.add_cube(280,16,280, 0,-5,0, RR_CLOUD)
    m.add_cube(56,380,56, 0,192,0, (144,136,120))
    m.add_cube(96,16,96, 0,380,0, RR_CLOUD)
    m.add_cube(36,36,36, 0,400,0, RED)
    for i in range(8):
        a=i*math.pi/4
        m.add_cube(96,8,96, math.cos(a)*380,192,math.sin(a)*380, RR_CLOUD)
    stars = [Star(0,420,0,0)]
    coins = [Coin(math.cos(i*math.pi/4)*380,204,math.sin(i*math.pi/4)*380) for i in range(8)]
    return m, stars, coins


# === BOWSER LEVELS ===

def build_bowser_dark_world():
    m = Mesh()
    m.add_cube(200,16,200, 0,-5,0, BDW_STONE)
    path = [(200,0),(400,40),(600,80),(600,160),(400,240),(200,240),
            (0,320),(200,400),(400,400),(600,480),(800,480),(1000,400)]
    for px,pz in path:
        m.add_cube(112,16,112, px,8,pz, (96,72,96))
    for fx,fz in [(400,40),(600,160),(200,240)]:
        m.add_cube(8,8,72, fx,28,fz, ORANGE)
    m.add_cube(400,16,400, 1000,8,400, BDW_STONE)
    m.add_cube(56,72,56, 1000,52,400, DARK_GREEN)
    m.add_cube(36,36,36, 1000,108,400, (0,176,0))
    m.add_cube(16,16,8, 1000,124,372, RED)
    for i in range(8):
        a=i*math.pi/4; bx=1000+math.cos(a)*172; bz=400+math.sin(a)*172
        m.add_cube(16,16,16, bx,24,bz, BLACK)
    stars = [Star(1000,112,400,0)]
    return m, stars, []

def build_bowser_fire_sea():
    m = Mesh()
    for x in range(-6,6):
        for z in range(-6,6):
            c = LLL_LAVA_1 if (x+z)%2==0 else LLL_LAVA_2
            m.add_cube(200,6,200, x*200,-3,z*200, c)
    m.add_cube(200,16,200, 0,8,0, BFS_METAL)
    pp = [(0,0),(140,200),(280,400),(140,600),(0,800),
          (-200,1000),(-400,1000),(-400,800),(-200,600),(0,400)]
    for i,(px,pz) in enumerate(pp):
        m.add_cube(96,16,96, px,8+i*4,pz, BFS_METAL)
    m.add_cube(200,6,36, 200,16,200, (96,64,24))
    m.add_cube(200,6,36, -200,16,800, (96,64,24))
    m.add_cube(8,192,8, -400,96,1000, BFS_METAL)
    m.add_cube(480,16,480, 0,52,1200, BDW_STONE)
    m.add_cube(72,96,72, 0,100,1200, DARK_GREEN)
    m.add_cube(48,48,48, 0,168,1200, (0,152,0))
    m.add_cube(24,16,8, 0,184,1160, RED)
    m.add_cube(84,24,84, 0,68,1200, (88,56,24))
    stars = [Star(0,168,1200,0)]
    return m, stars, []

def build_bowser_sky():
    m = Mesh()
    m.add_cube(200,16,200, 0,-5,0, BITS_STONE)
    sp = []
    for i in range(25):
        a=i*0.24; r=200+i*18; px=math.cos(a)*r; pz=math.sin(a)*r; py=i*36
        sp.append((px,py,pz))
        c = [BITS_STONE,(80,56,80),DARK_GREY,BFS_METAL][i%4]
        m.add_cube(96,12,96, px,py,pz, c)
    for i in range(0,25,3):
        px,py,pz = sp[i]
        m.add_cube(8,8,56, px+36,py+16,pz, ORANGE)
    last = sp[-1]
    ax,ay,az = last[0],last[1]+36,last[2]
    m.add_cube(560,16,560, ax,ay,az, BITS_STONE)
    for i in range(12):
        a=i*math.pi/6; bx=ax+math.cos(a)*260; bz=az+math.sin(a)*260
        m.add_cube(16,16,16, bx,ay+16,bz, BLACK)
    m.add_cube(96,112,96, ax,ay+72,az, DARK_GREEN)
    m.add_cube(56,56,56, ax,ay+168,az, (0,168,0))
    m.add_cube(36,24,8, ax,ay+188,az-44, RED)
    for sx,sz in [(-28,0),(28,0),(0,-28),(0,28)]:
        m.add_cube(12,20,12, ax+sx,ay+120,az+sz, (88,56,24))
    stars = [Star(ax,ay+208,az,0)]
    return m, stars, []


# =====================================================================
# LEVEL REGISTRY
# =====================================================================
LEVELS = {
    "castle_grounds": {"name":"Castle Grounds","builder":build_castle_grounds,"req":0},
    "castle_f1": {"name":"Castle Interior","builder":build_castle_interior_f1,"req":0},
    "castle_basement": {"name":"Castle Basement","builder":build_castle_basement,"req":8},
    "castle_upper": {"name":"Castle Upper Floor","builder":build_castle_upper,"req":30},
    "castle_top": {"name":"Castle Top","builder":build_castle_top,"req":50},
    "c01_bob": {"name":"Bob-omb Battlefield","builder":build_bob_omb_battlefield,"req":0},
    "c02_whomp": {"name":"Whomp's Fortress","builder":build_whomps_fortress,"req":1},
    "c03_jolly": {"name":"Jolly Roger Bay","builder":build_jolly_roger_bay,"req":3},
    "c04_cool": {"name":"Cool, Cool Mountain","builder":build_cool_cool_mountain,"req":3},
    "c05_boo": {"name":"Big Boo's Haunt","builder":build_big_boos_haunt,"req":12},
    "c06_hazy": {"name":"Hazy Maze Cave","builder":build_hazy_maze_cave,"req":8},
    "c07_lava": {"name":"Lethal Lava Land","builder":build_lethal_lava_land,"req":8},
    "c08_sand": {"name":"Shifting Sand Land","builder":build_shifting_sand_land,"req":8},
    "c09_dock": {"name":"Dire, Dire Docks","builder":build_dire_dire_docks,"req":30},
    "c10_snow": {"name":"Snowman's Land","builder":build_snowmans_land,"req":30},
    "c11_wet": {"name":"Wet-Dry World","builder":build_wet_dry_world,"req":30},
    "c12_tall": {"name":"Tall, Tall Mountain","builder":build_tall_tall_mountain,"req":30},
    "c13_tiny": {"name":"Tiny-Huge Island","builder":build_tiny_huge_island,"req":30},
    "c14_clock": {"name":"Tick Tock Clock","builder":build_tick_tock_clock,"req":50},
    "c15_rainbow": {"name":"Rainbow Ride","builder":build_rainbow_ride,"req":50},
    "s_slide": {"name":"Princess's Secret Slide","builder":build_princess_secret_slide,"req":1},
    "s_wing": {"name":"Wing Mario Over Rainbow","builder":build_wing_mario_rainbow,"req":10},
    "s_metal": {"name":"Metal Cap Cavern","builder":build_metal_cap_cavern,"req":8},
    "s_vanish": {"name":"Vanish Cap Moat","builder":build_vanish_cap,"req":8},
    "s_tower": {"name":"Tower of Wing Cap","builder":build_tower_wing_cap,"req":10},
    "b1_dark": {"name":"Bowser Dark World","builder":build_bowser_dark_world,"req":8},
    "b2_fire": {"name":"Bowser Fire Sea","builder":build_bowser_fire_sea,"req":30},
    "b3_sky": {"name":"Bowser in the Sky","builder":build_bowser_sky,"req":70},
}

# Painting portal info for castle navigation
CASTLE_F1_PAINTINGS = [
    {"pos":(-978,140,-300),"level":"c01_bob"},{"pos":(-978,140,-500),"level":"c02_whomp"},
    {"pos":(-978,140,-700),"level":"c03_jolly"},{"pos":(978,140,-300),"level":"c04_cool"},
    {"pos":(978,140,-500),"level":"c05_boo"},
]
BASEMENT_PAINTINGS = [
    {"pos":(-1178,100,-400),"level":"c06_hazy"},{"pos":(-1178,100,-600),"level":"c07_lava"},
    {"pos":(-1178,100,-800),"level":"c08_sand"},{"pos":(1178,100,-400),"level":"c09_dock"},
]
UPPER_PAINTINGS = [
    {"pos":(-778,100,-300),"level":"c10_snow"},{"pos":(-778,100,-500),"level":"c11_wet"},
    {"pos":(778,100,-300),"level":"c12_tall"},{"pos":(778,100,-500),"level":"c13_tiny"},
    {"pos":(0,60,-778),"level":"c14_clock"},{"pos":(0,75,-790),"level":"c15_rainbow"},
]


# =====================================================================
# RENDERER (with SM64 PC port distance fog + pitch support)
# =====================================================================
def render_mesh(screen, mesh, cam_x, cam_y, cam_z, cam_yaw, cam_pitch, cx, cy, is_menu=False):
    render_list = []
    c_cos = math.cos(-cam_yaw); c_sin = math.sin(-cam_yaw)
    p_cos = math.cos(-cam_pitch); p_sin = math.sin(-cam_pitch)
    m_cos = math.cos(mesh.yaw); m_sin = math.sin(mesh.yaw)
    menu_tilt = 0.2
    wiggle = math.sin(pygame.time.get_ticks()/500.0)*10 if is_menu else 0

    for face in mesh.faces:
        transformed = []; avg_z = 0; valid = True
        for i in face.indices:
            v = mesh.vertices[i]
            # Object rotation
            rx = v.x*m_cos - v.z*m_sin
            rz = v.x*m_sin + v.z*m_cos
            ry = v.y
            if is_menu:
                ry_t = ry*math.cos(menu_tilt)-rz*math.sin(menu_tilt)
                rz = ry*math.sin(menu_tilt)+rz*math.cos(menu_tilt)
                ry = ry_t + wiggle
            # World translate
            wx=rx+mesh.x; wy=ry+mesh.y; wz=rz+mesh.z
            # Camera translate
            dcx=wx-cam_x; dcy=wy-cam_y; dcz=wz-cam_z
            if not is_menu:
                # Yaw rotation
                xx=dcx*c_cos-dcz*c_sin; zz=dcx*c_sin+dcz*c_cos; yy=dcy
                # Pitch rotation
                yy2=yy*p_cos-zz*p_sin; zz2=yy*p_sin+zz*p_cos
                xx,yy,zz = xx,yy2,zz2
            else:
                xx=dcx; yy=dcy; zz=dcz
            if zz < 5:
                valid = False; break
            transformed.append((xx,yy,zz)); avg_z += zz
        if not valid: continue
        screen_points = []
        for xx,yy,zz in transformed:
            s = FOV/zz
            screen_points.append((int(xx*s+cx), int(-yy*s+cy)))
        if len(screen_points)>=3:
            area = 0
            for i in range(len(screen_points)):
                j=(i+1)%len(screen_points)
                area+=(screen_points[j][0]-screen_points[i][0])*(screen_points[j][1]+screen_points[i][1])
            if area > 0:
                render_list.append({'poly':screen_points,'depth':avg_z/len(transformed),'color':face.color})
    return render_list


# =====================================================================
# MENU HEAD
# =====================================================================
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


# =====================================================================
# MAIN LOOP
# =====================================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ULTRA MARIO 64 — SM64 PC PORT EDITION")
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
        font_hud = font_small; font_big = font_menu

    STATE_MENU=0; STATE_GAME=1; STATE_LEVEL_SELECT=2; STATE_PAUSE=3
    current_state = STATE_MENU

    menu_head = create_menu_head()
    menu_items = ["PLAY GAME","LEVEL SELECT","HOW TO PLAY","CREDITS","EXIT GAME"]
    selected_index = 0; active_overlay = None

    level_keys = list(LEVELS.keys())
    level_select_idx = 0

    mario = None
    current_level_mesh = None
    current_level_stars = []
    current_level_coins = []
    current_level_id = None
    cam_x=cam_y=cam_z=0.0; cam_yaw=0.0; cam_pitch=0.0
    vel_x=vel_z=0.0; head_bob_phase=0.0; mouse_captured=False
    cx,cy = WIDTH//2,HEIGHT//2
    collected_stars = set(); total_coins = 0
    star_flash=0; coin_flash=0; level_name_timer=0; level_display_name=""

    def release_mouse():
        nonlocal mouse_captured
        pygame.mouse.set_visible(True); pygame.event.set_grab(False); mouse_captured=False

    def capture_mouse():
        nonlocal mouse_captured
        pygame.mouse.set_visible(False); pygame.event.set_grab(True); mouse_captured=True
        pygame.mouse.set_pos(cx, cy)

    def load_level(level_id):
        nonlocal mario, current_level_mesh, current_level_stars, current_level_coins
        nonlocal current_level_id, cam_x,cam_y,cam_z,cam_yaw,cam_pitch
        nonlocal vel_x,vel_z,head_bob_phase, level_name_timer,level_display_name
        info = LEVELS[level_id]
        current_level_id = level_id
        level_display_name = info["name"]; level_name_timer = 180
        result = info["builder"]()
        if isinstance(result,tuple):
            if len(result)==3: current_level_mesh,current_level_stars,current_level_coins=result
            elif len(result)==2: current_level_mesh,current_level_stars=result; current_level_coins=[]
            else: current_level_mesh=result[0]; current_level_stars=[]; current_level_coins=[]
        else: current_level_mesh=result; current_level_stars=[]; current_level_coins=[]
        mario = Mario(0,50,400)
        cam_yaw=math.pi; cam_pitch=0.0
        cam_x=mario.x; cam_y=mario.y+EYE_HEIGHT; cam_z=mario.z
        vel_x=vel_z=0.0; head_bob_phase=0.0
        capture_mouse()

    def draw_sm64_sky(level_id):
        """SM64 PC port gradient sky"""
        sky = SM64_SKIES.get(level_id, ((80,144,248),(184,216,248),(160,200,240)))
        top, bot, fog = sky
        for y in range(HEIGHT):
            t = y/HEIGHT
            r=int(top[0]*(1-t)+bot[0]*t)
            g=int(top[1]*(1-t)+bot[1]*t)
            b=int(top[2]*(1-t)+bot[2]*t)
            pygame.draw.line(screen,(max(0,min(255,r)),max(0,min(255,g)),max(0,min(255,b))),(0,y),(WIDTH,y))
        return fog

    def draw_hud():
        nonlocal star_flash, coin_flash
        bar = pygame.Surface((WIDTH,50)); bar.set_alpha(180); bar.fill(BLACK)
        screen.blit(bar,(0,HEIGHT-50))
        pygame.draw.line(screen,METAL_GREY,(0,HEIGHT-50),(WIDTH,HEIGHT-50),2)
        sc = YELLOW if star_flash<=0 else WHITE
        screen.blit(font_hud.render(f"★ {len(collected_stars)}",True,sc),(16,HEIGHT-38))
        cc = YELLOW if coin_flash<=0 else WHITE
        screen.blit(font_hud.render(f"● {total_coins}",True,cc),(112,HEIGHT-38))
        screen.blit(font_hud.render(f"♥ x{mario.lives}",True,RED),(208,HEIGHT-38))
        for i in range(8):
            c = RED if i<mario.health else DARK_GREY
            pygame.draw.rect(screen,c,(308+i*18,HEIGHT-38,14,14))
        screen.blit(font_hud.render(f"FPS:{int(clock.get_fps())}",True,(0,200,0)),(WIDTH-96,HEIGHT-38))
        if current_level_id:
            n = font_small.render(LEVELS[current_level_id]["name"],True,WHITE)
            screen.blit(n,(WIDTH//2-n.get_width()//2,HEIGHT-38))
        star_flash=max(0,star_flash-1); coin_flash=max(0,coin_flash-1)

    def draw_level_intro():
        nonlocal level_name_timer
        if level_name_timer > 0:
            a = min(255,level_name_timer*3)
            ov = pygame.Surface((WIDTH,72)); ov.set_alpha(a); ov.fill(BLACK)
            screen.blit(ov,(0,HEIGHT//2-36))
            t = font_big.render(level_display_name,True,YELLOW)
            screen.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//2-18))
            level_name_timer -= 1

    def draw_crosshair():
        """Small + crosshair for first-person"""
        pygame.draw.line(screen,(255,255,255,128),(cx-8,cy),(cx+8,cy),1)
        pygame.draw.line(screen,(255,255,255,128),(cx,cy-8),(cx,cy+8),1)

    running = True
    while running:
        dt = clock.tick(FPS)
        time_sec = pygame.time.get_ticks()/1000.0

        # Mouse delta for first-person look
        mouse_dx = mouse_dy = 0
        if mouse_captured:
            mx,my = pygame.mouse.get_pos()
            mouse_dx = mx - cx; mouse_dy = my - cy
            if abs(mouse_dx)>0 or abs(mouse_dy)>0:
                pygame.mouse.set_pos(cx,cy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            if current_state == STATE_MENU:
                if event.type == pygame.KEYDOWN:
                    if active_overlay:
                        if event.key in (pygame.K_ESCAPE,pygame.K_b,pygame.K_RETURN): active_overlay=None
                    else:
                        if event.key==pygame.K_UP: selected_index=(selected_index-1)%len(menu_items)
                        elif event.key==pygame.K_DOWN: selected_index=(selected_index+1)%len(menu_items)
                        elif event.key in (pygame.K_RETURN,pygame.K_SPACE):
                            ch = menu_items[selected_index]
                            if ch=="EXIT GAME": running=False
                            elif ch=="PLAY GAME": current_state=STATE_GAME; load_level("castle_grounds")
                            elif ch=="LEVEL SELECT": current_state=STATE_LEVEL_SELECT; level_select_idx=0
                            elif ch=="HOW TO PLAY": active_overlay="how"
                            elif ch=="CREDITS": active_overlay="credits"

            elif current_state == STATE_LEVEL_SELECT:
                if event.type == pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: current_state=STATE_MENU
                    elif event.key==pygame.K_UP: level_select_idx=(level_select_idx-1)%len(level_keys)
                    elif event.key==pygame.K_DOWN: level_select_idx=(level_select_idx+1)%len(level_keys)
                    elif event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        current_state=STATE_GAME; load_level(level_keys[level_select_idx])

            elif current_state == STATE_GAME:
                if event.type == pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        current_state=STATE_PAUSE; release_mouse()
                    elif event.key==pygame.K_SPACE and mario and not mario.is_jumping:
                        mario.dy=JUMP_FORCE; mario.is_jumping=True
                    elif event.key==pygame.K_e:
                        # Level transitions
                        if current_level_id=="castle_grounds":
                            if abs(mario.x)<100 and mario.z<-900: load_level("castle_f1")
                        elif current_level_id=="castle_f1":
                            entered=False
                            for p in CASTLE_F1_PAINTINGS:
                                if abs(mario.x-p["pos"][0])<150 and abs(mario.z-p["pos"][2])<150:
                                    load_level(p["level"]); entered=True; break
                            if not entered:
                                if abs(mario.x-600)<100 and abs(mario.z-600)<100: load_level("castle_basement")
                                elif abs(mario.x)<200 and mario.z<-800: load_level("castle_upper")
                                elif abs(mario.x)<200 and mario.z>800: load_level("castle_grounds")
                                elif abs(mario.x)<100 and abs(mario.z)<100 and mario.y>50: load_level("s_slide")
                        elif current_level_id=="castle_basement":
                            entered=False
                            for p in BASEMENT_PAINTINGS:
                                if abs(mario.x-p["pos"][0])<150 and abs(mario.z-p["pos"][2])<150:
                                    load_level(p["level"]); entered=True; break
                            if not entered:
                                if abs(mario.x-800)<100 and abs(mario.z-800)<100: load_level("s_metal")
                                elif abs(mario.x-600)<100 and abs(mario.z+1178)<100: load_level("s_vanish")
                                elif abs(mario.x)<200 and mario.z>1000: load_level("castle_f1")
                                elif abs(mario.x)<100 and abs(mario.z+600)<100: load_level("b1_dark")
                        elif current_level_id=="castle_upper":
                            entered=False
                            for p in UPPER_PAINTINGS:
                                if abs(mario.x-p["pos"][0])<150 and abs(mario.z-p["pos"][2])<150:
                                    load_level(p["level"]); entered=True; break
                            if not entered:
                                if abs(mario.x)<200 and mario.z<-600: load_level("castle_top")
                                elif abs(mario.x)<200 and mario.z>600: load_level("castle_f1")
                                elif abs(mario.x-600)<200 and abs(mario.z)<200: load_level("b2_fire")
                        elif current_level_id=="castle_top":
                            if abs(mario.x)<100 and abs(mario.z)<100: load_level("s_tower")
                            elif abs(mario.x)<200 and mario.z>300: load_level("castle_upper")
                            elif mario.y>100: load_level("b3_sky")
                        else:
                            load_level("castle_f1")
                    elif event.key==pygame.K_TAB:
                        # Toggle mouse capture
                        if mouse_captured: release_mouse()
                        else: capture_mouse()

            elif current_state == STATE_PAUSE:
                if event.type == pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: current_state=STATE_GAME; capture_mouse()
                    elif event.key==pygame.K_q: current_state=STATE_MENU; release_mouse()
                    elif event.key==pygame.K_r:
                        if current_level_id: load_level(current_level_id); current_state=STATE_GAME

        # ============ RENDER ============

        if current_state == STATE_MENU:
            for y in range(HEIGHT):
                t=y/HEIGHT
                r=int(26*(1-t)); g=int(26*(1-t)); b=int(77*(1-t))
                pygame.draw.line(screen,(r,g,b),(0,y),(WIDTH,y))
            menu_head.yaw += 0.02
            polys = render_mesh(screen,menu_head,0,0,200,0,0,cx,cy,is_menu=True)
            polys.sort(key=lambda x:x['depth'],reverse=True)
            for p in polys:
                pygame.draw.polygon(screen,p['color'],p['poly'])
                pygame.draw.polygon(screen,BLACK,p['poly'],1)
            ly = 40+math.sin(time_sec)*5
            ts = font_title.render("ULTRA MARIO 64",True,WHITE)
            th = font_title.render("ULTRA MARIO 64",True,RED)
            screen.blit(th,(WIDTH//2-ts.get_width()//2+3,ly+3))
            screen.blit(ts,(WIDTH//2-ts.get_width()//2,ly))
            sub = font_small.render("SM64 PC PORT EDITION — ALL 26 LEVELS",True,YELLOW)
            screen.blit(sub,(WIDTH//2-sub.get_width()//2,ly+55))
            my = HEIGHT-220
            for i,item in enumerate(menu_items):
                c = YELLOW if i==selected_index else WHITE
                l = font_menu.render(item,True,c)
                screen.blit(l,(50+(20 if i==selected_index else 0),my+i*38))
                if i==selected_index:
                    pygame.draw.polygon(screen,RED,[(32,my+i*38+8),(44,my+i*38+14),(32,my+i*38+20)])
            sc = font_small.render(f"Stars: {len(collected_stars)}/{STAR_TOTAL}",True,YELLOW)
            screen.blit(sc,(WIDTH-140,HEIGHT-28))

            if active_overlay=="how":
                ov=pygame.Surface((WIDTH,HEIGHT)); ov.set_alpha(230); ov.fill(BLACK); screen.blit(ov,(0,0))
                pygame.draw.rect(screen,RED,(60,60,WIDTH-120,HEIGHT-120),3)
                lines=["CONTROLS:","Mouse — Look Around","WASD — Move (Shift = Sprint)",
                       "SPACE — Jump","E — Enter Door/Painting/Exit Level",
                       "TAB — Toggle Mouse Capture","ESC — Pause","","FIRST PERSON LAKITU CAMERA",
                       "Explore Peach's Castle! Enter paintings!","Collect Stars and defeat Bowser!","","ENTER to close"]
                for i,ln in enumerate(lines):
                    c=YELLOW if i==0 else WHITE
                    f=font_menu if i==0 else font_small
                    screen.blit(f.render(ln,True,c),(100,92+i*32))
            elif active_overlay=="credits":
                ov=pygame.Surface((WIDTH,HEIGHT)); ov.set_alpha(230); ov.fill(BLACK); screen.blit(ov,(0,0))
                pygame.draw.rect(screen,BUTTON_GOLD,(60,60,WIDTH-120,HEIGHT-120),3)
                lines=["ULTRA MARIO 64 — SM64 PC PORT EDITION","",
                       "Engine: Pure Pygame 3D + First-Person Lakitu",
                       "All 15 Courses + 5 Secret + 3 Bowser Levels",
                       "SM64 Authentic Color Palettes",
                       "PC Port Sky Gradients + Distance Fog","",
                       f"Programming: Team Flames / Samsoft",
                       "Inspired by: Super Mario 64 (1996)","SM64 PC Port (sm64ex)","","ENTER to close"]
                for i,ln in enumerate(lines):
                    c=YELLOW if i==0 else WHITE
                    f=font_menu if i==0 else font_small
                    screen.blit(f.render(ln,True,c),(100,88+i*32))

        elif current_state == STATE_LEVEL_SELECT:
            screen.fill((8,8,24))
            t = font_big.render("LEVEL SELECT",True,YELLOW)
            screen.blit(t,(WIDTH//2-t.get_width()//2,16))
            vs = max(0,level_select_idx-12); ve = min(len(level_keys),vs+18)
            y = 64
            for i in range(vs,ve):
                k=level_keys[i]; info=LEVELS[k]
                sel = i==level_select_idx
                c = YELLOW if sel else WHITE
                pfx = "► " if sel else "  "
                if k.startswith("castle"): dc=CG_CASTLE_WALL
                elif k.startswith("c"): dc=BOB_GRASS_1
                elif k.startswith("s"): dc=(0,200,200)
                else: dc=LLL_LAVA_1
                screen.blit(font_menu.render(f"{pfx}{info['name']}",True,c),(36,y))
                screen.blit(font_small.render(f"Req:{info['req']}★",True,dc),(580,y+4))
                pygame.draw.circle(screen,dc,(22,y+12),5)
                y += 27
            screen.blit(font_small.render("UP/DOWN: Navigate | ENTER: Play | ESC: Back",True,METAL_GREY),
                        (WIDTH//2-180,HEIGHT-28))

        elif current_state == STATE_GAME:
            fog_color = draw_sm64_sky(current_level_id)

            # === FIRST-PERSON MOVEMENT ===
            if mouse_captured:
                cam_yaw += mouse_dx * MOUSE_SENS_X
                cam_pitch -= mouse_dy * MOUSE_SENS_Y
                cam_pitch = max(PITCH_MIN, min(PITCH_MAX, cam_pitch))

            keys = pygame.key.get_pressed()
            # Keyboard look (C-button equivalent)
            if keys[pygame.K_LEFT]: cam_yaw -= KEY_TURN
            if keys[pygame.K_RIGHT]: cam_yaw += KEY_TURN
            if keys[pygame.K_UP]: cam_pitch = min(PITCH_MAX, cam_pitch + KEY_TURN*0.7)
            if keys[pygame.K_DOWN]: cam_pitch = max(PITCH_MIN, cam_pitch - KEY_TURN*0.7)

            # SM64-style movement
            fwd_x = -math.sin(cam_yaw); fwd_z = -math.cos(cam_yaw)
            right_x = math.cos(cam_yaw); right_z = -math.sin(cam_yaw)
            accel_x = accel_z = 0
            sprint = SPRINT_MULT if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1.0
            if keys[pygame.K_w]: accel_x += fwd_x*MOVE_ACCEL*sprint; accel_z += fwd_z*MOVE_ACCEL*sprint
            if keys[pygame.K_s]: accel_x -= fwd_x*MOVE_ACCEL*0.6; accel_z -= fwd_z*MOVE_ACCEL*0.6
            if keys[pygame.K_a]: accel_x -= right_x*MOVE_ACCEL*0.8; accel_z -= right_z*MOVE_ACCEL*0.8
            if keys[pygame.K_d]: accel_x += right_x*MOVE_ACCEL*0.8; accel_z += right_z*MOVE_ACCEL*0.8

            vel_x = (vel_x + accel_x) * MOVE_DECEL
            vel_z = (vel_z + accel_z) * MOVE_DECEL
            speed = math.sqrt(vel_x*vel_x + vel_z*vel_z)
            max_spd = MAX_SPEED * sprint
            if speed > max_spd:
                vel_x *= max_spd/speed; vel_z *= max_spd/speed
                speed = max_spd

            if mario:
                mario.x += vel_x; mario.z += vel_z
                mario.yaw = cam_yaw
                mario.update()

                # Head bob
                if speed > 1.0 and not mario.is_jumping:
                    head_bob_phase += speed * 0.15
                    bob = math.sin(head_bob_phase) * HEAD_BOB_AMT * min(1.0, speed/8.0)
                else:
                    bob = 0; head_bob_phase *= 0.8

                # Camera = Mario's eyes (smooth)
                target_x = mario.x; target_y = mario.y + EYE_HEIGHT + bob; target_z = mario.z
                cam_x += (target_x - cam_x) * CAM_LERP
                cam_y += (target_y - cam_y) * CAM_LERP
                cam_z += (target_z - cam_z) * CAM_LERP

                # Collectibles
                for star in current_level_stars:
                    if not star.collected:
                        star.yaw += 0.05
                        dx=mario.x-star.x; dy=mario.y-star.y; dz=mario.z-star.z
                        if math.sqrt(dx*dx+dy*dy+dz*dz)<60:
                            star.collected=True; collected_stars.add(f"{current_level_id}_{star.star_id}")
                            star_flash=30
                for coin in current_level_coins:
                    if not coin.collected:
                        coin.yaw += 0.08
                        dx=mario.x-coin.x; dy=mario.y-coin.y; dz=mario.z-coin.z
                        if math.sqrt(dx*dx+dy*dy+dz*dz)<40:
                            coin.collected=True; total_coins+=1; coin_flash=15
                            if total_coins%50==0: mario.lives+=1

            # === RENDER SCENE ===
            all_polys = []
            if current_level_mesh:
                all_polys.extend(render_mesh(screen,current_level_mesh,cam_x,cam_y,cam_z,cam_yaw,cam_pitch,cx,cy))
            for star in current_level_stars:
                if not star.collected:
                    all_polys.extend(render_mesh(screen,star,cam_x,cam_y,cam_z,cam_yaw,cam_pitch,cx,cy))
            for coin in current_level_coins:
                if not coin.collected:
                    all_polys.extend(render_mesh(screen,coin,cam_x,cam_y,cam_z,cam_yaw,cam_pitch,cx,cy))

            all_polys.sort(key=lambda x:x['depth'],reverse=True)

            for item in all_polys:
                depth = item['depth']
                fog = min(1.0, depth/VIEW_DISTANCE)
                r,g,b = item['color']
                fr=int(r+(fog_color[0]-r)*fog); fg=int(g+(fog_color[1]-g)*fog); fb=int(b+(fog_color[2]-b)*fog)
                pygame.draw.polygon(screen,(max(0,min(255,fr)),max(0,min(255,fg)),max(0,min(255,fb))),item['poly'])

            draw_crosshair()
            draw_hud()
            draw_level_intro()

            hint = "E: Enter Door/Painting" if current_level_id and "castle" in current_level_id else "E: Exit Level" if current_level_id else ""
            if hint:
                screen.blit(font_small.render(hint,True,YELLOW),(WIDTH//2-60,8))

        elif current_state == STATE_PAUSE:
            ov=pygame.Surface((WIDTH,HEIGHT)); ov.set_alpha(180); ov.fill(BLACK); screen.blit(ov,(0,0))
            screen.blit(font_big.render("PAUSED",True,YELLOW),(WIDTH//2-60,140))
            for i,(t,c) in enumerate([("ESC - Resume",WHITE),("R - Restart Level",WHITE),
                                       ("Q - Quit to Menu",WHITE),("",WHITE),
                                       (f"Stars: {len(collected_stars)}/{STAR_TOTAL}",YELLOW),
                                       (f"Coins: {total_coins}",YELLOW),
                                       (f"Lives: {mario.lives if mario else 4}",RED)]):
                if t: screen.blit(font_menu.render(t,True,c),(WIDTH//2-100,212+i*34))

        # SM64 CRT scanlines (subtle)
        for y in range(0,HEIGHT,4):
            pygame.draw.line(screen,(0,0,0),(0,y),(WIDTH,y),1)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
