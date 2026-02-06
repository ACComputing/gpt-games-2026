import pygame
import math
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500
VIEW_DISTANCE = 5000
ROTATION_SPEED = 0.05
MOVE_SPEED = 12
JUMP_FORCE = 18
GRAVITY = 0.9

# --- COLORS (N64DD / Spaceworld Palette) ---
DD_SKY = (20, 20, 60)       # Deep twilight blue
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
METAL_GREY = (160, 170, 180) # For DD branding
CHECKER_LIGHT = (50, 200, 50)
CHECKER_DARK = (30, 140, 30)

# --- 3D ENGINE MATH ---

class Vector3:
    __slots__ = ['x', 'y', 'z']  # Optimization: Reduce memory footprint
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Face:
    __slots__ = ['indices', 'color', 'avg_z', 'normal']
    def __init__(self, indices, color):
        self.indices = indices
        self.color = color
        self.avg_z = 0
        self.normal = None # Calculated during build

class Mesh:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vertices = []
        self.faces = []
        self.yaw = 0

    def add_cube(self, w, h, d, offset_x, offset_y, offset_z, color):
        start_idx = len(self.vertices)
        hw, hh, hd = w/2, h/2, d/2
        
        # Define vertices
        corners = [
            (-hw, -hh, -hd), (hw, -hh, -hd), (hw, hh, -hd), (-hw, hh, -hd), # Back
            (-hw, -hh, hd), (hw, -hh, hd), (hw, hh, hd), (-hw, hh, hd)      # Front
        ]
        
        for cx, cy, cz in corners:
            self.vertices.append(Vector3(cx + offset_x, cy + offset_y, cz + offset_z))
            
        # Define faces with winding order (Counter-Clockwise usually, but we check normals)
        # Indices: 0-3 back, 4-7 front
        cube_faces = [
            ([0, 1, 2, 3], color), # Back
            ([5, 4, 7, 6], color), # Front
            ([4, 0, 3, 7], color), # Left
            ([1, 5, 6, 2], color), # Right
            ([3, 2, 6, 7], color), # Top
            ([4, 5, 1, 0], color)  # Bottom
        ]
        
        for f_indices, f_color in cube_faces:
            shifted_indices = [i + start_idx for i in f_indices]
            face = Face(shifted_indices, f_color)
            
            # Pre-calculate normal for backface culling
            # Using first 3 vertices of the face to calculate normal
            v0 = self.vertices[shifted_indices[0]]
            v1 = self.vertices[shifted_indices[1]]
            v2 = self.vertices[shifted_indices[2]]
            
            # Vector A (v1 - v0)
            ax, ay, az = v1.x - v0.x, v1.y - v0.y, v1.z - v0.z
            # Vector B (v2 - v0)
            bx, by, bz = v2.x - v0.x, v2.y - v0.y, v2.z - v0.z
            
            # Cross Product (AxB)
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            
            # Normalize
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length != 0:
                face.normal = (nx/length, ny/length, nz/length)
            else:
                face.normal = (0, 0, 1)

            self.faces.append(face)

# --- GAME OBJECTS ---

class Mario(Mesh):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.dy = 0
        self.is_jumping = False
        self.build_model()
        
    def build_model(self):
        # 1. FEET
        self.add_cube(10, 8, 14, -6, -25, -2, BROWN)
        self.add_cube(10, 8, 14, 6, -25, -2, BROWN)
        
        # 2. LEGS
        self.add_cube(8, 12, 8, -6, -15, 0, BLUE)
        self.add_cube(8, 12, 8, 6, -15, 0, BLUE)
        
        # 3. BODY
        self.add_cube(20, 10, 14, 0, -4, 0, BLUE)
        self.add_cube(22, 14, 14, 0, 8, 0, RED)
        
        self.add_cube(2, 2, 1, -5, 4, -8, BUTTON_GOLD)
        self.add_cube(2, 2, 1, 5, 4, -8, BUTTON_GOLD)

        # 4. ARMS
        self.add_cube(8, 8, 8, -16, 12, 0, RED)
        self.add_cube(6, 12, 6, -16, 2, 0, RED)
        self.add_cube(7, 7, 7, -16, -8, 0, WHITE)

        self.add_cube(8, 8, 8, 16, 12, 0, RED)
        self.add_cube(6, 12, 6, 16, 2, 0, RED)
        self.add_cube(7, 7, 7, 16, -8, 0, WHITE)

        # 5. HEAD
        self.add_cube(18, 16, 18, 0, 22, 0, SKIN)
        self.add_cube(20, 6, 20, 0, 32, 0, RED)
        self.add_cube(24, 2, 24, 0, 29, -4, RED)

        # 6. FACE
        self.add_cube(4, 4, 4, 0, 22, -10, SKIN)
        self.add_cube(10, 3, 2, 0, 18, -10, MUSTACHE_BLACK) # Wider mustache
        self.add_cube(4, 8, 4, -9, 22, -2, BROWN)
        self.add_cube(4, 8, 4, 9, 22, -2, BROWN)
        self.add_cube(18, 10, 6, 0, 22, 8, BROWN)

        # Eyes
        self.add_cube(4, 4, 1, -6, 24, -9, WHITE)
        self.add_cube(2, 2, 1, -5, 24, -10, EYE_BLUE)
        self.add_cube(4, 4, 1, 6, 24, -9, WHITE)
        self.add_cube(2, 2, 1, 5, 24, -10, EYE_BLUE)

    def update(self):
        self.dy -= GRAVITY
        self.y += self.dy
        if self.y < 0: 
            self.y = 0
            self.dy = 0
            self.is_jumping = False

class Level(Mesh):
    def __init__(self):
        super().__init__(0, 0, 0)
        self.build_courtyard()

    def build_courtyard(self):
        # 1. Procedural Checkerboard Floor
        # We create multiple large tiles instead of one giant one for the checker effect
        tile_size = 400
        grid_range = 3 # 3x3 grid centered
        
        for x in range(-grid_range, grid_range):
            for z in range(-grid_range, grid_range):
                color = CHECKER_LIGHT if (x + z) % 2 == 0 else CHECKER_DARK
                self.add_cube(tile_size, 10, tile_size, x * tile_size, -5, z * tile_size, color)

        # 2. Walls
        self.add_cube(2400, 300, 50, 0, 150, 1200, METAL_GREY)
        self.add_cube(2400, 300, 50, 0, 150, -1200, METAL_GREY)
        self.add_cube(50, 300, 2400, 1200, 150, 0, METAL_GREY)
        self.add_cube(50, 300, 2400, -1200, 150, 0, METAL_GREY)

        # 3. Fountain / Statue Base
        self.add_cube(300, 40, 300, 0, -20, 0, METAL_GREY)
        self.add_cube(250, 10, 250, 0, -5, 0, (100, 200, 255)) # Water

        # 4. Large Star
        self.add_cube(40, 40, 10, 0, 100, 0, YELLOW)
        self.add_cube(10, 60, 10, 0, 100, 0, YELLOW)
        self.add_cube(60, 10, 10, 0, 100, 0, YELLOW)

        # 5. Pillars (Floating for surreal N64DD feel)
        positions = [(-600, -600), (600, -600), (-600, 600), (600, 600)]
        for px, pz in positions:
            self.add_cube(60, 200, 60, px, 100, pz, WHITE)
            self.add_cube(80, 20, 80, px, 200, pz, RED) # Cap

# --- ENGINE ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SUPER MARIO 64DD - EXPANSION KIT")
    clock = pygame.time.Clock()
    
    mario = Mario(0, 0, 0)
    level = Level()
    
    cam_x, cam_y, cam_z = 0, 300, 800
    cam_yaw = 0
    cam_pitch = 0.2
    
    # Pre-allocate for speed
    cx = WIDTH // 2
    cy = HEIGHT // 2
    
    running = True
    while running:
        dt = clock.tick(FPS)
        
        # Dynamic Sky Gradient
        screen.fill(DD_SKY)
        pygame.draw.rect(screen, (10, 10, 30), (0, cy, WIDTH, cy)) # Ground fog fake

        # --- INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not mario.is_jumping:
                    mario.dy = JUMP_FORCE
                    mario.is_jumping = True
                if event.key == pygame.K_ESCAPE: running = False

        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_a]: cam_yaw -= ROTATION_SPEED
        if keys[pygame.K_d]: cam_yaw += ROTATION_SPEED
        
        move_x, move_z = 0, 0
        moved = False
        
        if keys[pygame.K_w]: move_z -= MOVE_SPEED; moved = True
        if keys[pygame.K_s]: move_z += MOVE_SPEED; moved = True
        
        if moved:
            mx = move_x * math.cos(cam_yaw) - move_z * math.sin(cam_yaw)
            mz = move_x * math.sin(cam_yaw) + move_z * math.cos(cam_yaw)
            mario.x += mx
            mario.z += mz
            mario.yaw = -math.atan2(mz, mx) - math.pi/2

        mario.update()
        
        # Smooth Camera
        target_cam_x = mario.x + math.sin(cam_yaw) * 500
        target_cam_z = mario.z + math.cos(cam_yaw) * 500
        cam_x += (target_cam_x - cam_x) * 0.08
        cam_z += (target_cam_z - cam_z) * 0.08
        
        # --- RENDERER (Optimized) ---
        render_list = []
        
        # Precompute Camera Trig
        c_cos = math.cos(-cam_yaw)
        c_sin = math.sin(-cam_yaw)
        
        def process_mesh(mesh, world_x, world_y, world_z, rotation):
            m_cos = math.cos(rotation)
            m_sin = math.sin(rotation)
            
            # View vector roughly points forward from camera
            # For strict culling, we need exact vector from cam to face center, 
            # but using the camera's forward vector is a fast approximation for 'is facing me'
            # simplified to: is the transformed normal z < 0?
            
            for face in mesh.faces:
                # 1. Transform Vertices
                transformed_verts = []
                avg_z = 0
                
                # OPTIMIZATION: Check face culling first?
                # We need rotated normal. 
                # Rotate normal by object rotation (mesh.yaw)
                if face.normal:
                    nx, ny, nz = face.normal
                    # Rotate normal only by object rotation (not camera yet)
                    r_nx = nx * m_cos - nz * m_sin
                    r_nz = nx * m_sin + nz * m_cos
                    
                    # Calculate approximate view vector from camera to object
                    # (Simplified: just check if normal points roughly to camera)
                    # We skip this for now to ensure we don't accidentally cull wrong 
                    # because we haven't done camera transform yet.
                
                valid = True
                local_verts = []
                
                for i in face.indices:
                    v = mesh.vertices[i]
                    
                    # World Rotate & Translate
                    rx = v.x * m_cos - v.z * m_sin
                    rz = v.x * m_sin + v.z * m_cos
                    wx = rx + world_x
                    wy = v.y + world_y
                    wz = rz + world_z
                    
                    # Camera Translate
                    dcx = wx - cam_x
                    dcy = wy - cam_y
                    dcz = wz - cam_z
                    
                    # Camera Rotate (Y only for now)
                    xx = dcx * c_cos - dcz * c_sin
                    zz = dcx * c_sin + dcz * c_cos
                    yy = dcy
                    
                    if zz < 5: # Near clip
                        valid = False
                        break
                        
                    local_verts.append((xx, yy, zz))
                    avg_z += zz
                
                if not valid: continue

                # Back-face Culling (Dynamic)
                # Calculate normal of the transformed face in camera space
                # V1-V0 cross V2-V0
                v0 = local_verts[0]
                v1 = local_verts[1]
                v2 = local_verts[2]
                
                # Normal Z component is enough to determine if it faces camera
                # (v1.x-v0.x)*(v2.y-v0.y) - (v1.y-v0.y)*(v2.x-v0.x)
                # Check winding order. Positive Z usually means facing away if standard.
                # Assuming counter-clockwise winding is front.
                
                ux = v1[0] - v0[0]
                uy = v1[1] - v0[1]
                vx = v2[0] - v0[0]
                vy = v2[1] - v0[1]
                
                # 2D Cross product of projected coordinates essentially gives Z normal direction
                # But we are in 3D camera space.
                # Normal Z = ux*vy - uy*vx. 
                # If Z > 0 it faces camera? Or < 0?
                # Let's trust the sort primarily, but simple normal check helps.
                # Actually, simpler method:
                # If dot product of Normal and Vector_to_Cam is positive.
                
                # Let's project first, it's safer for 2D poly rendering
                screen_points = []
                for xx, yy, zz in local_verts:
                    scale = FOV / zz
                    sx = int(xx * scale + cx)
                    sy = int(-yy * scale + cy)
                    screen_points.append((sx, sy))

                # 2D Backface Culling (Shoelace)
                # (x2 - x1)(y2 + y1) sum
                area = 0
                for i in range(len(screen_points)):
                    j = (i + 1) % len(screen_points)
                    area += (screen_points[j][0] - screen_points[i][0]) * (screen_points[j][1] + screen_points[i][1])
                
                if area > 0: # Visible if area is positive (or negative depending on coord system)
                    render_list.append({
                        'poly': screen_points,
                        'depth': avg_z / len(local_verts),
                        'color': face.color
                    })

        process_mesh(level, level.x, level.y, level.z, 0)
        process_mesh(mario, mario.x, mario.y, mario.z, mario.yaw)
        
        # Sort painter's algorithm
        render_list.sort(key=lambda x: x['depth'], reverse=True)
        
        for item in render_list:
            depth = item['depth']
            # Distance Fog
            fog_factor = min(1.0, depth / VIEW_DISTANCE)
            # Mix item color with Sky color
            r, g, b = item['color']
            sr, sg, sb = DD_SKY
            
            fr = int(r + (sr - r) * fog_factor)
            fg = int(g + (sg - g) * fog_factor)
            fb = int(b + (sb - b) * fog_factor)
            
            pygame.draw.polygon(screen, (fr, fg, fb), item['poly'])
            # Only draw outlines for Mario, level looks cleaner without
            if item['depth'] < 1000: 
                pygame.draw.polygon(screen, (0,0,0), item['poly'], 1)

        # --- HUD ---
        # Draw HUD Box
        pygame.draw.rect(screen, (0, 0, 0), (0, HEIGHT-50, WIDTH, 50))
        pygame.draw.line(screen, METAL_GREY, (0, HEIGHT-50), (WIDTH, HEIGHT-50), 2)
        
        # Status Text
        font = pygame.font.SysFont('Arial', 20, bold=True)
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, CHECKER_LIGHT)
        dd_text = font.render("DISK DRIVE [ACTIVE]", True, EYE_BLUE)
        
        screen.blit(fps_text, (20, HEIGHT - 40))
        screen.blit(dd_text, (WIDTH - 200, HEIGHT - 40))
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
