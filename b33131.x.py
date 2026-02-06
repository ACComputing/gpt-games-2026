import pygame
import math
import random
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 400  # Field of view scale factor
SENSITIVITY = 0.003
MOVE_SPEED = 0.3
SPRINT_SPEED = 0.6
RENDER_DISTANCE = 150
MAX_POLY_COUNT = 2000

# --- COLORS ---
SKY_BLUE = (135, 206, 235)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRASS_GREEN = (34, 139, 34)
WATER_BLUE = (0, 0, 255)
BLOOD_RED = (139, 0, 0)
WALL_GREY = (224, 224, 224)
ROOF_RED = (139, 0, 0)
BRIDGE_BROWN = (160, 82, 45)
MIPS_YELLOW = (255, 255, 0)
LIME = (0, 255, 0)

# --- 3D MATH & CLASSES ---

class Vector3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

class Camera:
    def __init__(self, x, y, z):
        self.pos = Vector3(x, y, z)
        self.yaw = 0.0    # Horizontal rotation
        self.pitch = 0.0  # Vertical rotation

class Face:
    def __init__(self, vertices, color):
        self.vertices = vertices # List of Vector3
        self.color = color
        self.dist = 0.0 # Distance to camera for sorting

    def update_dist(self, cam_pos):
        # Calculate centroid distance for depth sorting
        cx = sum(v.x for v in self.vertices) / len(self.vertices)
        cy = sum(v.y for v in self.vertices) / len(self.vertices)
        cz = sum(v.z for v in self.vertices) / len(self.vertices)
        self.dist = math.sqrt((cx - cam_pos.x)**2 + (cy - cam_pos.y)**2 + (cz - cam_pos.z)**2)

# --- ENGINE FUNCTIONS ---

def project(v, cam):
    """
    Project 3D world coordinates to 2D screen coordinates.
    Returns (x, y) or None if behind camera.
    """
    # Relative to camera
    x = v.x - cam.pos.x
    y = v.y - cam.pos.y
    z = v.z - cam.pos.z

    # Rotate Yaw (around Y axis)
    # x' = x*cos(yaw) - z*sin(yaw)
    # z' = x*sin(yaw) + z*cos(yaw)
    cos_yaw = math.cos(cam.yaw)
    sin_yaw = math.sin(cam.yaw)
    rx = x * cos_yaw - z * sin_yaw
    rz = x * sin_yaw + z * cos_yaw

    # Rotate Pitch (around X axis)
    # y' = y*cos(pitch) - z'*sin(pitch)
    # z'' = y*sin(pitch) + z'*cos(pitch)
    cos_pitch = math.cos(cam.pitch)
    sin_pitch = math.sin(cam.pitch)
    ry = y * cos_pitch - rz * sin_pitch
    rz_final = y * sin_pitch + rz * cos_pitch

    # Clipping (Near plane)
    if rz_final <= 1.0:
        return None

    # Projection
    scale = FOV / rz_final
    screen_x = WIDTH / 2 + rx * scale
    screen_y = HEIGHT / 2 - ry * scale # Invert Y for screen coords

    return (screen_x, screen_y)

def create_cube(x, y, z, w, h, d, color):
    """Generates faces for a cube/box."""
    hw, hh, hd = w/2, h/2, d/2
    # Vertices
    v = [
        Vector3(x-hw, y-hh, z-hd), Vector3(x+hw, y-hh, z-hd),
        Vector3(x+hw, y+hh, z-hd), Vector3(x-hw, y+hh, z-hd), # Front
        Vector3(x-hw, y-hh, z+hd), Vector3(x+hw, y-hh, z+hd),
        Vector3(x+hw, y+hh, z+hd), Vector3(x-hw, y+hh, z+hd)  # Back
    ]
    # Faces (Indices) - Counter Clockwise winding
    indices = [
        (0, 1, 2, 3), (5, 4, 7, 6), # Front, Back
        (4, 0, 3, 7), (1, 5, 6, 2), # Left, Right
        (3, 2, 6, 7), (1, 0, 4, 5)  # Top, Bottom
    ]
    faces = []
    for idx_list in indices:
        face_verts = [v[i] for i in idx_list]
        faces.append(Face(face_verts, color))
    return faces

def create_pyramid(x, y, z, r, h, color):
    """Generates a simple 4-sided pyramid (like MIPS ears/spires)."""
    top = Vector3(x, y + h/2, z)
    # Base square
    v0 = Vector3(x-r, y-h/2, z-r)
    v1 = Vector3(x+r, y-h/2, z-r)
    v2 = Vector3(x+r, y-h/2, z+r)
    v3 = Vector3(x-r, y-h/2, z+r)
    
    faces = [
        Face([v0, v1, v2, v3], color), # Base
        Face([v0, top, v1], color),
        Face([v1, top, v2], color),
        Face([v2, top, v3], color),
        Face([v3, top, v0], color)
    ]
    return faces

def create_prism(x, y, z, r, h, sides, color):
    """Generates a vertical prism (cylinder approximation)."""
    top_verts = []
    bot_verts = []
    angle_step = (math.pi * 2) / sides
    
    for i in range(sides):
        angle = i * angle_step
        vx = math.cos(angle) * r
        vz = math.sin(angle) * r
        top_verts.append(Vector3(x + vx, y + h/2, z + vz))
        bot_verts.append(Vector3(x + vx, y - h/2, z + vz))
    
    faces = []
    # Side faces
    for i in range(sides):
        next_i = (i + 1) % sides
        faces.append(Face([bot_verts[i], top_verts[i], top_verts[next_i], bot_verts[next_i]], color))
    
    # Caps (simplified as single polygon, might glitch if non-convex but prism is convex)
    faces.append(Face(top_verts, color)) 
    faces.append(Face(list(reversed(bot_verts)), color))
    
    return faces

# --- GAME STATE ---

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("B3313 - Internal Plexus (Pygame Port)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 14, bold=True)
        self.title_font = pygame.font.SysFont("Courier New", 40, bold=True)
        
        # State
        self.state = "START" # START, PLAY
        self.running = True
        
        # World
        self.camera = Camera(0, 2, -40)
        self.camera.yaw = math.pi # Face castle
        self.geometry = []
        self.dynamic_objects = [] # (type, obj, x, z)
        
        # Personalization
        self.p_value = "INITIALIZING..."
        self.last_ai_update = 0
        self.water_color = WATER_BLUE
        self.sky_color = SKY_BLUE
        self.message = ""
        self.message_timer = 0
        self.mips_pos = Vector3(5, 1, 25)
        self.glitch_active = False
        
        # Assets
        self.build_world()
        
        # Input
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)

    def build_world(self):
        self.geometry = []
        
        # 1. GROUND & WATER
        # Huge grass plane (simulated by large rect)
        self.geometry.extend(create_cube(0, -3, 0, 200, 1, 200, GRASS_GREEN))
        
        # Water Plane
        self.water_faces = create_cube(0, -1.5, 0, 200, 1, 200, self.water_color)
        self.geometry.extend(self.water_faces)
        
        # Bridge
        self.geometry.extend(create_cube(0, -0.5, -30, 10, 1, 60, BRIDGE_BROWN))
        
        # Fountain Base
        self.geometry.extend(create_prism(0, -1, -45, 8, 2, 8, WALL_GREY))
        self.geometry.extend(create_prism(0, 1, -45, 1, 6, 4, WALL_GREY))

        # 2. CASTLE
        # Main Block (The "Lobby" box)
        # We model the exterior walls
        self.geometry.extend(create_cube(0, 15, 20, 40, 30, 40, WALL_GREY))
        
        # Towers
        self.geometry.extend(create_prism(-20, 20, 0, 5, 40, 6, WALL_GREY))
        self.geometry.extend(create_prism(20, 20, 0, 5, 40, 6, WALL_GREY))
        
        # Roofs
        self.geometry.extend(create_pyramid(-20, 45, 0, 7, 10, ROOF_RED))
        self.geometry.extend(create_pyramid(20, 45, 0, 7, 10, ROOF_RED))
        
        # Main Spire
        self.geometry.extend(create_pyramid(0, 45, 20, 15, 20, ROOF_RED))
        
        # Door
        self.geometry.extend(create_cube(0, 3, 0, 4, 6, 1, ROOF_RED)) # Front door
        
        # The Hole (Black Circle on bridge/lobby transition)
        self.geometry.extend(create_prism(-10, 0.1, 25, 2, 0.1, 8, BLACK))
        
    def update_ai(self):
        now = pygame.time.get_ticks()
        if now - self.last_ai_update > 2000:
            self.last_ai_update = now
            # Generate ID
            self.p_value = hex(random.randint(0, 0xFFFFFF))[2:].upper()
            
            rand = random.random()
            
            # Event: Blood Water
            if rand > 0.90:
                self.water_color = BLOOD_RED
                self.show_message("FLUID DATA CORRUPTION")
            elif rand < 0.10:
                self.water_color = WATER_BLUE
                
            # Event: Sky Glitch
            if rand > 0.95:
                self.glitch_active = True
            else:
                self.glitch_active = False

            # Mips Teleport logic
            dist_to_mips = math.sqrt((self.camera.pos.x - self.mips_pos.x)**2 + (self.camera.pos.z - self.mips_pos.z)**2)
            if dist_to_mips < 8:
                self.mips_pos.x = random.uniform(-15, 15)
                self.mips_pos.z = random.uniform(10, 30)

    def show_message(self, text):
        self.message = text
        self.message_timer = 180 # 3 seconds at 60fps

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Speed
        speed = SPRINT_SPEED if keys[pygame.K_LSHIFT] else MOVE_SPEED
        
        dx, dz = 0, 0
        if keys[pygame.K_w]: dz += 1
        if keys[pygame.K_s]: dz -= 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1
        
        # Normalize diagonal movement
        if dx != 0 or dz != 0:
            length = math.sqrt(dx*dx + dz*dz)
            dx /= length
            dz /= length
            
            # Apply Rotation
            # Move forward direction is based on Yaw
            # Forward vector: (sin(yaw), cos(yaw))
            # Right vector: (cos(yaw), -sin(yaw))
            
            # Simple 2D rotation for movement
            sin_y = math.sin(self.camera.yaw)
            cos_y = math.cos(self.camera.yaw)
            
            move_x = (dx * cos_y + dz * sin_y) * speed
            move_z = (-dx * sin_y + dz * cos_y) * speed
            
            # Collision / Boundary Check (Simple)
            next_x = self.camera.pos.x + move_x
            next_z = self.camera.pos.z + move_z
            
            # Collision Logic (Hardcoded boundaries for castle/bridge)
            # Bridge is approx X: -5 to 5, Z: -60 to 0
            # Courtyard is approx Z > 0
            
            can_move = True
            
            # Very simple collision: Don't walk through the main castle block walls
            if 0 < next_z < 40 and -20 < next_x < 20:
                # Inside lobby area - check walls
                pass 
                
            self.camera.pos.x = next_x
            self.camera.pos.z = next_z

        # Mouse Look
        if self.state == "PLAY":
            mx, my = pygame.mouse.get_rel()
            self.camera.yaw += mx * SENSITIVITY
            self.camera.pitch += my * SENSITIVITY
            # Clamp pitch
            self.camera.pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.camera.pitch))

    def update(self):
        self.update_ai()
        self.handle_input()
        
        # Gravity / Height Logic
        floor_h = 0
        # Bridge
        if self.camera.pos.z < -2 and abs(self.camera.pos.x) < 6:
            floor_h = 0.5
        elif self.camera.pos.z > 0 and abs(self.camera.pos.x) < 20:
            floor_h = 0.1 # Lobby
        else:
            floor_h = -2.0 # Water/Grass level
            
        # The Hole Logic
        dist_to_hole = math.sqrt((self.camera.pos.x - -10)**2 + (self.camera.pos.z - 25)**2)
        if dist_to_hole < 2.5:
             # Fall
             self.camera.pos.y -= 0.5
             if self.camera.pos.y < -20:
                 self.camera.pos = Vector3(0, 2, -40) # Respawn
                 self.show_message("NEGATIVE EMOTIONAL AURA")
        else:
            target_y = floor_h + 2.0
            # Simple lerp gravity
            self.camera.pos.y += (target_y - self.camera.pos.y) * 0.1

        # MIPS Animation (Hopping)
        hop_offset = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 1.5
        self.mips_pos.y = 1 + hop_offset

    def render(self):
        # Background
        bg = BLACK if self.glitch_active else self.sky_color
        self.screen.fill(bg)
        
        # Prepare Geometry
        render_list = []
        
        # 1. Static Geometry
        # Only add faces that might be visible (simple frustum cull or distance check)
        for face in self.geometry:
            # Update color for water if changed
            if face in self.water_faces:
                face.color = self.water_color
                
            face.update_dist(self.camera.pos)
            if face.dist < RENDER_DISTANCE and face.dist > 1:
                render_list.append(face)
                
        # 2. Dynamic Geometry (MIPS)
        # Recreate MIPS geometry every frame at new pos
        mips_faces = create_pyramid(self.mips_pos.x, self.mips_pos.y, self.mips_pos.z, 0.5, 1.5, MIPS_YELLOW)
        for f in mips_faces:
            f.update_dist(self.camera.pos)
            render_list.append(f)
            
        # Sort Painter's Algorithm (Furthest first)
        render_list.sort(key=lambda f: f.dist, reverse=True)
        
        # Project and Draw
        for face in render_list:
            points = []
            valid = True
            for v in face.vertices:
                p = project(v, self.camera)
                if p:
                    points.append(p)
                else:
                    valid = False
                    break # Simple clipping: if any point is behind, don't draw face
            
            if valid and len(points) > 2:
                # Shade color based on distance (Fog effect)
                shade_factor = min(1.0, 1.0 - (face.dist / RENDER_DISTANCE))
                c = (
                    int(face.color[0] * shade_factor),
                    int(face.color[1] * shade_factor),
                    int(face.color[2] * shade_factor)
                )
                pygame.draw.polygon(self.screen, c, points)
                pygame.draw.polygon(self.screen, BLACK, points, 1) # Wireframe outline

        # UI Overlay
        self.render_ui()
        
        pygame.display.flip()

    def render_ui(self):
        if self.state == "START":
            # Glitch text effect
            off_x = random.randint(-2, 2)
            off_y = random.randint(-2, 2)
            
            title = self.title_font.render("B3313", True, BLOOD_RED)
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2 + off_x, HEIGHT//2 - 60 + off_y))
            
            sub = self.font.render("INTERNAL PLEXUS BUILD 1.0", True, WHITE)
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2))
            
            click = self.font.render("[ CLICK TO INITIALIZE ]", True, LIME)
            self.screen.blit(click, (WIDTH//2 - click.get_width()//2, HEIGHT//2 + 40))
            
            ctrls = self.font.render("WASD to Move | Mouse to Look", True, (150, 150, 150))
            self.screen.blit(ctrls, (WIDTH//2 - ctrls.get_width()//2, HEIGHT - 50))
            
        else:
            # Debug Box
            s = pygame.Surface((250, 100))
            s.set_alpha(128)
            s.fill(BLACK)
            self.screen.blit(s, (10, 10))
            
            lines = [
                f"SYSTEM: BOOT",
                f"ZONE: CASTLE GROUNDS",
                f"AI: CALIBRATING...",
                f"P-VALUE: {self.p_value}"
            ]
            
            for i, line in enumerate(lines):
                col = LIME if "P-VALUE" not in line else (0, 0, 255)
                t = self.font.render(line, True, col)
                self.screen.blit(t, (20, 20 + i*20))
                
            # Center Message
            if self.message_timer > 0:
                self.message_timer -= 1
                mt = self.title_font.render(self.message, True, WHITE)
                self.screen.blit(mt, (WIDTH//2 - mt.get_width()//2, HEIGHT//2 - 50))
                
            # Crosshair
            pygame.draw.circle(self.screen, WHITE, (WIDTH//2, HEIGHT//2), 2)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    global WIDTH, HEIGHT
                    WIDTH, HEIGHT = event.w, event.h
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "START":
                        self.state = "PLAY"
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            if self.state == "PLAY":
                self.update()
                
            self.render()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
