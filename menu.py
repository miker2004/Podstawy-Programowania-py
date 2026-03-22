import pygame
import sys
import random

# --- INICJALIZACJA ---
pygame.init()
app = {
    "state": "profile_select",
    "selected_profile": 0,
    "profiles": [
        {"name": "Gamer 1", "icon": "controller"},
        {"name": "Gamer 2", "icon": "skull"}
    ],
    "selected_idx": 0,
    "in_settings": False,
    "sel_setting": 0,
    "theme": "dark",
    "volume": 70,
    "res_idx": 2, # 1920x1080
    "resolutions": [(1280, 720), (1600, 900), (1920, 1080)],
    "fullscreen": False,
    "gear_rot": 0
}

WIDTH, HEIGHT = app["resolutions"][app["res_idx"]]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PS5 Launcher Pro - Stable Version")
clock = pygame.time.Clock()

# --- CZCIONKI ---
font_sm = pygame.font.SysFont("Segoe UI", 28)
font_md = pygame.font.SysFont("Segoe UI", 42, bold=True)
font_lg = pygame.font.SysFont("Segoe UI", 90, bold=True)

# --- KOLORY ---
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

# --- RYSOWANIE IKON ---
def draw_profile_icon(surface, x, y, size, icon_type, color):
    if icon_type == "heart":
        pts = [(x, y + size//3), (x - size//2, y - size//4), (x - size//4, y - size//2), 
               (x, y - size//4), (x + size//4, y - size//2), (x + size//2, y - size//4)]
        pygame.draw.polygon(surface, color, pts)
    elif icon_type == "controller":
        pygame.draw.rect(surface, color, (x - size//2, y - size//4, size, size//2), border_radius=10)
        pygame.draw.circle(surface, color, (x - size//3, y + size//6), size//4)
        pygame.draw.circle(surface, color, (x + size//3, y + size//6), size//4)
    elif icon_type == "skull":
        pygame.draw.circle(surface, color, (x, y - size//6), size//2)
        pygame.draw.rect(surface, color, (x - size//4, y + size//8, size//2, size//3), border_radius=5)
    elif icon_type == "eye":
        pygame.draw.ellipse(surface, color, (x - size//2, y - size//4, size, size//2))
        pygame.draw.circle(surface, (20,20,20), (x, y), size//6)

def draw_gear(surface, x, y, size, color, rotation):
    num_teeth = 8
    pts = []
    for i in range(num_teeth * 2):
        angle = (i * 3.14159 / num_teeth) + rotation
        rad = size if i % 2 == 0 else size * 0.65
        pts.append((x + rad * pygame.math.Vector2(1, 0).rotate_rad(angle).x,
                    y + rad * pygame.math.Vector2(1, 0).rotate_rad(angle).y))
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.circle(surface, (10,10,15), (x, y), int(size * 0.3))

def draw_door(surface, x, y, size, color):
    pygame.draw.rect(surface, color, (x - size//2, y - size//2, size, size), 4, border_radius=3)
    pygame.draw.rect(surface, color, (x - size//3, y - size//2.5, size*0.6, size*0.8), border_radius=2)

class Tile:
    def __init__(self, index):
        self.index = index
        self.x = WIDTH // 2
        self.scale = 0.5
    def update(self, selected):
        target_scale = 1.35 if self.index == selected else 0.5
        self.scale += (target_scale - self.scale) * 0.12
        target_x = (WIDTH // 2) + (self.index - selected) * 400
        self.x += (target_x - self.x) * 0.12
    def draw(self, surface, theme):
        size = int(320 * self.scale)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (self.x, HEIGHT // 2 + 150)
        is_sel = (self.index == app["selected_idx"])
        if is_sel:
            pygame.draw.rect(surface, theme["accent"], rect.inflate(20, 20), width=5, border_radius=25)
            txt = font_md.render(GAMES[self.index]["title"], True, theme["text"])
            surface.blit(txt, (rect.centerx - txt.get_width()//2, rect.bottom + 40))
        if self.index < 3: pygame.draw.rect(surface, GAMES[self.index]["color"], rect, border_radius=20)
        elif self.index == 3:
            pygame.draw.rect(surface, (60, 60, 70), rect, border_radius=20)
            app["gear_rot"] += 0.02 if is_sel else 0.005
            draw_gear(surface, rect.centerx, rect.centery, size//3, theme["text"], app["gear_rot"])
        elif self.index == 4:
            pygame.draw.rect(surface, (50, 50, 60), rect, border_radius=20)
            draw_door(surface, rect.centerx, rect.centery, size//2, theme["text"])

tiles = [Tile(i) for i in range(len(GAMES))]

# --- GŁÓWNA PĘTLA ---
while True:
    theme = THEMES[app["theme"]]
    screen.fill(theme["bg"])
    
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if app["state"] == "profile_select":
        # EKRAN WYBORU PROFILU
        title = font_lg.render("Kto używa konsoli?", True, theme["text"])
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        
        items = app["profiles"] + [{"name": "Nowy Profil", "icon": "plus"}]
        for i, p in enumerate(items):
            is_sel = (i == app["selected_profile"])
            x_pos = WIDTH // 2 - (len(items)-1)*150 + (i*300)
            y_pos = HEIGHT // 2 + 50
            
            size = 200 if is_sel else 160
            color = theme["accent"] if is_sel else theme["text"]
            
            pygame.draw.rect(screen, theme["panel"], (x_pos-size//2, y_pos-size//2, size, size), border_radius=30)
            if is_sel: pygame.draw.rect(screen, theme["accent"], (x_pos-size//2, y_pos-size//2, size, size), width=5, border_radius=30)
            
            if p["icon"] == "plus":
                pygame.draw.line(screen, color, (x_pos-30, y_pos), (x_pos+30, y_pos), 6)
                pygame.draw.line(screen, color, (x_pos, y_pos-30), (x_pos, y_pos+30), 6)
            else:
                draw_profile_icon(screen, x_pos, y_pos, size//2, p["icon"], color)
            
            name_txt = font_sm.render(p["name"], True, color)
            screen.blit(name_txt, (x_pos - name_txt.get_width()//2, y_pos + size//2 + 30))

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RIGHT, pygame.K_d]: app["selected_profile"] = min(len(items)-1, app["selected_profile"]+1)
                    if event.key in [pygame.K_LEFT, pygame.K_a]: app["selected_profile"] = max(0, app["selected_profile"]-1)
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if i == len(items)-1: # Dodawanie automatem
                            new_name = f"Gracz {len(app['profiles'])+1}"
                            new_icon = random.choice(["heart", "controller", "skull", "eye"])
                            app["profiles"].append({"name": new_name, "icon": new_icon})
                        else:
                            app["state"] = "main_menu"

    elif app["state"] == "main_menu":
        # MENU GŁÓWNE
        for event in events:
            if event.type == pygame.KEYDOWN:
                if not app["in_settings"]:
                    if event.key in [pygame.K_RIGHT, pygame.K_d]: app["selected_idx"] = min(len(GAMES)-1, app["selected_idx"]+1)
                    if event.key in [pygame.K_LEFT, pygame.K_a]: app["selected_idx"] = max(0, app["selected_idx"]-1)
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if app["selected_idx"] == 3: app["in_settings"] = True
                        elif app["selected_idx"] == 4: pygame.quit(); sys.exit()
                else: # Logika ustawień
                    if event.key in [pygame.K_DOWN, pygame.K_s]: app["sel_setting"] = (app["sel_setting"] + 1) % 5
                    if event.key in [pygame.K_UP, pygame.K_w]: app["sel_setting"] = (app["sel_setting"] - 1) % 5
                    if event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_LEFT, pygame.K_a]:
                        mod = 1 if event.key in [pygame.K_RIGHT, pygame.K_d] else -1
                        if app["sel_setting"] == 3: app["theme"] = "light" if app["theme"]=="dark" else "dark"
                    if event.key == pygame.K_ESCAPE or (event.key in [pygame.K_RETURN, pygame.K_SPACE] and app["sel_setting"] == 4): app["in_settings"] = False

        # RYSOWANIE
        if app["selected_idx"] < 3:
            pygame.draw.rect(screen, (0,0,0), (WIDTH//2-500, 100, 1000, 450), border_radius=30)
        
        for t in tiles: 
            t.update(app["selected_idx"])
            t.draw(screen, theme)
        
        # UI PROFILU W ROGU
        p = app["profiles"][app["selected_profile"]]
        pygame.draw.rect(screen, theme["panel"], (40, 40, 250, 80), border_radius=15)
        draw_profile_icon(screen, 80, 80, 40, p["icon"], theme["accent"])
        name_l = font_sm.render(p["name"], True, theme["text"])
        screen.blit(name_l, (130, 62))

        if app["in_settings"]:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,230)); screen.blit(overlay, (0,0))
            panel = pygame.Rect(WIDTH//2-300, HEIGHT//2-300, 600, 600); pygame.draw.rect(screen, theme["panel"], panel, border_radius=35)
            opts = ["Głośność", "Rozdzielczość", "Fullscreen", f"Motyw: {app['theme'].upper()}", "POWRÓT"]
            for i, o in enumerate(opts):
                col = theme["accent"] if i == app["sel_setting"] else theme["text"]
                screen.blit(font_md.render(o, True, col), (panel.x + 70, panel.y + 100 + i*100))

    pygame.display.flip()
    clock.tick(60)
