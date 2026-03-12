import tkinter as tk
import math

BACKGROUND = "black"
FOREGROUND = "white"

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 800
POINT_RADIUS = 10
FPS = 60

root = tk.Tk()
game = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=BACKGROUND, highlightthickness=0)
game.pack()


def clear() -> None:
    game.delete("all")


class Point:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z


def rotate_xz(point: Point, angle: float) -> Point:
    c = math.cos(angle)
    s = math.sin(angle)
    return Point(
        x=point.x * c - point.z * s,
        y=point.y,
        z=point.x * s + point.z * c,
    )


def translate_z(point: Point, dz: float) -> Point:
    return Point(point.x, point.y, point.z + dz)


def project(point: Point) -> tuple[float, float]:
    return point.x / point.z, point.y / point.z


def screen(x: float, y: float) -> tuple[float, float]:
    x_screen = (x + 1) / 2 * game.winfo_width()
    y_screen = (1 - (y + 1) / 2) * game.winfo_height()
    return x_screen, y_screen

def line(x1: float, y1: float, x2: float, y2: float):
    game.create_line(x1, y1, x2, y2, fill=FOREGROUND, width=3)

def render(x_screen: float, y_screen: float) -> None:

    game.create_rectangle(
        x_screen - POINT_RADIUS,
        y_screen - POINT_RADIUS,
        x_screen + POINT_RADIUS,
        y_screen + POINT_RADIUS,
        fill=FOREGROUND,
        outline=FOREGROUND,
    )


angle = 0.0
dz = 1.0


def animate(points: list[Point]) -> None:
    global angle, dz

    dt = 1 / FPS
    dz += 1*dt
    angle += math.pi * dt

    clear()

    #for point in points:
        #render(*screen(*project(translate_z(rotate_xz(point, angle), dz))))

    for face in faces:
        for i in range(0, len(face)):
            a = points[face[i]]
            b = points[face[(i+1)%len(face)]]
            line(
                *screen(*project(translate_z(rotate_xz(a, angle), dz))),
                *screen(*project(translate_z(rotate_xz(b, angle), dz)))
            )

    root.after(int(1000 / FPS), animate, points)


root.update_idletasks()

points = [
    Point(0.5, 0.5, 0.5),
    Point(-0.5, 0.5, 0.5),
    Point(-0.5, -0.5, 0.5),
    Point(0.5, -0.5, 0.5),

    Point(0.5, 0.5, -0.5),
    Point(-0.5, 0.5, -0.5),
    Point(-0.5, -0.5, -0.5),
    Point(0.5, -0.5, -0.5),
]

faces = [
    [0, 1, 2, 3],
    [4 ,5, 6, 7],
    [0,4],
    [1,5],
    [2,6],
    [3,7],

]

animate(points)
root.mainloop()