import pygame
import random

pygame.init()

# ----------------------------
# AUDIO SETUP
# ----------------------------
try:
    pygame.mixer.init()
    audio_ok = True
except pygame.error:
    audio_ok = False

def load_sound(path, volume=0.5):
    if not audio_ok:
        return None
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        return s
    except:
        return None

def play_sound(snd):
    if snd:
        snd.play()

jump_snd = load_sound("jump.wav", 0.5)
coin_snd = load_sound("coin.wav", 0.6)
fuel_snd = load_sound("fuel.wav", 0.6)
crash_snd = load_sound("crash.wav", 0.8)

if audio_ok:
    try:
        pygame.mixer.music.load("bgm.ogg")
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)
    except:
        pass

# ----------------------------
# SCREEN
# ----------------------------
WIDTH, HEIGHT = 600, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NoCtraX Vehicle Survival Mini Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (230, 70, 70)
GREEN = (80, 200, 90)
YELLOW = (255, 220, 80)
BLUE = (70, 140, 255)
ORANGE = (240, 160, 60)
GRAY = (160, 160, 160)
DARK_GRAY = (60, 60, 60)
BROWN = (140, 90, 50)
GRASS1 = (76, 170, 76)
GRASS2 = (66, 160, 66)
ROAD = (76, 76, 76)
ROAD_EDGE = (35, 35, 35)
ROAD_LINE = (235, 235, 235)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 48)

# ----------------------------
# ROAD SETTINGS
# ----------------------------
ROAD_W = 360
ROAD_X = (WIDTH - ROAD_W) // 2
ROAD_LEFT = ROAD_X + 12
ROAD_RIGHT = ROAD_X + ROAD_W - 12

LANES = [
    ROAD_X + ROAD_W // 6,
    ROAD_X + ROAD_W // 2,
    ROAD_X + ROAD_W * 5 // 6
]

# Spawn timers
SPAWN_OBS = pygame.USEREVENT + 1
SPAWN_COIN = pygame.USEREVENT + 2
SPAWN_FUEL = pygame.USEREVENT + 3

pygame.time.set_timer(SPAWN_OBS, 800)
pygame.time.set_timer(SPAWN_COIN, 1200)
pygame.time.set_timer(SPAWN_FUEL, 3800)

# ----------------------------
# DRAW HELPERS
# ----------------------------
def draw_grass():
    for y in range(0, HEIGHT, 40):
        for x in range(0, WIDTH, 40):
            c = GRASS1 if (x // 40 + y // 40) % 2 == 0 else GRASS2
            pygame.draw.rect(screen, c, (x, y, 40, 40))

def draw_dashed_line(x, scroll, w=4):
    dash_h = 36
    gap = 26
    offset = scroll % (dash_h + gap)
    for y in range(-dash_h - gap, HEIGHT + dash_h, dash_h + gap):
        pygame.draw.rect(screen, ROAD_LINE, (x, y + offset, w, dash_h))

def draw_road(scroll):
    pygame.draw.rect(screen, ROAD, (ROAD_X, 0, ROAD_W, HEIGHT))
    pygame.draw.rect(screen, ROAD_EDGE, (ROAD_X, 0, ROAD_W, HEIGHT), 4)
    draw_dashed_line(ROAD_X + ROAD_W // 3 - 2, scroll, 4)
    draw_dashed_line(ROAD_X + 2 * ROAD_W // 3 - 2, scroll, 4)

# ----------------------------
# PLAYER
# ----------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((56, 88), pygame.SRCALPHA)
        self.build()

        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 20

        self.base_x = self.rect.x
        self.base_y = self.rect.y

        self.speed = 7

        # Jump physics
        self.jump_offset = 0
        self.jump_velocity = 0
        self.gravity = 1.2
        self.on_ground = True

        # short safe time after landing
        self.landing_grace = 0

    def build(self):
        self.image.fill((0, 0, 0, 0))

        # Body
        pygame.draw.rect(self.image, BLUE, (7, 10, 42, 68), border_radius=6)
        pygame.draw.rect(self.image, (30, 30, 30), (14, 4, 28, 20), border_radius=4)
        pygame.draw.rect(self.image, (180, 220, 255), (18, 8, 20, 10), border_radius=3)

        # Wheels
        pygame.draw.rect(self.image, (20, 20, 20), (2, 16, 8, 16), border_radius=2)
        pygame.draw.rect(self.image, (20, 20, 20), (46, 16, 8, 16), border_radius=2)
        pygame.draw.rect(self.image, (20, 20, 20), (2, 58, 8, 16), border_radius=2)
        pygame.draw.rect(self.image, (20, 20, 20), (46, 58, 8, 16), border_radius=2)

        # Lights
        pygame.draw.rect(self.image, YELLOW, (10, 71, 12, 9))
        pygame.draw.rect(self.image, YELLOW, (34, 71, 12, 9))

    def get_hitbox(self):
        # Smaller collision box so edge touches don't count too easily
        return self.rect.inflate(-14, -20)

    def update(self, world_speed=0, jump=False):
        keys = pygame.key.get_pressed()
        dx = dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed

        self.base_x += dx
        self.base_y += dy

        # Jump start
        if jump and self.on_ground:
            self.jump_velocity = -18
            self.on_ground = False
            self.landing_grace = 0

        # Jump physics
        if not self.on_ground:
            self.jump_offset += self.jump_velocity
            self.jump_velocity += self.gravity

            if self.jump_offset >= 0:
                self.jump_offset = 0
                self.jump_velocity = 0
                self.on_ground = True
                self.landing_grace = 12

        self.rect.x = self.base_x
        self.rect.y = self.base_y + self.jump_offset

        # Bounds
        if self.rect.left < ROAD_LEFT:
            self.rect.left = ROAD_LEFT
            self.base_x = self.rect.x

        if self.rect.right > ROAD_RIGHT:
            self.rect.right = ROAD_RIGHT
            self.base_x = self.rect.x

        if self.rect.top < 20:
            self.rect.top = 20
            if not self.on_ground:
                self.jump_offset = self.rect.y - self.base_y
            else:
                self.base_y = self.rect.y

        if self.rect.bottom > HEIGHT - 10:
            self.rect.bottom = HEIGHT - 10
            self.base_y = self.rect.y - self.jump_offset

        if self.landing_grace > 0:
            self.landing_grace -= 1

# ----------------------------
# OBSTACLES
# ----------------------------
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, speed_boost=0):
        super().__init__()
        self.kind = random.choice(["car", "truck", "block"])
        self.make_image()

        self.rect = self.image.get_rect()
        self.rect.centerx = random.choice(LANES) + random.randint(-8, 8)
        self.rect.y = random.randrange(-160, -40)

        self.speed = random.randint(4, 7) + speed_boost

    def make_image(self):
        if self.kind == "car":
            self.image = pygame.Surface((50, 78), pygame.SRCALPHA)
            pygame.draw.rect(self.image, RED, (6, 10, 38, 56), border_radius=6)
            pygame.draw.rect(self.image, (30, 30, 30), (13, 4, 24, 16), border_radius=4)
            pygame.draw.rect(self.image, (20, 20, 20), (1, 16, 7, 14), border_radius=2)
            pygame.draw.rect(self.image, (20, 20, 20), (42, 16, 7, 14), border_radius=2)
            pygame.draw.rect(self.image, (20, 20, 20), (1, 48, 7, 14), border_radius=2)
            pygame.draw.rect(self.image, (20, 20, 20), (42, 48, 7, 14), border_radius=2)

        elif self.kind == "truck":
            self.image = pygame.Surface((62, 92), pygame.SRCALPHA)
            pygame.draw.rect(self.image, ORANGE, (6, 18, 50, 60), border_radius=6)
            pygame.draw.rect(self.image, (200, 130, 40), (14, 6, 22, 18), border_radius=4)
            pygame.draw.rect(self.image, (30, 30, 30), (0, 24, 6, 16), border_radius=2)
            pygame.draw.rect(self.image, (30, 30, 30), (56, 24, 6, 16), border_radius=2)
            pygame.draw.rect(self.image, (30, 30, 30), (0, 58, 6, 16), border_radius=2)
            pygame.draw.rect(self.image, (30, 30, 30), (56, 58, 6, 16), border_radius=2)

        else:
            self.image = pygame.Surface((46, 46), pygame.SRCALPHA)
            pygame.draw.rect(self.image, GRAY, (6, 20, 28, 18), border_radius=4)
            pygame.draw.rect(self.image, DARK_GRAY, (10, 10, 14, 10), border_radius=3)
            pygame.draw.rect(self.image, (190, 190, 190), (16, 6, 10, 8), border_radius=2)

    def update(self, world_speed=0):
        self.rect.y += self.speed + world_speed // 4
        if self.rect.top > HEIGHT:
            self.kill()

# ----------------------------
# COINS
# ----------------------------
class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (2, 2, 20, 20), border_radius=4)
        pygame.draw.rect(self.image, (150, 120, 0), (2, 2, 20, 20), 2, border_radius=4)
        pygame.draw.rect(self.image, WHITE, (8, 6, 4, 4))

        self.rect = self.image.get_rect()
        self.rect.centerx = random.choice(LANES)
        self.rect.y = random.randrange(-300, -40)
        self.speed = random.randint(4, 6)

    def update(self, world_speed=0):
        self.rect.y += self.speed + world_speed // 3
        if self.rect.top > HEIGHT:
            self.kill()

# ----------------------------
# FUEL
# ----------------------------
class FuelCan(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((28, 34), pygame.SRCALPHA)

        pygame.draw.rect(self.image, GREEN, (5, 6, 18, 24), border_radius=4)
        pygame.draw.rect(self.image, BLACK, (5, 6, 18, 24), 2, border_radius=4)
        pygame.draw.rect(self.image, RED, (10, 0, 8, 8), border_radius=2)

        pygame.draw.rect(self.image, WHITE, (12, 9, 4, 16))
        pygame.draw.rect(self.image, WHITE, (8, 15, 12, 4))

        self.rect = self.image.get_rect()
        self.rect.centerx = random.choice(LANES)
        self.rect.y = random.randrange(-500, -80)
        self.speed = random.randint(4, 6)

    def update(self, world_speed=0):
        self.rect.y += self.speed + world_speed // 3
        if self.rect.top > HEIGHT:
            self.kill()

# ----------------------------
# DECOR
# ----------------------------
class Decor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.kind = random.choice(["tree", "tree", "rock"])
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        self.build()
        self.rect = self.image.get_rect()
        self.speed = random.randint(2, 4)
        self.reset_pos()

    def build(self):
        self.image.fill((0, 0, 0, 0))

        if self.kind == "tree":
            pygame.draw.rect(self.image, BROWN, (16, 30, 8, 22))
            pygame.draw.rect(self.image, (40, 150, 60), (6, 8, 28, 18), border_radius=4)
            pygame.draw.rect(self.image, (30, 130, 50), (3, 18, 34, 20), border_radius=4)
            pygame.draw.rect(self.image, (50, 170, 70), (10, 2, 20, 10), border_radius=3)
        else:
            pygame.draw.rect(self.image, GRAY, (6, 20, 28, 18), border_radius=4)
            pygame.draw.rect(self.image, DARK_GRAY, (10, 14, 12, 10), border_radius=3)
            pygame.draw.rect(self.image, (190, 190, 190), (14, 8, 10, 8), border_radius=2)

    def reset_pos(self):
        side = random.choice(["left", "right"])
        if side == "left":
            self.rect.x = random.randrange(10, max(11, ROAD_X - 50))
        else:
            self.rect.x = random.randrange(ROAD_X + ROAD_W + 10, WIDTH - 50)
        self.rect.y = random.randrange(-HEIGHT, 0)

    def update(self, world_speed=0):
        self.rect.y += max(1, world_speed // 2)
        if self.rect.top > HEIGHT:
            self.kind = random.choice(["tree", "tree", "rock"])
            self.build()
            self.reset_pos()

# ----------------------------
# GAME RESET
# ----------------------------
def new_game():
    player = Player()
    obstacles = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    fuels = pygame.sprite.Group()
    decor = pygame.sprite.Group()

    for _ in range(12):
        decor.add(Decor())

    distance = 0
    fuel = 100
    road_scroll = 0
    game_over = False

    return player, obstacles, coins, fuels, decor, distance, fuel, road_scroll, game_over

# Game state
player, obstacles, coins, fuels, decor, distance, fuel, road_scroll, game_over = new_game()

# ----------------------------
# MAIN LOOP
# ----------------------------
running = True
while running:
    clock.tick(60)

    jump_pressed = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and player.on_ground:
                jump_pressed = True
                play_sound(jump_snd)

            if event.type == SPAWN_OBS:
                obstacles.add(Obstacle(speed_boost=distance // 5000))

            elif event.type == SPAWN_COIN:
                if random.random() < 0.75:
                    coins.add(Coin())

            elif event.type == SPAWN_FUEL:
                if random.random() < 0.45:
                    fuels.add(FuelCan())

        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player, obstacles, coins, fuels, decor, distance, fuel, road_scroll, game_over = new_game()

    if not game_over:
        world_speed = 6 + distance // 3500

        road_scroll += world_speed
        distance += world_speed
        fuel -= 0.03 + world_speed * 0.002

        player.update(world_speed, jump_pressed)
        obstacles.update(world_speed)
        coins.update(world_speed)
        fuels.update(world_speed)
        decor.update(world_speed)

        # Collision only when on ground and not in landing grace
        if player.on_ground and player.landing_grace == 0:
            player_box = player.get_hitbox()
            for obs in obstacles:
                obs_box = obs.rect.inflate(-10, -10)
                if player_box.colliderect(obs_box):
                    play_sound(crash_snd)
                    game_over = True
                    break

        coin_hits = pygame.sprite.spritecollide(player, coins, True)
        if coin_hits:
            distance += 150 * len(coin_hits)
            play_sound(coin_snd)

        fuel_hits = pygame.sprite.spritecollide(player, fuels, True)
        if fuel_hits:
            fuel = min(100, fuel + 25 * len(fuel_hits))
            play_sound(fuel_snd)

        if fuel <= 0:
            fuel = 0
            play_sound(crash_snd)
            game_over = True

    # Draw
    draw_grass()
    decor.draw(screen)
    draw_road(road_scroll)

    coins.draw(screen)
    fuels.draw(screen)
    obstacles.draw(screen)

    # Shadow while jumping
    if not player.on_ground:
        shadow_rect = pygame.Rect(player.base_x + 6, player.base_y + 72, 44, 12)
        pygame.draw.ellipse(screen, (35, 35, 35), shadow_rect)

    screen.blit(player.image, player.rect)

    # HUD
    score_text = font.render(f"Score: {distance // 10}", True, WHITE)
    fuel_text = font.render(f"Fuel: {int(fuel)}%", True, WHITE)
    info_text = font.render("Arrow Keys / WASD | SPACE = Jump | R = Restart", True, WHITE)

    screen.blit(score_text, (10, 10))
    screen.blit(fuel_text, (10, 40))
    screen.blit(info_text, (10, HEIGHT - 34))

    # Fuel bar
    pygame.draw.rect(screen, (40, 40, 40), (10, 70, 180, 18), border_radius=4)
    bar_color = GREEN if fuel > 50 else YELLOW if fuel > 20 else RED
    pygame.draw.rect(screen, bar_color, (10, 70, int(180 * fuel / 100), 18), border_radius=4)

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        over = big_font.render("GAME OVER", True, RED)
        msg = font.render("Press R to restart", True, WHITE)
        final = font.render(f"Final Score: {distance // 10}", True, WHITE)

        screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 60))
        screen.blit(final, (WIDTH // 2 - final.get_width() // 2, HEIGHT // 2 - 10))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 + 25))

    pygame.display.flip()

pygame.quit()