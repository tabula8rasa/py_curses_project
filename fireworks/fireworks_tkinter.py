import tkinter as tk
import random
import colorsys
import math
from dataclasses import dataclass

class Particle:
    def __init__(self, size: int, canvas_width: int, canvas_height: int, particle_count: int, i: int):
        
        self.shape_id: int | None = None
        self.size = size
        self.x = 0.5 * canvas_width
        self.y = 0.3 * canvas_height
        self.prev_x = 0.5 * canvas_width
        self.prev_y = 0.3 * canvas_height

        v = 1.6 * random.random()
        self.vx = v * math.cos(i * ((2 * math.pi) / particle_count))
        self.vy = v * math.sin(i * ((2 * math.pi) / particle_count))

        h, s, v = i * (1.0 / particle_count), 1.0, 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        self.color = f"#{r:02x}{g:02x}{b:02x}"

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

    def update(self, width: int, height: int) -> None:
        # запоминаем прошлую позицию
        self.prev_x = self.x
        self.prev_y = self.y

        self.x += self.vx
        self.y += self.vy
        self.vy += 0.01 # гравитация

    def redraw(self, canvas: tk.Canvas) -> None:
        # рисуем след в предыдущей позиции
        
        trail_r = max(1, self.size // 2)
        trail_r = self.size
        canvas.create_oval(
            self.prev_x - trail_r,
            self.prev_y - trail_r,
            self.prev_x + trail_r,
            self.prev_y + trail_r,
            fill=self.color,
            outline=""
        )

        # двигаем основную частицу
        if self.shape_id is not None:
            r = self.size
            canvas.coords(
                self.shape_id,
                self.x - r,
                self.y - r,
                self.x + r,
                self.y + r
            )

@dataclass
class Config:
    canvas_width: int = 1000
    canvas_height: int = 1000
    particle_size: int = 3
    particle_count: int = 300

def main():

    cfg = Config()
    # Главное окно
    root = tk.Tk()
    root.title("Firework")

    canvas = tk.Canvas(root, width=cfg.canvas_width, height=cfg.canvas_height, bg="black")
    canvas.pack()


    particles: list[Particle] = []

    for i in range(cfg.particle_count):
        
        particle = Particle(cfg.particle_size, cfg.canvas_width, cfg.canvas_height, cfg.particle_count, i)
        particles.append(particle)
        particle.draw(canvas)


    def animate() -> None:
        for particle in particles:
            particle.update(cfg.canvas_width, cfg.canvas_height)
            particle.redraw(canvas)

        root.after(16, animate)


    animate()
    root.mainloop()


if __name__ == "__main__":
    main()
