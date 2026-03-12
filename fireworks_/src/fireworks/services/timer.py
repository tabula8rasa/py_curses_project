import time

class Timer:
    def __init__(self, *, dt: float, delay: int):
        self.last = time.perf_counter()
        self.dt = dt
        self.delay = delay
        self.counter = 0

    def wait_frame(self) -> None:
        now = time.perf_counter()
        elapsed = now - self.last

        if elapsed < self.dt:
            time.sleep(self.dt - elapsed)
            now = time.perf_counter()

        self.last = now