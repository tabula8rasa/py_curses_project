import tkinter as tk

BACKGROUND = "black"
FOREGROUND = "white"

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
POINT_RADIUS = 20

root = tk.Tk()
root.title("Tkinter canvas")

game = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=BACKGROUND, highlightthickness=0)
game.pack()


class Point:
    
    def __init__(self, x_n: float, y_n: float):
        self.x_normalized: float = x_n
        self.y_normalized: float = y_n
        self.x_screen: float = (self.x_normalized + 1)/2 * game.winfo_width()
        self.y_screen: float = (self.y_normalized + 1)/2 * game.winfo_height()
        self.radius: float = POINT_RADIUS


def clear() -> None:
    game.delete("all")
    '''
    game.create_rectangle(
        0, 0, game.winfo_width(), game.winfo_height(),
        fill=BACKGROUND,
        outline=BACKGROUND
    )
    '''


def render(point: Point) -> None:
    game.create_rectangle(
        point.x_screen-point.radius, 
        point.y_screen-point.radius,
        point.x_screen+point.radius,
        point.y_screen+point.radius,
        fill=FOREGROUND,
        outline=FOREGROUND
    )


root.update_idletasks()

clear()
point = Point(0.5, 0)
render(point)

root.mainloop()