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

# Ustawienia ekranu
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rytmiczny Bullet Hell z Powerupami")
clock = pygame.time.Clock()

# Czcionki
font_title = pygame.font.SysFont("Arial", 48, bold=True)
font_btn = pygame.font.SysFont("Arial", 28)
font_text = pygame.font.SysFont("Arial", 20)
font_small_bold = pygame.font.SysFont("Arial", 14, bold=True)

# Kolory
BG_COLOR = (17, 17, 17)
PLAYER_COLOR = (0, 255, 255)
BULLET_COLOR = (255, 0, 85)
BTN_COLOR = (50, 50, 50)
BTN_HOVER = (100, 100, 100)

class Bullet:
    def __init__(self, x, y, vx, vy, speed):
        self.x = x
        self.y = y
        self.vx = vx * speed
        self.vy = vy * speed
        self.radius = 6

    def update(self, speed_multiplier=1.0):
        # Modyfikator prędkości dla power-upa spowolnienia
        self.x += self.vx * speed_multiplier
        self.y += self.vy * speed_multiplier

    def draw(self, surface):
        pygame.draw.circle(surface, BULLET_COLOR, (int(self.x), int(self.y)), self.radius)

class Powerup:
    def __init__(self, x, y, p_type):
        self.x = x
        self.y = y
        self.type = p_type # 'x2' lub 'slow'
        self.radius = 12
        self.vy = 2.0 # Spadają z góry na dół
        
        if self.type == 'x2':
            self.color = (255, 215, 0) # Złoty
            self.text = "x2"
        else:
            self.color = (0, 150, 255) # Niebieski
            self.text = "S" # S jak Slow

    def update(self):
        self.y += self.vy

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Rysowanie literki/napisu na środku powerupa
        txt_surf = font_small_bold.render(self.text, True, (0, 0, 0))
        surface.blit(txt_surf, (self.x - txt_surf.get_width()//2, self.y - txt_surf.get_height()//2))

def create_bullet_nova(bullets):
    num_bullets = 12
    edges = [
        (random.randint(0, WIDTH), 0),
        (random.randint(0, WIDTH), HEIGHT),
        (0, random.randint(0, HEIGHT)),
        (WIDTH, random.randint(0, HEIGHT))
    ]
    spawn_point = random.choice(edges)
    for i in range(num_bullets):
        angle = (math.pi * 2 / num_bullets) * i
        vx = math.cos(angle)
        vy = math.sin(angle)
        speed = random.uniform(4.0, 6.0)
        bullets.append(Bullet(spawn_point[0], spawn_point[1], vx, vy, speed))

def generate_random_music(filepath="tymczasowa_muzyka.wav", duration=30):
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
    pygame.draw.rect(surface, BULLET_COLOR, rect, width=2, border_radius=8)
    text_surf = font_btn.render(text, True, (255, 255, 255))
    surface.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
    return rect.collidepoint(mouse_pos)

def main():
    state = "MENU"
    music_file = None
    beat_times_ms = []
    volume = 0.5
    pygame.mixer.music.set_volume(volume)
    
    # Zmienne do rozgrywki
    bullets = []
    powerups = []
    player_radius = 8
    score = 0
    beat_index = 0
    
    # Timery dla powerupów (w milisekundach wg. czasu utworu)
    multiplier_timer = 0
    slowdown_timer = 0
    
    btn_w, btn_h = 240, 50
    btn_start = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2, btn_w, btn_h)
    btn_settings = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 70, btn_w, btn_h)
    
    btn_vol_down = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 25, 50, 50)
    btn_vol_up = pygame.Rect(WIDTH//2 + 70, HEIGHT//2 - 25, 50, 50)
    btn_back = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 80, btn_w, btn_h)
    
    btn_restart = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 70, btn_w, btn_h)
    btn_menu = pygame.Rect(WIDTH//2 - btn_w//2, HEIGHT//2 + 140, btn_w, btn_h)

    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)
        
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
                        state = "PLAYING"
                        pygame.mixer.music.play()
                    elif btn_menu.collidepoint(mouse_pos):
                        state = "MENU"
                elif state == "ERROR":
                    if btn_back.collidepoint(mouse_pos):
                        state = "MENU"

        if state == "MENU":
            pygame.mouse.set_visible(True)
            title = font_title.render("RYTMICZNY BULLET HELL", True, BULLET_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 200))

            if music_file:
                file_name = os.path.basename(music_file)
                info = font_text.render(f"Załadowano: {file_name}", True, (0, 255, 0))
            else:
                info = font_text.render("Przeciągnij plik .WAV lub .MP3 do okna gry!", True, (200, 200, 200))
                info2 = font_text.render("(Jeśli klikniesz START bez pliku, wygenerujemy losowy utwór)", True, (100, 100, 100))
                screen.blit(info2, (WIDTH//2 - info2.get_width()//2, HEIGHT//2 - 80))
            
            screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 - 110))

            draw_button(screen, btn_start, "START", mouse_pos)
            draw_button(screen, btn_settings, "Ustawienia", mouse_pos)

        elif state == "SETTINGS":
            pygame.mouse.set_visible(True)
            title = font_title.render("USTAWIENIA", True, PLAYER_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            
            vol_text = font_btn.render(f"Głośność muzyki: {int(volume * 100)}%", True, (255, 255, 255))
            screen.blit(vol_text, (WIDTH//2 - vol_text.get_width()//2, HEIGHT//2 - 80))
            
            draw_button(screen, btn_vol_down, "-", mouse_pos)
            draw_button(screen, btn_vol_up, "+", mouse_pos)
            draw_button(screen, btn_back, "Powrót", mouse_pos)

        elif state == "LOADING":
            pygame.mouse.set_visible(True)
            load_text = font_btn.render("Trwa analiza utworu... Okno może przyciąć.", True, (255, 255, 255))
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
            
            # Reakcja na BIT
            if beat_index < len(beat_times_ms) and current_time >= beat_times_ms[beat_index]:
                create_bullet_nova(bullets)
                
                # Szansa na pojawienie się powerupa (15% szansy na każdym bicie)
                if random.random() < 0.15:
                    p_type = random.choice(['x2', 'slow'])
                    powerups.append(Powerup(random.randint(50, WIDTH-50), -20, p_type))
                    
                beat_index += 1
                screen.fill((80, 0, 0))

            # Sprawdzenie czy efekty powerupów są aktywne
            current_speed_mult = 0.5 if current_time < slowdown_timer else 1.0
            current_score_mult = 2.0 if current_time < multiplier_timer else 1.0

            # Aktualizacja pocisków
            for b in bullets[:]:
                b.update(current_speed_mult) # Wysyłamy mnożnik prędkości
                b.draw(screen)
                if b.x < -50 or b.x > WIDTH + 50 or b.y < -50 or b.y > HEIGHT + 50:
                    bullets.remove(b)
                    continue

                # Kolizja z graczem
                dist = math.hypot(b.x - mouse_x, b.y - mouse_y)
                if dist - b.radius - player_radius < 0:
                    pygame.mixer.music.stop()
                    state = "GAME_OVER"

            # Aktualizacja powerupów
            for p in powerups[:]:
                p.update()
                p.draw(screen)
                if p.y > HEIGHT + 50:
                    powerups.remove(p)
                    continue
                
                # Zbieranie powerupów
                dist = math.hypot(p.x - mouse_x, p.y - mouse_y)
                if dist - p.radius - player_radius < 0:
                    if p.type == 'x2':
                        multiplier_timer = current_time + 5000 # 5000 ms = 5 sekund
                    elif p.type == 'slow':
                        slowdown_timer = current_time + 5000
                    powerups.remove(p)

            # Rysowanie gracza
            pygame.draw.circle(screen, PLAYER_COLOR, (mouse_x, mouse_y), player_radius)
            
            # Naliczanie wyniku
            score += (1 / 60) * current_score_mult 
            score_text = font_text.render(f"Wynik: {int(score)}", True, (255, 255, 255))
            screen.blit(score_text, (10, 10))
            
            # Wyświetlanie informacji o aktywnych powerupach (HUD w prawym rogu)
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
            over_text = font_title.render("KONIEC GRY", True, BULLET_COLOR)
            score_txt = font_btn.render(f"Twój wynik: {int(score)}", True, (255, 255, 255))
            screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 80))
            screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, HEIGHT//2))
            
            draw_button(screen, btn_restart, "Zagraj ponownie", mouse_pos)
            draw_button(screen, btn_menu, "Wróć do menu", mouse_pos)
            
        elif state == "ERROR":
            pygame.mouse.set_visible(True)
            err_title = font_title.render("Błąd wczytywania!", True, (255, 100, 100))
            err_info = font_text.render("Nie udało się przeanalizować pliku (prawdopodobnie brak ffmpeg dla MP3).", True, (255, 255, 255))
            screen.blit(err_title, (WIDTH//2 - err_title.get_width()//2, HEIGHT//2 - 80))
            screen.blit(err_info, (WIDTH//2 - err_info.get_width()//2, HEIGHT//2))
            draw_button(screen, btn_back, "Powrót", mouse_pos)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()