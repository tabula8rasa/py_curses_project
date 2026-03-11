#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import curses
import time
import argparse
import numpy as np
from typing import Any

# Глифы для замены яркости пикселя (от тёмного к светлому)
ASCII_CHARS: str = "#@%* "


def pixel_to_ascii(pixel_value: int | np.uint8) -> str:
    """Преобразует значение яркости (0-255) в символ ASCII."""
    # Индекс в списке ASCII_CHARS: чем светлее пиксель, тем меньше индекс
    index: int = int(pixel_value / 255 * (len(ASCII_CHARS) - 1))
    return ASCII_CHARS[index]

# Вместо MatLike лучше использовать np.ndarray, если нет специфических нужд
def frame_to_ascii(frame: np.ndarray, new_width: int, new_height: int) -> list[str]:
    resized = cv2.resize(
        frame, (new_width, new_height), interpolation=cv2.INTER_AREA
    )

    # Убеждаемся, что работаем с массивом numpy явно
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    ascii_img: list[str] = []
    for y in range(new_height):
        row_chars: list[str] = []
        for x in range(new_width):
            pixel = int(gray[y, x]) 
            row_chars.append(pixel_to_ascii(pixel))
        ascii_img.append("".join(row_chars))
    
    return ascii_img


def main(stdscr: curses.window, video_path: str) -> None:
    curses.start_color()
    if curses.has_colors():
        # Определяем пару №1: красный текст на чёрном фоне
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        # Пару №2: зелёный текст на синем фоне
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    # Настройка curses
    curses.curs_set(0)  # скрыть курсор
    stdscr.nodelay(True)  # неблокирующий ввод
    stdscr.timeout(0)  # timeout для getch()

    # Получение размеров терминала (количество символов)
    height: int
    width: int
    height, width = stdscr.getmaxyx()

    # Чтение видео
    cap: cv2.VideoCapture = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Не удалось открыть видео: {video_path}")

    # Параметры видео
    fps: float = float(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0:
        fps = 30  # значение по умолчанию
    delay: float = 1.0 / fps

    # Основной цикл воспроизведения
    while True:
        start_time: float = time.time()

        ret: bool
        frame: np.ndarray[Any, np.dtype[np.generic]]
        ret, frame = cap.read()
        if not ret:
            break  # конец видео

        # Преобразование кадра в ASCII
        # Для компенсации соотношения сторон символов уменьшаем ширину в 2 раза
        ascii_frame: list[str] = frame_to_ascii(frame, width, height)

        # Вывод ASCII-изображения
        stdscr.clear()
        for y, line in enumerate(ascii_frame):
            if y < height:
                try:
                    stdscr.addstr(y, 0, line[:width], curses.color_pair(2))
                except curses.error:
                    # Игнорируем ошибки при попытке записи за пределы экрана
                    pass
        stdscr.refresh()

        # Проверка нажатия клавиши 'q' для выхода
        key: int = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            break

        # Синхронизация с FPS
        elapsed: float = time.time() - start_time
        if elapsed < delay:
            time.sleep(delay - elapsed)

    cap.release()


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Воспроизведение Bad Apple в терминале через ASCII-графику"
    )
    parser.add_argument(
        "video",
        nargs="?",
        default="bad_apple.mp4",
        help="Путь к видеофайлу (по умолчанию bad_apple.mp4)",
    )
    args: argparse.Namespace = parser.parse_args()

    # Запуск curses-приложения
    curses.wrapper(main, args.video)