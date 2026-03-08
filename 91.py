import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Heart - Happy Women Day")
clock = pygame.time.Clock()

font_main = pygame.font.SysFont("arial", 42, bold=True)
font_sub = pygame.font.SysFont("arial", 20, italic=True)

NUM = 700

points = []
for i in range(NUM):
    t = math.pi*2*i/NUM
    x = 16*math.sin(t)**3
    y = 13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
    z = random.uniform(-8,8)
    points.append([x,y,z])


class Particle:

    def __init__(self,p):

        self.x,self.y,self.z = p
        self.color = (255, random.randint(90,130), random.randint(170,255))
        self.size = random.uniform(1,3)

    def draw(self,angle):

        cosA = math.cos(angle)
        sinA = math.sin(angle)

        x = self.x*cosA - self.z*sinA
        z = self.x*sinA + self.z*cosA

        scale = 12/(z+15)

        sx = WIDTH//2 + x*scale*12
        sy = HEIGHT//2 - self.y*scale*12

        pygame.draw.circle(screen,self.color,(int(sx),int(sy)),int(self.size*scale))


particles = [Particle(p) for p in points]

running=True

while running:

    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False

    screen.fill((10,5,20))

    time_now = pygame.time.get_ticks()
    angle = time_now/1500

    beat = abs(math.sin(time_now/350))
    scale = 1 + beat*0.15

    for p in particles:
        p.draw(angle)

    text = font_main.render("Happy women day 8/3",True,(255,150,210))
    rect = text.get_rect(center=(WIDTH//2,HEIGHT-70))
    screen.blit(text,rect)

    sub = font_sub.render("Huy Vũ",True,(150,150,255))
    rect2 = sub.get_rect(center=(WIDTH//2,HEIGHT-40))
    screen.blit(sub,rect2)

    names=["Nguyễn Huyền","Lan Anh","Phương Linh"]
    sizes=[32,26,20]

    for i,name in enumerate(names):

        font=pygame.font.SysFont("arial",sizes[i],bold=True)

        angle2 = time_now/800 + i*2
        r = 170 - i*25

        x = WIDTH//2 + math.cos(angle2)*r
        y = HEIGHT//2 + math.sin(angle2)*r

        txt = font.render(name,True,(255,200,230))
        screen.blit(txt,txt.get_rect(center=(x,y)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
