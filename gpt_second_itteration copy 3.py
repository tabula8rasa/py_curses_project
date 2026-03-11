#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np

ASCII_CHARS: str = "#@%* "

class ConvertorFrame2ASCII:
    def frame_to_ascii(
        self, frame: Image, new_width: int, new_height: int
    ) -> list[str]:
        
        resized: MatLike = cv2.resize(
            frame, (new_width, new_height), interpolation=cv2.INTER_AREA
        )

        gray_video: Image = self._video2gray(resized)

        ascii_img: list[str] = []
        for y in range(new_height):
            row_chars: list[str] = []
            for x in range(new_width):
                pixel: int = int(gray_video[y, x])
                row_chars.append(self._pixel_to_ascii(pixel))
            ascii_img.append("".join(row_chars))

        return ascii_img

    def _pixel_to_ascii(self, pixel_value: int | np.uint8) -> str:
        index: int = int(pixel_value / 255 * (len(ASCII_CHARS) - 1))
        return ASCII_CHARS[index]

    def _video2gray(self, resized: Image) -> Image:
        if len(resized.shape) == 3:
            gray: Image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            return gray
        return resized