from dataclasses import dataclass, field

@dataclass
class Config():
    fps: int = 90                               # частота кадров в секунду
    dt: float = field(init=False)               # длительность одного кадра

    scale_x: float = 3.5                        # масштаб по X Сколько пикселей в одном метре по горизонтале
    scale_y: float = 2.0                        # масштаб по Y

    g: float = 9.81                             # ускорение свободного падения

    v_min: float = 0.0                          # минимальная начальная скорость
    v_max: float = 16.0                         # базовая начальная скорость

    num_particles_min: int = 150                # число частиц
    num_particles_max: int = 200

    head_frames: list[str] = field(
        default_factory=lambda: list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )                                           # символы головы

    tail_frames: list[str] = field(
        default_factory=lambda: list("0123456789")
    )                                           # символы хвоста

    confetti_frames: list[str] = field(
        default_factory=lambda: list("()|\\?/.!")
    )

    confetti_init_coef_for_vy: float = 0.5
    confetti_init_vy: float = field(init = False)

    confetti_lifetime_min: int = 50
    confetti_lifetime_max: int = 70

    tail_len_min: int = 15                      # длина хвоста
    tail_len_max: int = 20

    tail_change_base: int = 20                  # базовый интервал смены хвоста
    tail_change_delta: int = 5                  # разброс интервала хвоста

    head_change_base: int = 20                  # базовый интервал смены головы
    head_change_delta: int = 5                  # разброс интервала головы

    death_base: int = 120                       # базовое время жизни
    death_delta: int = 5                        # разброс времени жизни

    is_or_not_bold = [True]                     #[False]: только обычные, [True]: только жирыне, [False, True]: оба варианта
    has_or_not_confetti = [False, True]

    time_delay_to_a_new_firework: int = 200

    firework_color_schemas: list[list[int]] = field(
        default_factory=lambda: [[6,9,12], [0], [0,3], [18], [12,15,18], [0,3,6,9,12,15,18], [21], [24], [27]]
    )

    def __post_init__(self):
        if self.fps <= 0:
            raise ValueError("fps must be > 0")
        if self.scale_x <= 0 or self.scale_y <= 0:
            raise ValueError("scale_x and scale_y must be > 0")
        if self.v_min > self.v_max:
            raise ValueError("v_min should not greater that v")
        self.dt = 1.0 / self.fps
        self.confetti_init_vy = self.g * self.confetti_init_coef_for_vy

config = Config()