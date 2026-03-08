import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Happy Women Day")
clock = pygame.time.Clock()

font_main = pygame.font.SysFont("arial", 46, bold=True)
font_sub = pygame.font.SysFont("arial", 20, italic=True)

NUM_PARTICLES = 800

target_points = []
for i in range(NUM_PARTICLES):
    t = math.pi * 2 * i / NUM_PARTICLES
    x = 16 * math.sin(t)**3
    y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
    target_points.append((x, y))


class SwarmParticle:
    def __init__(self, tx, ty):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)

        self.tx = tx
        self.ty = ty

        self.color = (255, random.randint(80,120), random.randint(150,255))
        self.size = random.uniform(1,3)
        self.speed = random.uniform(0.03,0.08)

    def update(self):
        target_x = WIDTH//2 + self.tx * 11
        target_y = HEIGHT//2 - 30 - self.ty * 11

        self.x += (target_x - self.x) * self.speed
        self.y += (target_y - self.y) * self.speed

    def draw(self):
        pygame.draw.circle(screen,self.color,(int(self.x),int(self.y)),int(self.size))


particles = [SwarmParticle(p[0],p[1]) for p in target_points]


running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((10,5,15))

    for p in particles:
        p.update()
        p.draw()

    # TEXT CHÍNH
    text = font_main.render("Happy women day 8/3", True, (255,150,200))
    rect = text.get_rect(center=(WIDTH//2, HEIGHT-70))
    screen.blit(text,rect)

    sub = font_sub.render("Huy Vũ", True, (150,150,255))
    rect2 = sub.get_rect(center=(WIDTH//2, HEIGHT-30))
    screen.blit(sub,rect2)

    # TÊN CHẠY QUANH TRÁI TIM
    names = ["Nguyễn Huyền","Lan Anh","Phương Linh"]
    sizes = [32,26,20]

    time_now = pygame.time.get_ticks()

    for i,name in enumerate(names):

        font = pygame.font.SysFont("arial",sizes[i],bold=True)

        angle = time_now/800 + i*2
        radius = 170 - i*30

        x = WIDTH//2 + math.cos(angle)*radius
        y = HEIGHT//2 - 30 + math.sin(angle)*radius

        txt = font.render(name,True,(255,200,220))
        r = txt.get_rect(center=(x,y))
        screen.blit(txt,r)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
