import pygame
import pymunk
from typing import List, Any, Optional
from random import randint, choices
from math import degrees

pygame.init()
main_surface = pygame.display.set_mode((480, 640))
clock = pygame.time.Clock()


space = pymunk.Space()
space.gravity = 0, -1000

vertical_offset = 0

# Assets
spring0 = pygame.image.load("./assets/spring_0.png")
spring1 = pygame.image.load("./assets/spring_1.png")


def convert(pos):
    return pos[0], main_surface.get_height() - pos[1]


class Dog:
    def __init__(self, pos) -> None:
        self.state = 0
        self.state_imgs = []
        for sname in ("idle", "jump", "fly", "falling"):
            img = pygame.image.load(f"assets/kat_{sname}.png")
            self.state_imgs.append(img)
        self.body = pymunk.Body()
        self.body.position = convert(pos)
        self.shape = pymunk.Circle(self.body, 40)
        self.shape.density = 1
        self.shape.friction = 0.95
        self.shape.collision_type = 1
        self.shape.filter = pymunk.ShapeFilter(group=5)
        space.add(self.body, self.shape)

    def draw(self):
        state = 0
        vel_y = self.body.velocity[1]
        if vel_y > 0:
            state = 1
        if vel_y < 0:
            state = 3
        img = self.state_imgs[state]
        pos = list(convert(self.body.position))
        pos[1] -= vertical_offset
        dest = img.get_rect(center=pos)
        main_surface.blit(img, dest)
        # pygame.draw.circle(
        #     main_surface,
        #     (255, 220, 220),
        #     pos,
        #     self.shape.radius,
        #     1,
        # )


class Spring:
    def __init__(self, pos: pygame.Vector2) -> None:
        self.state = 0
        self.pos = pos

    def draw(self):
        img = spring1 if self.state == 1 else spring0
        main_surface.blit(img, self.pos + pygame.Vector2(0, -vertical_offset - img.get_height()))


class Platform:
    def __init__(self, pos: pygame.Vector2, ptype: int = 0, spring: bool = False) -> None:
        self.pos = pos
        size = 71, 17
        if ptype == 0:
            self.img = pygame.image.load("./assets/pregular.png")
        if ptype == 1:
            self.img = pygame.image.load("./assets/pmoving.png")
        if ptype == 2:
            self.img = pygame.image.load("./assets/pweak.png")
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = convert(pos)
        self.shape = pymunk.Poly(
            self.body, vertices=((0, 0), (size[0], 0), size, (0, size[1]))
        )
        self.shape.density = 1
        self.shape.friction = 0.95
        self.shape.collision_type = 2
        self.shape.ptype = ptype
        self.shape.filter = pymunk.ShapeFilter(group=6)
        self.ptype = ptype
        self.direction = 1
        space.add(
            self.body,
            self.shape,
        )
        self.spring: Optional[Spring] = None
        if spring:
            xd = randint(0, self.img.get_width() - spring0.get_width())
            self.spring = Spring(self.pos + pygame.Vector2(xd, 0))

    def draw(self):
        pos = list(convert(self.body.position))
        pos[1] -= vertical_offset
        main_surface.blit(self.img, pos)
        if self.spring is not None:
            self.spring.draw()
        if self.ptype == 1:
            self.body.position = (
                self.body.position[0] + self.direction,
                self.body.position[1],
            )
        if self.body.position[0] < 0:
            self.direction = 1
        if (
            self.body.position[0]
            > main_surface.get_width() - self.img.get_width()
        ):
            self.direction = -1


class PlatformHalf:
    def __init__(self, pos, phtype: int) -> None:
        self.body = pymunk.Body()
        self.phtype = phtype
        if self.phtype == 0:
            self.img = pygame.image.load("./assets/pweak_half1.png")
        if self.phtype == 1:
            self.img = pygame.image.load("./assets/pweak_half2.png")
        self.size = self.img.get_size()
        self.body.position = pos
        self.shape = pymunk.Poly(self.body, vertices=(
            (0, 0),
            (self.size[0], 0),
            self.size,
            (0, self.size[1]),
        ), radius=1)
        self.shape.density = 1
        self.shape.filter = pymunk.ShapeFilter(group=6)
        space.add(self.body, self.shape)

    def draw(self):
        pos = list(convert(self.body.position))
        pos[1] += vertical_offset + self.img.get_height()/2
        pos[0] += self.img.get_width()/2
        angle = degrees(self.body.angle)
        img = pygame.transform.rotate(self.img, angle)
        dest = img.get_rect(center=pos)
        main_surface.blit(img, dest)


dog = Dog((250, 250))
platforms: List[Platform] = []
phalves: List[PlatformHalf] = []

y = 800
for i in range(400):
    ptype = choices((0, 1, 2), (0.7, 0.1, 0.2))[0]
    x = randint(0, 380)
    spring = randint(0, 5)
    platforms.append(Platform(pygame.Vector2(x, y), ptype=ptype, spring=(spring == 0 and ptype == 0)))
    y -= randint(50, 120)


jump_handler = space.add_collision_handler(1, 2)


def jump_begin(arb: pymunk.Arbiter, space: pymunk.Space, _: Any) -> bool:
    shape_dog, shape_platform = arb.shapes
    if shape_dog.body.velocity[1] > 0:
        return False
    if hasattr(shape_platform, "ptype"):
        if shape_platform.ptype == 2:
            try:
                p = list(filter(lambda x: x.shape == shape_platform, platforms))[0]
            except IndexError:
                return False
            platforms.remove(p)
            phalves.append(PlatformHalf(p.pos, 0))
            phalves.append(PlatformHalf((p.pos[0] + 40, p.pos[1]), 1))
            return False
    shape_dog.body.velocity = (0, 0)
    shape_dog.body.apply_impulse_at_local_point((0, 4 * 10**6), (0, 0))

    return False


jump_handler.begin = jump_begin

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()

    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_a]:
        dog.body.apply_impulse_at_local_point((-10**5, 0), (0, 0))
    if pressed[pygame.K_d]:
        dog.body.apply_impulse_at_local_point((10**5, 0), (0, 0))

    main_surface.fill((255, 255, 255))
    for p in platforms:
        p.draw()
    for h in phalves:
        h.draw()
    dog.draw()

    pygame.display.update()

    vertical_offset = convert(dog.body.position)[1] - 250

    clock.tick(60)
    space.step(1 / 60)
