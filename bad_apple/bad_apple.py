#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from cv2.typing import MatLike
from pathlib import Path
import cv2
import curses
import time
import argparse
import numpy as np
from typing import Any, ClassVar


class ArgsParser:
    @staticmethod
    def parse() -> argparse.Namespace:
        parser: argparse.ArgumentParser = argparse.ArgumentParser(
            description="Воспроизведение Bad Apple в терминале через ASCII-графику"
        )
        parser.add_argument(
            "-p",
            "--path",
            default="__default__",
            help="Путь к видеофайлу (по умолчанию <папка_с_этим_файлом>/bad_apple.mp4)",
        )
        parser.add_argument(
            "-c",
            "--color",
            choices=["r", "g", "b", "m", "w"],
            default="g",
            help="Цвет символов ASCII. Этим цветом будут отображаться символы.",
        )
        parser.add_argument(
            "-b",
            "--bold",
            action="store_true",
            help="Включить жирное отображение символов ASCII.",
        )

        return parser.parse_args()

class Config:

    color_map: ClassVar[dict[str, int]] = {
        "r": 1,
        "g": 2,
        "m": 3,
        "b": 4,
        "w": 5
    }
    ascii_chars: ClassVar[str] = "#@%* "

    def __init__(self, stdscr: curses.window, video_path: str, color_schema_name: str, is_bold: bool):

        self.stdscr = stdscr
        self.video_path: Path | str = Path(__file__).resolve().parent  / "bad_apple.mp4" if video_path == '__default__' else video_path
        self.color_schema = self.color_map[color_schema_name]
        self.is_bold = is_bold
        self.height, self.width = self.stdscr.getmaxyx()
        self._validate_video_path(self.video_path)
        self._setup_screen(self.stdscr)

    def config_fps_and_delay(self, video: Video):
        _fps = float(video.capture.get(cv2.CAP_PROP_FPS))

        self.fps = _fps if _fps > 0 else 30 
        self.delay = 1.0 / self.fps

    @staticmethod
    def _validate_video_path(video_path: Path | str) -> None:
        capture = cv2.VideoCapture(video_path)
        try:
            if not capture.isOpened():
                raise IOError(f"Не удалось открыть видео: {video_path}")
        finally:
            capture.release()

    @staticmethod
    def _setup_screen(stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(0)

        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    
class ConvertorFrame2ASCII:
    def __init__(self, config: Config) -> None:
        self.config = config

    def frame2ascii(self, frame: np.ndarray, new_width: int, new_height: int) -> list[str]:
        resized: MatLike = cv2.resize(
            frame, (new_width, new_height), interpolation=cv2.INTER_AREA
        )

        gray_video = self._video2gray(resized)

        ascii_img: list[str] = []
        for y in range(new_height):
            row_chars: list[str] = []
            for x in range(new_width):
                pixel = int(gray_video[y, x]) 
                row_chars.append(self._pixel2ascii(pixel))
            ascii_img.append("".join(row_chars))
        
        return ascii_img
    
    def _video2gray(self, resized: MatLike) -> MatLike:

        if len(resized.shape) == 3:
            return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        return resized
    
    def _pixel2ascii(self, pixel_value: int | np.uint8) -> str:
        """Преобразует значение яркости (0-255) в символ ASCII."""

        index: int = int(pixel_value / 255 * (len(self.config.ascii_chars) - 1))
        return self.config.ascii_chars[index]
    
class Video:
    def __init__(self, video_path: Path | str):
        self.capture = cv2.VideoCapture(video_path)

class Timer:
    def __init__(self):
        self.__start_time: float = 0

    def set_start_time(self):
        self.__start_time = time.time()
    
    def delay(self, delay: float):
        elapsed = time.time() - self.__start_time
        if elapsed < delay:
            time.sleep(delay - elapsed)

class RenderVideo:
    def __init__(self, video: Video, config: Config, convertor: ConvertorFrame2ASCII):
        self.video = video
        self.config = config
        self.convertor = convertor
        self.ret: bool
        self.frame: np.ndarray[Any, np.dtype[np.generic]]
        self.ascii_frame: list[str]

    def read_frame(self):
        self.ret, self.frame = self.video.capture.read()
    
    def render_frame(self):

        self.config.stdscr.clear()

        for y, line in enumerate(self.ascii_frame):
            if y < self.config.height:
                try:
                    self.config.stdscr.addstr(y, 0, line[:self.config.width], curses.color_pair(self.config.color_schema))
                except curses.error:
                    pass
        self.config.stdscr.refresh()

def main(stdscr: curses.window, video_path: str, color_schema_name: str, is_bold: bool) -> None:

    config: Config = Config(stdscr, video_path, color_schema_name, is_bold)

    convertor: ConvertorFrame2ASCII = ConvertorFrame2ASCII(config)

    video: Video = Video(config.video_path)

    render: RenderVideo = RenderVideo(video, config, convertor)

    config.config_fps_and_delay(video)

    timer = Timer()

    while True:
        timer.set_start_time()

        render.read_frame()

        if not render.ret:
            break

        render.ascii_frame = convertor.frame2ascii(render.frame, config.width, config.height)

        render.render_frame()
        
        key: int = stdscr.getch()
        if key in [ord('q'),ord('Q')]:
            break

        timer.delay(config.delay)

    video.capture.release()

if __name__ == "__main__":
    args = ArgsParser.parse()

    curses.wrapper(main, args.path, args.color, args.bold)