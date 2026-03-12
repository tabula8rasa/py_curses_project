import time
from fireworks.config import Config

class Timer:
    def __init__(self, config: Config):
        self.last = time.perf_counter()
        self.config = config
        self.counter = 0

    def wait_frame(self) -> None:
        now = time.perf_counter()
        elapsed = now - self.last

        if elapsed < self.config.dt:
            time.sleep(self.config.dt - elapsed)
            now = time.perf_counter()

        self.last = now