import pygame
import random
import math
from settings import *
   
# UTILS

def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def normalize(dx, dy):
    length = math.hypot(dx, dy)
    if length == 0:
        return 0, 0
    return dx / length, dy / length

# UI CONTROLS

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


class Slider:
    def __init__(self, x, y, w, label, min_val, max_val, default, step=0.01, precision=2):
        self.x = x
        self.y = y
        self.w = w
        self.label = label
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.value = float(default)
        self.step = step
        self.precision = precision
        self.dragging = False

        self.track_rect = pygame.Rect(x, y + 18, w, 6)
        self.knob_radius = 8
        self.knob_x = self._value_to_knob(self.value)
        self.knob_y = self.track_rect.y + self.track_rect.h // 2

    def _value_to_knob(self, v):
        v = max(self.min_val, min(self.max_val, v))
        t = (v - self.min_val) / (self.max_val - self.min_val)
        return self.track_rect.x + int(t * self.track_rect.w)

    def _knob_to_value(self, kx):
        kx = max(self.track_rect.x, min(self.track_rect.x + self.track_rect.w, kx))
        t = (kx - self.track_rect.x) / self.track_rect.w
        v = self.min_val + t * (self.max_val - self.min_val)
        if self.step:
            v = round(v / self.step) * self.step
        v = max(self.min_val, min(self.max_val, v))
        return round(v, self.precision)

    def handle_event(self, event, pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dx = pos[0] - self.knob_x
            dy = pos[1] - self.knob_y
            if dx * dx + dy * dy <= self.knob_radius * self.knob_radius * 4:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.knob_x = pos[0]
            self.value = self._knob_to_value(self.knob_x)

    def update(self):
        self.knob_x = self._value_to_knob(self.value)

    def draw(self, screen, font):
        label = font.render(f"{self.label}: {self.value:.{self.precision}f}", True, (200, 200, 200))
        screen.blit(label, (self.x, self.y))

        pygame.draw.rect(screen, (120, 120, 120), self.track_rect)
        pygame.draw.circle(screen, (220, 220, 220), (self.knob_x, self.knob_y), self.knob_radius)

# ANIMALS
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


class Prey(Animal):
    def __init__(self, x, y, speed, repro_threshold):
        super().__init__(x, y, speed, (0, 255, 0), 30, repro_threshold)

    def update(self, predators, params):
        self.energy -= params["prey_energy_loss"]
        self.energy += params["prey_graze_gain"]

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


class Predator(Animal):
    def __init__(self, x, y, speed, repro_threshold):
        super().__init__(x, y, speed, (255, 0, 0), 40, repro_threshold)

    def update(self, prey_list, params):
        self.energy -= params["pred_energy_loss"]

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


# WORLD

class World:
    def __init__(self, params):
        self.params = params
        self.predators = [
            Predator(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT - UI_HEIGHT),
                params["pred_speed"],
                params["pred_repro"]
            )
            for _ in range(5)
        ]
        self.prey = [
            Prey(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT - UI_HEIGHT),
                params["prey_speed"],
                params["prey_repro"]
            )
            for _ in range(20)
        ]

    def update(self):
        for p in self.predators:
            p.speed = self.params["pred_speed"]
            p.repro_threshold = self.params["pred_repro"]
        for pr in self.prey:
            pr.speed = self.params["prey_speed"]
            pr.repro_threshold = self.params["prey_repro"]

        new_preds = []
        for p in self.predators:
            baby = p.update(self.prey, self.params)
            if baby:
                new_preds.append(baby)

        new_prey = []
        for p in self.prey:
            baby = p.update(self.predators, self.params)
            if baby:
                new_prey.append(baby)

        for pred in self.predators:
            for pr in list(self.prey):
                if distance(pred, pr) < (pred.size + pr.size):
                    pred.energy += self.params["pred_eat_gain"]
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


# SIMULATION

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Predator Prey Simulation (Tunable)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)

        self.running = True
        self.paused = False

        self.params = {
            "pred_speed": DEFAULT_PREDATOR_SPEED,
            "prey_speed": DEFAULT_PREY_SPEED,
            "pred_repro": DEFAULT_PREDATOR_REPRO_THRESHOLD,
            "prey_repro": DEFAULT_PREY_REPRO_THRESHOLD,
            "pred_energy_loss": DEFAULT_PREDATOR_ENERGY_LOSS,
            "prey_energy_loss": DEFAULT_PREY_ENERGY_LOSS,
            "pred_eat_gain": DEFAULT_PREDATOR_EAT_GAIN,
            "prey_graze_gain": DEFAULT_PREY_GRAZE_GAIN,
        }

        btn_w = 90
        btn_h = 24
        self.btn_start = Button(20, HEIGHT - 90, btn_w, btn_h, "Start/Pause")
        self.btn_reset = Button(120, HEIGHT - 90, btn_w, btn_h, "Reset")
        self.btn_add_pred = Button(220, HEIGHT - 90, btn_w, btn_h, "Add Pred")
        self.btn_add_prey = Button(320, HEIGHT - 90, btn_w, btn_h, "Add Prey")

        slider_x = 480
        slider_y_base = HEIGHT - 110
        slider_w = 260
        slider_spacing_y = 24

        self.sliders = [
            Slider(slider_x, slider_y_base + 0, slider_w, "Pred Speed", 0.5, 10.0, self.params["pred_speed"], step=0.1),
            Slider(slider_x, slider_y_base + slider_spacing_y, slider_w, "Prey Speed", 0.5, 10.0, self.params["prey_speed"], step=0.1),
            Slider(slider_x, slider_y_base + slider_spacing_y * 2, slider_w, "Pred Repro", 10.0, 120.0, self.params["pred_repro"], step=1.0),
            Slider(slider_x, slider_y_base + slider_spacing_y * 3, slider_w, "Prey Repro", 10.0, 120.0, self.params["prey_repro"], step=1.0),

            Slider(slider_x + slider_w + 40, slider_y_base + 0, slider_w, "Pred Loss", 0.0, 2.0, self.params["pred_energy_loss"], step=0.01),
            Slider(slider_x + slider_w + 40, slider_y_base + slider_spacing_y, slider_w, "Prey Loss", 0.0, 2.0, self.params["prey_energy_loss"], step=0.01),
            Slider(slider_x + slider_w + 40, slider_y_base + slider_spacing_y * 2, slider_w, "Pred Eat+", 0.0, 100.0, self.params["pred_eat_gain"], step=1.0),
            Slider(slider_x + slider_w + 40, slider_y_base + slider_spacing_y * 3, slider_w, "Prey Graze+", 0.0, 2.0, self.params["prey_graze_gain"], step=0.01),
        ]

        self.reset_world()

    def reset_world(self):
        self.world = World(self.params)

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused:
                self.world.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            for s in self.sliders:
                s.handle_event(event, pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_start.clicked(pos):
                    self.paused = not self.paused
                elif self.btn_reset.clicked(pos):
                    self.reset_world()
                elif self.btn_add_pred.clicked(pos):
                    self.world.predators.append(
                        Predator(
                            random.randint(0, WIDTH),
                            random.randint(0, HEIGHT - UI_HEIGHT),
                            self.params["pred_speed"],
                            self.params["pred_repro"]
                        )
                    )
                elif self.btn_add_prey.clicked(pos):
                    self.world.prey.append(
                        Prey(
                            random.randint(0, WIDTH),
                            random.randint(0, HEIGHT - UI_HEIGHT),
                            self.params["prey_speed"],
                            self.params["prey_repro"]
                        )
                    )

        self.params["pred_speed"] = self.sliders[0].value
        self.params["prey_speed"] = self.sliders[1].value
        self.params["pred_repro"] = self.sliders[2].value
        self.params["prey_repro"] = self.sliders[3].value
        self.params["pred_energy_loss"] = self.sliders[4].value
        self.params["prey_energy_loss"] = self.sliders[5].value
        self.params["pred_eat_gain"] = self.sliders[6].value
        self.params["prey_graze_gain"] = self.sliders[7].value

        for s in self.sliders:
            s.update()

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.world.draw(self.screen)

        pygame.draw.line(
            self.screen,
            (30, 30, 30),
            (0, HEIGHT - UI_HEIGHT),
            (WIDTH, HEIGHT - UI_HEIGHT),
            2
        )

        self.btn_start.draw(self.screen, self.font)
        self.btn_reset.draw(self.screen, self.font)
        self.btn_add_pred.draw(self.screen, self.font)
        self.btn_add_prey.draw(self.screen, self.font)

        counts = f"Predators: {len(self.world.predators)}   Prey: {len(self.world.prey)}"
        count_surf = self.font.render(counts, True, (200, 200, 200))
        count_rect = count_surf.get_rect()
        count_rect.top = 10
        count_rect.right = WIDTH - 10
        self.screen.blit(count_surf, count_rect)

        for s in self.sliders:
            s.draw(self.screen, self.font)

        pygame.display.flip()
