import pygame
import random
import math
from settings import *

# Functions

def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def normalize(dx, dy):
    length = math.hypot(dx, dy)
    if length == 0:
        return 0, 0
    return dx / length, dy / length


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (80, 80, 80), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, (self.rect.x + 5, self.rect.y + 5))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


# Base Animal Class

class Animal:
    def __init__(self, x, y, speed, color, energy, repro_threshold):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.energy = energy
        self.repro_threshold = repro_threshold
        self.repro_cooldown = 0
        self.size = 8

        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT - UI_HEIGHT, self.y))

    def wander(self):
        self.dx += random.uniform(-0.1, 0.1)
        self.dy += random.uniform(-0.1, 0.1)

        length = math.hypot(self.dx, self.dy)
        if length != 0:
            self.dx /= length
            self.dy /= length

        self.move(self.dx, self.dy)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)


# Prey

class Prey(Animal):
    def __init__(self, x, y, speed, repro_threshold):
        super().__init__(x, y, speed, (0, 255, 0), 30, repro_threshold)

    def update(self, predators):
        self.energy -= PREY_ENERGY_LOSS
        self.energy += PREY_GRAZE_GAIN

        nearest = None
        nearest_dist = FEAR_RADIUS

        for p in predators:
            d = distance(self, p)
            if d < nearest_dist:
                nearest = p
                nearest_dist = d

        if nearest:
            dx, dy = normalize(self.x - nearest.x, self.y - nearest.y)
            self.move(dx, dy)
        else:
            self.wander()

        self.repro_cooldown = max(0, self.repro_cooldown - 1)

        if self.energy > self.repro_threshold and self.repro_cooldown == 0:
            self.energy *= 0.5
            self.repro_cooldown = 120
            return Prey(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT - UI_HEIGHT),
                self.speed,
                self.repro_threshold
            )
        return None

# Predator

class Predator(Animal):
    def __init__(self, x, y, speed, repro_threshold):
        super().__init__(x, y, speed, (255, 0, 0), 40, repro_threshold)

    def update(self, prey_list):
        self.energy -= PREDATOR_ENERGY_LOSS

        nearest = None
        nearest_dist = SEEK_RADIUS

        for p in prey_list:
            d = distance(self, p)
            if d < nearest_dist:
                nearest = p
                nearest_dist = d

        if nearest:
            dx, dy = normalize(nearest.x - self.x, nearest.y - self.y)
            self.move(dx, dy)
        else:
            self.wander()

        self.repro_cooldown = max(0, self.repro_cooldown - 1)

        if self.energy > self.repro_threshold and self.repro_cooldown == 0:
            self.energy = max(self.energy * 0.5, 25)
            self.repro_cooldown = 180
            return Predator(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT - UI_HEIGHT),
                self.speed,
                self.repro_threshold
            )
        return None


# World

class World:
    def __init__(self, pred_speed, prey_speed, pred_repro, prey_repro):
        self.predators = [
            Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT - UI_HEIGHT), pred_speed, pred_repro)
            for _ in range(3)
        ]

        self.prey = [
            Prey(random.randint(0, WIDTH), random.randint(0, HEIGHT - UI_HEIGHT), prey_speed, prey_repro)
            for _ in range(10)
        ]

    def update(self):
        new_preds = []
        for p in self.predators:
            baby = p.update(self.prey)
            if baby:
                new_preds.append(baby)

        new_prey = []
        for p in self.prey:
            baby = p.update(self.predators)
            if baby:
                new_prey.append(baby)

        # collisions
        for pred in self.predators:
            for pr in list(self.prey):
                if distance(pred, pr) < (pred.size + pr.size):
                    pred.energy += PREDATOR_EAT_GAIN
                    self.prey.remove(pr)

        self.predators = [p for p in self.predators if p.energy > 0]
        self.prey = [p for p in self.prey if p.energy > 0]

        self.predators.extend(new_preds)
        self.prey.extend(new_prey)

        if len(self.prey) > MAX_PREY:
            self.prey = random.sample(self.prey, MAX_PREY)

    def draw(self, screen):
        for p in self.predators:
            p.draw(screen)
        for p in self.prey:
            p.draw(screen)


# Simulation

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Predator Prey Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)

        self.running = True
        self.paused = False

        # Buttons
        self.btn_start = Button(20, HEIGHT - 60, 120, 30, "Start/Pause")
        self.btn_reset = Button(160, HEIGHT - 60, 120, 30, "Reset")
        self.btn_add_pred = Button(320, HEIGHT - 60, 140, 30, "Add Predator")
        self.btn_add_prey = Button(480, HEIGHT - 60, 140, 30, "Add Prey")

        self.reset_world()

    def reset_world(self):
        self.world = World(
            DEFAULT_PREDATOR_SPEED,
            DEFAULT_PREY_SPEED,
            DEFAULT_PREDATOR_REPRO_THRESHOLD,
            DEFAULT_PREY_REPRO_THRESHOLD
        )

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused:
                self.world.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                if self.btn_start.clicked(pos):
                    self.paused = not self.paused

                elif self.btn_reset.clicked(pos):
                    self.reset_world()

                elif self.btn_add_pred.clicked(pos):
                    self.world.predators.append(
                        Predator(
                            random.randint(0, WIDTH),
                            random.randint(0, HEIGHT - UI_HEIGHT),
                            DEFAULT_PREDATOR_SPEED,
                            DEFAULT_PREDATOR_REPRO_THRESHOLD
                        )
                    )

                elif self.btn_add_prey.clicked(pos):
                    self.world.prey.append(
                        Prey(
                            random.randint(0, WIDTH),
                            random.randint(0, HEIGHT - UI_HEIGHT),
                            DEFAULT_PREY_SPEED,
                            DEFAULT_PREY_REPRO_THRESHOLD
                        )
                    )

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.world.draw(self.screen)

        # UI bar
        pygame.draw.line(
            self.screen,
            (30, 30, 30),
            (0, HEIGHT - UI_HEIGHT),
            (WIDTH, HEIGHT - UI_HEIGHT),
            2
        )

        # Buttons
        self.btn_start.draw(self.screen, self.font)
        self.btn_reset.draw(self.screen, self.font)
        self.btn_add_pred.draw(self.screen, self.font)
        self.btn_add_prey.draw(self.screen, self.font)

        pygame.display.flip()