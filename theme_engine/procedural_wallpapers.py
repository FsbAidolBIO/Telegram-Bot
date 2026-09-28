"""
Procedural Aesthetic Wallpaper Generator for Telegram Theme Studio.
Generates dynamic geometric waves, topography, bokeh, and synthwave grids in theme colors.
"""

from typing import Tuple, List
import math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from theme_engine.palette import ResolvedThemePalette


def generate_procedural_bokeh(
    width: int,
    height: int,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    bg_color: Tuple[int, int, int]
) -> Image.Image:
    """Generate aesthetic soft ambient bokeh light circles."""
    # Render at half size then upscale for smooth rendering
    sw, sh = width // 2, height // 2
    img = Image.new("RGB", (sw, sh), bg_color)
    draw = ImageDraw.Draw(img)

    for i in range(14):
        cx = int(sw * (0.15 + (i * 0.17) % 0.8))
        cy = int(sh * (0.12 + (i * 0.14) % 0.8))
        r = int(sw * (0.15 + (i * 0.06) % 0.28))
        c = color1 if i % 2 == 0 else color2
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=c)

    blurred = img.filter(ImageFilter.GaussianBlur(radius=35))
    return blurred.resize((width, height), Image.Resampling.LANCZOS)


def generate_procedural_waves(
    width: int,
    height: int,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    bg_color: Tuple[int, int, int]
) -> Image.Image:
    """Generate flowing sinusoidal organic ribbon waves."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    steps = 100
    for wave_idx in range(6):
        points = []
        phase = wave_idx * 0.8
        amplitude = height * (0.05 + wave_idx * 0.015)
        base_y = height * (0.35 + wave_idx * 0.09)

        for step in range(steps + 1):
            x = (width * step) // steps
            y = base_y + math.sin(step * 0.1 + phase) * amplitude + math.cos(step * 0.05 + phase * 0.5) * (amplitude * 0.5)
            points.append((x, y))

        points.append((width, height))
        points.append((0, height))

        # Blend color from color1 to color2
        factor = wave_idx / 5.0
        wave_c = (
            int(color1[0] * (1 - factor) + color2[0] * factor),
            int(color1[1] * (1 - factor) + color2[1] * factor),
            int(color1[2] * (1 - factor) + color2[2] * factor)
        )
        draw.polygon(points, fill=wave_c)

    blurred = img.filter(ImageFilter.GaussianBlur(radius=15))
    return Image.blend(img, blurred, 0.4)


def generate_procedural_topography(
    width: int,
    height: int,
    stroke_color: Tuple[int, int, int],
    bg_color: Tuple[int, int, int]
) -> Image.Image:
    """Generate modern topographic contour elevation map lines."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    lines_count = 18
    for line_idx in range(lines_count):
        points = []
        base_y = (height * line_idx) // lines_count
        freq = 0.008 + (line_idx % 3) * 0.002
        amp = 40 + (line_idx % 4) * 15

        for x in range(0, width + 20, 20):
            y = base_y + math.sin(x * freq + line_idx * 0.5) * amp + math.cos(x * (freq * 0.5)) * (amp * 0.6)
            points.append((x, y))

        draw.line(points, fill=stroke_color, width=2)

    return img


def generate_procedural_synthwave(
    width: int,
    height: int,
    neon_color: Tuple[int, int, int],
    sun_color: Tuple[int, int, int],
    bg_color: Tuple[int, int, int]
) -> Image.Image:
    """Generate 80s retro synthwave glowing sun & perspective grid."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    horizon_y = int(height * 0.55)

    # 1. Glowing Neon Sun
    sun_r = int(min(width, height) * 0.22)
    sun_cx, sun_cy = width // 2, horizon_y - sun_r // 3
    draw.ellipse([(sun_cx - sun_r, sun_cy - sun_r), (sun_cx + sun_r, sun_cy + sun_r)], fill=sun_color)

    # Sun horizontal slice blinds
    for y in range(sun_cy - sun_r // 4, sun_cy + sun_r, 14):
        draw.rectangle([(sun_cx - sun_r, y), (sun_cx + sun_r, y + 4)], fill=bg_color)

    # 2. Perspective Ground Grid
    draw.rectangle([(0, horizon_y), (width, height)], fill=(bg_color[0] // 2, bg_color[1] // 2, bg_color[2] // 2))
    
    # Horizontal perspective lines
    num_h_lines = 14
    for i in range(1, num_h_lines + 1):
        ratio = (i / num_h_lines) ** 2
        y = int(horizon_y + (height - horizon_y) * ratio)
        draw.line([(0, y), (width, y)], fill=neon_color, width=1)

    # Vanishing vertical perspective lines
    vanishing_x = width // 2
    for x in range(-width // 2, int(width * 1.5), 60):
        draw.line([(vanishing_x, horizon_y), (x, height)], fill=neon_color, width=1)

    return img
