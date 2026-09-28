"""
Color extraction, harmony generator, and color naming utilities for Telegram themes.
Uses advanced multi-pass color clustering, saturated micro-detail detection, and W3C WCAG accessibility standards.
"""

from typing import List, Tuple, Dict, Any, Optional, Union
import io
import math
from PIL import Image
from collections import Counter


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers (0-255) to hex string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string (#RRGGBB or #RGB) to RGB tuple."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    if len(hex_clean) != 6:
        return (0, 136, 204)  # fallback telegram blue
    try:
        return (
            int(hex_clean[0:2], 16),
            int(hex_clean[2:4], 16),
            int(hex_clean[4:6], 16)
        )
    except ValueError:
        return (0, 136, 204)


def is_valid_hex(hex_str: str) -> bool:
    """Check if string is a valid HEX color code."""
    clean = hex_str.strip().lstrip("#")
    if len(clean) not in (3, 6):
        return False
    try:
        int(clean, 16)
        return True
    except ValueError:
        return False


def get_luminance(r: int, g: int, b: int) -> float:
    """Calculate perceived luminance (0.0 to 1.0)."""
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def srgb_to_linear(val: int) -> float:
    """Convert sRGB channel (0-255) to linear light for WCAG 2.1."""
    v = val / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def calculate_wcag_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate standard W3C WCAG 2.1 relative luminance."""
    r, g, b = [srgb_to_linear(x) for x in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG contrast ratio between two colors (1.0 to 21.0).
    """
    l1 = calculate_wcag_luminance(rgb1)
    l2 = calculate_wcag_luminance(rgb2)
    bright = max(l1, l2)
    dark = min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)


def get_wcag_badge(contrast: float) -> str:
    """Return friendly WCAG accessibility badge."""
    if contrast >= 7.0:
        return f"{contrast:.1f}:1 ⭐⭐⭐ (WCAG AAA Превосходная)"
    elif contrast >= 4.5:
        return f"{contrast:.1f}:1 ⭐⭐ (WCAG AA Отличная)"
    elif contrast >= 3.0:
        return f"{contrast:.1f}:1 ⭐ (WCAG A Хорошая)"
    else:
        return f"{contrast:.1f}:1 ⚠️ (Низкий контраст)"


def get_saturation(r: int, g: int, b: int) -> float:
    """Calculate color saturation (0.0 to 1.0)."""
    mx = max(r, g, b)
    mn = min(r, g, b)
    if mx == 0:
        return 0.0
    return (mx - mn) / mx


def get_best_text_color(bg_rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Return crisp white or dark text depending on background luminance."""
    lum = get_luminance(*bg_rgb)
    return (255, 255, 255) if lum < 0.60 else (20, 20, 24)


def blend_colors(c1: Tuple[int, int, int], c2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Blend two RGB colors by a factor (0.0 = c1, 1.0 = c2)."""
    factor = max(0.0, min(1.0, factor))
    return (
        int(c1[0] * (1.0 - factor) + c2[0] * factor),
        int(c1[1] * (1.0 - factor) + c2[1] * factor),
        int(c1[2] * (1.0 - factor) + c2[2] * factor)
    )


def adjust_lightness(rgb: Tuple[int, int, int], target_lum: float) -> Tuple[int, int, int]:
    """Adjust lightness of an RGB color toward a target luminance (0.0 to 1.0)."""
    curr_lum = get_luminance(*rgb)
    if curr_lum == 0:
        val = int(target_lum * 255)
        return (val, val, val)
    ratio = target_lum / max(0.01, curr_lum)
    return (
        min(255, max(0, int(rgb[0] * ratio))),
        min(255, max(0, int(rgb[1] * ratio))),
        min(255, max(0, int(rgb[2] * ratio)))
    )


def adjust_saturation(rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Boost or attenuate color saturation."""
    gray = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    return (
        min(255, max(0, int(gray + (rgb[0] - gray) * factor))),
        min(255, max(0, int(gray + (rgb[1] - gray) * factor))),
        min(255, max(0, int(gray + (rgb[2] - gray) * factor)))
    )


def get_poetic_color_name(r_or_rgb: Union[int, Tuple[int, int, int]], g: Optional[int] = None, b: Optional[int] = None) -> str:
    """Return a poetic Russian color name based on hue, saturation, and lightness."""
    if isinstance(r_or_rgb, (tuple, list)):
        r, g, b = r_or_rgb[0], r_or_rgb[1], r_or_rgb[2]
    else:
        r = r_or_rgb
        g = 0 if g is None else g
        b = 0 if b is None else b

    lum = get_luminance(r, g, b)
    sat = get_saturation(r, g, b)

    if lum < 0.08:
        return "Глубокий обсидиан"
    if lum < 0.18 and sat < 0.15:
        return "Графитовый оникс"
    if lum > 0.92 and sat < 0.10:
        return "Жемчужно-белый"
    if sat < 0.12:
        return "Серебристый туман" if lum > 0.5 else "Тёмный кварц"

    mx = max(r, g, b)
    mn = min(r, g, b)
    delta = mx - mn

    if delta == 0:
        hue = 0
    elif mx == r:
        hue = 60 * (((g - b) / delta) % 6)
    elif mx == g:
        hue = 60 * (((b - r) / delta) + 2)
    else:
        hue = 60 * (((r - g) / delta) + 4)

    if (hue >= 345 or hue < 15):
        if lum > 0.65: return "Коралловый румянец"
        if lum < 0.35: return "Бордовый вельвет"
        return "Пламенный рубин"
    elif 15 <= hue < 45:
        if lum > 0.70: return "Персиковый мусс"
        if lum < 0.40: return "Жжёная охра"
        return "Закатный янтарь"
    elif 45 <= hue < 70:
        if lum > 0.70: return "Лимонный сорбет"
        if lum < 0.40: return "Старинное золото"
        return "Солнечный топаз"
    elif 70 <= hue < 160:
        if lum > 0.70: return "Нежная фисташка"
        if lum < 0.35: return "Изумрудная хвоя"
        return "Неоновый нефрит"
    elif 160 <= hue < 200:
        if lum > 0.70: return "Ледяная лагуна"
        if lum < 0.35: return "Морская глубина"
        return "Бирюзовая волна"
    elif 200 <= hue < 255:
        if lum > 0.70: return "Лазурное небо"
        if lum < 0.35: return "Полуночный сапфир"
        return "Электрический кобальт"
    elif 255 <= hue < 290:
        if lum > 0.70: return "Цветущая глициния"
        if lum < 0.35: return "Королевский аметист"
        return "Неоновый ультрафиолет"
    elif 290 <= hue < 345:
        if lum > 0.70: return "Розовая сакура"
        if lum < 0.35: return "Тёмная маджента"
        return "Киберпанк фуксия"

    return "Атмосферный оттенок"


def get_color_emoji(r: int, g: int, b: int) -> str:
    """Return color emoji based on RGB values."""
    col = ExtractedColor((r, g, b))
    return col.emoji


def shift_temperature(rgb: Tuple[int, int, int], shift: float) -> Tuple[int, int, int]:
    """Shift color temperature (positive for warmer, negative for cooler)."""
    r, g, b = rgb
    new_r = min(255, max(0, int(r + shift * 30)))
    new_b = min(255, max(0, int(b - shift * 30)))
    return (new_r, g, new_b)


get_color_name = get_poetic_color_name


class ExtractedColor:
    """Represents an extracted dominant or vibrant color with metadata."""
    def __init__(self, rgb: Tuple[int, int, int], count: int = 1):
        self.rgb = rgb
        self.r, self.g, self.b = rgb
        self.count = count
        self.hex = rgb_to_hex(self.r, self.g, self.b)
        self.luminance = get_luminance(self.r, self.g, self.b)
        self.saturation = get_saturation(self.r, self.g, self.b)
        self.vibrancy = self.saturation * (1.0 - abs(self.luminance - 0.5) * 1.5)
        self.name = get_poetic_color_name(self.r, self.g, self.b)

    @property
    def emoji(self) -> str:
        """Visual color swatch emoji for Telegram UI."""
        lum = self.luminance
        sat = self.saturation
        if sat < 0.15:
            return "⚪" if lum > 0.6 else "⚫"
        mx, mn = max(self.rgb), min(self.rgb)
        delta = mx - mn
        if delta == 0:
            hue = 0
        elif mx == self.r:
            hue = 60 * (((self.g - self.b) / delta) % 6)
        elif mx == self.g:
            hue = 60 * (((self.b - self.r) / delta) + 2)
        else:
            hue = 60 * (((self.r - self.g) / delta) + 4)

        if hue < 20 or hue >= 340:
            return "🔴"
        elif 20 <= hue < 45:
            return "🟠"
        elif 45 <= hue < 75:
            return "🟡"
        elif 75 <= hue < 165:
            return "🟢"
        elif 165 <= hue < 260:
            return "🔵"
        else:
            return "🟣"

    def to_dict(self) -> Dict[str, Any]:
        """Convert color object to dictionary."""
        return {
            "hex": self.hex,
            "rgb": list(self.rgb),
            "name": self.name,
            "emoji": self.emoji,
            "luminance": round(self.luminance, 3),
            "saturation": round(self.saturation, 3),
            "vibrancy": round(self.vibrancy, 3),
            "count": self.count
        }


def extract_palette_from_image(image: Image.Image, num_colors: int = 8) -> List[ExtractedColor]:
    """
    Extract dominant and accent colors using multi-pass color clustering.
    Discovers saturated micro-details (e.g. glowing eyes, blush, logos) in dark/B&W images,
    and provides stylish aesthetic accents if the artwork is purely monochrome.
    """
    thumb = image.copy()
    thumb.thumbnail((250, 250), Image.Resampling.BILINEAR)
    thumb = thumb.convert("RGB")
    
    # Pass 1: Saturated Micro-Detail Scanner
    # Detects saturated colors (sat > 0.20) even if they represent only 0.2% of the art
    raw_pixels = list(thumb.getdata())
    saturated_pixels = [
        p for p in raw_pixels
        if get_saturation(*p) > 0.20 and 0.10 <= get_luminance(*p) <= 0.90
    ]
    
    accent_candidates: List[ExtractedColor] = []
    if saturated_pixels:
        sat_counts = Counter(saturated_pixels)
        for rgb, count in sat_counts.most_common(15):
            # Boost the weight of vibrant accents
            accent_candidates.append(ExtractedColor(rgb, count=count * 5))

    # Pass 2: Quantized Dominant Clusterer
    quantized = thumb.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()[:72]
    color_counts = Counter(quantized.getdata())

    dominant_candidates: List[ExtractedColor] = []
    for idx, count in color_counts.most_common():
        r = palette_data[idx * 3]
        g = palette_data[idx * 3 + 1]
        b = palette_data[idx * 3 + 2]
        dominant_candidates.append(ExtractedColor((r, g, b), count=count))

    # Merge candidates with Euclidean color distance deduplication
    all_candidates = accent_candidates + dominant_candidates
    unique_colors: List[ExtractedColor] = []
    for col in all_candidates:
        is_too_close = False
        for chosen in unique_colors:
            dr = col.r - chosen.r
            dg = col.g - chosen.g
            db = col.b - chosen.b
            dist = math.sqrt(dr * dr + dg * dg + db * db)
            if dist < 28:
                is_too_close = True
                break
        if not is_too_close:
            unique_colors.append(col)
        if len(unique_colors) >= num_colors + 3:
            break

    # Pass 3: Monochrome Fallback
    # If image is truly black & white (max saturation < 0.12), provide vibrant aesthetic accent options
    max_sat = max([c.saturation for c in unique_colors], default=0.0)
    if max_sat < 0.14:
        curated_vibrants = [
            ExtractedColor((0, 136, 204), count=999),   # Telegram Azure Blue
            ExtractedColor((255, 59, 48), count=998),   # Electric Crimson Red
            ExtractedColor((142, 82, 234), count=997),  # Cyber Purple
            ExtractedColor((0, 229, 255), count=996),   # Neon Cyan
            ExtractedColor((48, 164, 108), count=995),  # Emerald Mint
        ]
        # Insert curated accents at top
        unique_colors = curated_vibrants[:3] + unique_colors[:5]

    unique_colors.sort(key=lambda c: (c.vibrancy * 2.2 + (1.0 if 0.25 <= c.luminance <= 0.75 else 0.3)), reverse=True)
    return unique_colors[:num_colors]


def detect_image_brightness(image: Image.Image) -> bool:
    """Return True if image is primarily light/bright, False if dark."""
    thumb = image.copy()
    thumb.thumbnail((64, 64), Image.Resampling.BILINEAR)
    thumb = thumb.convert("L")
    stat = thumb.getdata()
    avg = sum(stat) / len(stat)
    return avg > 135
