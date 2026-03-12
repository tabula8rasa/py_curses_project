import tkinter as tk

BACKGROUND = "black"
FOREGROUND = "white"

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
POINT_RADIUS = 10
FPS = 120

root = tk.Tk()
root.title("Tkinter canvas")

game = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=BACKGROUND, highlightthickness=0)
game.pack()

def clear() -> None:
    game.delete("all")
    '''
    game.create_rectangle(
        0, 0, game.winfo_width(), game.winfo_height(),
        fill=BACKGROUND,
        outline=BACKGROUND
    )
    '''


class Point:
    
    def __init__(self, x_n: float, y_n: float, z_n: float):
        self.x_normalized: float = x_n
        self.y_normalized: float = y_n
        self.z_normalized: float = z_n
        self.radius: float = POINT_RADIUS

    def update(self):
        self.z_normalized += 1/FPS

def render(point: Point) -> None:
    x_screen: float = (point.x_normalized/point.z_normalized + 1)/2 * game.winfo_width()
    y_screen: float = (1 - (point.y_normalized/point.z_normalized + 1)/2) * game.winfo_height()

    game.create_rectangle(
        x_screen-point.radius, 
        y_screen-point.radius,
        x_screen+point.radius,
        y_screen+point.radius,
        fill=FOREGROUND,
        outline=FOREGROUND
    )

def animate(points: list[Point]) -> None:
    clear()

    for point in points:
        point.update()
        render(point)

    root.after(int(1000/FPS), animate, points)

root.update_idletasks()

points = [
    Point(x_n=0.5, y_n=0.5, z_n=1), 
    Point(x_n=-0.5, y_n=0.5, z_n=1), 
    Point(x_n=0.5, y_n=-0.5, z_n=1), 
    Point(x_n=-0.5, y_n=-0.5, z_n=1),
]

animate(points)
root.mainloop()