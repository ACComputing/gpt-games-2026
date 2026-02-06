import pygame
import math
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# --- COLORS (N64DD Palette) ---
DD_SKY_TOP = (26, 26, 77)     # #1a1a4d
DD_SKY_BOT = (0, 0, 0)
RED = (220, 20, 60)           # Crimson
BLUE = (0, 0, 205)
WHITE = (255, 255, 255)
SKIN = (255, 204, 153)
BROWN = (139, 69, 19)
MUSTACHE_BLACK = (20, 20, 20)
BUTTON_GOLD = (255, 215, 0)
EYE_BLUE = (0, 128, 255)
YELLOW = (255, 255, 0)
GREY_TEXT = (150, 150, 150)

# --- 3D ENGINE CLASSES ---
class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Face:
    def __init__(self, indices, color):
        self.indices = indices
        self.color = color

class Mesh:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def add_cube(self, w, h, d, ox, oy, oz, color):
        start_idx = len(self.vertices)
        hw, hh, hd = w/2, h/2, d/2
        
        corners = [
            (-hw, -hh, -hd), (hw, -hh, -hd), (hw, hh, -hd), (-hw, hh, -hd),
            (-hw, -hh, hd), (hw, -hh, hd), (hw, hh, hd), (-hw, hh, hd)
        ]
        
        for cx, cy, cz in corners:
            self.vertices.append(Vector3(cx + ox, cy + oy, cz + oz))
            
        # Winding order for backface culling
        cube_faces = [
            ([0, 1, 2, 3], color), ([5, 4, 7, 6], color), # Back, Front
            ([4, 0, 3, 7], color), ([1, 5, 6, 2], color), # Left, Right
            ([3, 2, 6, 7], color), ([4, 5, 1, 0], color)  # Top, Bottom
        ]
        
        for f_indices, f_color in cube_faces:
            shifted_indices = [i + start_idx for i in f_indices]
            self.faces.append(Face(shifted_indices, f_color))

def create_mario_head():
    m = Mesh()
    # Note: In Pygame screen coords, Y increases downwards. 
    # We might need to invert some Y offsets relative to the React version to keep it looking upright.
    
    # 1. Main Head
    m.add_cube(40, 36, 40, 0, 0, 0, SKIN)
    
    # 2. Cap
    m.add_cube(44, 12, 44, 0, -20, 0, RED)
    m.add_cube(52, 4, 52, 0, -15, 10, RED) # Brim
    
    # 3. Nose
    m.add_cube(10, 10, 10, 0, 2, 22, SKIN)
    
    # 4. Mustache
    m.add_cube(24, 6, 4, 0, 10, 21, MUSTACHE_BLACK)
    
    # 5. Eyes
    m.add_cube(10, 12, 2, -12, -6, 20, WHITE)
    m.add_cube(10, 12, 2, 12, -6, 20, WHITE)
    m.add_cube(4, 6, 3, -12, -6, 21, EYE_BLUE)
    m.add_cube(4, 6, 3, 12, -6, 21, EYE_BLUE)
    
    # 6. Hair/Back
    m.add_cube(42, 24, 10, 0, 0, -18, BROWN)
    
    return m

# --- MAIN ENGINE ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ULTRA MARIO 3D BROS - 64DD MENU")
    clock = pygame.time.Clock()

    # Fonts
    try:
        font_title = pygame.font.Font(None, 80)
        font_menu = pygame.font.Font(None, 40)
        font_small = pygame.font.Font(None, 24)
    except:
        font_title = pygame.font.SysFont('Arial', 60, bold=True)
        font_menu = pygame.font.SysFont('Arial', 30, bold=True)
        font_small = pygame.font.SysFont('Arial', 18)

    mario = create_mario_head()
    
    # Menu State
    menu_items = ["PLAY GAME", "HOW TO PLAY", "CREDITS", "HELP", "ABOUT", "EXIT GAME"]
    selected_index = 0
    active_overlay = None # 'about', 'help', etc.

    # Camera/Animation
    angle = 0.0
    cam_z = 200
    fov = 400
    cx, cy = WIDTH // 2, HEIGHT // 2

    running = True
    while running:
        dt = clock.tick(FPS)
        time_sec = pygame.time.get_ticks() / 1000.0

        # --- INPUT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if active_overlay:
                    if event.key in (pygame.K_ESCAPE, pygame.K_b):
                        active_overlay = None
                else:
                    if event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(menu_items)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(menu_items)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        choice = menu_items[selected_index]
                        if choice == "EXIT GAME": running = False
                        elif choice == "PLAY GAME": print("Loading World 1-1...")
                        elif choice == "HOW TO PLAY": active_overlay = "HOW TO PLAY"
                        elif choice == "CREDITS": active_overlay = "CREDITS"
                        elif choice == "HELP": active_overlay = "HELP"
                        elif choice == "ABOUT": active_overlay = "ABOUT 64DD"

        # --- DRAW BACKGROUND ---
        # Vertical Gradient
        for y in range(HEIGHT):
            # Interpolate between DD_SKY_TOP and DD_SKY_BOT
            ratio = y / HEIGHT
            r = int(DD_SKY_TOP[0] * (1 - ratio) + DD_SKY_BOT[0] * ratio)
            g = int(DD_SKY_TOP[1] * (1 - ratio) + DD_SKY_BOT[1] * ratio)
            b = int(DD_SKY_TOP[2] * (1 - ratio) + DD_SKY_BOT[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # --- 3D RENDERING ---
        angle += 0.02
        bounce = math.sin(time_sec * 2) * 10
        
        render_list = []
        
        for face in mario.faces:
            transformed = []
            avg_z = 0
            
            for idx in face.indices:
                v = mario.vertices[idx]
                
                # Rotate Y
                rx = v.x * math.cos(angle) - v.z * math.sin(angle)
                rz = v.x * math.sin(angle) + v.z * math.cos(angle)
                
                # Rotate X (Tilt + Bounce)
                ry = v.y 
                # Apply slight tilt
                tilt = 0.2
                ry_rot = ry * math.cos(tilt) - rz * math.sin(tilt)
                rz_rot = ry * math.sin(tilt) + rz * math.cos(tilt)
                
                ry_rot += bounce # Bobbing animation
                
                # Project
                zz = rz_rot + cam_z
                if zz > 1:
                    scale = fov / zz
                    sx = rx * scale + cx
                    sy = ry_rot * scale + cy
                    transformed.append((sx, sy))
                    avg_z += zz
            
            if len(transformed) == 4:
                # Shoelace formula for backface culling
                # (x2-x1)(y2+y1)
                area = 0
                for i in range(4):
                    j = (i + 1) % 4
                    area += (transformed[j][0] - transformed[i][0]) * (transformed[j][1] + transformed[i][1])
                
                # Check area sign (depends on winding order and Y axis)
                if area > 0: 
                    render_list.append({
                        'poly': transformed,
                        'depth': avg_z,
                        'color': face.color
                    })

        # Painter's Algorithm Sort
        render_list.sort(key=lambda x: x['depth'], reverse=True)
        
        for item in render_list:
            pygame.draw.polygon(screen, item['color'], item['poly'])
            pygame.draw.polygon(screen, (0, 0, 0), item['poly'], 1) # Outline

        # --- HUD & UI ---
        
        # Logo
        logo_y = 50 + math.sin(time_sec) * 5
        title_surf = font_title.render("ULTRA MARIO 3D", True, WHITE)
        title_shadow = font_title.render("ULTRA MARIO 3D", True, RED)
        screen.blit(title_shadow, (WIDTH//2 - title_surf.get_width()//2 + 4, logo_y + 4))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, logo_y))
        
        sub_surf = font_small.render("- 64 DISK DRIVE EXPANSION -", True, YELLOW)
        screen.blit(sub_surf, (WIDTH//2 - sub_surf.get_width()//2, logo_y + 60))

        # Menu Options
        menu_start_y = HEIGHT - 250
        for i, item in enumerate(menu_items):
            color = WHITE if i != selected_index else YELLOW
            offset_x = 20 if i == selected_index else 0
            
            label = font_menu.render(item, True, color)
            screen.blit(label, (50 + offset_x, menu_start_y + i * 40))
            
            if i == selected_index:
                # Draw cursor
                pygame.draw.polygon(screen, RED, [
                    (30, menu_start_y + i * 40 + 10),
                    (40, menu_start_y + i * 40 + 15),
                    (30, menu_start_y + i * 40 + 20)
                ])

        # Footer
        footer_rect = pygame.Rect(0, HEIGHT - 30, WIDTH, 30)
        pygame.draw.rect(screen, (0, 0, 0), footer_rect)
        pygame.draw.line(screen, (100, 100, 100), (0, HEIGHT-30), (WIDTH, HEIGHT-30), 2)
        
        status_text = font_small.render("64DD SYSTEM LINK [STABLE]", True, (150, 150, 150))
        screen.blit(status_text, (10, HEIGHT - 25))

        # --- OVERLAYS ---
        if active_overlay:
            # Dim background
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Box
            box_rect = pygame.Rect(100, 100, WIDTH-200, HEIGHT-200)
            pygame.draw.rect(screen, (20, 20, 60), box_rect)
            pygame.draw.rect(screen, WHITE, box_rect, 4)
            
            # Title
            head = font_title.render(active_overlay, True, YELLOW)
            screen.blit(head, (WIDTH//2 - head.get_width()//2, 130))
            
            # Text content (Placeholder for now)
            info = font_menu.render("Press 'B' or ESC to Return", True, WHITE)
            screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT - 180))

        # --- CRT SCANLINES EFFECT ---
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(screen, (0, 0, 0), (0, y), (WIDTH, y), 1)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
