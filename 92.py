import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 700, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spark Heart")

clock = pygame.time.Clock()

NUM = 1800

points = []

for i in range(NUM):
    t = random.uniform(0, math.pi*2)

    x = 16*math.sin(t)**3
    y = 13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)

    x += random.uniform(-0.8,0.8)
    y += random.uniform(-0.8,0.8)

    points.append((x,y))


class Particle:

    def __init__(self,p):

        self.tx,self.ty = p

        self.x = random.uniform(0,WIDTH)
        self.y = random.uniform(0,HEIGHT)

        self.size = random.uniform(1,2.5)

        self.color = (
            255,
            random.randint(120,180),
            random.randint(160,220)
        )

        self.speed = random.uniform(0.02,0.05)

    def update(self):

        target_x = WIDTH//2 + self.tx*15
        target_y = HEIGHT//2 - self.ty*15

        self.x += (target_x-self.x)*self.speed
        self.y += (target_y-self.y)*self.speed

        self.x += random.uniform(-0.6,0.6)
        self.y += random.uniform(-0.6,0.6)

    def draw(self):

        glow = pygame.Surface((20,20),pygame.SRCALPHA)

        pygame.draw.circle(glow,(255,120,180,40),(10,10),8)
        screen.blit(glow,(self.x-10,self.y-10))

        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x),int(self.y)),
            int(self.size)
        )


particles = [Particle(p) for p in points]

fade = pygame.Surface((WIDTH,HEIGHT))
fade.set_alpha(25)
fade.fill((10,5,20))

running=True

while running:

    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False

    screen.blit(fade,(0,0))

    for p in particles:
        p.update()
        p.draw()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
