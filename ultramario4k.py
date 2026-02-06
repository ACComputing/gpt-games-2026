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
CASTLE_FLOOR = (245, 222, 179) # Wheat/Tan
CASTLE_WALL = (255, 250, 240)  # Floral White
RUG_RED = (178, 34, 34)     # Red Carpet
STAIR_COLOR = (210, 180, 140)

# --- 3D ENGINE CLASSES ---

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def rotate_y(self, center, angle):
        # Rotate point around a center on the Y axis
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
        self.indices = indices # List of vertex indices
        self.color = color
        self.avg_z = 0 # For sorting (Painter's Algorithm)

class Mesh:
    def __init__(self, x, y, z, color=WHITE):
        self.x = x
        self.y = y
        self.z = z
        self.vertices = [] # List of Vector3 relative to center
        self.faces = []    # List of Face objects
        self.color = color
        self.yaw = 0

    def add_cube(self, w, h, d, offset_x, offset_y, offset_z, color):
        # Adds a cube to this mesh's geometry
        start_idx = len(self.vertices)
        hw, hh, hd = w/2, h/2, d/2
        
        # Define 8 corners relative to offset
        corners = [
            Vector3(-hw, -hh, -hd), Vector3(hw, -hh, -hd),
            Vector3(hw, hh, -hd), Vector3(-hw, hh, -hd),
            Vector3(-hw, -hh, hd), Vector3(hw, -hh, hd),
            Vector3(hw, hh, hd), Vector3(-hw, hh, hd)
        ]
        
        for c in corners:
            self.vertices.append(Vector3(c.x + offset_x, c.y + offset_y, c.z + offset_z))
            
        # Define 6 faces (indices)
        # Front, Back, Left, Right, Top, Bottom
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
        # Procedural Voxel Mario
        # Legs (Blue)
        self.add_cube(10, 15, 10, -6, 15, 0, BLUE)
        self.add_cube(10, 15, 10, 6, 15, 0, BLUE)
        # Torso (Red shirt + Blue overalls)
        self.add_cube(24, 20, 14, 0, -5, 0, RED) 
        self.add_cube(24, 12, 15, 0, 0, 0, BLUE) # Overall strap area
        # Arms (Red)
        self.add_cube(8, 20, 8, -18, -5, 0, RED)
        self.add_cube(8, 20, 8, 18, -5, 0, RED)
        # Head (Skin)
        self.add_cube(18, 18, 18, 0, -25, 0, SKIN)
        # Hat (Red)
        self.add_cube(20, 6, 22, 0, -35, 2, RED)
        self.add_cube(20, 10, 20, 0, -30, 0, RED)
        # Nose (Skin)
        self.add_cube(6, 6, 6, 0, -25, -12, SKIN)
        # Shoes (Brown)
        self.add_cube(12, 8, 14, -6, 25, -2, BROWN)
        self.add_cube(12, 8, 14, 6, 25, -2, BROWN)

    def update(self):
        # Gravity
        self.y += self.dy
        self.dy += GRAVITY
        
        # Floor collision (Ground is at y=0 relative to world, but model origin needs offset)
        if self.y > 0: 
            self.y = 0
            self.dy = 0
            self.is_jumping = False

class Level(Mesh):
    def __init__(self):
        super().__init__(0, 0, 0)
        self.build_castle_lobby()

    def build_castle_lobby(self):
        # 1. Main Floor (Approximated by tiles)
        floor_size = 2000
        self.add_cube(floor_size, 10, floor_size, 0, 40, 0, CASTLE_FLOOR)
        
        # 2. Sun Rug (Red octagon approximation)
        self.add_cube(400, 2, 400, 0, 34, 0, RUG_RED)
        self.add_cube(300, 4, 300, 0, 32, 0, (255, 215, 0)) # Gold center

        # 3. Back Stairs
        stair_w = 400
        stair_h = 20
        stair_d = 60
        for i in range(5):
            self.add_cube(stair_w, stair_h, stair_d, 0, 30 - (i*stair_h), -600 - (i*stair_d), STAIR_COLOR)

        # 4. Top Platform
        self.add_cube(600, 10, 400, 0, -80, -900, CASTLE_FLOOR)
        
        # 5. Walls (Simple bounding boxes)
        wall_h = 600
        self.add_cube(2000, wall_h, 50, 0, -200, 1000, CASTLE_WALL) # Front
        self.add_cube(2000, wall_h, 50, 0, -200, -1200, CASTLE_WALL) # Back
        self.add_cube(50, wall_h, 2200, 1000, -200, 0, CASTLE_WALL) # Right
        self.add_cube(50, wall_h, 2200, -1000, -200, 0, CASTLE_WALL) # Left
        
        # 6. Painting Doors (Green blobs)
        self.add_cube(120, 200, 10, -950, -60, 0, (34, 139, 34)) # Left door
        self.add_cube(120, 200, 10, 950, -60, 0, (34, 139, 34))  # Right door

# --- MAIN ENGINE ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ULTRA MARIO 3D BROS > DIMENSONAL EDITION")
    clock = pygame.time.Clock()
    
    # Instantiate Objects
    mario = Mario(0, 0, 0)
    level = Level()
    
    # Camera
    cam_x, cam_y, cam_z = 0, -200, 600
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
                    mario.dy = -JUMP_FORCE
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
            # Rotate movement vector by camera yaw
            mx = move_x * math.cos(cam_yaw) - move_z * math.sin(cam_yaw)
            mz = move_x * math.sin(cam_yaw) + move_z * math.cos(cam_yaw)
            mario.x += mx
            mario.z += mz
            
            # Simple facing direction logic
            mario.facing_angle = -math.atan2(mz, mx) - math.pi/2

        mario.update()
        
        # Camera Follow Logic (Tight follow)
        target_cam_x = mario.x + math.sin(cam_yaw) * 400
        target_cam_z = mario.z + math.cos(cam_yaw) * 400
        cam_x += (target_cam_x - cam_x) * 0.1
        cam_z += (target_cam_z - cam_z) * 0.1
        
        # --- RENDERER ---
        
        render_list = []
        
        # Helper to process a mesh
        def process_mesh(mesh, world_x, world_y, world_z, rotation=0):
            # Precompute sin/cos for mesh rotation
            m_cos = math.cos(rotation)
            m_sin = math.sin(rotation)
            
            # Precompute sin/cos for camera rotation (inverse)
            c_cos = math.cos(-cam_yaw)
            c_sin = math.sin(-cam_yaw)
            
            for face in mesh.faces:
                transformed_verts = []
                avg_z = 0
                valid_verts = 0
                
                for v_idx in face.indices:
                    v = mesh.vertices[v_idx]
                    
                    # 1. Model Rotation (if needed, e.g. Mario turning)
                    # Rotate v around (0,0,0)
                    rx = v.x * m_cos - v.z * m_sin
                    rz = v.x * m_sin + v.z * m_cos
                    ry = v.y
                    
                    # 2. World Translation
                    wx = rx + world_x
                    wy = ry + world_y
                    wz = rz + world_z
                    
                    # 3. Camera Translation
                    cx = wx - cam_x
                    cy = wy - cam_y
                    cz = wz - cam_z
                    
                    # 4. Camera Rotation (World rotates around camera)
                    # Rotate around Y axis
                    xx = cx * c_cos - cz * c_sin
                    zz = cx * c_sin + cz * c_cos
                    yy = cy
                    
                    # 5. Projection
                    # Simple Perspective Projection: x' = x * (f / z)
                    if zz < 10: # Near clipping plane (don't render behind camera)
                        continue
                        
                    valid_verts += 1
                    scale = FOV / zz
                    sx = int(xx * scale + WIDTH / 2)
                    sy = int(yy * scale + HEIGHT / 2)
                    
                    transformed_verts.append((sx, sy))
                    avg_z += zz
                
                if valid_verts == len(face.indices):
                    face.avg_z = avg_z / valid_verts
                    # Basic lighting based on face normal (simulated by checking index order or just depth)
                    # Simple depth shading
                    shade_factor = max(0.2, min(1.0, 1.0 - (face.avg_z / VIEW_DISTANCE)))
                    r = int(face.color[0] * shade_factor)
                    g = int(face.color[1] * shade_factor)
                    b = int(face.color[2] * shade_factor)
                    
                    render_list.append({
                        'poly': transformed_verts,
                        'depth': face.avg_z,
                        'color': (r, g, b)
                    })

        # Process Level
        process_mesh(level, level.x, level.y, level.z)
        
        # Process Mario (Apply rotation based on movement)
        # Note: Mario rotates to face movement, but for this simple engine we just render him
        process_mesh(mario, mario.x, mario.y, mario.z, mario.facing_angle)
        
        # Sort by depth (Painter's Algorithm: Draw far things first)
        render_list.sort(key=lambda x: x['depth'], reverse=True)
        
        # Draw
        for item in render_list:
            pygame.draw.polygon(screen, item['color'], item['poly'])
            pygame.draw.polygon(screen, BLACK, item['poly'], 1) # Wireframe outline for "Dimensional" look

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
