import pygame
import math
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500  # Field of View / Focal Length
VIEW_DISTANCE = 4000
ROTATION_SPEED = 0.05
MOVE_SPEED = 10
JUMP_FORCE = 15
GRAVITY = 0.8

# --- COLORS (SM64 Palette approximations) ---
SKY_BLUE = (100, 149, 237)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)         # Mario Hat / Shirt
BLUE = (0, 0, 205)          # Mario Overalls
SKIN = (255, 204, 153)      # Mario Skin
BROWN = (139, 69, 19)       # Shoes / Wood
MUSTACHE_BLACK = (20, 20, 20)
BUTTON_GOLD = (255, 215, 0)
EYE_BLUE = (0, 128, 255)    # Added for eyes
YELLOW = (255, 255, 0)      # For star and emblem

# Level Colors
GRASS_GREEN = (34, 139, 34)
BRICK_RED = (165, 42, 42)
WATER_BLUE = (64, 224, 208)
STONE_GREY = (169, 169, 169)
TREE_GREEN = (0, 100, 0)

# --- 3D ENGINE CLASSES ---

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def rotate_y(self, center, angle):
        cx, cz = center.x, center.z
        dx = self.x - cx
        dz = self.z - cz
        
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        rx = dx * cos_a - dz * sin_a
        rz = dx * sin_a + dz * cos_a
        
        return Vector3(rx + cx, self.y, rz + cz)

    def add(self, v):
        return Vector3(self.x + v.x, self.y + v.y, self.z + v.z)

class Face:
    def __init__(self, indices, color):
        self.indices = indices
        self.color = color
        self.avg_z = 0

class Mesh:
    def __init__(self, x, y, z, color=WHITE):
        self.x = x
        self.y = y
        self.z = z
        self.vertices = []
        self.faces = []
        self.color = color
        self.yaw = 0

    def add_cube(self, w, h, d, offset_x, offset_y, offset_z, color):
        start_idx = len(self.vertices)
        hw, hh, hd = w/2, h/2, d/2
        
        corners = [
            Vector3(-hw, -hh, -hd), Vector3(hw, -hh, -hd),
            Vector3(hw, hh, -hd), Vector3(-hw, hh, -hd),
            Vector3(-hw, -hh, hd), Vector3(hw, -hh, hd),
            Vector3(hw, hh, hd), Vector3(-hw, hh, hd)
        ]
        
        for c in corners:
            self.vertices.append(Vector3(c.x + offset_x, c.y + offset_y, c.z + offset_z))
            
        cube_faces = [
            ([0, 1, 2, 3], color), ([5, 4, 7, 6], color),
            ([4, 0, 3, 7], color), ([1, 5, 6, 2], color),
            ([3, 2, 6, 7], color), ([4, 5, 1, 0], color)
        ]
        
        for f_indices, f_color in cube_faces:
            shifted_indices = [i + start_idx for i in f_indices]
            self.faces.append(Face(shifted_indices, f_color))

# --- GAME OBJECTS ---

class Mario(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.dy = 0
        self.is_jumping = False
        self.facing_angle = 0
        self.build_model()
        
    def build_model(self):
        # --- High-Fidelity Voxel Mario (Enhanced for SM64 Accuracy) ---
        
        # 1. FEET
        self.add_cube(10, 8, 14, -6, -25, -2, BROWN) # L Shoe
        self.add_cube(10, 8, 14, 6, -25, -2, BROWN)  # R Shoe
        
        # 2. LEGS
        self.add_cube(8, 12, 8, -6, -15, 0, BLUE)    # L Leg
        self.add_cube(8, 12, 8, 6, -15, 0, BLUE)     # R Leg
        
        # 3. BODY
        self.add_cube(20, 10, 14, 0, -4, 0, BLUE)    # Pelvis/Overalls
        self.add_cube(22, 14, 14, 0, 8, 0, RED)      # Chest/Shirt
        
        # Buttons
        self.add_cube(2, 2, 1, -5, 4, -8, BUTTON_GOLD) # L Button
        self.add_cube(2, 2, 1, 5, 4, -8, BUTTON_GOLD)  # R Button

        # 4. ARMS
        self.add_cube(8, 8, 8, -16, 12, 0, RED)      # L Shoulder
        self.add_cube(6, 12, 6, -16, 2, 0, RED)      # L Arm
        self.add_cube(7, 7, 7, -16, -8, 0, WHITE)    # L Hand (Glove)

        self.add_cube(8, 8, 8, 16, 12, 0, RED)       # R Shoulder
        self.add_cube(6, 12, 6, 16, 2, 0, RED)       # R Arm
        self.add_cube(7, 7, 7, 16, -8, 0, WHITE)     # R Hand (Glove)

        # 5. HEAD
        self.add_cube(18, 16, 18, 0, 22, 0, SKIN)    # Face
        self.add_cube(20, 6, 20, 0, 32, 0, RED)      # Hat Dome
        self.add_cube(24, 2, 24, 0, 29, -4, RED)     # Hat Brim

        # 6. FACE FEATURES
        self.add_cube(4, 4, 4, 0, 22, -10, SKIN)     # Nose
        self.add_cube(8, 3, 2, 0, 18, -10, MUSTACHE_BLACK) # Mustache
        self.add_cube(4, 8, 4, -9, 22, -2, BROWN)    # L Sideburn
        self.add_cube(4, 8, 4, 9, 22, -2, BROWN)     # R Sideburn
        self.add_cube(18, 10, 6, 0, 22, 8, BROWN)    # Back Hair

        # Added: Eyes (White with Blue pupils)
        self.add_cube(4, 4, 1, -6, 22, -9, WHITE)    # L Eye
        self.add_cube(2, 2, 1, -5, 21, -10, EYE_BLUE)
        self.add_cube(4, 4, 1, 6, 22, -9, WHITE)     # R Eye
        self.add_cube(2, 2, 1, 5, 21, -10, EYE_BLUE)

        # Added: Eyebrows
        self.add_cube(6, 2, 1, -7, 26, -9, BROWN)    # L Eyebrow
        self.add_cube(6, 2, 1, 7, 26, -9, BROWN)     # R Eyebrow

        # Added: M Emblem on Hat
        self.add_cube(2, 4, 1, -2, 30, -10, WHITE)   # M Left
        self.add_cube(2, 2, 1, 0, 30, -10, WHITE)    # M Middle Top
        self.add_cube(2, 4, 1, 2, 30, -10, WHITE)    # M Right
        self.add_cube(2, 2, 1, 0, 28, -10, WHITE)    # M Middle Bottom

    def update(self):
        # Gravity (positive Y up)
        self.dy -= GRAVITY
        self.y += self.dy
        
        # Floor collision
        if self.y < 0: 
            self.y = 0
            self.dy = 0
            self.is_jumping = False

class Level(Mesh):
    def __init__(self):
        super().__init__(0, 0, 0)
        self.build_courtyard()

    def build_courtyard(self):
        # 1. Main Courtyard Floor (Grass)
        floor_size = 2000
        self.add_cube(floor_size, 10, floor_size, 0, -5, 0, GRASS_GREEN)  # Top at y=0
        
        # 2. Brick Walls (Enclosing the courtyard, symmetric)
        wall_h = 300
        wall_thick = 50
        wall_dist = 1000
        
        self.add_cube(floor_size, wall_h, wall_thick, 0, 150, wall_dist, BRICK_RED) # Front Wall
        self.add_cube(floor_size, wall_h, wall_thick, 0, 150, -wall_dist, BRICK_RED) # Back Wall
        self.add_cube(wall_thick, wall_h, floor_size, wall_dist, 150, 0, BRICK_RED) # Right Wall
        self.add_cube(wall_thick, wall_h, floor_size, -wall_dist, 150, 0, BRICK_RED) # Left Wall
        
        # 3. Central Fountain (with Star Statue)
        self.add_cube(300, 40, 300, 0, -20, 0, STONE_GREY)  # Base
        self.add_cube(250, 10, 250, 0, -5, 0, WATER_BLUE)  # Water
        self.add_cube(50, 150, 50, 0, 40, 0, STONE_GREY)    # Center Spire
        self.add_cube(120, 20, 120, 0, 100, 0, STONE_GREY)  # Top Basin
        # Added: Star Statue
        self.add_cube(40, 40, 10, 0, 120, 0, YELLOW)        # Star Base
        self.add_cube(20, 20, 10, -30, 120, 0, YELLOW)      # Star Point Left
        self.add_cube(20, 20, 10, 30, 120, 0, YELLOW)       # Star Point Right
        self.add_cube(20, 20, 10, 0, 150, 0, YELLOW)        # Star Point Top
        self.add_cube(20, 20, 10, -15, 90, 0, YELLOW)       # Star Point Bottom Left
        self.add_cube(20, 20, 10, 15, 90, 0, YELLOW)        # Star Point Bottom Right

        # 4. Trees (More for symmetry, 8 total)
        positions = [(-500, -500), (500, -500), (-500, 500), (500, 500),
                     (-700, -200), (700, -200), (-700, 200), (700, 200)]
        for tx, tz in positions:
            self.add_cube(40, 150, 40, tx, 35, tz, BROWN) # Trunk
            self.add_cube(150, 150, 150, tx, 150, tz, TREE_GREEN) # Leaves
            
        # 5. Boos (Added more for SM64 feel)
        boo_positions = [(-300, 300), (300, 300), (-300, -300), (300, -300), (0, 400)]
        for bx, bz in boo_positions:
            self.add_cube(60, 60, 60, bx, 200, bz, WHITE) # Body
            self.add_cube(60, 20, 20, bx, 210, bz-10, WHITE) # Arms

        # 6. Added: 4 Signposts (Symmetric placement)
        sign_positions = [(-800, 800), (800, 800), (-800, -800), (800, -800)]
        for sx, sz in sign_positions:
            self.add_cube(10, 100, 10, sx, 50, sz, BROWN)   # Post
            self.add_cube(60, 40, 5, sx, 90, sz, STONE_GREY) # Sign Board

# --- MAIN ENGINE ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ULTRA MARIO 3D BROS > COURTYARD EDITION")
    clock = pygame.time.Clock()
    
    # Instantiate Objects
    mario = Mario(0, 0, 0)
    level = Level()
    
    # Camera
    cam_x, cam_y, cam_z = 0, 200, 600
    cam_yaw = 0
    
    running = True
    while running:
        dt = clock.tick(FPS)
        screen.fill(SKY_BLUE)
        
        # --- INPUT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not mario.is_jumping:
                    mario.dy = JUMP_FORCE
                    mario.is_jumping = True

        keys = pygame.key.get_pressed()
        
        # Camera Rotation (Left/Right)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            cam_yaw -= ROTATION_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            cam_yaw += ROTATION_SPEED
            
        # Movement relative to Camera
        move_x = 0
        move_z = 0
        moved = False
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_z -= MOVE_SPEED
            moved = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_z += MOVE_SPEED
            moved = True
            
        if moved:
            mx = move_x * math.cos(cam_yaw) - move_z * math.sin(cam_yaw)
            mz = move_x * math.sin(cam_yaw) + move_z * math.cos(cam_yaw)
            mario.x += mx
            mario.z += mz
            
            mario.facing_angle = -math.atan2(mz, mx) - math.pi/2

        mario.update()
        
        # Camera Follow Logic
        target_cam_x = mario.x + math.sin(cam_yaw) * 400
        target_cam_z = mario.z + math.cos(cam_yaw) * 400
        cam_x += (target_cam_x - cam_x) * 0.1
        cam_z += (target_cam_z - cam_z) * 0.1
        
        # --- RENDERER ---
        
        render_list = []
        
        def process_mesh(mesh, world_x, world_y, world_z, rotation=0):
            m_cos = math.cos(rotation)
            m_sin = math.sin(rotation)
            
            c_cos = math.cos(-cam_yaw)
            c_sin = math.sin(-cam_yaw)
            
            for face in mesh.faces:
                transformed_verts = []
                avg_z = 0
                valid_verts = 0
                
                for v_idx in face.indices:
                    v = mesh.vertices[v_idx]
                    
                    rx = v.x * m_cos - v.z * m_sin
                    rz = v.x * m_sin + v.z * m_cos
                    ry = v.y
                    
                    wx = rx + world_x
                    wy = ry + world_y
                    wz = rz + world_z
                    
                    cx = wx - cam_x
                    cy = wy - cam_y
                    cz = wz - cam_z
                    
                    xx = cx * c_cos - cz * c_sin
                    zz = cx * c_sin + cz * c_cos
                    yy = cy
                    
                    if zz < 10:
                        continue
                        
                    valid_verts += 1
                    scale = FOV / zz
                    sx = int(xx * scale + WIDTH / 2)
                    sy = int(-yy * scale + HEIGHT / 2)  # Inverted for positive Y up
                    
                    transformed_verts.append((sx, sy))
                    avg_z += zz
                
                if valid_verts == len(face.indices):
                    face.avg_z = avg_z / valid_verts
                    shade_factor = max(0.2, min(1.0, 1.0 - (face.avg_z / VIEW_DISTANCE)))
                    r = int(face.color[0] * shade_factor)
                    g = int(face.color[1] * shade_factor)
                    b = int(face.color[2] * shade_factor)
                    
                    render_list.append({
                        'poly': transformed_verts,
                        'depth': face.avg_z,
                        'color': (r, g, b)
                    })

        process_mesh(level, level.x, level.y, level.z)
        process_mesh(mario, mario.x, mario.y, mario.z, mario.facing_angle)
        
        render_list.sort(key=lambda x: x['depth'], reverse=True)
        
        for item in render_list:
            pygame.draw.polygon(screen, item['color'], item['poly'])
            pygame.draw.polygon(screen, BLACK, item['poly'], 1)

        # --- HUD ---
        font = pygame.font.SysFont('Arial', 24, bold=True)
        text = font.render(f"ULTRA MARIO 3D - STARS: 0", True, (255, 215, 0))
        screen.blit(text, (20, 20))
        
        controls = font.render(f"ARROWS/WASD to Move | SPACE to Jump", True, WHITE)
        screen.blit(controls, (20, HEIGHT - 40))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
