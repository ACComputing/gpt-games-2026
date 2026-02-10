#!/usr/bin/env python3
"""
AC's Ultra!TETRIS - Pygame Edition
AC Entertainment [C] 1999-2026 Tetris Co. 1984

1:1 authentic 1990s Game Boy/NES Tetris at 60 FPS.
NRS rotation, instant lock, no hold, no ghost, NES DAS,
NES/Famicom gravity, NES scoring, level select, piece stats,
GB Korobeiniki chiptune (DMG-01 pulse+wave synthesis).
"""

import pygame, sys, random, math, struct, array

# ====================== CONSTANTS ======================
SW, SH = 800, 600
COLS, ROWS = 10, 20
BLK = 24
FPS = 60
BRD_X = SW // 2 - COLS * BLK // 2
BRD_Y = SH // 2 - ROWS * BLK // 2 + 8

C_BG    = (8, 8, 20)
C_GRID  = (22, 22, 44)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_RED   = (255, 48, 48)
C_DRED  = (128, 0, 0)
C_YEL   = (255, 204, 0)
C_GRAY  = (136, 136, 170)
C_DGRAY = (60, 60, 80)
C_PBG   = (12, 12, 30)
C_PBOR  = (55, 55, 85)

PNAMES = ['T', 'J', 'Z', 'O', 'S', 'L', 'I']

# ====================== NRS ROTATION (1:1 Authentic) ======================
# Nintendo Rotation System (Right-Handed / CW).
# T, J, L spawn flat-side up (or T pointing down). I, S, Z spawn horizontal.
ROT = {
    'I': [
        [(0,1),(1,1),(2,1),(3,1)], # Horizontal
        [(2,0),(2,1),(2,2),(2,3)], # Vertical
    ],
    'O': [[(0,0),(1,0),(0,1),(1,1)]],
    'T': [
        [(0,0),(1,0),(2,0),(1,1)], # Down (Spawn)
        [(1,0),(0,1),(1,1),(1,2)], # Left
        [(1,0),(0,1),(1,1),(2,1)], # Up
        [(1,0),(1,1),(2,1),(1,2)], # Right
    ],
    'J': [
        [(0,0),(1,0),(2,0),(2,1)], # Flat Up (Spawn)
        [(1,0),(1,1),(0,2),(1,2)], # Left
        [(0,0),(0,1),(1,1),(2,1)], # Flat Down
        [(1,0),(2,0),(1,1),(1,2)], # Right
    ],
    'L': [
        [(0,0),(1,0),(2,0),(0,1)], # Flat Up (Spawn)
        [(0,0),(1,0),(1,1),(1,2)], # Left
        [(2,0),(0,1),(1,1),(2,1)], # Flat Down
        [(1,0),(1,1),(1,2),(2,2)], # Right
    ],
    'S': [
        [(1,0),(2,0),(0,1),(1,1)], # Horizontal
        [(0,0),(0,1),(1,1),(1,2)], # Vertical
    ],
    'Z': [
        [(0,0),(1,0),(1,1),(2,1)], # Horizontal
        [(1,0),(0,1),(1,1),(0,2)], # Vertical
    ]
}

# ====================== GRAVITY (frames per drop at 60fps) ======================
# Authentic Famicom/NES (NTSC) speeds (1:1)
# Level 0 starts at 48 frames. Level 29 is the "Kill Screen" (1 frame).
GRAV = {
    0: 48, 1: 43, 2: 38, 3: 33, 4: 28, 5: 23, 6: 18, 7: 13, 8: 8, 9: 6,
    10: 5, 11: 5, 12: 5,
    13: 4, 14: 4, 15: 4,
    16: 3, 17: 3, 18: 3,
    19: 2, 20: 2, 21: 2, 22: 2, 23: 2, 24: 2, 25: 2, 26: 2, 27: 2, 28: 2
}

DAS_INIT = 16
DAS_REP  = 6
ARE_FR   = 10
LSCORES  = {1: 40, 2: 100, 3: 300, 4: 1200}

# ====================== NES LEVEL PALETTES ======================
# Two colours per level. A=T,J,Z  B=O,S,L,I
PALS = [
    ((0,88,248),   (60,188,252)),
    ((0,168,0),    (128,208,16)),
    ((148,0,148),  (248,56,248)),
    ((0,88,248),   (108,136,252)),
    ((172,0,32),   (0,168,68)),
    ((0,168,148),  (104,68,252)),
    ((200,16,16),  (132,132,132)),
    ((104,68,252), (60,24,168)),
    ((0,148,0),    (172,0,0)),
    ((172,0,32),   (248,56,0)),
]
A_SET = {'T', 'J', 'Z'}

def pcol(name, lv):
    p = PALS[lv % len(PALS)]
    return p[0] if name in A_SET else p[1]

# ====================== GB AUDIO ENGINE ======================
SR = 44100

def _pulse(freq, dur, duty=0.25, vol=0.3, decay=0.0, cut=0.92):
    n = int(SR * dur)
    cs = int(n * cut)
    at = int(SR * 0.004)
    fz = int(SR * 0.006)
    out = array.array('h')
    for i in range(n):
        if freq <= 0 or i >= cs:
            out.append(0)
            continue
        t = i / SR
        w = 1.0 if (freq * t) % 1.0 < duty else -1.0
        v = max(0.0, vol - decay * t) if decay > 0 else vol
        if i < at:
            v *= i / at
        dc = cs - i
        if 0 < dc < fz:
            v *= dc / fz
        out.append(int(max(-32767, min(32767, w * v * 32767))))
    return out

def _wave(freq, dur, vol=0.25, cut=0.88):
    wt = [0xF,0xE,0xD,0xC,0xB,0xA,0x9,0x8,0x7,0x6,0x5,0x4,0x3,0x2,0x1,0x0,
          0x0,0x1,0x2,0x3,0x4,0x5,0x6,0x7,0x8,0x9,0xA,0xB,0xC,0xD,0xE,0xF]
    wn = [(s / 7.5) - 1.0 for s in wt]
    n = int(SR * dur)
    cs = int(n * cut)
    at = int(SR * 0.003)
    fz = int(SR * 0.008)
    out = array.array('h')
    for i in range(n):
        if freq <= 0 or i >= cs:
            out.append(0)
            continue
        t = i / SR
        w = wn[int((freq * t) % 1.0 * 32) % 32]
        v = vol
        if i < at:
            v *= i / at
        dc = cs - i
        if 0 < dc < fz:
            v *= dc / fz
        out.append(int(max(-32767, min(32767, w * v * 32767))))
    return out

def _noise(dur, vol=0.15, pitch=6):
    n = int(SR * dur)
    at = int(SR * 0.002)
    out = array.array('h')
    lfsr = 0x7FFF
    ctr = 0
    per = max(1, pitch * 4)
    cb = 1
    for i in range(n):
        ctr += 1
        if ctr >= per:
            ctr = 0
            b0 = lfsr & 1
            b1 = (lfsr >> 1) & 1
            lfsr = (lfsr >> 1) | ((b0 ^ b1) << 14)
            cb = 1 if lfsr & 1 else -1
        v = vol
        if i < at:
            v *= i / at
        v *= max(0.0, 1.0 - (i / n) * 1.5)
        out.append(int(max(-32767, min(32767, cb * v * 32767))))
    return out

def _snd(s):
    return pygame.mixer.Sound(buffer=struct.pack(f'<{len(s)}h', *s))

def _mix(*arrs):
    ml = max(len(a) for a in arrs)
    m = array.array('h', [0] * ml)
    for a in arrs:
        for i in range(len(a)):
            m[i] = int(max(-32767, min(32767, m[i] + a[i])))
    return m

NF = {
    'B2':123.47, 'C3':130.81, 'D3':146.83, 'E3':164.81,
    'F3':174.61, 'G3':196.00, 'Ab3':207.65, 'A3':220.00,
    'B3':246.94, 'C4':261.63, 'D4':293.66, 'E4':329.63,
    'F4':349.23, 'G4':392.00, 'A4':440.00, 'R':0,
}

BPM = 152
BT = 60.0 / BPM

MEL = [
    ('E4',1),('B3',.5),('C4',.5),('D4',1),('C4',.5),('B3',.5),
    ('A3',1),('A3',.5),('C4',.5),('E4',1),('D4',.5),('C4',.5),
    ('B3',1.5),('C4',.5),('D4',1),('E4',1),
    ('C4',1),('A3',1),('A3',1),('R',1),
    ('R',.5),('D4',1),('F4',.5),('A4',1),('G4',.5),('F4',.5),
    ('E4',1.5),('C4',.5),('E4',1),('D4',.5),('C4',.5),
    ('B3',1),('B3',.5),('C4',.5),('D4',1),('E4',1),
    ('C4',1),('A3',1),('A3',1),('R',1),
]
HAR = [
    ('E3',2),('R',2),('A3',2),('R',2),
    ('G3',2),('R',2),('A3',2),('R',2),
    ('D3',2),('R',2),('E3',2),('R',2),
    ('G3',2),('R',2),('A3',2),('R',2),
]
BAS = [
    ('E3',.5),('R',.5),('E3',.5),('R',.5),('E3',.5),('R',.5),('E3',.5),('R',.5),
    ('A3',.5),('R',.5),('A3',.5),('R',.5),('A3',.5),('R',.5),('A3',.5),('R',.5),
    ('Ab3',.5),('R',.5),('Ab3',.5),('R',.5),('Ab3',.5),('R',.5),('Ab3',.5),('R',.5),
    ('A3',.5),('R',.5),('A3',.5),('R',.5),('A3',.5),('R',.5),('A3',.5),('R',.5),
    ('D3',.5),('R',.5),('D3',.5),('R',.5),('D3',.5),('R',.5),('D3',.5),('R',.5),
    ('C3',.5),('R',.5),('C3',.5),('R',.5),('E3',.5),('R',.5),('E3',.5),('R',.5),
    ('Ab3',.5),('R',.5),('Ab3',.5),('R',.5),('E3',.5),('R',.5),('E3',.5),('R',.5),
    ('A3',.5),('R',.5),('A3',.5),('R',.5),('A3',.5),('R',.5),('A3',.5),('R',.5),
]

def _build_music():
    m = array.array('h')
    for note, d in MEL:
        m.extend(_pulse(NF.get(note, 0), d * BT, .25, .22, .3, .88))
    h = array.array('h')
    for note, d in HAR:
        h.extend(_pulse(NF.get(note, 0), d * BT, .125, .10, .6, .80))
    b = array.array('h')
    for note, d in BAS:
        b.extend(_wave(NF.get(note, 0), d * BT, .18, .75))
    return _snd(_mix(m, h, b))

def _build_sfx(name):
    if name == 'move':
        return _snd(_pulse(880, .025, .125, .10, cut=.9))
    elif name == 'rotate':
        s = array.array('h')
        s.extend(_pulse(600, .02, .25, .12, cut=.9))
        s.extend(_pulse(900, .025, .25, .10, cut=.9))
        return _snd(s)
    elif name == 'land':
        return _snd(_mix(_wave(100, .04, .15), _noise(.03, .06, 4)))
    elif name == 'clear':
        s = array.array('h')
        s.extend(_pulse(523, .06, .25, .18, cut=.85))
        s.extend(_pulse(659, .06, .25, .16, cut=.85))
        s.extend(_pulse(784, .08, .25, .18, cut=.9))
        return _snd(s)
    elif name == 'tetris':
        s = array.array('h')
        s.extend(_pulse(523, .05, .5, .20, cut=.85))
        s.extend(_pulse(659, .05, .5, .20, cut=.85))
        s.extend(_pulse(784, .05, .5, .20, cut=.85))
        s.extend(_pulse(1047, .12, .5, .22, cut=.95))
        return _snd(s)
    elif name == 'gameover':
        s = array.array('h')
        s.extend(_pulse(392, .18, .5, .20, decay=1.0, cut=.9))
        s.extend(_pulse(330, .18, .5, .18, decay=1.0, cut=.9))
        s.extend(_pulse(262, .35, .5, .20, decay=.8, cut=.95))
        return _snd(s)
    elif name == 'levelup':
        s = array.array('h')
        s.extend(_pulse(440, .07, .25, .18, cut=.85))
        s.extend(_pulse(554, .07, .25, .18, cut=.85))
        s.extend(_pulse(659, .07, .25, .18, cut=.85))
        s.extend(_pulse(880, .14, .25, .20, cut=.95))
        return _snd(s)
    elif name == 'menu':
        return _snd(_pulse(740, .03, .125, .08, cut=.85))
    elif name == 'sel':
        s = array.array('h')
        s.extend(_pulse(880, .03, .25, .12, cut=.85))
        s.extend(_pulse(1100, .05, .25, .12, cut=.9))
        return _snd(s)
    return None

# ====================== DRAWING ======================
def _font(sz):
    return pygame.font.SysFont('couriernew', sz, bold=True)

def dblk(srf, x, y, c, sz=BLK):
    # Authentic 8-bit block style: Solid fill with high-contrast border
    # White highlight (Top/Left), Black shadow (Bottom/Right)
    # Border width approx 1/8th of block size
    bw = max(2, sz // 8)
    
    # Main fill
    pygame.draw.rect(srf, c, (x, y, sz, sz))
    
    # Highlights (Top, Left)
    pygame.draw.rect(srf, C_WHITE, (x, y, sz, bw))       # Top
    pygame.draw.rect(srf, C_WHITE, (x, y, bw, sz))       # Left
    
    # Shadows (Bottom, Right)
    pygame.draw.rect(srf, C_BLACK, (x, y + sz - bw, sz, bw)) # Bottom
    pygame.draw.rect(srf, C_BLACK, (x + sz - bw, y, bw, sz)) # Right
    
    # Inner border line for extra detail (optional, keeps it crisp)
    pygame.draw.rect(srf, C_BLACK, (x, y, sz, sz), 1)

def dpnl(srf, x, y, w, h, title=""):
    pygame.draw.rect(srf, C_PBG, (x, y, w, h))
    pygame.draw.rect(srf, C_PBOR, (x, y, w, h), 2)
    if title:
        f = _font(10)
        t = f.render(title, True, C_YEL)
        srf.blit(t, (x + (w - t.get_width()) // 2, y + 6))

def dtc(srf, txt, f, c, y, cx=None):
    r = f.render(txt, True, c)
    srf.blit(r, ((cx or SW // 2) - r.get_width() // 2, y))

def dmini(srf, name, cx, cy, lv=0, bs=12):
    bl = ROT[name][0]
    col = pcol(name, lv)
    xs = [b[0] for b in bl]
    ys = [b[1] for b in bl]
    w = (max(xs) - min(xs) + 1) * bs
    h = (max(ys) - min(ys) + 1) * bs
    ox = cx - w // 2
    oy = cy - h // 2
    for bx, by in bl:
        dblk(srf, ox + (bx - min(xs)) * bs, oy + (by - min(ys)) * bs, col, bs)

# ====================== BG ANIM ======================
class BgBlk:
    def __init__(self):
        self.x = random.randint(0, SW)
        self.y = random.randint(-SH, SH)
        self.sz = random.randint(14, 22)
        self.sp = random.uniform(.3, .8)
        self.c = PALS[random.randint(0, 9)][random.randint(0, 1)]
        self.r = random.uniform(0, 6.28)

    def update(self):
        self.y += self.sp
        self.r += .003
        if self.y > SH + 40:
            self.y = random.randint(-60, -20)
            self.x = random.randint(0, SW)

    def draw(self, srf):
        s = pygame.Surface((self.sz, self.sz), pygame.SRCALPHA)
        s.fill((*self.c, 18))
        rt = pygame.transform.rotate(s, math.degrees(self.r))
        srf.blit(rt, (self.x - rt.get_width() // 2, self.y - rt.get_height() // 2))

# ====================== CLASSIC TETRIS ENGINE ======================
class Game:
    def __init__(self):
        self.board = [[None]*COLS for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 0
        self.slevel = 0
        self.high = 0
        self.running = False
        self.paused = False
        self.gameover = False
        self.go_anim = False
        self.go_row = ROWS - 1
        self.pname = ''
        self.pcol = 0
        self.prow = 0
        self.rot = 0
        self.nxt = ''
        self.stats = {n: 0 for n in PNAMES}
        self.das_ct = 0
        self.das_dir = 0
        self.das_charged = False
        self.grav_ct = 0
        self.sdrop = False
        self.are_ct = 0
        self.in_are = False
        self.clines = []
        self.cl_timer = 0
        self._last = ''

    def _rng(self):
        c = random.choice(PNAMES)
        if c == self._last:
            c = random.choice(PNAMES)
        self._last = c
        return c

    def start(self, sl=0):
        self.__init__()
        self.slevel = sl
        self.level = sl
        self.running = True
        self.nxt = self._rng()
        self._spawn()

    def _grav(self):
        # NES Famicom caps at level 29 with speed 1 (Kill Screen)
        if self.level >= 29:
            return 1
        return GRAV.get(self.level, 1)

    def _spawn(self):
        self.pname = self.nxt
        self.nxt = self._rng()
        self.rot = 0
        self.stats[self.pname] += 1
        bl = ROT[self.pname][0]
        xs = [b[0] for b in bl]
        self.pcol = (COLS - (max(xs) - min(xs) + 1)) // 2 - min(xs)
        self.prow = -1 if self.pname == 'I' else 0
        self.grav_ct = 0
        if not self._valid(self.pcol, self.prow, self.rot):
            self._die()

    def _blocks(self, c=None, r=None, ro=None):
        if c is None: c = self.pcol
        if r is None: r = self.prow
        if ro is None: ro = self.rot
        st = ROT[self.pname][ro % len(ROT[self.pname])]
        return [(c + bx, r + by) for bx, by in st]

    def _valid(self, c, r, ro):
        for x, y in self._blocks(c, r, ro):
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def _move(self, dx):
        if self._valid(self.pcol + dx, self.prow, self.rot):
            self.pcol += dx
            return True
        return False

    def _rotate(self):
        if self.pname == 'O':
            return False
        nr = (self.rot + 1) % len(ROT[self.pname])
        if self._valid(self.pcol, self.prow, nr):
            self.rot = nr
            return True
        return False

    def _lock(self):
        col = pcol(self.pname, self.level)
        for x, y in self._blocks():
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.board[y][x] = col

    def _check(self):
        full = [r for r in range(ROWS) if all(c is not None for c in self.board[r])]
        if full:
            self.clines = full
            self.cl_timer = 20
            return True
        return False

    def _doclear(self):
        n = len(self.clines)
        self.score += LSCORES.get(n, 0) * (self.level + 1)
        for r in sorted(self.clines, reverse=True):
            self.board.pop(r)
            self.board.insert(0, [None] * COLS)
        ol = self.level
        self.lines += n
        thr = min(self.slevel * 10 + 10, max(100, self.slevel * 10 - 50))
        if self.lines >= thr:
            self.level = self.slevel + (self.lines - thr) // 10 + 1
        else:
            self.level = self.slevel
        self.clines = []
        return self.level > ol

    def _die(self):
        self.running = False
        self.go_anim = True
        self.go_row = ROWS - 1
        if self.score > self.high:
            self.high = self.score

    def frame(self):
        """One frame of game logic at 60fps. Returns list of SFX event names."""
        if not self.running or self.paused:
            return []
        ev = []

        # game over curtain
        if self.go_anim:
            if self.go_row >= 0:
                for c in range(COLS):
                    self.board[self.go_row][c] = (50, 50, 68)
                self.go_row -= 1
            else:
                self.go_anim = False
                self.gameover = True
                ev.append('gameover')
            return ev

        # line clear flash
        if self.clines:
            self.cl_timer -= 1
            if self.cl_timer <= 0:
                if self._doclear():
                    ev.append('levelup')
                self.in_are = True
                self.are_ct = ARE_FR
            return ev

        # ARE
        if self.in_are:
            self.are_ct -= 1
            if self.are_ct <= 0:
                self.in_are = False
                self._spawn()
            return ev

        # DAS
        if self.das_dir != 0:
            self.das_ct += 1
            if self.das_ct == 1:
                if self._move(self.das_dir):
                    ev.append('move')
            elif self.das_ct >= DAS_INIT:
                self.das_charged = True
                if (self.das_ct - DAS_INIT) % DAS_REP == 0:
                    if self._move(self.das_dir):
                        ev.append('move')

        # gravity
        spd = 2 if self.sdrop else self._grav()
        self.grav_ct += 1
        if self.grav_ct >= spd:
            self.grav_ct = 0
            if self._valid(self.pcol, self.prow + 1, self.rot):
                self.prow += 1
                if self.sdrop:
                    self.score += 1
            else:
                # INSTANT LOCK
                self._lock()
                ev.append('land')
                if self._check():
                    ev.append('tetris' if len(self.clines) == 4 else 'clear')
                else:
                    self.in_are = True
                    self.are_ct = ARE_FR
        return ev

# ====================== TEXT DATA ======================
T_HOWTO = [
    "", "CONTROLS:", "",
    "LEFT / RIGHT .... Move",
    "DOWN ............ Soft Drop",
    "UP / X .......... Rotate CW",
    "P / ESC ......... Pause", "",
    "RULES:", "",
    "Clear lines to score.",
    "4 lines at once = TETRIS!",
    "Speed increases with level.", "",
    "No hold. No ghost. Classic.",
]
T_ABOUT = [
    "", "AC's Ultra!TETRIS", "Version 1.0", "",
    "1:1 recreation of 1990s Tetris.", "",
    "Nintendo Rotation System.",
    "NES scoring. GB speed curve.",
    "Instant lock. No wall kicks.", "",
    "Game Boy Korobeiniki chiptune.",
]
T_CREDITS = [
    "", "GAME DESIGN & CODE",
    "AC Entertainment / Team Flames", "",
    "MUSIC",
    "Korobeiniki (Traditional Folk)",
    "GB Chiptune Arrangement", "",
    "ORIGINAL CONCEPT",
    "Alexey Pajitnov (1984)", "",
    "SPECIAL THANKS",
    "All classic Tetris players",
]
T_HELP = [
    "", "NES SCORING:", "",
    "1 Line:   40 x (Level+1)",
    "2 Lines: 100 x (Level+1)",
    "3 Lines: 300 x (Level+1)",
    "TETRIS: 1200 x (Level+1)", "",
    "Soft Drop: 1pt per cell", "",
    "LEVELING:",
    "Start at chosen level.",
    "Advances every 10 lines.", "",
    "SPEED:",
    "Level 0=slow  Level 9=fast",
    "Level 29+ = kill screen",
]

# ====================== APP ======================
class App:
    def __init__(self):
        pygame.init()
        self.aok = False
        try:
            pygame.mixer.init(frequency=SR, size=-16, channels=1, buffer=2048)
            self.aok = True
        except Exception:
            print("No audio device. Running silent.")

        self.scr = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("AC's Ultra!TETRIS")
        self.clk = pygame.time.Clock()

        # fonts
        self.ft  = _font(34)
        self.fm  = _font(15)
        self.fs  = _font(12)
        self.fti = _font(10)
        self.fh  = _font(16)
        self.fb  = _font(26)
        self.fst = _font(9)

        # audio
        self.mus = None
        self.sfx = {}
        if self.aok:
            print("Building audio...")
            self.mus = _build_music()
            for n in ['move','rotate','land','clear','tetris',
                      'gameover','levelup','menu','sel']:
                self.sfx[n] = _build_sfx(n)
            print("Audio ready!")

        self.mvol = 0.7
        self.svol = 0.8
        self.men = True
        self.mch = None
        self.sch = None
        if self.aok:
            self.mch = pygame.mixer.Channel(0)
            self.sch = pygame.mixer.Channel(1)
        self.mplay = False
        self.mev = pygame.USEREVENT + 1
        if self.mch:
            self.mch.set_endevent(self.mev)

        # state
        self.state = 'menu'
        self.mi = 0
        self.lsel = 0
        self.si = 0
        self.g = Game()
        self.bg = [BgBlk() for _ in range(22)]

        # scanlines
        self.scan = pygame.Surface((SW, SH), pygame.SRCALPHA)
        for y in range(0, SH, 4):
            pygame.draw.line(self.scan, (0, 0, 0, 15), (0, y+2), (SW, y+2))

    # --- audio helpers ---
    def _psfx(self, n):
        if not self.aok or not self.sch:
            return
        if n in self.sfx and self.svol > 0:
            self.sfx[n].set_volume(self.svol)
            self.sch.play(self.sfx[n])

    def _mstart(self):
        if not self.aok or not self.mch or not self.mus:
            return
        if self.men and not self.mplay:
            self.mus.set_volume(self.mvol)
            self.mch.play(self.mus)
            self.mplay = True

    def _mstop(self):
        if self.mch:
            self.mch.stop()
        self.mplay = False

    # --- main loop ---
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == self.mev and self.men and self.mplay:
                    self.mus.set_volume(self.mvol)
                    self.mch.play(self.mus)
                self._evt(e)
            self._upd()
            self._drw()
            pygame.display.flip()
            self.clk.tick(FPS)

    # --- input ---
    def _evt(self, e):
        g = self.g

        # key release (DAS)
        if e.type == pygame.KEYUP and self.state == 'game':
            if e.key == pygame.K_LEFT and g.das_dir == -1:
                g.das_dir = 0; g.das_ct = 0; g.das_charged = False
            elif e.key == pygame.K_RIGHT and g.das_dir == 1:
                g.das_dir = 0; g.das_ct = 0; g.das_charged = False
            elif e.key == pygame.K_DOWN:
                g.sdrop = False
            return

        if e.type != pygame.KEYDOWN:
            return
        k = e.key

        # MENU
        if self.state == 'menu':
            items = ['play','howto','sound','about','credits','help']
            if k == pygame.K_UP:
                self.mi = (self.mi - 1) % 6; self._psfx('menu')
            elif k == pygame.K_DOWN:
                self.mi = (self.mi + 1) % 6; self._psfx('menu')
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                self._psfx('sel')
                a = items[self.mi]
                if a == 'play':
                    self.state = 'lvl'
                    self.lsel = 0
                else:
                    self.state = a
            return

        # LEVEL SELECT
        if self.state == 'lvl':
            if k == pygame.K_LEFT:
                self.lsel = max(0, self.lsel - 1); self._psfx('menu')
            elif k == pygame.K_RIGHT:
                self.lsel = min(9, self.lsel + 1); self._psfx('menu')
            elif k == pygame.K_UP:
                self.lsel = max(0, self.lsel - 5); self._psfx('menu')
            elif k == pygame.K_DOWN:
                self.lsel = min(9, self.lsel + 5); self._psfx('menu')
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                self._psfx('sel')
                self.state = 'game'
                g.start(self.lsel)
                self._mstart()
            elif k == pygame.K_ESCAPE:
                self.state = 'menu'; self._psfx('menu')
            return

        # SUB SCREENS
        if self.state in ('howto', 'about', 'credits', 'help'):
            if k in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.state = 'menu'; self._psfx('menu')
            return

        # SOUND SETTINGS
        if self.state == 'sound':
            if k == pygame.K_ESCAPE:
                self.state = 'menu'; self._psfx('menu')
            elif k == pygame.K_UP:
                self.si = (self.si - 1) % 3; self._psfx('menu')
            elif k == pygame.K_DOWN:
                self.si = (self.si + 1) % 3; self._psfx('menu')
            elif k == pygame.K_LEFT:
                if self.si == 0:
                    self.mvol = max(0, round(self.mvol - .1, 1))
                    if self.mus: self.mus.set_volume(self.mvol)
                elif self.si == 1:
                    self.svol = max(0, round(self.svol - .1, 1))
                    self._psfx('menu')
            elif k == pygame.K_RIGHT:
                if self.si == 0:
                    self.mvol = min(1, round(self.mvol + .1, 1))
                    if self.mus: self.mus.set_volume(self.mvol)
                elif self.si == 1:
                    self.svol = min(1, round(self.svol + .1, 1))
                    self._psfx('menu')
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.si == 2:
                    self.men = not self.men
                    if not self.men:
                        self._mstop()
                    self._psfx('sel')
            return

        # GAME
        if self.state == 'game':
            # game over
            if g.gameover and not g.go_anim:
                if k == pygame.K_RETURN:
                    self.state = 'menu'; self._psfx('menu')
                return
            # pause
            if k in (pygame.K_p, pygame.K_ESCAPE):
                if g.running:
                    g.paused = not g.paused
                    if g.paused:
                        self._mstop()
                    elif self.men:
                        self._mstart()
                return
            if g.paused or not g.running or g.in_are or g.clines:
                return
            # movement
            if k == pygame.K_LEFT:
                g.das_dir = -1; g.das_ct = 0; g.das_charged = False
            elif k == pygame.K_RIGHT:
                g.das_dir = 1; g.das_ct = 0; g.das_charged = False
            elif k == pygame.K_DOWN:
                g.sdrop = True
            elif k in (pygame.K_UP, pygame.K_x): # Fixed pygame-ce missing K_X
                if g._rotate():
                    self._psfx('rotate')

    # --- update ---
    def _upd(self):
        for b in self.bg:
            b.update()
        if self.state != 'game':
            return
        evs = self.g.frame()
        for ev in evs:
            self._psfx(ev)
            if ev == 'gameover':
                self._mstop()

    # --- drawing ---
    def _drw(self):
        self.scr.fill(C_BG)

        if self.state != 'game' or self.g.paused:
            for b in self.bg:
                b.draw(self.scr)

        if self.state == 'menu':       self._drw_menu()
        elif self.state == 'lvl':      self._drw_lvl()
        elif self.state == 'howto':    self._drw_txt("HOW TO PLAY", T_HOWTO)
        elif self.state == 'about':    self._drw_txt("ABOUT", T_ABOUT)
        elif self.state == 'credits':  self._drw_txt("CREDITS", T_CREDITS)
        elif self.state == 'help':     self._drw_txt("HELP", T_HELP)
        elif self.state == 'sound':    self._drw_snd()
        elif self.state == 'game':     self._drw_game()

        self.scr.blit(self.scan, (0, 0))

    def _drw_menu(self):
        sh = self.ft.render("AC's Ultra!TETRIS", True, C_DRED)
        self.scr.blit(sh, (SW//2 - sh.get_width()//2 + 3, 103))
        dtc(self.scr, "AC's Ultra!TETRIS", self.ft, C_RED, 100)
        dtc(self.scr, "AC Entertainment [C] 1999-2026 Tetris Co. 1984", self.fti, C_YEL, 148)

        labs = ['PLAY GAME','HOW TO PLAY','SOUND SETTINGS','ABOUT','CREDITS','HELP']
        y = 220
        for i, l in enumerate(labs):
            sel = i == self.mi
            c = C_WHITE if sel else C_GRAY
            t = self.fm.render(l, True, c)
            tx = SW // 2 - t.get_width() // 2
            self.scr.blit(t, (tx, y))
            if sel and pygame.time.get_ticks() % 500 < 300:
                a = self.fm.render(">", True, C_RED)
                self.scr.blit(a, (tx - 28, y))
            y += 34

        dtc(self.scr, "UP/DOWN: SELECT   ENTER: CONFIRM", self.fti, C_DGRAY, 555)

    def _drw_lvl(self):
        dtc(self.scr, "SELECT LEVEL", self.fb, C_RED, 100)
        dtc(self.scr, "Choose starting level", self.fs, C_GRAY, 142)
        gx = SW // 2 - 160
        gy = 220
        for i in range(10):
            ro = i // 5
            co = i % 5
            x = gx + co * 70
            y = gy + ro * 80
            sel = i == self.lsel
            pal = PALS[i]
            bc = C_WHITE if sel else C_DGRAY
            pygame.draw.rect(self.scr, C_PBG, (x, y, 56, 56))
            pygame.draw.rect(self.scr, bc, (x, y, 56, 56), 3 if sel else 1)
            nc = C_WHITE if sel else C_GRAY
            n = self.fh.render(str(i), True, nc)
            self.scr.blit(n, (x + 28 - n.get_width()//2, y + 6))
            dblk(self.scr, x + 8, y + 32, pal[0], 16)
            dblk(self.scr, x + 32, y + 32, pal[1], 16)
            if sel and pygame.time.get_ticks() % 500 < 300:
                pygame.draw.rect(self.scr, C_YEL, (x-2, y-2, 60, 60), 2)
        dtc(self.scr, "ARROWS: SELECT  ENTER: START  ESC: BACK", self.fti, C_DGRAY, 440)

    def _drw_txt(self, title, lines):
        dtc(self.scr, title, self.fb, C_RED, 60)
        y = 120
        for l in lines:
            if not l:
                y += 10
                continue
            hdr = l.isupper() and len(l) < 28
            dtc(self.scr, l, self.fti, C_YEL if hdr else C_GRAY, y)
            y += 22
        dtc(self.scr, "PRESS ESC OR ENTER TO GO BACK", self.fti, C_DGRAY, 540)

    def _drw_snd(self):
        dtc(self.scr, "SOUND SETTINGS", self.fb, C_RED, 80)
        items = [
            ("MUSIC VOLUME", f"{int(self.mvol*100)}%", self.mvol),
            ("SFX VOLUME", f"{int(self.svol*100)}%", self.svol),
            ("MUSIC", "ON" if self.men else "OFF", None),
        ]
        y = 200
        for i, (lab, vt, bv) in enumerate(items):
            sel = i == self.si
            c = C_WHITE if sel else C_GRAY
            if sel and pygame.time.get_ticks() % 500 < 300:
                a = self.fs.render(">", True, C_RED)
                self.scr.blit(a, (150, y + 2))
            ls = self.fs.render(lab, True, c)
            self.scr.blit(ls, (180, y))
            if bv is not None:
                bx, by, bw, bh = 430, y + 2, 180, 16
                pygame.draw.rect(self.scr, (25, 25, 50), (bx, by, bw, bh))
                pygame.draw.rect(self.scr, C_PBOR, (bx, by, bw, bh), 2)
                fw = int(bv * (bw - 4))
                if fw > 0:
                    pygame.draw.rect(self.scr, C_RED, (bx+2, by+2, fw, bh-4))
                vs = self.fti.render(vt, True, C_YEL)
                self.scr.blit(vs, (bx + bw + 12, y + 2))
            else:
                tc = (0, 255, 0) if self.men else C_RED
                vs = self.fs.render(vt, True, tc)
                self.scr.blit(vs, (430, y))
            y += 50
        dtc(self.scr, "LEFT/RIGHT: ADJUST   ENTER: TOGGLE", self.fti, C_DGRAY, 440)
        dtc(self.scr, "PRESS ESC TO GO BACK", self.fti, C_DGRAY, 470)

    def _drw_game(self):
        g = self.g

        # board bg
        pygame.draw.rect(self.scr, (5, 5, 15),
                         (BRD_X - 2, BRD_Y - 2, COLS*BLK + 4, ROWS*BLK + 4))
        pygame.draw.rect(self.scr, C_PBOR,
                         (BRD_X - 3, BRD_Y - 3, COLS*BLK + 6, ROWS*BLK + 6), 2)

        # grid
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(self.scr, C_GRID,
                                 (BRD_X + c*BLK, BRD_Y + r*BLK, BLK, BLK), 1)

        # board cells
        for r in range(ROWS):
            for c in range(COLS):
                if g.board[r][c]:
                    x = BRD_X + c * BLK
                    y = BRD_Y + r * BLK
                    if r in g.clines:
                        # flash white/normal
                        if (pygame.time.get_ticks() // 80) % 2 == 0:
                            pygame.draw.rect(self.scr, C_WHITE, (x, y, BLK, BLK))
                        else:
                            dblk(self.scr, x, y, g.board[r][c])
                    else:
                        dblk(self.scr, x, y, g.board[r][c])

        # active piece (no ghost — authentic!)
        if g.running and not g.paused and not g.in_are and not g.clines:
            col = pcol(g.pname, g.level)
            for bx, by in g._blocks():
                if 0 <= by < ROWS:
                    dblk(self.scr, BRD_X + bx*BLK, BRD_Y + by*BLK, col)

        # === LEFT PANEL ===
        lx = BRD_X - 155

        # STATISTICS
        dpnl(self.scr, lx, BRD_Y, 140, 310, "STATISTICS")
        sy = BRD_Y + 28
        for i, name in enumerate(PNAMES):
            # mini piece
            dmini(self.scr, name, lx + 45, sy + i * 40, g.level, 10)
            # count
            ct = self.fst.render(f"{g.stats[name]:03d}", True, C_WHITE)
            self.scr.blit(ct, (lx + 85, sy + i * 40 - 5))

        # LINES
        dpnl(self.scr, lx, BRD_Y + 325, 140, 50, "LINES")
        lt = self.fh.render(f"{g.lines:03d}", True, C_WHITE)
        self.scr.blit(lt, (lx + 70 - lt.get_width()//2, BRD_Y + 350))

        # === RIGHT PANEL ===
        rx = BRD_X + COLS * BLK + 15

        # NEXT
        dpnl(self.scr, rx, BRD_Y, 140, 80, "NEXT")
        if g.nxt:
            dmini(self.scr, g.nxt, rx + 70, BRD_Y + 50, g.level, 14)

        # SCORE
        dpnl(self.scr, rx, BRD_Y + 95, 140, 60, "SCORE")
        st = self.fh.render(f"{g.score:07d}", True, C_WHITE)
        self.scr.blit(st, (rx + 70 - st.get_width()//2, BRD_Y + 122))

        # LEVEL
        dpnl(self.scr, rx, BRD_Y + 170, 140, 55, "LEVEL")
        vt = self.fh.render(f"{g.level:02d}", True, C_WHITE)
        self.scr.blit(vt, (rx + 70 - vt.get_width()//2, BRD_Y + 196))

        # HIGH SCORE
        dpnl(self.scr, rx, BRD_Y + 240, 140, 55, "HIGH")
        ht = self.fs.render(f"{g.high:07d}", True, C_WHITE)
        self.scr.blit(ht, (rx + 70 - ht.get_width()//2, BRD_Y + 266))

        # SPEED indicator
        dpnl(self.scr, rx, BRD_Y + 310, 140, 55, "SPEED")
        gf = g._grav()
        bar_w = max(4, int(130 * (1.0 - gf / 48.0)))
        pygame.draw.rect(self.scr, (25, 25, 50), (rx + 5, BRD_Y + 336, 130, 12))
        bar_col = C_RED if gf <= 3 else C_YEL if gf <= 8 else (0, 200, 0)
        pygame.draw.rect(self.scr, bar_col, (rx + 5, BRD_Y + 336, bar_w, 12))

        # === PAUSE OVERLAY ===
        if g.paused:
            ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 180))
            self.scr.blit(ov, (0, 0))
            dtc(self.scr, "PAUSED", self.ft, C_RED, 240)
            dtc(self.scr, "PRESS P OR ESC TO RESUME", self.fti, C_GRAY, 290)

        # === GAME OVER OVERLAY ===
        if g.gameover and not g.go_anim:
            ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 200))
            self.scr.blit(ov, (0, 0))
            dtc(self.scr, "GAME OVER", self.ft, C_RED, 180)
            dtc(self.scr, f"SCORE: {g.score}", self.fs, C_GRAY, 240)
            dtc(self.scr, f"LEVEL: {g.level}", self.fs, C_GRAY, 268)
            dtc(self.scr, f"LINES: {g.lines}", self.fs, C_GRAY, 296)
            if g.score >= g.high and g.score > 0:
                dtc(self.scr, "NEW HIGH SCORE!", self.fs, C_YEL, 336)
            dtc(self.scr, "PRESS ENTER TO CONTINUE", self.fti, C_DGRAY, 400)


# ====================== ENTRY ======================
if __name__ == '__main__':
    App().run()
