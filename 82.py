
  import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("happy women day")
clock = pygame.time.Clock()

try:
    font_main = pygame.font.SysFont("arial", 46, bold=True)
    font_sub = pygame.font.SysFont("arial", 20, italic=True)
except:
    font_main = pygame.font.Font(None, 46)
    font_sub = pygame.font.Font(None, 20)

NUM_PARTICLES = 800

target_points = []
for i in range(NUM_PARTICLES):
    t = math.pi * 2 * i / NUM_PARTICLES
    x = 16 * math.sin(t)**3
    y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
    target_points.append((x, y))


class SwarmParticle:
    def __init__(self, target_x, target_y):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)

        self.heart_x = target_x
        self.heart_y = target_y

        self.scatter_x = self.x
        self.scatter_y = self.y

        self.color = (random.randint(220, 255), random.randint(50, 100), random.randint(150, 255))
        self.size = random.uniform(1.0, 3.0)
        self.speed = random.uniform(0.03, 0.08)

    def update(self, state, beat_scale):
        if state == "CONVERGE" or state == "BEAT":
            tx = WIDTH // 2 + self.heart_x * 11 * beat_scale
            ty = HEIGHT // 2 - 30 - self.heart_y * 11 * beat_scale
            self.x += (tx - self.x) * self.speed
            self.y += (ty - self.y) * self.speed

        elif state == "EXPLODE":
            self.x += (self.scatter_x - self.x) * self.speed
            self.y += (self.scatter_y - self.y) * self.speed

        self.x += random.uniform(-0.5, 0.5)
        self.y += random.uniform(-0.5, 0.5)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))


class FallingDust:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-HEIGHT, HEIGHT)
        self.speed_y = random.uniform(1, 3)
        self.color = (random.randint(200, 255), 150, 200)

    def update_and_draw(self, surface):
        self.y += self.speed_y
        self.x += math.sin(self.y / 50.0) * 0.5

        if self.y > HEIGHT:
            self.y = random.uniform(-50, 0)
            self.x = random.uniform(0, WIDTH)

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 1)


particles = [SwarmParticle(target_points[i][0], target_points[i][1]) for i in range(NUM_PARTICLES)]
rain = [FallingDust() for _ in range(60)]

fade_surf = pygame.Surface((WIDTH, HEIGHT))
fade_surf.set_alpha(35)
fade_surf.fill((10, 5, 15))

running = True
screen.fill((10, 5, 15))
current_state = "CONVERGE"

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    time_now = pygame.time.get_ticks()

    cycle = time_now % 8500
    if cycle < 3500:
        new_state = "CONVERGE"
    elif cycle < 5000:
        new_state = "BEAT"
    else:
        new_state = "EXPLODE"

    if new_state == "EXPLODE" and current_state != "EXPLODE":
        for p in particles:
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(300, 800)
            p.scatter_x = WIDTH // 2 + math.cos(angle) * distance
            p.scatter_y = HEIGHT // 2 + math.sin(angle) * distance
            p.speed = random.uniform(0.05, 0.1)

    if new_state == "CONVERGE" and current_state != "CONVERGE":
        for p in particles:
            p.speed = random.uniform(0.02, 0.06)

    current_state = new_state

    screen.blit(fade_surf, (0, 0))

    for drop in rain:
        drop.update_and_draw(screen)

    beat = abs(math.sin(time_now / 300.0)) if current_state == "BEAT" else 0
    beat_scale = 1.0 + 0.1 * beat

    for p in particles:
        p.update(current_state, beat_scale)
        p.draw(screen)

    # TEXT
    text_color = (255, 150, 200)
    text_surf = font_main.render("Happy women day 8/3", True, text_color)
    text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT - 70))
    screen.blit(text_surf, text_rect)

    sub_text = font_sub.render("Huy Vũ", True, (150, 150, 255))
    sub_rect = sub_text.get_rect(center=(WIDTH//2, HEIGHT - 30))
    screen.blit(sub_text, sub_rect)

    # TÊN BAY QUANH TRÁI TIM
    names = ["Nguyễn Huyền", "Lan Anh", "Phương Linh"]
    sizes = [32, 26, 20]

    for i, name in enumerate(names):
        font_name = pygame.font.SysFont("arial", sizes[i], bold=True)

        angle = time_now / 800 + i * 2
        radius = 180 - i * 25

        x = WIDTH // 2 + math.cos(angle) * radius
        y = HEIGHT // 2 - 30 + math.sin(angle) * radius

        text_name = font_name.render(name, True, (255, 200, 220))
        rect_name = text_name.get_rect(center=(x, y))

        screen.blit(text_name, rect_name)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
