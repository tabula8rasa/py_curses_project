from __future__ import annotations
import math
import random
import curses

from ..config import Config
from ..domain.particle import Particle
from ..services.randomizer import Randomizer
from ..ui.screen_mapper import ScreenMapper

class Firework:
    def __init__(self, config: Config, setup: ScreenMapper, randomizer: Randomizer, stdscr: curses.window):

        self.cx = random.randint(int(setup.world_width_m * 0.2), int(setup.world_width_m * 0.8))
        self.cy = random.randint(int(setup.world_height_m * 0.4), int(setup.world_height_m * 0.6))

        self.color_scheme_bunch = randomizer.rnd.choice(config.firework_color_schemas)

        self.tail_len = randomizer.rnd.randint(config.tail_len_min, config.tail_len_max)
        self.num_particles = randomizer.rnd.randint(config.num_particles_min, config.num_particles_max)
        self.is_bold: bool = randomizer.rnd.choice(config.is_or_not_bold)
        self.has_confetti: bool = randomizer.rnd.choice(config.has_or_not_confetti)

        self.particles: list[Particle] = self.generate_particles(config, setup, randomizer, stdscr)

    def generate_particles(self, config: Config, setup: ScreenMapper, randomizer: Randomizer, stdscr: curses.window):
        particles: list[Particle] = []

        for i in range(self.num_particles):
            phi = 2.0 * math.pi * i / self.num_particles
            v = random.uniform(config.v_min, config.v_max)
            particles.append(Particle(phi, 
                v, 
                config, 
                setup, 
                randomizer, 
                stdscr, 
                self.cx, self.cy, 
                self.color_scheme_bunch, 
                self.tail_len, 
                self.is_bold,
                self.has_confetti
            ))

        return particles

    def render_firework(self) -> bool:
        firework_is_alive: bool = False

        for particle in self.particles:
            if particle.alive:
                firework_is_alive = True
                particle.render_particle()

        return firework_is_alive
    
    def update_particles(self) -> None:

        for particle in self.particles:
            if not particle.alive:
                continue

            particle.update_state()
