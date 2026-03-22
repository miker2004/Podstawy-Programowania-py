import pygame
import librosa
import math
import random
import sys
import os
import wave
import struct

# Inicjalizacja Pygame
pygame.init()
pygame.mixer.init()

# Zmienne globalne dla ekranu
RESOLUTIONS = [(800, 600), (1280, 720), (1920, 1080)]
current_res_index = 0
WIDTH, HEIGHT = RESOLUTIONS[current_res_index]
is_fullscreen = False

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rytmiczny Bullet Hell - Boss Update")
clock = pygame.time.Clock()

# Czcionki
font_title = pygame.font.SysFont("Arial", 48, bold=True)
font_btn = pygame.font.SysFont("Arial", 28)
font_text = pygame.font.SysFont("Arial", 20)
font_small_bold = pygame.font.SysFont("Arial", 14, bold=True)

# Kolory ogólne
BG_COLOR = (17, 17, 17)
PLAYER_COLOR = (0, 255, 255)
BTN_COLOR = (50, 50, 50)
BTN_HOVER = (100, 100, 100)

class Bullet:
    def __init__(self, x, y, vx, vy, speed, color):
        self.x = x
        self.y = y
        self.vx = vx * speed
        self.vy = vy * speed
        self.radius = 6
        self.color = color

    def update(self, speed_multiplier=1.0):
        self.x += self.vx * speed_multiplier
        self.y += self.vy * speed_multiplier

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

class Powerup:
    def __init__(self, x, y, p_type):
        self.x = x
        self.y = y
        self.type = p_type
        self.radius = 12
        self.vy = 2.0 
        
        if self.type == 'x2':
            self.color = (255, 215, 0)
            self.text = "x2"
        else:
            self.color = (0, 150, 255)
            self.text = "S" 

    def update(self):
        self.y += self.vy

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        txt_surf = font_small_bold.render(self.text, True, (0, 0, 0))
        surface.blit(txt_surf, (self.x - txt_surf.get_width()//2, self.y - txt_surf.get_height()//2))

class Boss:
    def __init__(self, hp_beats):
        self.x = WIDTH // 2
        self.y = 100
        self.hp = hp_beats
        self.max_hp = hp_beats
        self.radius = 35
        self.color = (255, 20, 20)
        self.start_ticks = pygame.time.get_ticks()

    def update(self):
        # Boss płynnie lata od lewej do prawej
        t = (pygame.time.get_ticks() - self.start_ticks) / 1000.0
        self.x = (WIDTH // 2) + math.sin(t * 1.5) * (WIDTH // 2 - 100)

    def draw(self, surface):
        # Rysowanie bossa
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (0,0,0), (int(self.x), int(self.y)), self.radius - 8, 3)
        
        # Pasek zdrowia bossa
        bar_w = 150
        bar_h = 10
        bg_rect = (self.x - bar_w//2, self.y - 60, bar_w, bar_h)
        pygame.draw.rect(surface, (100, 100, 100), bg_rect)
        
        hp_ratio = max(0, self.hp / self.max_hp)
        hp_rect = (self.x - bar_w//2, self.y - 60, int(bar_w * hp_ratio), bar_h)
        pygame.draw.rect(surface, (0, 255, 50), hp_rect)
        
        txt = font_small_bold.render("BOSS", True, (255, 255, 255))
        surface.blit(txt, (self.x - txt.get_width()//2, self.y - 80))

# --- PATTERNY ZWYKŁE ---

def pattern_nova(bullets, difficulty):
    num_bullets = int(8 * difficulty)
    speed_mult = 0.6 + (0.4 * difficulty)
    edges = [(random.randint(0, WIDTH), -20), (random.randint(0, WIDTH), HEIGHT+20), 
             (-20, random.randint(0, HEIGHT)), (WIDTH+20, random.randint(0, HEIGHT))]
    spawn_point = random.choice(edges)
    for i in range(num_bullets):
        angle = (math.pi * 2 / num_bullets) * i
        vx = math.cos(angle)
        vy = math.sin(angle)
        speed = random.uniform(4.0, 6.0) * speed_mult
        bullets.append(Bullet(spawn_point[0], spawn_point[1], vx, vy, speed, (255, 0, 85)))

def pattern_rain(bullets, difficulty):
    num_bullets = int(8 * difficulty)
    speed_mult = 0.6 + (0.4 * difficulty)
    for i in range(num_bullets):
        sx = random.randint(0, WIDTH)
        sy = random.randint(-80, -20)
        vx = random.uniform(-0.2, 0.2)
        vy = random.uniform(0.8, 1.2)
        speed = random.uniform(3.5, 5.5) * speed_mult
        bullets.append(Bullet(sx, sy, vx, vy, speed, (0, 255, 150)))

def pattern_targeted(bullets, player_x, player_y, difficulty):
    edges = [(random.randint(0, WIDTH), -20), (random.randint(0, WIDTH), HEIGHT+20), 
             (-20, random.randint(0, HEIGHT)), (WIDTH+20, random.randint(0, HEIGHT))]
    sx, sy = random.choice(edges)
    speed_mult = 0.6 + (0.4 * difficulty)
    angle = math.atan2(player_y - sy, player_x - sx)
    spread_range = int(1 + (1.5 * difficulty)) 
    for i in range(-spread_range, spread_range + 1):
        spread = angle + (i * 0.15)
        vx = math.cos(spread)
        vy = math.sin(spread)
        speed = random.uniform(5.0, 7.0) * speed_mult 
        bullets.append(Bullet(sx, sy, vx, vy, speed, (255, 100, 0)))

def pattern_circle_in(bullets, difficulty):
    num_bullets = int(14 * difficulty)
    speed_mult = 0.6 + (0.4 * difficulty)
    cx, cy = WIDTH//2, HEIGHT//2
    for i in range(num_bullets):
        angle = (math.pi * 2 / max(1, num_bullets)) * i
        sx = cx + math.cos(angle) * max(WIDTH, HEIGHT)
        sy = cy + math.sin(angle) * max(WIDTH, HEIGHT)
        vx = -math.cos(angle)
        vy = -math.sin(angle)
        speed = random.uniform(3.0, 4.5) * speed_mult
        bullets.append(Bullet(sx, sy, vx, vy, speed, (150, 0, 255)))

# --- PATTERNY BOSSA ---

def pattern_boss_spiral(bullets, bx, by, difficulty, beat_idx):
    num_bullets = int(10 * difficulty)
    speed_mult = 0.8 + (0.2 * difficulty)
    base_angle = (beat_idx % 20) * 0.4 # Kąt przesuwa się z każdym bitem tworząc spiralę
    
    for i in range(num_bullets):
        angle = base_angle + (math.pi * 2 / num_bullets) * i
        vx = math.cos(angle)
        vy = math.sin(angle)
        speed = random.uniform(4.5, 5.5) * speed_mult
        bullets.append(Bullet(bx, by, vx, vy, speed, (255, 50, 255)))

def pattern_boss_shotgun(bullets, bx, by, player_x, player_y, difficulty):
    angle = math.atan2(player_y - by, player_x - bx)
    spread_range = int(3 + difficulty)
    speed_mult = 0.8 + (0.3 * difficulty)
    
    for i in range(-spread_range, spread_range + 1):
        spread = angle + (i * 0.12)
        vx = math.cos(spread)
        vy = math.sin(spread)
        speed = random.uniform(6.0, 8.0) * speed_mult
        bullets.append(Bullet(bx, by, vx, vy, speed, (255, 150, 0)))

# -------------------------

def generate_random_music(filepath="tymczasowa_muzyka.wav", duration=60):
    sample_rate = 44100
    bpm = random.randint(110, 160)
    beat_interval = 60.0 / bpm
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1) 
        wav_file.setsampwidth(2) 
        wav_file.setframerate(sample_rate)
        for i in range(int(sample_rate * duration)):
            time_in_sec = i / sample_rate
            beat_time = time_in_sec % beat_interval
            if beat_time < 0.1:
                freq = 150 * math.exp(-beat_time * 30)
                amplitude = 30000 * math.exp(-beat_time * 20)
                value = int(math.sin(2 * math.pi * freq * time_in_sec) * amplitude)
            elif 0.5 < (beat_time / beat_interval) < 0.55:
                value = random.randint(-4000, 4000)
            else:
                value = 0
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)
    return filepath

def analyze_audio(filepath):
    try:
        y, sr = librosa.load(filepath)
        _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        return [t * 1000 for t in beat_times]
    except Exception as e:
        print(f"Błąd analizy: {e}")
        return None 

def draw_button(surface, rect, text, mouse_pos):
    color = BTN_HOVER if rect.collidepoint(mouse_pos) else BTN_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, (255, 0, 85), rect, width=2, border_radius=8)
    text_surf = font_btn.render(text, True, (255, 255, 255))
    surface.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
    return rect.collidepoint(mouse_pos)

def main():
    global WIDTH, HEIGHT, screen, current_res_index, is_fullscreen
    
    state = "MENU"
    music_file = None
    beat_times_ms = []
    volume = 0.5
    pygame.mixer.music.set_volume(volume)
    
    bullets = []
    powerups = []
    player_radius = 8
    score = 0
    beat_index = 0
    
    multiplier_timer = 0
    slowdown_timer = 0
    
    boss = None
    next_boss_score = 50000
    
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)
        
        btn_w, btn_h = 240, 50
        btn_start = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2, btn_w, btn_h)
        btn_settings = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 70, btn_w, btn_h)
        btn_vol_down = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 80, 50, 50)
        btn_vol_up = pygame.Rect(WIDTH//2 + 70, HEIGHT//2 - 80, 50, 50)
        btn_res = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 - 10, btn_w, btn_h)
        btn_fs = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 50, btn_w, btn_h)
        btn_back = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 120, btn_w, btn_h)
        btn_restart = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 70, btn_w, btn_h)
        btn_menu = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 140, btn_w, btn_h)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.DROPFILE:
                if state == "MENU":
                    music_file = event.file
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "PLAYING":
                        pygame.mixer.music.stop()
                        state = "MENU"
                    elif state in ["SETTINGS", "GAME_OVER", "ERROR"]:
                        state = "MENU"
                    else:
                        running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "MENU":
                    if btn_start.collidepoint(mouse_pos):
                        state = "LOADING"
                    elif btn_settings.collidepoint(mouse_pos):
                        state = "SETTINGS"
                elif state == "SETTINGS":
                    if btn_vol_down.collidepoint(mouse_pos):
                        volume = max(0.0, volume - 0.1)
                        pygame.mixer.music.set_volume(volume)
                    elif btn_vol_up.collidepoint(mouse_pos):
                        volume = min(1.0, volume + 0.1)
                        pygame.mixer.music.set_volume(volume)
                    elif btn_res.collidepoint(mouse_pos):
                        current_res_index = (current_res_index + 1) % len(RESOLUTIONS)
                        WIDTH, HEIGHT = RESOLUTIONS[current_res_index]
                        flags = pygame.FULLSCREEN if is_fullscreen else 0
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
                    elif btn_fs.collidepoint(mouse_pos):
                        is_fullscreen = not is_fullscreen
                        flags = pygame.FULLSCREEN if is_fullscreen else 0
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
                    elif btn_back.collidepoint(mouse_pos):
                        state = "MENU"
                elif state == "GAME_OVER":
                    if btn_restart.collidepoint(mouse_pos):
                        bullets.clear()
                        powerups.clear()
                        score = 0
                        beat_index = 0
                        multiplier_timer = 0
                        slowdown_timer = 0
                        boss = None
                        next_boss_score = 50000
                        state = "PLAYING"
                        pygame.mixer.music.play()
                    elif btn_menu.collidepoint(mouse_pos):
                        state = "MENU"
                elif state == "ERROR":
                    if btn_back.collidepoint(mouse_pos):
                        state = "MENU"

        if state == "MENU":
            pygame.mouse.set_visible(True)
            title = font_title.render("RYTMICZNY BULLET HELL", True, (255, 0, 85))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 200))
            if music_file:
                file_name = os.path.basename(music_file)
                info = font_text.render(f"Załadowano: {file_name}", True, (0, 255, 0))
            else:
                info = font_text.render("Przeciągnij plik .WAV lub .MP3 do okna gry!", True, (200, 200, 200))
            screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 - 110))
            draw_button(screen, btn_start, "START", mouse_pos)
            draw_button(screen, btn_settings, "Ustawienia", mouse_pos)

        elif state == "SETTINGS":
            pygame.mouse.set_visible(True)
            title = font_title.render("USTAWIENIA", True, PLAYER_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 180))
            vol_text = font_btn.render(f"Głośność: {int(volume * 100)}%", True, (255, 255, 255))
            screen.blit(vol_text, (WIDTH//2 - vol_text.get_width()//2, HEIGHT//2 - 70))
            draw_button(screen, btn_vol_down, "-", mouse_pos)
            draw_button(screen, btn_vol_up, "+", mouse_pos)
            draw_button(screen, btn_res, f"Rozdzielczość: {WIDTH}x{HEIGHT}", mouse_pos)
            draw_button(screen, btn_fs, "Pełny ekran: WŁ" if is_fullscreen else "Pełny ekran: WYŁ", mouse_pos)
            draw_button(screen, btn_back, "Powrót", mouse_pos)

        elif state == "LOADING":
            pygame.mouse.set_visible(True)
            load_text = font_btn.render("Trwa analiza utworu...", True, (255, 255, 255))
            screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2, HEIGHT//2))
            pygame.display.flip() 
            
            current_file = music_file if music_file else generate_random_music()
            beat_times_ms = analyze_audio(current_file)
            
            if beat_times_ms is None:
                state = "ERROR"
            else:
                try:
                    pygame.mixer.music.load(current_file)
                    bullets.clear()
                    powerups.clear()
                    score = 0
                    beat_index = 0
                    multiplier_timer = 0
                    slowdown_timer = 0
                    boss = None
                    next_boss_score = 50000
                    state = "PLAYING"
                    pygame.mixer.music.play()
                except Exception as e:
                    print(e)
                    state = "ERROR"

        elif state == "PLAYING":
            pygame.mouse.set_visible(False)
            current_time = pygame.mixer.music.get_pos()
            mouse_x, mouse_y = mouse_pos
            
            if not pygame.mixer.music.get_busy() and current_time == -1:
                state = "GAME_OVER"

            # Trudność zmienia się co 10 000 pkt
            difficulty_tier = int(score // 10000)
            current_difficulty = 1.0 + (difficulty_tier * 0.15)
            
            # Spawn Bossa
            if score >= next_boss_score and boss is None:
                boss = Boss(hp_beats=40) # Boss musi przeżyć 40 bitów, żeby zostać "pokonanym"
            
            if boss:
                boss.update()
                boss.draw(screen)
            
            if beat_index < len(beat_times_ms) and current_time >= beat_times_ms[beat_index]:
                spawn_attack = True
                if current_time < 15000:
                    if beat_index % 2 != 0:
                        spawn_attack = False
                
                if spawn_attack:
                    if boss:
                        # Atakuje Boss
                        boss.hp -= 1
                        boss_attack = random.choice([1, 2])
                        if boss_attack == 1:
                            pattern_boss_spiral(bullets, boss.x, boss.y, current_difficulty, beat_index)
                        else:
                            pattern_boss_shotgun(bullets, boss.x, boss.y, mouse_x, mouse_y, current_difficulty)
                        
                        screen.fill((100, 0, 0)) # Błysk mocniejszy przy bossie
                        
                        if boss.hp <= 0:
                            score += 10000 # Premia za pokonanie bossa
                            next_boss_score += 50000
                            powerups.append(Powerup(boss.x - 30, boss.y, 'x2'))
                            powerups.append(Powerup(boss.x + 30, boss.y, 'slow'))
                            boss = None
                    else:
                        # Atakują zwykłe patterny
                        pattern_choice = random.randint(1, 4)
                        if pattern_choice == 1:
                            pattern_nova(bullets, current_difficulty)
                        elif pattern_choice == 2:
                            pattern_rain(bullets, current_difficulty)
                        elif pattern_choice == 3:
                            pattern_targeted(bullets, mouse_x, mouse_y, current_difficulty)
                        elif pattern_choice == 4:
                            pattern_circle_in(bullets, current_difficulty)
                        
                        if random.random() < 0.15:
                            p_type = random.choice(['x2', 'slow'])
                            powerups.append(Powerup(random.randint(50, WIDTH-50), -20, p_type))
                            
                        screen.fill((80, 0, 0))
                    
                beat_index += 1

            current_speed_mult = 0.5 if current_time < slowdown_timer else 1.0
            current_score_mult = 2.0 if current_time < multiplier_timer else 1.0

            for b in bullets[:]:
                b.update(current_speed_mult) 
                b.draw(screen)
                
                if b.x < -400 or b.x > WIDTH + 400 or b.y < -400 or b.y > HEIGHT + 400:
                    bullets.remove(b)
                    continue

                dist = math.hypot(b.x - mouse_x, b.y - mouse_y)
                if dist - b.radius - player_radius < 0:
                    pygame.mixer.music.stop()
                    state = "GAME_OVER"

            for p in powerups[:]:
                p.update()
                p.draw(screen)
                if p.y > HEIGHT + 50:
                    powerups.remove(p)
                    continue
                
                dist = math.hypot(p.x - mouse_x, p.y - mouse_y)
                if dist - p.radius - player_radius < 0:
                    if p.type == 'x2':
                        multiplier_timer = current_time + 5000 
                        score += 1000 
                    elif p.type == 'slow':
                        slowdown_timer = current_time + 5000
                        score += 500
                    powerups.remove(p)

            pygame.draw.circle(screen, PLAYER_COLOR, (mouse_x, mouse_y), player_radius)
            
            score += 10 * current_score_mult * current_difficulty
            
            score_text = font_text.render(f"Wynik: {int(score)}", True, (255, 255, 255))
            screen.blit(score_text, (10, 10))
            
            diff_text = font_small_bold.render(f"POZIOM: {difficulty_tier + 1} (Mnożnik: {current_difficulty:.2f}x)", True, (200, 200, 200))
            screen.blit(diff_text, (10, 40))
            
            hud_y = 10
            if current_time < multiplier_timer:
                time_left = (multiplier_timer - current_time) / 1000
                p_text = font_text.render(f"x2 PUNKTY: {time_left:.1f}s", True, (255, 215, 0))
                screen.blit(p_text, (WIDTH - p_text.get_width() - 10, hud_y))
                hud_y += 30
            if current_time < slowdown_timer:
                time_left = (slowdown_timer - current_time) / 1000
                p_text = font_text.render(f"SPOWOLNIENIE: {time_left:.1f}s", True, (0, 150, 255))
                screen.blit(p_text, (WIDTH - p_text.get_width() - 10, hud_y))

        elif state == "GAME_OVER":
            pygame.mouse.set_visible(True)
            over_text = font_title.render("KONIEC GRY", True, (255, 0, 85))
            score_txt = font_btn.render(f"Twój wynik: {int(score)}", True, (255, 255, 255))
            screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 80))
            screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, HEIGHT//2))
            draw_button(screen, btn_restart, "Zagraj ponownie", mouse_pos)
            draw_button(screen, btn_menu, "Wróć do menu", mouse_pos)

        elif state == "ERROR":
            pygame.mouse.set_visible(True)
            err_title = font_title.render("Błąd wczytywania!", True, (255, 100, 100))
            err_info = font_text.render("Nie udało się przeanalizować pliku.", True, (255, 255, 255))
            screen.blit(err_title, (WIDTH//2 - err_title.get_width()//2, HEIGHT//2 - 80))
            screen.blit(err_info, (WIDTH//2 - err_info.get_width()//2, HEIGHT//2))
            draw_button(screen, btn_back, "Powrót", mouse_pos)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()