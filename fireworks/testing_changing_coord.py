import tkinter as tk
import math
import time 

BACKGROUND = "black"
FOREGROUND = "white"

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 800
POINT_RADIUS = 5
FPS = 60
SCALE = min(CANVAS_WIDTH, CANVAS_HEIGHT) / 2


root = tk.Tk()
game = tk.Canvas(
    root,
    width=CANVAS_WIDTH,
    height=CANVAS_HEIGHT,
    bg=BACKGROUND,
    highlightthickness=0,
)
game.pack()


def clear() -> None:
    game.delete("all")


class Point:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def copy(self) -> "Point":
        return Point(self.x, self.y, self.z)


class Mesh:
    def __init__(self, points: list[Point], edges: list[list[int]]):
        self.points = points
        self.edges = edges

    def rotate_y(self, angle: float) -> None:
        """Поворачивает сам объект вокруг оси Y (плоскость XZ)."""
        c = math.cos(angle)
        s = math.sin(angle)

        for point in self.points:
            old_x = point.x
            old_z = point.z

            point.x = old_x * c - old_z * s
            point.z = old_x * s + old_z * c

    def move_z(self, dz: float) -> None:
        """Сдвигает сам объект по оси Z."""
        for point in self.points:
            point.z += dz


def project(point: Point) -> tuple[float, float]:
    return point.x / point.z, point.y / point.z


def screen(x: float, y: float) -> tuple[float, float]:
    x_screen = CANVAS_WIDTH / 2 + x * SCALE
    y_screen = CANVAS_HEIGHT / 2 - y * SCALE
    return x_screen, y_screen


def line(x1: float, y1: float, x2: float, y2: float) -> None:
    game.create_line(x1, y1, x2, y2, fill=FOREGROUND, width=3)


def render_point(x_screen: float, y_screen: float) -> None:
    game.create_oval(
        x_screen - POINT_RADIUS,
        y_screen - POINT_RADIUS,
        x_screen + POINT_RADIUS,
        y_screen + POINT_RADIUS,
        fill=FOREGROUND,
        outline=FOREGROUND,
    )


def render_mesh(mesh: Mesh) -> None:
    clear()

    # Можно рисовать точки
    for point in mesh.points:
        # защита от деления на ноль и точек "за камерой"
        if point.z <= 0:
            continue
        render_point(*screen(*project(point)))

    # И рёбра
    for edge in mesh.edges:
        a = mesh.points[edge[0]]
        b = mesh.points[edge[1]]


        line(
            *screen(*project(a)),
            *screen(*project(b)),
        )

def on_s(event):
    print("sleep start")
    time.sleep(10)
    print("sleep end")


def make_animator(mesh: Mesh):
    dt = 1 / FPS
    angular_speed = math.pi  # рад/сек
    dz = 1/(10*FPS)

    def animate() -> None:


        root.bind("s", on_s)

        # 1. Обновляем состояние объекта
        mesh.move_z(dz)
        #mesh.rotate_y(2*math.pi/dt)
        print(mesh.points[0].z)

        # 2. Рендерим уже изменённый объект
        render_mesh(mesh)

        root.after(int(1000 / FPS), animate)

    return animate


cube_points = [
    Point(0.5, 0.5, 2.5),
    Point(-0.5, 0.5, 2.5),
    Point(-0.5, -0.5, 2.5),
    Point(0.5, -0.5, 2.5),

    Point(0.5, 0.5, 1.5),
    Point(-0.5, 0.5, 1.5),
    Point(-0.5, -0.5, 1.5),
    Point(0.5, -0.5, 1.5),
]

cube_edges = [
    [0, 1], [1, 2], [2, 3], [3, 0],
    [4, 5], [5, 6], [6, 7], [7, 4],
    [0, 4], [1, 5], [2, 6], [3, 7],
]

cube_points_1 = [
    Point(0.25, 0.5, 0)
]

cube_edges_1 = [
]

cube = Mesh(cube_points_1, cube_edges_1)

animate = make_animator(cube)
animate()
root.mainloop()