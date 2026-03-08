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

NUM_PARTICLES = 900

target_points = []
for i in range(NUM_PARTICLES):
    t = math.pi * 2 * i / NUM_PARTICLES
    x = 16 * math.sin(t)**3
    y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
    target_points.append((x, y))


class Particle:

    def __init__(self, hx, hy):

        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)

        self.hx = hx
        self.hy = hy

        self.scatter_x = self.x
        self.scatter_y = self.y

        self.color = (255, random.randint(80,120), random.randint(160,255))
        self.size = random.uniform(1.5,3)

        self.speed = random.uniform(0.03,0.07)

    def update(self, state, beat):

        if state != "EXPLODE":

            tx = WIDTH//2 + self.hx * 11 * beat
            ty = HEIGHT//2 - 30 - self.hy * 11 * beat

            self.x += (tx - self.x) * self.speed
            self.y += (ty - self.y) * self.speed

        else:

            self.x += (self.scatter_x - self.x) * self.speed
            self.y += (self.scatter_y - self.y) * self.speed

        self.x += random.uniform(-0.4,0.4)
        self.y += random.uniform(-0.4,0.4)

    def draw(self):

        pygame.draw.circle(screen,self.color,(int(self.x),int(self.y)),int(self.size))


particles = [Particle(p[0],p[1]) for p in target_points]

running = True
current_state = "CONVERGE"

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    time_now = pygame.time.get_ticks()

    cycle = time_now % 9000

    if cycle < 3500:
        new_state = "CONVERGE"
    elif cycle < 5500:
        new_state = "BEAT"
    else:
        new_state = "EXPLODE"

    if new_state == "EXPLODE" and current_state != "EXPLODE":

        for p in particles:

            angle = random.uniform(0,math.pi*2)
            distance = random.uniform(250,700)

            p.scatter_x = WIDTH//2 + math.cos(angle)*distance
            p.scatter_y = HEIGHT//2 + math.sin(angle)*distance
            p.speed = random.uniform(0.05,0.1)

    if new_state == "CONVERGE" and current_state != "CONVERGE":

        for p in particles:
            p.speed = random.uniform(0.02,0.05)

    current_state = new_state

    fade = pygame.Surface((WIDTH,HEIGHT))
    fade.set_alpha(35)
    fade.fill((10,5,15))
    screen.blit(fade,(0,0))

    beat = abs(math.sin(time_now/300)) if current_state == "BEAT" else 0
    beat_scale = 1 + beat*0.15

    for p in particles:
        p.update(current_state,beat_scale)
        p.draw()

    # TEXT
    text = font_main.render("Happy women day 8/3",True,(255,150,200))
    rect = text.get_rect(center=(WIDTH//2,HEIGHT-70))
    screen.blit(text,rect)

    sub = font_sub.render("Huy Vũ",True,(150,150,255))
    rect2 = sub.get_rect(center=(WIDTH//2,HEIGHT-30))
    screen.blit(sub,rect2)

    # TÊN BAY QUANH TRÁI TIM
    names = ["Nguyễn Huyền","Lan Anh","Phương Linh"]
    sizes = [34,26,20]

    for i,name in enumerate(names):

        font = pygame.font.SysFont("arial",sizes[i],bold=True)

        angle = time_now/700 + i*2
        radius = 170 - i*25

        x = WIDTH//2 + math.cos(angle)*radius
        y = HEIGHT//2 - 30 + math.sin(angle)*radius

        txt = font.render(name,True,(255,200,230))
        r = txt.get_rect(center=(x,y))

        screen.blit(txt,r)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
