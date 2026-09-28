"""
Color extraction module for Telegram themes.
Extracts dominant colors, vibrant accents, harmonic color schemes, and human-friendly color names.
"""

from typing import List, Tuple, Dict, Any, Optional
import colorsys
import io
from PIL import Image
import numpy as np


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers (0-255) to hex string #RRGGBB."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string (#RRGGBB or RRGGBB) to (r, g, b) tuple."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    elif len(hex_str) == 8:
        hex_str = hex_str[2:8]
    elif len(hex_str) != 6:
        return (42, 114, 212)
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (r, g, b)
    except ValueError:
        return (42, 114, 212)


def is_valid_hex(hex_str: str) -> bool:
    """Check if string is a valid hex color code."""
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) not in (3, 6, 8):
        return False
    return all(c in "0123456789abcdefABCDEF" for c in cleaned)


def get_color_emoji(rgb: Tuple[int, int, int]) -> str:
    """Return an appropriate colored circle emoji based on RGB hue and saturation."""
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    if s < 0.16:
        return "⚪" if l > 0.65 else ("🔘" if l > 0.3 else "⚫")
    deg = h * 360.0
    if deg < 20 or deg >= 345:
        return "🔴"
    elif deg < 48:
        return "🟠"
    elif deg < 72:
        return "🟡"
    elif deg < 160:
        return "🟢"
    elif deg < 200:
        return "🔷"
    elif deg < 260:
        return "🔵"
    elif deg < 315:
        return "🟣"
    else:
        return "🌸"


def get_color_name(rgb: Tuple[int, int, int]) -> str:
    """Return a poetic Russian color name for swatches and palette cards."""
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    if s < 0.14:
        if l > 0.82:
            return "Жемчужно-белый"
        if l < 0.22:
            return "Глубокий чёрный"
        return "Графитовый серый"
    deg = h * 360.0
    if deg < 18 or deg >= 345:
        return "Рубиновый" if l < 0.4 else ("Алый неон" if l < 0.7 else "Коралловый")
    elif deg < 45:
        return "Янтарный" if l < 0.4 else ("Оранжевый" if l < 0.7 else "Персиковый")
    elif deg < 72:
        return "Золотистый" if l < 0.4 else ("Солнечный" if l < 0.7 else "Лимонный")
    elif deg < 160:
        return "Изумрудный" if l < 0.4 else ("Неоново-зелёный" if l < 0.7 else "Мятный")
    elif deg < 200:
        return "Морская волна" if l < 0.4 else ("Лазурный" if l < 0.7 else "Аквамарин")
    elif deg < 260:
        return "Кобальтовый" if l < 0.4 else ("Сапфировый" if l < 0.7 else "Небесно-голубой")
    elif deg < 315:
        return "Аметистовый" if l < 0.4 else ("Пурпурный" if l < 0.7 else "Лавандовый")
    else:
        return "Малиновый" if l < 0.5 else "Неоново-розовый"


def get_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative perceived luminance (0.0 to 1.0)."""
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def get_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """Calculate WCAG contrast ratio between two RGB colors (1.0 to 21.0)."""
    l1 = get_luminance(*rgb1) + 0.05
    l2 = get_luminance(*rgb2) + 0.05
    return max(l1, l2) / min(l1, l2)


def get_best_text_color(bg_rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Return pure white or near black text for optimal readability."""
    lum = get_luminance(*bg_rgb)
    return (255, 255, 255) if lum < 0.52 else (20, 20, 24)


def color_distance(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two colors in RGB space."""
    return (
        (rgb1[0] - rgb2[0]) ** 2 +
        (rgb1[1] - rgb2[1]) ** 2 +
        (rgb1[2] - rgb2[2]) ** 2
    ) ** 0.5


def blend_colors(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Blend rgb1 with rgb2 by factor (0.0 = rgb1, 1.0 = rgb2)."""
    factor = max(0.0, min(1.0, factor))
    return (
        int(rgb1[0] * (1 - factor) + rgb2[0] * factor),
        int(rgb1[1] * (1 - factor) + rgb2[1] * factor),
        int(rgb1[2] * (1 - factor) + rgb2[2] * factor)
    )


def adjust_lightness(rgb: Tuple[int, int, int], target_l: float) -> Tuple[int, int, int]:
    """Adjust lightness of an RGB color to target_l (0.0 to 1.0) in HLS space."""
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    target_l = max(0.0, min(1.0, target_l))
    nr, ng, nb = colorsys.hls_to_rgb(h, target_l, s)
    return (int(nr * 255), int(ng * 255), int(nb * 255))


def adjust_saturation(rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Multiply saturation of an RGB color by factor."""
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    ns = max(0.0, min(1.0, s * factor))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, ns)
    return (int(nr * 255), int(ng * 255), int(nb * 255))


def shift_temperature(rgb: Tuple[int, int, int], kelvin_shift: float) -> Tuple[int, int, int]:
    """
    Shift color temperature: positive = warmer (amber/red), negative = cooler (cyan/blue).
    kelvin_shift: -0.3 to +0.3
    """
    r, g, b = rgb
    if kelvin_shift > 0:
        r = min(255, int(r + 255 * kelvin_shift * 0.4))
        g = min(255, int(g + 255 * kelvin_shift * 0.2))
        b = max(0, int(b - 255 * kelvin_shift * 0.3))
    else:
        shift = abs(kelvin_shift)
        r = max(0, int(r - 255 * shift * 0.3))
        g = min(255, int(g + 255 * shift * 0.1))
        b = min(255, int(b + 255 * shift * 0.4))
    return (r, g, b)


def generate_harmonic_color(base_rgb: Tuple[int, int, int], hue_shift_degrees: float) -> Tuple[int, int, int]:
    """Generate a harmonic color by shifting hue."""
    h, l, s = colorsys.rgb_to_hls(base_rgb[0] / 255.0, base_rgb[1] / 255.0, base_rgb[2] / 255.0)
    new_h = (h + hue_shift_degrees / 360.0) % 1.0
    new_s = max(0.55, s)
    new_l = max(0.42, min(0.68, l))
    nr, ng, nb = colorsys.hls_to_rgb(new_h, new_l, new_s)
    return (int(nr * 255), int(ng * 255), int(nb * 255))


class ExtractedColor:
    """Represents an extracted color with metadata."""
    def __init__(self, rgb: Tuple[int, int, int], count: int = 1):
        self.rgb = rgb
        self.r, self.g, self.b = rgb
        self.hex = rgb_to_hex(self.r, self.g, self.b)
        self.count = count
        
        # HLS values
        self.h, self.l, self.s = colorsys.rgb_to_hls(self.r / 255.0, self.g / 255.0, self.b / 255.0)
        self.luminance = get_luminance(self.r, self.g, self.b)
        self.emoji = get_color_emoji(self.rgb)
        self.name = get_color_name(self.rgb)
        
        # Vibrancy score: high saturation + moderate lightness is most vibrant
        lightness_penalty = abs(self.l - 0.5) * 1.5
        self.vibrancy = self.s * max(0.15, 1.0 - lightness_penalty)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hex": self.hex,
            "rgb": [self.r, self.g, self.b],
            "emoji": self.emoji,
            "name": self.name,
            "vibrancy": round(self.vibrancy, 3),
            "luminance": round(self.luminance, 3),
            "count": self.count
        }


def extract_palette_from_image(image: Image.Image, num_colors: int = 8) -> List[ExtractedColor]:
    """
    Extract a rich, diverse, and vibrant palette from a PIL Image.
    Separates dominant background tones from vibrant foreground accents.
    """
    thumb = image.convert("RGB")
    thumb.thumbnail((250, 250), Image.Resampling.BILINEAR)
    
    quantized = thumb.quantize(colors=36, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()[: 36 * 3]
    color_counts = quantized.getcolors() or []
    
    colors_raw: List[ExtractedColor] = []
    for count, idx in color_counts:
        r = palette_data[idx * 3]
        g = palette_data[idx * 3 + 1]
        b = palette_data[idx * 3 + 2]
        colors_raw.append(ExtractedColor((r, g, b), count=count))
    
    if not colors_raw:
        default_hexes = ["#2A72D4", "#5EB5F7", "#8E52EA", "#E5484D", "#30A46C", "#F76808", "#1E232A", "#FFFFFF"]
        return [ExtractedColor(hex_to_rgb(h)) for h in default_hexes]

    max_count = max((c.count for c in colors_raw), default=1)
    colors_raw.sort(key=lambda c: (c.vibrancy * 2.0 + (c.count / max_count)), reverse=True)
    
    distinct_colors: List[ExtractedColor] = []
    min_distance = 32.0
    
    for color in colors_raw:
        if not distinct_colors:
            distinct_colors.append(color)
            continue
        
        if all(color_distance(color.rgb, s.rgb) >= min_distance for s in distinct_colors):
            distinct_colors.append(color)
            if len(distinct_colors) >= num_colors:
                break
                
    if len(distinct_colors) < num_colors:
        for color in colors_raw:
            if color not in distinct_colors and all(color_distance(color.rgb, s.rgb) >= 20.0 for s in distinct_colors):
                distinct_colors.append(color)
                if len(distinct_colors) >= num_colors:
                    break

    if len(distinct_colors) < 6:
        base_color = distinct_colors[0].rgb
        shifts = [35.0, 75.0, 140.0, 180.0, 215.0, 290.0]
        for shift in shifts:
            h_rgb = generate_harmonic_color(base_color, shift)
            new_c = ExtractedColor(h_rgb, count=1)
            if all(color_distance(new_c.rgb, c.rgb) >= 20.0 for c in distinct_colors):
                distinct_colors.append(new_c)
            if len(distinct_colors) >= num_colors:
                break

    return distinct_colors


def detect_image_brightness(image: Image.Image) -> bool:
    """
    Returns True if the image is predominantly light, False if dark.
    """
    thumb = image.convert("L").resize((50, 50))
    arr = np.array(thumb)
    avg_brightness = np.mean(arr)
    return avg_brightness > 128
