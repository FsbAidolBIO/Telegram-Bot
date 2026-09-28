"""
Curated Theme Presets Library for Telegram Theme Studio.
Provides ready-to-use, designer-crafted aesthetic themes.
"""

from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw
import io
from theme_engine.color_extractor import ExtractedColor, hex_to_rgb
from theme_engine.palette import ThemeConfig, build_palette, ResolvedThemePalette
from theme_engine.wallpaper_generator import generate_wallpaper


class ThemePreset:
    """Represents a curated aesthetic theme preset."""
    def __init__(
        self,
        key: str,
        title: str,
        description: str,
        emoji: str,
        mode: str,
        accent_hex: str,
        secondary_hex: str,
        bg_hex: str,
        extra_hexes: List[str],
        bubble_style: str = "vibrant",
        chat_tint: str = "rich"
    ):
        self.key = key
        self.title = title
        self.description = description
        self.emoji = emoji
        self.mode = mode
        self.accent_hex = accent_hex
        self.secondary_hex = secondary_hex
        self.bg_hex = bg_hex
        self.extra_hexes = extra_hexes
        self.bubble_style = bubble_style
        self.chat_tint = chat_tint

    def get_extracted_colors(self) -> List[ExtractedColor]:
        all_hexes = [self.accent_hex, self.secondary_hex, self.bg_hex] + self.extra_hexes
        return [ExtractedColor(hex_to_rgb(h), count=100 - i * 10) for i, h in enumerate(all_hexes)]

    def get_config(self) -> ThemeConfig:
        return ThemeConfig(
            mode=self.mode,
            accent_idx=0,
            secondary_idx=1,
            bubble_style=self.bubble_style,
            chat_tint=self.chat_tint,
            wallpaper_mode="gradient"
        )

    def generate_preset_image(self, width: int = 1080, height: int = 2400) -> Image.Image:
        """Create an aesthetic procedural gradient background for this preset."""
        img = Image.new("RGB", (width, height), hex_to_rgb(self.bg_hex))
        draw = ImageDraw.Draw(img)
        
        c1 = hex_to_rgb(self.accent_hex)
        c2 = hex_to_rgb(self.secondary_hex)
        
        # Soft ambient glowing circles
        draw.ellipse([(width * 0.1, height * 0.15), (width * 0.9, height * 0.55)], fill=c1)
        draw.ellipse([(width * 0.2, height * 0.45), (width * 0.95, height * 0.85)], fill=c2)
        
        from PIL import ImageFilter
        return img.filter(ImageFilter.GaussianBlur(radius=80))


PRESETS_LIBRARY: Dict[str, ThemePreset] = {
    "cyberpunk": ThemePreset(
        key="cyberpunk",
        title="Cyberpunk 2077",
        description="Неоновый жёлтый и электрический циан на ультра-чёрном OLED",
        emoji="⚡",
        mode="amoled",
        accent_hex="#FEE715",
        secondary_hex="#00F0FF",
        bg_hex="#050508",
        extra_hexes=["#FF0055", "#7000FF", "#101018"]
    ),
    "sakura": ThemePreset(
        key="sakura",
        title="Sakura Dream",
        description="Нежный японский вишнёвый цвет и пастельная лаванда",
        emoji="🌸",
        mode="dark",
        accent_hex="#FF7597",
        secondary_hex="#C77DFF",
        bg_hex="#1E1424",
        extra_hexes=["#FFAFCC", "#9D4EDD", "#2D1B36"]
    ),
    "nebula": ThemePreset(
        key="nebula",
        title="Midnight Nebula",
        description="Глубокий космический индиго и звёздная бирюза",
        emoji="🌌",
        mode="dark",
        accent_hex="#38B6FF",
        secondary_hex="#7B2CBF",
        bg_hex="#0F1123",
        extra_hexes=["#00F5D4", "#5A189A", "#181A33"]
    ),
    "matcha": ThemePreset(
        key="matcha",
        title="Matcha & Forest",
        description="Спокойный зелёный чай матча и тёплые древесные тона",
        emoji="🍵",
        mode="dark",
        accent_hex="#52B788",
        secondary_hex="#95D5B2",
        bg_hex="#14211A",
        extra_hexes=["#74C69D", "#D8F3DC", "#1E3328"]
    ),
    "sunset": ThemePreset(
        key="sunset",
        title="Tokyo Sunset",
        description="Тёплый закатный коралл, золотой янтарь и сумеречное небо",
        emoji="🌇",
        mode="dark",
        accent_hex="#FF6B6B",
        secondary_hex="#FFD93D",
        bg_hex="#1F1522",
        extra_hexes=["#FF8E72", "#6C5CE7", "#2E1C33"]
    ),
    "nordic": ThemePreset(
        key="nordic",
        title="Nordic Frost",
        description="Ледяной скандинавский бриз и кристально чистый синий",
        emoji="❄️",
        mode="light",
        accent_hex="#0077B6",
        secondary_hex="#00B4D8",
        bg_hex="#F0F4F8",
        extra_hexes=["#90E0EF", "#CAF0F8", "#FFFFFF"]
    ),
    "dracula": ThemePreset(
        key="dracula",
        title="Dracula Modern",
        description="Легендарная тёмная палитра для ночной работы и кода",
        emoji="🧛",
        mode="dark",
        accent_hex="#BD93F9",
        secondary_hex="#50FA7B",
        bg_hex="#282A36",
        extra_hexes=["#FF79C6", "#8BE9FD", "#44475A"]
    ),
    "mocha": ThemePreset(
        key="mocha",
        title="Warm Mocha",
        description="Уютный горячий шоколад, карамель и обжаренный кофе",
        emoji="☕",
        mode="dark",
        accent_hex="#D4A373",
        secondary_hex="#CCD5AE",
        bg_hex="#1C1613",
        extra_hexes=["#FAEDCD", "#E9D8A6", "#2B211C"]
    )
}
