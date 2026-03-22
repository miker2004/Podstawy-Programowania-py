import math
import random
import sys

import pygame


pygame.init()

WIDTH, HEIGHT = 1280, 720
WORLD_WIDTH, WORLD_HEIGHT = 2400, 1600
FPS = 60
GRID_SIZE = 64
RESOLUTIONS = [(1280, 720), (1920, 1080)]
current_resolution_index = 0
fullscreen_enabled = False

DAY_LENGTH = 45.0
NIGHT_LENGTH = 32.0
HUB_INTERACT_DISTANCE = 120
NODE_INTERACT_DISTANCE = 90

SKY_DAY = (186, 223, 255)
SKY_NIGHT = (25, 34, 58)
GROUND_DAY = (127, 181, 114)
GROUND_NIGHT = (52, 83, 64)
DIRT = (107, 81, 58)
WOOD = (124, 85, 46)
STONE = (113, 113, 125)
SCRAP = (146, 158, 170)
HUB_COLOR = (61, 101, 196)
NPC_COLOR = (162, 103, 214)
PANEL_COLOR = (21, 30, 40)
PANEL_BORDER = (88, 116, 140)
TEXT_LIGHT = (242, 246, 250)
TEXT_DARK = (18, 22, 25)
ENEMY_COLOR = (194, 69, 69)
BULLET_COLOR = (255, 225, 120)
TURRET_COLOR = (72, 73, 95)
WALL_COLOR = (158, 143, 126)
MINE_COLOR = (89, 126, 151)
TRAP_COLOR = (162, 90, 52)
WORKSHOP_COLOR = (93, 145, 109)
CRATE_COLOR = (202, 161, 79)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Colony Lite")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("arial", 42, bold=True)
font_ui = pygame.font.SysFont("arial", 24, bold=True)
font_small = pygame.font.SysFont("arial", 18)

vec = pygame.Vector2


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_text(surface, text, font, color, x, y):
    surface.blit(font.render(text, True, color), (x, y))


def distance(a, b):
    return (a - b).length()


def update_display_mode():
    global screen, WIDTH, HEIGHT
    WIDTH, HEIGHT = RESOLUTIONS[current_resolution_index]
    flags = pygame.FULLSCREEN if fullscreen_enabled else 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)


def snap_to_grid(world_pos):
    snapped_x = round(world_pos.x / GRID_SIZE) * GRID_SIZE
    snapped_y = round(world_pos.y / GRID_SIZE) * GRID_SIZE
    return vec(snapped_x, snapped_y)


def draw_button(surface, rect, text, hovered):
    fill = (74, 112, 150) if hovered else PANEL_COLOR
    border = (168, 214, 255) if hovered else PANEL_BORDER
    pygame.draw.rect(surface, fill, rect, border_radius=14)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=14)
    label = font_ui.render(text, True, TEXT_LIGHT)
    surface.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))


def get_main_menu_buttons():
    button_width = min(360, WIDTH - 80)
    button_height = 62
    x = (WIDTH - button_width) // 2
    start_y = HEIGHT // 2 - 10
    return {
        "start": pygame.Rect(x, start_y, button_width, button_height),
        "settings": pygame.Rect(x, start_y + 82, button_width, button_height),
        "quit": pygame.Rect(x, start_y + 164, button_width, button_height),
    }


def get_pause_menu_buttons():
    button_width = min(360, WIDTH - 120)
    button_height = 58
    x = (WIDTH - button_width) // 2
    start_y = HEIGHT // 2 - 20
    return {
        "settings": pygame.Rect(x, start_y, button_width, button_height),
        "main_menu": pygame.Rect(x, start_y + 78, button_width, button_height),
        "resume": pygame.Rect(x, start_y + 156, button_width, button_height),
    }


def get_settings_buttons():
    panel_width = min(700, WIDTH - 80)
    panel_height = min(360, HEIGHT - 110)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
    button_width = min(360, panel.width - 48)
    button_height = 54
    x = panel.x + 24
    start_y = panel.y + 150
    return {
        "resolution": pygame.Rect(x, start_y, button_width, button_height),
        "fullscreen": pygame.Rect(x, start_y + 68, button_width, button_height),
        "back": pygame.Rect(x, start_y + 136, button_width, button_height),
    }


class Player:
    def __init__(self, pos):
        self.pos = vec(pos)
        self.radius = 20
        self.speed_level = 0
        self.gather_level = 0
        self.attack_level = 0
        self.max_hp = 120
        self.hp = self.max_hp
        self.attack_cooldown = 0.0
        self.gather_cooldown = 0.0
        self.direction = vec(1, 0)

    @property
    def speed(self):
        return 230 + self.speed_level * 22

    @property
    def attack_damage(self):
        return 22 + self.attack_level * 8

    @property
    def gather_damage(self):
        return 20 + self.gather_level * 10

    def update(self, dt, game):
        move = vec(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1

        if move.length_squared() > 0:
            move = move.normalize()
            self.direction = move

        previous_pos = vec(self.pos)
        self.pos.x += move.x * self.speed * dt
        if game.point_hits_solid(self.pos, self.radius):
            self.pos.x = previous_pos.x

        self.pos.y += move.y * self.speed * dt
        if game.point_hits_solid(self.pos, self.radius):
            self.pos.y = previous_pos.y

        self.pos.x = clamp(self.pos.x, 40, WORLD_WIDTH - 40)
        self.pos.y = clamp(self.pos.y, 40, WORLD_HEIGHT - 40)

        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.gather_cooldown = max(0.0, self.gather_cooldown - dt)

    def damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def heal_full(self):
        self.hp = self.max_hp

    def draw(self, surface, camera):
        screen_pos = self.pos - camera
        pygame.draw.circle(surface, (0, 0, 0), (int(screen_pos.x + 4), int(screen_pos.y + 6)), self.radius)
        pygame.draw.circle(surface, (69, 180, 246), (int(screen_pos.x), int(screen_pos.y)), self.radius)
        head_pos = (int(screen_pos.x + self.direction.x * 6), int(screen_pos.y - 4 + self.direction.y * 6))
        pygame.draw.circle(surface, (255, 255, 255), head_pos, 6)


class BaseHub:
    def __init__(self, pos):
        self.pos = vec(pos)
        self.size = 130
        self.level = 1
        self.max_hp = 280
        self.hp = self.max_hp

    def rect(self):
        return pygame.Rect(
            int(self.pos.x - self.size // 2),
            int(self.pos.y - self.size // 2),
            self.size,
            self.size,
        )

    def damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def repair_full(self):
        self.hp = self.max_hp

    def upgrade(self):
        self.level += 1
        self.max_hp += 80
        self.hp = self.max_hp

    def draw(self, surface, camera):
        rect = self.rect().move(-camera.x, -camera.y)
        pygame.draw.rect(surface, HUB_COLOR, rect, border_radius=18)
        pygame.draw.rect(surface, (220, 235, 255), rect.inflate(-44, -44), border_radius=14)
        hp_ratio = self.hp / self.max_hp if self.max_hp else 0
        bar = pygame.Rect(rect.x, rect.y - 18, rect.width, 12)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * hp_ratio), bar.height)
        pygame.draw.rect(surface, (35, 50, 60), bar, border_radius=6)
        pygame.draw.rect(surface, (67, 221, 117), fill, border_radius=6)


class ResourceNode:
    def __init__(self, kind, pos):
        self.kind = kind
        self.pos = vec(pos)
        self.dead = False

        if kind == "tree":
            self.radius = 30
            self.color = (48, 130, 54)
            self.hp = 55
            self.loot = {"wood": 18}
        elif kind == "rock":
            self.radius = 26
            self.color = STONE
            self.hp = 65
            self.loot = {"stone": 18}
        else:
            self.radius = 22
            self.color = SCRAP
            self.hp = 50
            self.loot = {"scrap": 14}

    def gather(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.dead = True
            return dict(self.loot)
        return {}

    def draw(self, surface, camera):
        p = self.pos - camera
        if self.kind == "tree":
            pygame.draw.rect(surface, WOOD, (p.x - 8, p.y + 8, 16, 30), border_radius=6)
            pygame.draw.circle(surface, self.color, (int(p.x), int(p.y - 4)), self.radius)
        elif self.kind == "rock":
            pygame.draw.circle(surface, self.color, (int(p.x), int(p.y)), self.radius)
            pygame.draw.circle(surface, (145, 145, 160), (int(p.x - 6), int(p.y - 6)), self.radius // 2)
        else:
            rect = pygame.Rect(int(p.x - 18), int(p.y - 18), 36, 36)
            pygame.draw.rect(surface, self.color, rect, border_radius=7)
            pygame.draw.rect(surface, (70, 80, 90), rect.inflate(-12, -12), border_radius=5)


class Structure:
    def __init__(self, kind, pos):
        self.kind = kind
        self.pos = vec(pos)
        self.cooldown = 0.0
        self.resource_timer = 10.0
        self.dead = False
        self.effect_timer = 0.0

        if kind == "wall":
            self.size = 52
            self.max_hp = 180
        elif kind == "turret":
            self.size = 58
            self.max_hp = 140
        elif kind == "trap":
            self.size = 48
            self.max_hp = 90
        elif kind == "workshop":
            self.size = 64
            self.max_hp = 160
        else:
            self.size = 54
            self.max_hp = 120

        self.hp = self.max_hp

    def rect(self):
        return pygame.Rect(
            int(self.pos.x - self.size // 2),
            int(self.pos.y - self.size // 2),
            self.size,
            self.size,
        )

    def damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.dead = True

    def update(self, dt, game):
        if self.kind == "turret":
            self.cooldown = max(0.0, self.cooldown - dt)
            if self.cooldown <= 0:
                target = self.find_target(game.enemies)
                if target is not None:
                    direction = target.pos - self.pos
                    if direction.length_squared() > 0:
                        game.projectiles.append(Projectile(self.pos, direction.normalize() * 520, 28 + game.hub.level * 2))
                        self.cooldown = 0.45
        elif self.kind == "mine":
            self.resource_timer -= dt
            if self.resource_timer <= 0:
                game.resources["stone"] += 1
                game.resources["scrap"] += 1
                self.resource_timer = max(5.5, 10.0 - game.hub.level * 0.4)
        elif self.kind == "workshop":
            self.resource_timer -= dt
            if self.resource_timer <= 0:
                game.resources["wood"] += 1
                game.resources["scrap"] += 1
                self.resource_timer = max(6.0, 11.0 - game.hub.level * 0.45)
        elif self.kind == "trap":
            self.effect_timer = max(0.0, self.effect_timer - dt)

    def find_target(self, enemies):
        best_target = None
        best_distance = 260
        for enemy in enemies:
            current = distance(enemy.pos, self.pos)
            if current < best_distance:
                best_distance = current
                best_target = enemy
        return best_target

    def draw(self, surface, camera):
        rect = self.rect().move(-camera.x, -camera.y)
        if self.kind == "wall":
            pygame.draw.rect(surface, WALL_COLOR, rect, border_radius=10)
            pygame.draw.rect(surface, (191, 176, 154), rect.inflate(-18, -18), border_radius=6)
        elif self.kind == "turret":
            pygame.draw.rect(surface, TURRET_COLOR, rect, border_radius=14)
            pygame.draw.circle(surface, (220, 230, 240), rect.center, 12)
            pygame.draw.rect(surface, (220, 230, 240), (rect.centerx - 4, rect.centery - 22, 8, 22), border_radius=4)
        elif self.kind == "trap":
            pygame.draw.rect(surface, TRAP_COLOR, rect, border_radius=8)
            pygame.draw.line(surface, (240, 230, 205), (rect.x + 8, rect.centery), (rect.right - 8, rect.centery), 3)
            pygame.draw.line(surface, (240, 230, 205), (rect.centerx, rect.y + 8), (rect.centerx, rect.bottom - 8), 3)
        elif self.kind == "workshop":
            pygame.draw.rect(surface, WORKSHOP_COLOR, rect, border_radius=14)
            pygame.draw.rect(surface, (221, 239, 222), rect.inflate(-18, -18), border_radius=8)
            pygame.draw.circle(surface, (55, 75, 62), rect.center, 10)
        else:
            pygame.draw.rect(surface, MINE_COLOR, rect, border_radius=12)
            pygame.draw.rect(surface, (210, 227, 239), rect.inflate(-18, -18), border_radius=8)

        bar = pygame.Rect(rect.x, rect.y - 12, rect.width, 8)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * (self.hp / self.max_hp)), bar.height)
        pygame.draw.rect(surface, (30, 40, 48), bar, border_radius=4)
        pygame.draw.rect(surface, (84, 224, 110), fill, border_radius=4)


class Enemy:
    def __init__(self, pos, wave_level, kind):
        self.pos = vec(pos)
        self.kind = kind
        self.radius = 18
        self.ranged = False
        self.attack_timer = 0.0

        if kind == "brute":
            self.max_hp = 78 + wave_level * 13
            self.speed = 52 + wave_level * 4
            self.damage = 10 + wave_level * 2
            self.color = (177, 76, 76)
        elif kind == "spitter":
            self.max_hp = 40 + wave_level * 8
            self.speed = 62 + wave_level * 4
            self.damage = 7 + wave_level * 2
            self.color = (121, 209, 118)
            self.ranged = True
        else:
            self.max_hp = 50 + wave_level * 10
            self.speed = 68 + wave_level * 5
            self.damage = 6 + wave_level * 2
            self.color = ENEMY_COLOR

        self.hp = self.max_hp

    def update(self, dt, game):
        self.attack_timer = max(0.0, self.attack_timer - dt)
        target, target_type = self.pick_target(game)
        direction = target - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()

        if target_type == "hub":
            stop_distance = 72
        elif target_type == "structure":
            stop_distance = 44 if not self.ranged else 140
        else:
            stop_distance = 28 if not self.ranged else 150

        if distance(self.pos, target) > stop_distance:
            self.pos += direction * self.speed * dt
        elif self.attack_timer <= 0:
            self.attack_timer = 1.1 if self.ranged else 0.85
            if self.ranged:
                shot_direction = target - self.pos
                if shot_direction.length_squared() > 0:
                    game.enemy_projectiles.append(
                        Projectile(self.pos, shot_direction.normalize() * 360, self.damage, friendly=False)
                    )
            elif target_type == "hub":
                game.hub.damage(self.damage)
            elif target_type == "structure":
                structure = game.find_structure_by_position(target)
                if structure is not None:
                    structure.damage(self.damage)
            else:
                game.player.damage(self.damage)

    def pick_target(self, game):
        best_target = game.hub.pos
        best_distance = distance(self.pos, best_target)
        target_type = "hub"

        player_distance = distance(self.pos, game.player.pos)
        if self.kind != "brute" and player_distance < best_distance * 0.8:
            best_target = game.player.pos
            best_distance = player_distance
            target_type = "player"

        for structure in game.structures:
            current = distance(self.pos, structure.pos)
            priority_bonus = -38 if self.kind == "brute" and structure.kind == "wall" else 0
            if current + priority_bonus < best_distance:
                best_target = structure.pos
                best_distance = current + priority_bonus
                target_type = "structure"

        return best_target, target_type

    def damage_me(self, amount):
        self.hp -= amount

    def dead(self):
        return self.hp <= 0

    def draw(self, surface, camera):
        p = self.pos - camera
        pygame.draw.circle(surface, (0, 0, 0), (int(p.x + 3), int(p.y + 4)), self.radius)
        pygame.draw.circle(surface, self.color, (int(p.x), int(p.y)), self.radius)
        bar = pygame.Rect(int(p.x - 22), int(p.y - 32), 44, 7)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * (self.hp / self.max_hp)), bar.height)
        pygame.draw.rect(surface, (35, 40, 45), bar, border_radius=4)
        pygame.draw.rect(surface, (235, 95, 95), fill, border_radius=4)


class Projectile:
    def __init__(self, pos, velocity, damage, friendly=True):
        self.pos = vec(pos)
        self.velocity = vec(velocity)
        self.damage = damage
        self.friendly = friendly
        self.dead = False

    def update(self, dt, game):
        self.pos += self.velocity * dt
        if self.friendly:
            for enemy in game.enemies:
                if distance(self.pos, enemy.pos) < enemy.radius + 6:
                    enemy.damage_me(self.damage)
                    self.dead = True
                    return
        else:
            if distance(self.pos, game.player.pos) < game.player.radius + 5:
                game.player.damage(self.damage)
                self.dead = True
                return
            for structure in game.structures:
                if structure.rect().collidepoint(self.pos.x, self.pos.y):
                    structure.damage(self.damage)
                    self.dead = True
                    return
            if game.hub.rect().collidepoint(self.pos.x, self.pos.y):
                game.hub.damage(self.damage)
                self.dead = True
                return

        if (
            self.pos.x < 0
            or self.pos.x > WORLD_WIDTH
            or self.pos.y < 0
            or self.pos.y > WORLD_HEIGHT
        ):
            self.dead = True

    def draw(self, surface, camera):
        p = self.pos - camera
        pygame.draw.circle(surface, BULLET_COLOR, (int(p.x), int(p.y)), 5)


class Crate:
    def __init__(self, pos):
        self.pos = vec(pos)
        self.radius = 22
        self.opened = False

    def loot(self):
        self.opened = True
        return {
            "wood": random.randint(10, 18),
            "stone": random.randint(8, 14),
            "scrap": random.randint(6, 12),
        }

    def draw(self, surface, camera):
        p = self.pos - camera
        rect = pygame.Rect(int(p.x - 18), int(p.y - 18), 36, 36)
        pygame.draw.rect(surface, CRATE_COLOR, rect, border_radius=7)
        pygame.draw.rect(surface, (120, 84, 38), rect.inflate(-12, -12), border_radius=4)


class Npc:
    def __init__(self, name, pos):
        self.name = name
        self.pos = vec(pos)
        self.radius = 18

    def draw(self, surface, camera):
        p = self.pos - camera
        pygame.draw.circle(surface, (0, 0, 0), (int(p.x + 3), int(p.y + 4)), self.radius)
        pygame.draw.circle(surface, NPC_COLOR, (int(p.x), int(p.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(p.x), int(p.y - 4)), 6)


class Quest:
    def __init__(self, key, title, description, requirement_type, requirement_value, reward, tip):
        self.key = key
        self.title = title
        self.description = description
        self.requirement_type = requirement_type
        self.requirement_value = requirement_value
        self.reward = reward
        self.tip = tip
        self.completed = False
        self.claimed = False

    def progress(self, game):
        if self.requirement_type == "collect_wood":
            return game.stats["wood_collected"]
        if self.requirement_type == "build_turret":
            return game.stats["turrets_built"]
        if self.requirement_type == "survive_night":
            return game.stats["nights_survived"]
        if self.requirement_type == "build_workshop":
            return game.stats["workshops_built"]
        if self.requirement_type == "kill_enemies":
            return game.stats["enemies_killed"]
        return 0

    def check_complete(self, game):
        if not self.completed and self.progress(game) >= self.requirement_value:
            self.completed = True
        return self.completed


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player((WORLD_WIDTH / 2, WORLD_HEIGHT / 2 + 160))
        self.hub = BaseHub((WORLD_WIDTH / 2, WORLD_HEIGHT / 2))
        self.resources = {"wood": 60, "stone": 40, "scrap": 24}
        self.structures = []
        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.nodes = self.generate_nodes()
        self.crates = self.generate_crates()
        self.npc = Npc("Mechanik Olek", (WORLD_WIDTH / 2 + 170, WORLD_HEIGHT / 2 - 20))
        self.quests = self.create_quests()
        self.selected_build = "wall"
        self.phase = "day"
        self.phase_timer = DAY_LENGTH
        self.day_index = 1
        self.message = "Dzien 1: zbieraj surowce, buduj i ulepsz HUB."
        self.message_timer = 8.0
        self.upgrade_open = False
        self.quest_open = False
        self.menu_state = "menu"
        self.settings_return_state = "menu"
        self.game_over = False
        self.stats = {
            "wood_collected": 0,
            "turrets_built": 0,
            "workshops_built": 0,
            "nights_survived": 0,
            "enemies_killed": 0,
        }

    def create_quests(self):
        return [
            Quest("wood", "Pierwsze zapasy", "Zbierz drewno do rozbudowy kolonii.", "collect_wood", 40, {"stone": 20, "scrap": 10}, "Podejdz do drzew i naciskaj E."),
            Quest("turret", "Pierwsza obrona", "Postaw wiezyczke obronna.", "build_turret", 1, {"wood": 25, "stone": 15}, "Wybierz 2 i kliknij obok bazy."),
            Quest("night", "Przetrwaj noc", "Przetrwaj pierwszy nocny atak.", "survive_night", 1, {"scrap": 25, "wood": 15}, "Buduj przed zmrokiem i walcz Spacja."),
            Quest("workshop", "Automatyzacja", "Postaw warsztat produkcyjny.", "build_workshop", 1, {"stone": 20, "scrap": 20}, "Wybierz 5 i buduj blisko bazy."),
            Quest("kills", "Oczyszczanie terenu", "Pokonaj 12 wrogow.", "kill_enemies", 12, {"wood": 30, "stone": 30, "scrap": 30}, "Turrety i pulapki pomagaja w obronie."),
        ]

    def generate_nodes(self):
        nodes = []
        safe_zone = vec(self.hub.pos)
        for _ in range(26):
            nodes.append(ResourceNode("tree", self.random_world_position(safe_zone, 220)))
        for _ in range(18):
            nodes.append(ResourceNode("rock", self.random_world_position(safe_zone, 220)))
        for _ in range(16):
            nodes.append(ResourceNode("scrap", self.random_world_position(safe_zone, 260)))
        return nodes

    def generate_crates(self):
        return [Crate(self.random_world_position(self.hub.pos, 260)) for _ in range(9)]

    def random_world_position(self, center, min_distance):
        while True:
            point = vec(random.randint(80, WORLD_WIDTH - 80), random.randint(80, WORLD_HEIGHT - 80))
            if distance(point, center) > min_distance and not self.point_hits_solid(point, 28):
                return point

    def point_hits_solid(self, point, radius):
        if self.hub.rect().inflate(radius * 2, radius * 2).collidepoint(point.x, point.y):
            return True

        for structure in self.structures:
            if structure.rect().inflate(radius * 2, radius * 2).collidepoint(point.x, point.y):
                return True

        return False

    def respawn_resources(self):
        minimums = {"tree": 24, "rock": 16, "scrap": 14}
        counts = {"tree": 0, "rock": 0, "scrap": 0}

        for node in self.nodes:
            counts[node.kind] += 1

        for kind, minimum in minimums.items():
            while counts[kind] < minimum:
                extra_distance = 230 if kind != "scrap" else 260
                self.nodes.append(ResourceNode(kind, self.random_world_position(self.hub.pos, extra_distance)))
                counts[kind] += 1

    def update(self, dt):
        if self.game_over:
            return

        self.player.update(dt, self)
        self.phase_timer -= dt
        self.message_timer = max(0.0, self.message_timer - dt)

        if self.phase_timer <= 0:
            if self.phase == "day":
                self.start_night()
            else:
                self.start_day()

        for structure in self.structures[:]:
            structure.update(dt, self)
            if structure.dead:
                self.structures.remove(structure)

        for enemy in self.enemies[:]:
            enemy.update(dt, self)
            self.apply_trap_effects(enemy)
            if enemy.dead():
                self.resources["scrap"] += 3
                self.stats["enemies_killed"] += 1
                self.enemies.remove(enemy)

        for projectile in self.projectiles[:]:
            projectile.update(dt, self)
            if projectile.dead:
                self.projectiles.remove(projectile)

        for projectile in self.enemy_projectiles[:]:
            projectile.update(dt, self)
            if projectile.dead:
                self.enemy_projectiles.remove(projectile)

        if self.phase == "night" and random.random() < 0.026 + self.day_index * 0.0018:
            self.spawn_enemy()

        self.nodes = [node for node in self.nodes if not node.dead]
        self.crates = [crate for crate in self.crates if not crate.opened]
        self.update_quests()

        if self.hub.hp <= 0 or self.player.hp <= 0:
            self.game_over = True

    def start_night(self):
        self.phase = "night"
        self.phase_timer = NIGHT_LENGTH
        self.upgrade_open = False
        self.message = f"Noc {self.day_index}: bron HUB-u przed napastnikami."
        self.message_timer = 7.0

    def start_day(self):
        self.phase = "day"
        self.phase_timer = DAY_LENGTH
        self.day_index += 1
        self.stats["nights_survived"] += 1
        self.player.heal_full()
        self.hub.hp = min(self.hub.max_hp, self.hub.hp + 35 + self.hub.level * 8)
        self.message = f"Dzien {self.day_index}: naprawiaj, buduj i rozwijaj baze."
        self.message_timer = 7.0
        self.respawn_resources()
        self.spawn_day_loot()

    def spawn_day_loot(self):
        for _ in range(2):
            self.crates.append(Crate(self.random_world_position(self.hub.pos, 250)))
        for _ in range(4):
            kind = random.choice(["tree", "rock", "scrap"])
            self.nodes.append(ResourceNode(kind, self.random_world_position(self.hub.pos, 220)))

    def spawn_enemy(self):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            pos = vec(random.randint(0, WORLD_WIDTH), -30)
        elif side == "bottom":
            pos = vec(random.randint(0, WORLD_WIDTH), WORLD_HEIGHT + 30)
        elif side == "left":
            pos = vec(-30, random.randint(0, WORLD_HEIGHT))
        else:
            pos = vec(WORLD_WIDTH + 30, random.randint(0, WORLD_HEIGHT))
        kind = random.choices(
            ["raider", "brute", "spitter"],
            weights=[68, max(12, 20 + self.day_index), max(8, 10 + self.day_index // 2)],
        )[0]
        self.enemies.append(Enemy(pos, self.day_index, kind))

    def attempt_gather_or_open(self):
        if self.player.gather_cooldown > 0:
            return

        if distance(self.npc.pos, self.player.pos) < HUB_INTERACT_DISTANCE:
            self.quest_open = not self.quest_open
            self.upgrade_open = False
            return

        best_node = None
        best_distance = NODE_INTERACT_DISTANCE
        for node in self.nodes:
            current = distance(node.pos, self.player.pos)
            if current < best_distance:
                best_distance = current
                best_node = node

        if best_node is not None:
            rewards = best_node.gather(self.player.gather_damage)
            for key, value in rewards.items():
                self.resources[key] += value
                if key == "wood":
                    self.stats["wood_collected"] += value
            self.player.gather_cooldown = 0.35
            self.message = "Zebrano surowce."
            self.message_timer = 1.4
            return

        for crate in self.crates:
            if distance(crate.pos, self.player.pos) < NODE_INTERACT_DISTANCE:
                rewards = crate.loot()
                for key, value in rewards.items():
                    self.resources[key] += value
                self.message = "Skrzynia otwarta."
                self.message_timer = 1.8
                return

        if distance(self.hub.pos, self.player.pos) < HUB_INTERACT_DISTANCE:
            self.upgrade_open = not self.upgrade_open
            self.quest_open = False
            return

    def attempt_attack(self):
        if self.player.attack_cooldown > 0:
            return

        best_enemy = None
        best_distance = 88
        for enemy in self.enemies:
            current = distance(enemy.pos, self.player.pos)
            if current < best_distance:
                best_distance = current
                best_enemy = enemy

        if best_enemy is not None:
            best_enemy.damage_me(self.player.attack_damage)
            self.player.attack_cooldown = 0.28
            self.message = "Atak trafiony."
            self.message_timer = 0.8

    def building_cost(self, kind):
        if kind == "wall":
            return {"wood": 18, "stone": 8}
        if kind == "turret":
            return {"wood": 12, "stone": 24, "scrap": 18}
        if kind == "trap":
            return {"wood": 8, "stone": 10, "scrap": 6}
        if kind == "workshop":
            return {"wood": 26, "stone": 24, "scrap": 22}
        return {"wood": 10, "stone": 18, "scrap": 14}

    def can_afford(self, cost):
        return all(self.resources[key] >= value for key, value in cost.items())

    def pay_cost(self, cost):
        for key, value in cost.items():
            self.resources[key] -= value

    def get_build_candidate(self, mouse_pos, camera):
        world_pos = snap_to_grid(vec(mouse_pos) + camera)
        return Structure(self.selected_build, world_pos)

    def validate_structure_placement(self, candidate):
        if self.phase == "night":
            return False, "Budowanie jest zablokowane w nocy."

        if distance(candidate.pos, self.player.pos) > 170:
            return False, "Buduj blisko postaci."

        if distance(candidate.pos, self.hub.pos) < 110:
            return False, "Za blisko HUB-u."

        candidate_rect = candidate.rect()
        if candidate_rect.left < 24 or candidate_rect.top < 24:
            return False, "Za blisko krawedzi mapy."
        if candidate_rect.right > WORLD_WIDTH - 24 or candidate_rect.bottom > WORLD_HEIGHT - 24:
            return False, "Za blisko krawedzi mapy."

        player_block_rect = pygame.Rect(
            int(self.player.pos.x - self.player.radius - 8),
            int(self.player.pos.y - self.player.radius - 8),
            int((self.player.radius + 8) * 2),
            int((self.player.radius + 8) * 2),
        )
        if candidate_rect.colliderect(player_block_rect):
            return False, "Nie mozesz postawic budynku na postaci."

        for structure in self.structures:
            if candidate_rect.colliderect(structure.rect().inflate(2, 2)):
                return False, "Brak miejsca na budynek."

        if candidate_rect.colliderect(self.hub.rect().inflate(18, 18)):
            return False, "Brak miejsca na budynek."

        cost = self.building_cost(self.selected_build)
        if not self.can_afford(cost):
            return False, "Za malo surowcow."

        return True, ""

    def place_structure(self, mouse_pos, camera):
        candidate = self.get_build_candidate(mouse_pos, camera)
        valid, reason = self.validate_structure_placement(candidate)
        if not valid:
            self.message = reason
            self.message_timer = 1.5
            return

        cost = self.building_cost(self.selected_build)
        self.pay_cost(cost)
        self.structures.append(candidate)
        self.message = f"Postawiono: {self.selected_build}."
        self.message_timer = 1.4
        if self.selected_build == "turret":
            self.stats["turrets_built"] += 1
        elif self.selected_build == "workshop":
            self.stats["workshops_built"] += 1

    def do_upgrade(self, choice):
        if choice == 1:
            cost = {"wood": 30, "stone": 30, "scrap": 24}
            if self.can_afford(cost):
                self.pay_cost(cost)
                self.hub.upgrade()
                self.message = "HUB ulepszony."
            else:
                self.message = "Za malo surowcow na ulepszenie HUB-u."
        elif choice == 2:
            cost = {"scrap": 18, "stone": 10}
            if self.can_afford(cost):
                self.pay_cost(cost)
                self.player.speed_level += 1
                self.message = "Predkosc zwiekszona."
            else:
                self.message = "Brakuje surowcow na szybkosc."
        elif choice == 3:
            cost = {"wood": 16, "scrap": 16}
            if self.can_afford(cost):
                self.pay_cost(cost)
                self.player.gather_level += 1
                self.message = "Zbieranie ulepszone."
            else:
                self.message = "Brakuje surowcow na zbieranie."
        elif choice == 4:
            cost = {"stone": 12, "scrap": 20}
            if self.can_afford(cost):
                self.pay_cost(cost)
                self.player.attack_level += 1
                self.message = "Bron ulepszona."
            else:
                self.message = "Brakuje surowcow na bron."
        elif choice == 5:
            cost = {"wood": 18, "stone": 18}
            if self.can_afford(cost):
                self.pay_cost(cost)
                self.hub.repair_full()
                self.player.heal_full()
                self.message = "Naprawy zakonczone."
            else:
                self.message = "Brakuje surowcow na naprawe."

        self.message_timer = 2.0

    def update_quests(self):
        for quest in self.quests:
            if quest.check_complete(self) and not quest.claimed:
                quest.claimed = True
                for key, value in quest.reward.items():
                    self.resources[key] += value
                self.message = f"Quest ukonczony: {quest.title}"
                self.message_timer = 3.2

    def active_quest(self):
        for quest in self.quests:
            if not quest.completed:
                return quest
        return None

    def apply_trap_effects(self, enemy):
        for structure in self.structures:
            if structure.kind == "trap" and distance(structure.pos, enemy.pos) < 34 and structure.effect_timer <= 0:
                enemy.damage_me(26 + self.hub.level * 2)
                structure.effect_timer = 1.1
                return

    def context_hint(self):
        if self.quest_open:
            return "Panel questow otwarty. Podejdz do NPC i nacisnij E, aby zamknac."
        if self.upgrade_open:
            return "Wybierz upgrade 1-5 albo nacisnij E, aby zamknac panel HUB-u."
        active = self.active_quest()
        if active is not None:
            return f"Quest: {active.title}. {active.tip}"
        if self.phase == "day":
            return "Dzien: zbieraj surowce, buduj i przygotuj obrone przed noca."
        return "Noc: bron HUB-u, cofaj sie za mury i korzystaj z turretow oraz pulapek."

    def find_structure_by_position(self, pos):
        for structure in self.structures:
            if structure.pos == pos:
                return structure
        return None

    def camera(self):
        x = clamp(self.player.pos.x - WIDTH / 2, 0, WORLD_WIDTH - WIDTH)
        y = clamp(self.player.pos.y - HEIGHT / 2, 0, WORLD_HEIGHT - HEIGHT)
        return vec(x, y)


def mix_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_world(surface, game, camera):
    if game.phase == "day":
        sky = SKY_DAY
        ground = GROUND_DAY
    else:
        t = 1.0 - game.phase_timer / NIGHT_LENGTH
        sky = mix_color(SKY_DAY, SKY_NIGHT, 0.75 + t * 0.2)
        ground = mix_color(GROUND_DAY, GROUND_NIGHT, 0.8)

    surface.fill(sky)
    pygame.draw.rect(surface, ground, (0, 0, WIDTH, HEIGHT))

    for x in range(0, WORLD_WIDTH + 1, 120):
        start = vec(x, 0) - camera
        end = vec(x, WORLD_HEIGHT) - camera
        pygame.draw.line(surface, mix_color(ground, TEXT_DARK, 0.12), start, end, 1)

    for y in range(0, WORLD_HEIGHT + 1, 120):
        start = vec(0, y) - camera
        end = vec(WORLD_WIDTH, y) - camera
        pygame.draw.line(surface, mix_color(ground, TEXT_DARK, 0.12), start, end, 1)

    for x in range(0, WORLD_WIDTH + 1, GRID_SIZE):
        start = vec(x, 0) - camera
        end = vec(x, WORLD_HEIGHT) - camera
        pygame.draw.line(surface, mix_color(ground, TEXT_LIGHT, 0.18), start, end, 1)

    for y in range(0, WORLD_HEIGHT + 1, GRID_SIZE):
        start = vec(0, y) - camera
        end = vec(WORLD_WIDTH, y) - camera
        pygame.draw.line(surface, mix_color(ground, TEXT_LIGHT, 0.18), start, end, 1)

    for node in game.nodes:
        node.draw(surface, camera)

    for crate in game.crates:
        crate.draw(surface, camera)

    game.hub.draw(surface, camera)
    game.npc.draw(surface, camera)

    for structure in game.structures:
        structure.draw(surface, camera)

    for projectile in game.projectiles:
        projectile.draw(surface, camera)

    for projectile in game.enemy_projectiles:
        projectile.draw(surface, camera)

    for enemy in game.enemies:
        enemy.draw(surface, camera)

    game.player.draw(surface, camera)

    if game.phase == "night":
        dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark.fill((12, 18, 30, 100))
        pygame.draw.circle(dark, (0, 0, 0, 0), (int(game.player.pos.x - camera.x), int(game.player.pos.y - camera.y)), 130)
        pygame.draw.circle(dark, (0, 0, 0, 0), (int(game.hub.pos.x - camera.x), int(game.hub.pos.y - camera.y)), 170)
        surface.blit(dark, (0, 0))


def draw_build_preview(surface, game, camera, mouse_pos):
    if game.game_over or game.upgrade_open or game.quest_open or game.menu_state == "settings" or game.phase == "night":
        return

    candidate = game.get_build_candidate(mouse_pos, camera)
    valid, _ = game.validate_structure_placement(candidate)
    rect = candidate.rect().move(-camera.x, -camera.y)

    preview = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    fill_color = (90, 215, 120, 90) if valid else (220, 85, 85, 90)
    border_color = (120, 255, 150) if valid else (255, 120, 120)
    pygame.draw.rect(preview, fill_color, preview.get_rect(), border_radius=10)
    pygame.draw.rect(preview, border_color, preview.get_rect(), width=3, border_radius=10)
    surface.blit(preview, rect.topleft)


def draw_top_ui(surface, game):
    panel = pygame.Rect(16, 14, min(420, WIDTH - 32), 142)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=14)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=2, border_radius=14)

    phase_text = f"{'Dzien' if game.phase == 'day' else 'Noc'} {game.day_index}"
    draw_text(surface, phase_text, font_ui, TEXT_LIGHT, 28, 24)
    draw_text(surface, f"Czas: {game.phase_timer:04.1f}s", font_small, TEXT_LIGHT, 28, 56)
    draw_text(surface, f"Drewno: {game.resources['wood']}", font_small, TEXT_LIGHT, 28, 84)
    draw_text(surface, f"Kamien: {game.resources['stone']}", font_small, TEXT_LIGHT, 160, 84)
    draw_text(surface, f"Zlom: {game.resources['scrap']}", font_small, TEXT_LIGHT, 290, 84)
    draw_text(surface, f"HUB HP: {int(game.hub.hp)}/{game.hub.max_hp}", font_small, TEXT_LIGHT, 28, 112)
    draw_text(surface, f"Gracz HP: {int(game.player.hp)}/{game.player.max_hp}", font_small, TEXT_LIGHT, 220, 112)

    build_panel = pygame.Rect(WIDTH - min(318, WIDTH - 32) - 16, 14, min(318, WIDTH - 32), 228)
    pygame.draw.rect(surface, PANEL_COLOR, build_panel, border_radius=14)
    pygame.draw.rect(surface, PANEL_BORDER, build_panel, width=2, border_radius=14)
    draw_text(surface, "Budowanie", font_ui, TEXT_LIGHT, WIDTH - 272, 24)
    items = [
        ("1. Wall", "18D 8K", "wall"),
        ("2. Turret", "12D 24K 18Z", "turret"),
        ("3. Mine", "10D 18K 14Z", "mine"),
        ("4. Trap", "8D 10K 6Z", "trap"),
        ("5. Workshop", "26D 24K 22Z", "workshop"),
    ]
    y = 60
    for title, cost, key in items:
        color = (255, 220, 120) if game.selected_build == key else TEXT_LIGHT
        draw_text(surface, title, font_small, color, WIDTH - 272, y)
        draw_text(surface, cost, font_small, TEXT_LIGHT, WIDTH - 140, y)
        y += 34
    draw_text(surface, "Klik myszy: postaw budynek", font_small, TEXT_LIGHT, WIDTH - 272, 204)
    draw_text(surface, f"Siatka budowy: {GRID_SIZE} px", font_small, TEXT_LIGHT, WIDTH - 272, 174)

    control_panel = pygame.Rect(16, HEIGHT - 84, min(760, WIDTH - 32), 60)
    pygame.draw.rect(surface, PANEL_COLOR, control_panel, border_radius=14)
    pygame.draw.rect(surface, PANEL_BORDER, control_panel, width=2, border_radius=14)
    draw_text(surface, "WASD ruch | E interakcja | Spacja atak | 1-5 wybierz budynek | Snap do siatki", font_small, TEXT_LIGHT, 30, HEIGHT - 64)

    if game.message_timer > 0:
        msg_width = min(640, WIDTH - 40)
        msg_panel = pygame.Rect((WIDTH - msg_width) // 2, HEIGHT - 92, msg_width, 40)
        pygame.draw.rect(surface, PANEL_COLOR, msg_panel, border_radius=12)
        pygame.draw.rect(surface, PANEL_BORDER, msg_panel, width=2, border_radius=12)
        draw_text(surface, game.message, font_small, TEXT_LIGHT, msg_panel.x + 16, msg_panel.y + 10)

    hint_width = min(520, WIDTH - 32)
    hint_panel = pygame.Rect(16, 168, hint_width, 44)
    pygame.draw.rect(surface, PANEL_COLOR, hint_panel, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, hint_panel, width=2, border_radius=12)
    draw_text(surface, game.context_hint(), font_small, TEXT_LIGHT, hint_panel.x + 14, hint_panel.y + 9)


def draw_quest_panel(surface, game):
    panel_width = min(760, WIDTH - 60)
    panel_height = min(520, HEIGHT - 90)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=3, border_radius=16)
    draw_text(surface, "NPC - questy i zadania", font_big, TEXT_LIGHT, panel.x + 24, panel.y + 18)
    draw_text(surface, "Mechanik Olek pomaga rozwijac kolonie.", font_small, TEXT_LIGHT, panel.x + 24, panel.y + 72)

    y = panel.y + 112
    for quest in game.quests:
        if y > panel.bottom - 110:
            break
        status = "ZALICZONY" if quest.completed else f"{quest.progress(game)}/{quest.requirement_value}"
        color = (115, 225, 132) if quest.completed else TEXT_LIGHT
        draw_text(surface, quest.title, font_ui, color, panel.x + 24, y)
        draw_text(surface, status, font_small, color, panel.right - 150, y + 5)
        y += 28
        draw_text(surface, quest.description, font_small, TEXT_LIGHT, panel.x + 24, y)
        y += 22
        draw_text(surface, f"Nagroda: {quest.reward}", font_small, (201, 213, 224), panel.x + 24, y)
        y += 36

    active = game.active_quest()
    if active is not None:
        draw_text(surface, f"Aktywny quest: {active.tip}", font_small, (255, 220, 120), panel.x + 24, panel.bottom - 54)
    draw_text(surface, "Nacisnij E, aby zamknac panel.", font_small, TEXT_LIGHT, panel.x + 24, panel.bottom - 28)


def draw_upgrade_panel(surface, game):
    panel_width = min(620, WIDTH - 60)
    panel_height = min(420, HEIGHT - 90)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=3, border_radius=16)

    draw_text(surface, "HUB - ulepszenia", font_big, TEXT_LIGHT, panel.x + 24, panel.y + 18)
    lines = [
        "1. Ulepsz HUB        koszt: 30 drewna, 30 kamienia, 24 zlomu",
        "2. Szybkosc gracza   koszt: 18 zlomu, 10 kamienia",
        "3. Zbieranie         koszt: 16 drewna, 16 zlomu",
        "4. Bron             koszt: 12 kamienia, 20 zlomu",
        "5. Pelna naprawa     koszt: 18 drewna, 18 kamienia",
        "",
        f"Poziom HUB: {game.hub.level}",
        f"Szybkosc: {game.player.speed_level} | Zbieranie: {game.player.gather_level} | Bron: {game.player.attack_level}",
        "Nacisnij E, aby zamknac panel.",
    ]
    y = panel.y + 92
    for line in lines:
        draw_text(surface, line, font_small, TEXT_LIGHT, panel.x + 24, y)
        y += 34


def draw_game_over(surface, game):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 12, 18, 180))
    surface.blit(overlay, (0, 0))

    panel_width = min(560, WIDTH - 60)
    panel_height = min(320, HEIGHT - 90)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(surface, (180, 92, 92), panel, width=3, border_radius=16)
    draw_text(surface, "Kolonia upadla", font_big, TEXT_LIGHT, panel.x + 88, panel.y + 34)
    draw_text(surface, f"Przetrwane dni: {game.day_index}", font_ui, TEXT_LIGHT, panel.x + 150, panel.y + 112)
    draw_text(surface, f"HUB poziom: {game.hub.level}", font_ui, TEXT_LIGHT, panel.x + 165, panel.y + 148)
    draw_text(surface, "R - nowa gra | ESC - wyjscie", font_ui, TEXT_LIGHT, panel.x + 120, panel.y + 214)


def draw_main_menu(surface):
    surface.fill((18, 28, 40))
    pygame.draw.rect(surface, (32, 55, 78), (0, HEIGHT - 220, WIDTH, 220))
    pygame.draw.circle(surface, (73, 118, 173), (210, 180), 120)
    pygame.draw.rect(surface, (90, 146, 101), (0, HEIGHT - 120, WIDTH, 120))

    title = "Colony Lite"
    subtitle = "Projekt: strategiczna gra survival-base-builder w pygame"
    description = [
        "Budujesz kolonie, zbierasz zasoby, rozmawiasz z NPC i wykonujesz questy.",
        "Za dnia rozwijasz baze, a nocą bronisz HUB-u przed roznymi typami wrogow.",
        "Sa tu budynki produkcyjne, pułapki, wiezyczki, ulepszenia i system podpowiedzi.",
    ]

    draw_text(surface, title, font_big, TEXT_LIGHT, 72, 70)
    draw_text(surface, subtitle, font_ui, TEXT_LIGHT, 72, 128)

    y = 200
    for line in description:
        draw_text(surface, line, font_small, TEXT_LIGHT, 72, y)
        y += 30

    box = pygame.Rect(72, 340, min(560, WIDTH - 120), 220)
    pygame.draw.rect(surface, PANEL_COLOR, box, border_radius=18)
    pygame.draw.rect(surface, PANEL_BORDER, box, width=2, border_radius=18)
    info = [
        "Sterowanie:",
        "WASD - ruch",
        "E - interakcja: surowce, HUB, NPC, skrzynie",
        "Spacja - atak",
        "1-5 - wybór budynku",
        "Klik myszy - stawianie budynkow",
        "",
        "ENTER - start gry",
    ]
    y = box.y + 20
    for line in info:
        draw_text(surface, line, font_small if line != "Sterowanie:" else font_ui, TEXT_LIGHT, box.x + 20, y)
        y += 28

    mouse_pos = pygame.mouse.get_pos()
    for key, label in [("start", "START"), ("settings", "USTAWIENIA"), ("quit", "WYJDZ Z GRY")]:
        rect = get_main_menu_buttons()[key]
        draw_button(surface, rect, label, rect.collidepoint(mouse_pos))


def draw_pause_menu(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 12, 18, 175))
    surface.blit(overlay, (0, 0))

    panel_width = min(520, WIDTH - 80)
    panel_height = min(320, HEIGHT - 100)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=18)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=2, border_radius=18)
    draw_text(surface, "Menu Pauzy", font_big, TEXT_LIGHT, panel.x + 110, panel.y + 26)

    mouse_pos = pygame.mouse.get_pos()
    labels = {
        "settings": "USTAWIENIA",
        "main_menu": "WYJDZ DO MENU GLOWNEGO",
        "resume": "WROC DO GRY",
    }
    for key, rect in get_pause_menu_buttons().items():
        draw_button(surface, rect, labels[key], rect.collidepoint(mouse_pos))


def draw_settings_menu(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 12, 18, 175))
    surface.blit(overlay, (0, 0))

    panel_width = min(700, WIDTH - 80)
    panel_height = min(360, HEIGHT - 110)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=18)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=2, border_radius=18)
    draw_text(surface, "Ustawienia", font_big, TEXT_LIGHT, panel.x + 28, panel.y + 24)
    draw_text(surface, "Konfiguracja ekranu", font_ui, TEXT_LIGHT, panel.x + 28, panel.y + 84)

    resolution = RESOLUTIONS[current_resolution_index]
    fullscreen_label = "WLACZONY" if fullscreen_enabled else "WYLACZONY"
    mouse_pos = pygame.mouse.get_pos()
    buttons = get_settings_buttons()
    draw_button(surface, buttons["resolution"], f"ROZDZIELCZOSC: {resolution[0]}x{resolution[1]}", buttons["resolution"].collidepoint(mouse_pos))
    draw_button(surface, buttons["fullscreen"], f"PELNY EKRAN: {fullscreen_label}", buttons["fullscreen"].collidepoint(mouse_pos))
    draw_button(surface, buttons["back"], "POWROT", buttons["back"].collidepoint(mouse_pos))

    draw_text(surface, "Kliknij przycisk albo uzyj R/F. ESC zamyka ustawienia.", font_small, TEXT_LIGHT, panel.x + 24, panel.bottom - 62)
    draw_text(surface, "Dostepne tryby: 1280x720 oraz Full HD 1920x1080.", font_small, TEXT_LIGHT, panel.x + 24, panel.bottom - 34)


def main():
    global current_resolution_index, fullscreen_enabled
    game = Game()

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.menu_state == "menu":
                    buttons = get_main_menu_buttons()
                    if buttons["start"].collidepoint(event.pos):
                        game.menu_state = "playing"
                    elif buttons["settings"].collidepoint(event.pos):
                        game.settings_return_state = "menu"
                        game.menu_state = "settings"
                    elif buttons["quit"].collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
                    continue

                if game.menu_state == "pause":
                    buttons = get_pause_menu_buttons()
                    if buttons["settings"].collidepoint(event.pos):
                        game.settings_return_state = "pause"
                        game.menu_state = "settings"
                    elif buttons["main_menu"].collidepoint(event.pos):
                        game = Game()
                        game.menu_state = "menu"
                    elif buttons["resume"].collidepoint(event.pos):
                        game.menu_state = "playing"
                    continue

                if game.menu_state == "settings":
                    buttons = get_settings_buttons()
                    if buttons["resolution"].collidepoint(event.pos):
                        current_resolution_index = (current_resolution_index + 1) % len(RESOLUTIONS)
                        update_display_mode()
                    elif buttons["fullscreen"].collidepoint(event.pos):
                        fullscreen_enabled = not fullscreen_enabled
                        update_display_mode()
                    elif buttons["back"].collidepoint(event.pos):
                        game.menu_state = game.settings_return_state
                    continue

            if event.type == pygame.KEYDOWN:
                if game.menu_state == "menu":
                    if event.key == pygame.K_RETURN:
                        game.menu_state = "playing"
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    continue

                if game.menu_state == "settings":
                    if event.key == pygame.K_ESCAPE:
                        game.menu_state = game.settings_return_state
                    elif event.key == pygame.K_RETURN:
                        game.menu_state = game.settings_return_state
                    elif event.key == pygame.K_r:
                        current_resolution_index = (current_resolution_index + 1) % len(RESOLUTIONS)
                        update_display_mode()
                    elif event.key == pygame.K_f:
                        fullscreen_enabled = not fullscreen_enabled
                        update_display_mode()
                    continue

                if game.menu_state == "pause":
                    if event.key == pygame.K_ESCAPE:
                        game.menu_state = "playing"
                    continue

                if event.key == pygame.K_ESCAPE:
                    if game.upgrade_open:
                        game.upgrade_open = False
                    elif game.quest_open:
                        game.quest_open = False
                    else:
                        game.menu_state = "pause"
                    continue

                if event.key == pygame.K_u:
                    game.upgrade_open = False
                    game.quest_open = False
                    game.settings_return_state = "playing"
                    game.menu_state = "settings"
                    continue

                if game.game_over:
                    if event.key == pygame.K_r:
                        game = Game()
                        game.menu_state = "playing"
                    continue

                if event.key == pygame.K_e:
                    game.attempt_gather_or_open()
                elif event.key == pygame.K_SPACE:
                    game.attempt_attack()
                elif event.key == pygame.K_1:
                    if game.upgrade_open:
                        game.do_upgrade(1)
                    else:
                        game.selected_build = "wall"
                elif event.key == pygame.K_2:
                    if game.upgrade_open:
                        game.do_upgrade(2)
                    else:
                        game.selected_build = "turret"
                elif event.key == pygame.K_3:
                    if game.upgrade_open:
                        game.do_upgrade(3)
                    else:
                        game.selected_build = "mine"
                elif event.key == pygame.K_4:
                    if game.upgrade_open:
                        game.do_upgrade(4)
                    else:
                        game.selected_build = "trap"
                elif event.key == pygame.K_5:
                    if game.upgrade_open:
                        game.do_upgrade(5)
                    else:
                        game.selected_build = "workshop"

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and game.menu_state == "playing"
                and not game.game_over
                and not game.upgrade_open
                and not game.quest_open
            ):
                if event.button in (1, 3):
                    game.place_structure(event.pos, game.camera())

        if game.menu_state == "menu":
            draw_main_menu(screen)
            pygame.display.flip()
            continue

        if game.menu_state == "playing":
            game.update(dt)
        camera = game.camera()

        draw_world(screen, game, camera)
        draw_build_preview(screen, game, camera, pygame.mouse.get_pos())
        draw_top_ui(screen, game)

        if game.upgrade_open and not game.game_over:
            draw_upgrade_panel(screen, game)

        if game.quest_open and not game.game_over:
            draw_quest_panel(screen, game)

        if game.menu_state == "settings":
            draw_settings_menu(screen)

        if game.menu_state == "pause":
            draw_pause_menu(screen)

        if game.game_over:
            draw_game_over(screen, game)

        pygame.display.flip()


if __name__ == "__main__":
    main()
