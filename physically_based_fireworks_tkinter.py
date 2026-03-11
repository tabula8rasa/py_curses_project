import tkinter as tk
import random
import colorsys
import math
from dataclasses import dataclass


@dataclass
class Config:
    canvas_width: int = 1000
    canvas_height: int = 1000
    particle_size: int = 3
    particle_count: int = 300

    fps: int = 60
    dt: float = 1 / 60          # секунд на кадр
    g: float = 9.81             # м/с^2
    scale: float = 5.0         # пикселей в 1 метре

    explosion_x: float = 0.5    # доля ширины холста
    explosion_y: float = 0.3    # доля высоты холста

    v0_min: float = 0.1        # м/с
    v0_max: float = 18.0        # м/с


class Particle:
    def __init__(self, cfg: Config, i: int):
        self.cfg = cfg
        self.shape_id: int | None = None

        self.size = cfg.particle_size

        # экранная точка взрыва
        self.origin_x = cfg.explosion_x * cfg.canvas_width
        self.origin_y = cfg.explosion_y * cfg.canvas_height

        self.prev_x = self.origin_x
        self.prev_y = self.origin_y

        # физическое время
        self.t = 0.0

        # угол разлета
        self.theta = i * (2 * math.pi / cfg.particle_count)

        # начальная скорость, уже в м/с
        self.v0 = random.uniform(cfg.v0_min, cfg.v0_max)

        # цвет по кругу оттенков
        h, s, v = 0.5 + 0.1 * i / cfg.particle_count, 1.0, 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        # стартовые координаты
        self.x = self.origin_x
        self.y = self.origin_y

    def _physical_position(self, t: float) -> tuple[float, float]:
        """
        Возвращает положение в физических координатах (в метрах),
        где y направлена вверх.
        """
        x = self.v0 * math.cos(self.theta) * t
        y = self.v0 * math.sin(self.theta) * t - 0.5 * self.cfg.g * t * t
        return x, y

    def _screen_position(self, t: float) -> tuple[float, float]:
        """
        Переводит физические координаты в экранные пиксели.
        """
        x_phys, y_phys = self._physical_position(t)

        x_screen = self.origin_x + x_phys * self.cfg.scale
        y_screen = self.origin_y - y_phys * self.cfg.scale
        return x_screen, y_screen

    def draw(self, canvas: tk.Canvas) -> None:
        r = self.size
        self.shape_id = canvas.create_oval(
            self.x - r,
            self.y - r,
            self.x + r,
            self.y + r,
            fill=self.color,
            outline=""
        )

    def update(self) -> None:
        self.prev_x = self.x
        self.prev_y = self.y

        self.t += self.cfg.dt
        self.x, self.y = self._screen_position(self.t)

    def redraw(self, canvas: tk.Canvas) -> None:
        # след
        trail_r = max(1, self.size // 2)
        canvas.create_oval(
            self.prev_x - trail_r,
            self.prev_y - trail_r,
            self.prev_x + trail_r,
            self.prev_y + trail_r,
            fill=self.color,
            outline=""
        )

        # основная частица
        if self.shape_id is not None:
            r = self.size
            canvas.coords(
                self.shape_id,
                self.x - r,
                self.y - r,
                self.x + r,
                self.y + r
            )

    def is_outside(self) -> bool:
        return (
            self.x < -50
            or self.x > self.cfg.canvas_width + 50
            or self.y > self.cfg.canvas_height + 50
        )


def main() -> None:
    cfg = Config()

    root = tk.Tk()
    root.title("Physically based firework")

    canvas = tk.Canvas(
        root,
        width=cfg.canvas_width,
        height=cfg.canvas_height,
        bg="black"
    )
    canvas.pack()

    particles: list[Particle] = []
    for i in range(cfg.particle_count):
        p = Particle(cfg, i)
        particles.append(p)
        p.draw(canvas)

    def animate() -> None:
        alive = False

        for p in particles:
            if not p.is_outside():
                p.update()
                p.redraw(canvas)
                alive = True

        if alive:
            root.after(int(1000 / cfg.fps), animate)

    animate()
    root.mainloop()


if __name__ == "__main__":
    main()