import random
from ..config import Config

class Randomizer:
    def __init__(self, config: Config, rnd: random.Random):
        self.config = config
        self.rnd = rnd

    def random_change_delay(self, base: int, delta: int) -> int:
        return max(1, base + self.rnd.randint(-delta, delta))

    def random_death_after(self) -> int:
        return max(
            1,
            self.config.death_base
            + self.rnd.randint(-self.config.death_delta, self.config.death_delta)
        )