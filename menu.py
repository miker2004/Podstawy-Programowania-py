import pygame
import sys

# --- INICJALIZACJA ---
pygame.init()
app = {
    "selected_idx": 0,
    "in_settings": False,
    "sel_setting": 0,
    "theme": "dark",
    "volume": 70,
    "res_idx": 2, # Startujemy od 1920x1080 (trzeci element listy poniżej)
    "resolutions": [(1280, 720), (1600, 900), (1920, 1080)],
    "fullscreen": False,
    "gear_rot": 0
}

# Ustawienie okna na 1080p
WIDTH, HEIGHT = app["resolutions"][app["res_idx"]]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PS5 Launcher Pro 1080p")
clock = pygame.time.Clock()

# --- CZCIONKI (Powiększone dla 1080p) ---
font_sm = pygame.font.SysFont("Segoe UI", 26)
font_md = pygame.font.SysFont("Segoe UI", 42, bold=True)
font_lg = pygame.font.SysFont("Segoe UI", 60, bold=True)

# --- KOLORY I MOTYWY ---
THEMES = {
    "dark": {"bg": (10, 10, 15), "text": (255, 255, 255), "accent": (0, 150, 255), "panel": (20, 20, 30)},
    "light": {"bg": (230, 230, 235), "text": (20, 20, 30), "accent": (0, 120, 215), "panel": (255, 255, 255)}
}

GAMES = [
    {"title": "CYBER PUNK", "color": (255, 45, 85)},
    {"title": "FROST LAND", "color": (0, 210, 255)},
    {"title": "FOREST RUN", "color": (50, 215, 75)},
    {"title": "USTAWIENIA", "color": (100, 100, 100)},
    {"title": "WYJŚCIE", "color": (180, 40, 40)}
]

def update_display():
    global WIDTH, HEIGHT, screen
    WIDTH, HEIGHT = app["resolutions"][app["res_idx"]]
    flags = pygame.FULLSCREEN if app["fullscreen"] else 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

def draw_gear(surface, x, y, size, color, rotation):
    num_teeth = 8
    pts = []
    for i in range(num_teeth * 2):
        angle = (i * 3.14159 / num_teeth) + rotation
        rad = size if i % 2 == 0 else size * 0.65
        pts.append((x + rad * pygame.math.Vector2(1, 0).rotate_rad(angle).x,
                    y + rad * pygame.math.Vector2(1, 0).rotate_rad(angle).y))
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.circle(surface, THEMES[app["theme"]]["bg"], (x, y), int(size * 0.3))

def draw_door(surface, x, y, size, color):
    # Ramka drzwi
    pygame.draw.rect(surface, color, (x - size//2, y - size//2, size, size), 4, border_radius=3)
    # Skrzydło drzwi
    pygame.draw.rect(surface, color, (x - size//3, y - size//2.5, size*0.6, size*0.8), border_radius=2)
    # Klamka
    pygame.draw.circle(surface, THEMES[app["theme"]]["bg"], (x + size//8, y), 4)

class Tile:
    def __init__(self, index):
        self.index = index
        self.x = WIDTH // 2
        self.scale = 0.5

    def update(self, selected):
        target_scale = 1.35 if self.index == selected else 0.55
        self.scale += (target_scale - self.scale) * 0.12
        # Większy odstęp dla 1080p
        target_x = (WIDTH // 2) + (self.index - selected) * 380
        self.x += (target_x - self.x) * 0.12

    def draw(self, surface, theme):
        size = int(300 * self.scale) # Bazowy rozmiar zwiększony do 300
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (self.x, HEIGHT // 2 + 150)
        is_sel = (self.index == app["selected_idx"])
        
        if is_sel:
            # Mocniejszy Glow
            pygame.draw.rect(surface, theme["accent"], rect.inflate(20, 20), width=5, border_radius=25)
            txt = font_md.render(GAMES[self.index]["title"], True, theme["text"])
            surface.blit(txt, (rect.centerx - txt.get_width()//2, rect.bottom + 40))

        if self.index < 3:
            pygame.draw.rect(surface, GAMES[self.index]["color"], rect, border_radius=20)
        elif self.index == 3: # Ustawienia
            pygame.draw.rect(surface, (60, 60, 70), rect, border_radius=20)
            app["gear_rot"] += 0.02 if is_sel else 0.005
            draw_gear(surface, rect.centerx, rect.centery, size//3, theme["text"], app["gear_rot"])
        elif self.index == 4: # Wyjście
            pygame.draw.rect(surface, (50, 50, 60), rect, border_radius=20)
            draw_door(surface, rect.centerx, rect.centery, size//2, theme["text"])

tiles = [Tile(i) for i in range(len(GAMES))]

while True:
    theme = THEMES[app["theme"]]
    screen.fill(theme["bg"])
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                app["fullscreen"] = not app["fullscreen"]
                update_display()

            if not app["in_settings"]:
                if event.key in [pygame.K_RIGHT, pygame.K_d]:
                    app["selected_idx"] = min(len(GAMES) - 1, app["selected_idx"] + 1)
                if event.key in [pygame.K_LEFT, pygame.K_a]:
                    app["selected_idx"] = max(0, app["selected_idx"] - 1)
                if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if app["selected_idx"] == 3: app["in_settings"] = True
                    elif app["selected_idx"] == 4: pygame.quit(); sys.exit()
                    else: print(f"Odpalam grę: {GAMES[app['selected_idx']]['title']}")
            
            else: # Menu Ustawień
                if event.key in [pygame.K_DOWN, pygame.K_s]:
                    app["sel_setting"] = (app["sel_setting"] + 1) % 5
                if event.key in [pygame.K_UP, pygame.K_w]:
                    app["sel_setting"] = (app["sel_setting"] - 1) % 5
                
                if event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_LEFT, pygame.K_a]:
                    mod = 1 if event.key in [pygame.K_RIGHT, pygame.K_d] else -1
                    if app["sel_setting"] == 0:
                        app["volume"] = max(0, min(100, app["volume"] + (mod * 10)))
                    elif app["sel_setting"] == 1:
                        app["res_idx"] = (app["res_idx"] + mod) % len(app["resolutions"])
                        update_display()
                    elif app["sel_setting"] == 2:
                        app["fullscreen"] = not app["fullscreen"]
                        update_display()
                    elif app["sel_setting"] == 3:
                        app["theme"] = "light" if app["theme"] == "dark" else "dark"
                
                if (event.key in [pygame.K_RETURN, pygame.K_SPACE] and app["sel_setting"] == 4) or event.key == pygame.K_ESCAPE:
                    app["in_settings"] = False

    # --- RENDERING ---
    if app["selected_idx"] < 3:
        # Wielki podgląd na górze (Styl PS5)
        prev_rect = pygame.Rect(WIDTH//2-500, 100, 1000, 450)
        pygame.draw.rect(screen, (0,0,0), prev_rect, border_radius=30)
        label = font_sm.render(f"P O D G L Ą D   G R Y :  {GAMES[app['selected_idx']]['title']}", True, (70,70,80))
        screen.blit(label, (WIDTH//2 - label.get_width()//2, 300))

    for tile in tiles:
        tile.update(app["selected_idx"])
        tile.draw(screen, theme)

    if app["in_settings"]:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        screen.blit(overlay, (0,0))
        
        panel = pygame.Rect(WIDTH//2-300, HEIGHT//2-300, 600, 600)
        pygame.draw.rect(screen, theme["panel"], panel, border_radius=35)
        
        fs_txt = "WŁĄCZONY" if app["fullscreen"] else "WYŁĄCZONY"
        opts = [
            f"Głośność: {app['volume']}%",
            f"Rozdzielczość: {app['resolutions'][app['res_idx']][0]}x{app['resolutions'][app['res_idx']][1]}",
            f"Pełny Ekran: {fs_txt}",
            f"Motyw: {app['theme'].upper()}",
            "ZAMKNIJ"
        ]
        
        for i, opt in enumerate(opts):
            is_sel = (i == app["sel_setting"])
            col = theme["accent"] if is_sel else theme["text"]
            if is_sel:
                pygame.draw.rect(screen, theme["accent"], (panel.x + 30, panel.y + 110 + i*100, 10, 40), border_radius=5)
            t_surf = font_md.render(opt, True, col)
            screen.blit(t_surf, (panel.x + 70, panel.y + 105 + i*100))

    pygame.display.flip()
    clock.tick(60)