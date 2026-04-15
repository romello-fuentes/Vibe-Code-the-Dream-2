import pygame
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider, win
import random

# -----------------
# Constants
# -----------------
WIDTH = 800
HEIGHT = 600
FPS = 30

NUM_PREDATORS = 3
NUM_PREY = 10

Prey_slider = None

# -----------------
# Animal Base Class
# -----------------
class Animal:
    def __init__(self, x, y, speed, color):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = 8

    def move_random(self):
        self.x += random.randint(-self.speed, self.speed)
        self.y += random.randint(-self.speed, self.speed)

        # keep inside screen
        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)


# -----------------
# Prey Class
# -----------------
class Prey(Animal):
    def __init__(self, x, y):
        super().__init__(x, y, speed=3, color=(0, 255, 0))

    def update(self):
        self.move_random()


# -----------------
# Predator Class
# -----------------
class Predator(Animal):
    def __init__(self, x, y):
        super().__init__(x, y, speed=4, color=(255, 0, 0))

    def update(self):
        self.move_random()


# -----------------
# World Class
# -----------------
class World:
    def __init__(self):
        self.predators = []
        self.prey = []

        for _ in range(NUM_PREDATORS):
            self.predators.append(
                Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT))
            )

        for _ in range(NUM_PREY):
            self.prey.append(
                Prey(random.randint(0, WIDTH), random.randint(0, HEIGHT))
            )

    def update(self):
        for p in self.predators:
            p.update()

        for p in self.prey:
            p.update()

    def draw(self, screen):
        for p in self.predators:
            p.draw(screen)

        for p in self.prey:
            p.draw(screen)


# -----------------
# Simulation Class
# -----------------
class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Predator Prey Simulation")
        self.clock = pygame.time.Clock()

        self.world = World()

        self.running = True

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        self.world.update()

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.world.draw(self.screen)
        pygame.display.flip()


# -----------------
# Run Program
# -----------------
if __name__ == "__main__":
    sim = Simulation()
    sim.run()