"""
Theme Palette generator and color logic for Telegram themes.
Handles mode switching (Dark, Light, AMOLED), contrast tuning, and bubble styling.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from theme_engine.color_extractor import (
    ExtractedColor,
    rgb_to_hex,
    hex_to_rgb,
    get_luminance,
    get_best_text_color,
    blend_colors,
    adjust_lightness,
    adjust_saturation
)


@dataclass
class ThemeConfig:
    """Settings selected by user for theme generation."""
    mode: str = "dark"               # "dark", "light", "amoled", "auto"
    accent_idx: int = 0             # Index into extracted vibrant colors
    secondary_idx: int = 1          # Index for secondary accent
    bubble_style: str = "accent"    # "accent", "tinted", "contrast", "minimal"
    wallpaper_mode: str = "blurred" # "blurred", "fit_blur", "cover", "dimmed", "gradient", "solid"
    brightness_offset: int = 0      # -30 to +30 percent
    contrast_boost: bool = False
    custom_accent_hex: Optional[str] = None

    def cycle_mode(self) -> str:
        modes = ["dark", "light", "amoled"]
        next_idx = (modes.index(self.mode) + 1) % len(modes) if self.mode in modes else 0
        self.mode = modes[next_idx]
        return self.mode

    def cycle_wallpaper(self) -> str:
        wallpapers = ["blurred", "fit_blur", "cover", "dimmed", "gradient", "solid"]
        next_idx = (wallpapers.index(self.wallpaper_mode) + 1) % len(wallpapers) if self.wallpaper_mode in wallpapers else 0
        self.wallpaper_mode = wallpapers[next_idx]
        return self.wallpaper_mode

    def cycle_bubble(self) -> str:
        bubbles = ["accent", "tinted", "contrast", "minimal"]
        next_idx = (bubbles.index(self.bubble_style) + 1) % len(bubbles) if self.bubble_style in bubbles else 0
        self.bubble_style = bubbles[next_idx]
        return self.bubble_style

    def cycle_accent(self, max_count: int) -> int:
        if max_count <= 0:
            return 0
        self.custom_accent_hex = None
        self.accent_idx = (self.accent_idx + 1) % max_count
        return self.accent_idx


@dataclass
class ResolvedThemePalette:
    """Complete set of calculated colors ready for theme rendering & file generation."""
    mode: str
    
    # Base background and surfaces
    bg_color: Tuple[int, int, int]
    bg_surface: Tuple[int, int, int]
    bg_elevated: Tuple[int, int, int]
    topbar_bg: Tuple[int, int, int]
    dialogs_bg: Tuple[int, int, int]
    
    # Accents
    primary_accent: Tuple[int, int, int]
    secondary_accent: Tuple[int, int, int]
    accent_hover: Tuple[int, int, int]
    
    # Chat bubbles
    in_bubble_bg: Tuple[int, int, int]
    in_bubble_text: Tuple[int, int, int]
    in_bubble_time: Tuple[int, int, int]
    in_bubble_reply_bar: Tuple[int, int, int]
    
    out_bubble_bg: Tuple[int, int, int]
    out_bubble_text: Tuple[int, int, int]
    out_bubble_time: Tuple[int, int, int]
    out_bubble_reply_bar: Tuple[int, int, int]
    
    # Text colors
    text_primary: Tuple[int, int, int]
    text_secondary: Tuple[int, int, int]
    text_link: Tuple[int, int, int]
    
    # Controls and badges
    send_button: Tuple[int, int, int]
    unread_badge_bg: Tuple[int, int, int]
    unread_badge_text: Tuple[int, int, int]
    separator_line: Tuple[int, int, int]
    input_bar_bg: Tuple[int, int, int]
    input_bar_text: Tuple[int, int, int]
    input_bar_hint: Tuple[int, int, int]

    # Hex helpers
    @property
    def hex_bg(self) -> str:
        return rgb_to_hex(*self.bg_color)
    
    @property
    def hex_surface(self) -> str:
        return rgb_to_hex(*self.bg_surface)
    
    @property
    def hex_primary_accent(self) -> str:
        return rgb_to_hex(*self.primary_accent)
    
    @property
    def hex_secondary_accent(self) -> str:
        return rgb_to_hex(*self.secondary_accent)
    
    @property
    def hex_in_bubble(self) -> str:
        return rgb_to_hex(*self.in_bubble_bg)
    
    @property
    def hex_out_bubble(self) -> str:
        return rgb_to_hex(*self.out_bubble_bg)
    
    @property
    def hex_text(self) -> str:
        return rgb_to_hex(*self.text_primary)


def build_palette(extracted_colors: List[ExtractedColor], config: ThemeConfig, is_image_light: bool = False) -> ResolvedThemePalette:
    """
    Generate a full harmonized color scheme based on extracted colors and user config.
    """
    if not extracted_colors:
        extracted_colors = [
            ExtractedColor((42, 114, 212)),
            ExtractedColor((94, 181, 247)),
            ExtractedColor((142, 82, 234)),
            ExtractedColor((229, 72, 77)),
            ExtractedColor((48, 164, 108)),
            ExtractedColor((247, 104, 8))
        ]

    # Determine mode
    mode = config.mode
    if mode == "auto":
        mode = "light" if is_image_light else "dark"

    # Sort colors by vibrancy for accents
    vibrant_sorted = sorted(extracted_colors, key=lambda c: c.vibrancy, reverse=True)
    
    # Pick primary accent
    if config.custom_accent_hex:
        primary_raw = hex_to_rgb(config.custom_accent_hex)
    else:
        accent_i = config.accent_idx % len(vibrant_sorted)
        primary_raw = vibrant_sorted[accent_i].rgb

    # Pick secondary accent
    sec_i = (config.accent_idx + 1) % len(vibrant_sorted)
    secondary_raw = vibrant_sorted[sec_i].rgb

    # Base dominant color from image
    base_raw = extracted_colors[0].rgb

    # Brightness adjustment helper
    b_offset = config.brightness_offset / 100.0

    if mode == "amoled":
        # OLED True Black Theme
        bg_color = (0, 0, 0)
        bg_surface = (18, 18, 20)
        bg_elevated = (28, 28, 32)
        topbar_bg = (0, 0, 0)
        dialogs_bg = (0, 0, 0)
        input_bar_bg = (16, 16, 18)
        
        primary_accent = adjust_lightness(primary_raw, min(0.65, max(0.50, get_luminance(*primary_raw))))
        secondary_accent = adjust_lightness(secondary_raw, min(0.65, max(0.50, get_luminance(*secondary_raw))))
        accent_hover = adjust_lightness(primary_accent, min(1.0, get_luminance(*primary_accent) + 0.1))

        text_primary = (255, 255, 255)
        text_secondary = (150, 150, 160)
        text_link = primary_accent
        separator_line = (35, 35, 40)
        
        input_bar_text = (255, 255, 255)
        input_bar_hint = (120, 120, 130)

        # Bubbles
        if config.bubble_style == "accent":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = (24, 24, 28)
            in_bubble_text = (245, 245, 245)
        elif config.bubble_style == "tinted":
            out_bubble_bg = blend_colors((30, 30, 35), primary_accent, 0.45)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = (22, 22, 26)
            in_bubble_text = (245, 245, 245)
        elif config.bubble_style == "contrast":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = secondary_accent
            in_bubble_text = get_best_text_color(in_bubble_bg)
        else: # minimal
            out_bubble_bg = (30, 30, 35)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = (18, 18, 22)
            in_bubble_text = (240, 240, 240)

    elif mode == "dark":
        # Deep Modern Dark Theme
        tinted_dark = blend_colors((22, 26, 33), base_raw, 0.08)
        
        l_bg = max(0.05, min(0.25, 0.10 + b_offset))
        bg_color = adjust_lightness(tinted_dark, l_bg)
        bg_surface = blend_colors(bg_color, (255, 255, 255), 0.06)
        bg_elevated = blend_colors(bg_color, (255, 255, 255), 0.12)
        topbar_bg = bg_color
        dialogs_bg = bg_color
        input_bar_bg = bg_surface

        primary_accent = adjust_lightness(primary_raw, min(0.68, max(0.52, get_luminance(*primary_raw))))
        secondary_accent = adjust_lightness(secondary_raw, min(0.68, max(0.52, get_luminance(*secondary_raw))))
        accent_hover = adjust_lightness(primary_accent, min(0.9, get_luminance(*primary_accent) + 0.08))

        text_primary = (248, 250, 252) if not config.contrast_boost else (255, 255, 255)
        text_secondary = (142, 155, 168)
        text_link = primary_accent
        separator_line = blend_colors(bg_color, (255, 255, 255), 0.10)
        
        input_bar_text = (248, 250, 252)
        input_bar_hint = (130, 140, 155)

        if config.bubble_style == "accent":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary
        elif config.bubble_style == "tinted":
            out_bubble_bg = blend_colors(bg_color, primary_accent, 0.45)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = blend_colors(bg_color, secondary_accent, 0.20)
            in_bubble_text = text_primary
        elif config.bubble_style == "contrast":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = secondary_accent
            in_bubble_text = get_best_text_color(in_bubble_bg)
        else: # minimal
            out_bubble_bg = bg_elevated
            out_bubble_text = text_primary
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary

    else:
        # Crisp Light Theme
        tinted_light = blend_colors((245, 247, 250), base_raw, 0.05)
        
        l_bg = max(0.90, min(1.0, 0.96 + b_offset))
        bg_color = adjust_lightness(tinted_light, l_bg)
        bg_surface = (255, 255, 255)
        bg_elevated = blend_colors((255, 255, 255), (0, 0, 0), 0.05)
        topbar_bg = (255, 255, 255)
        dialogs_bg = (255, 255, 255)
        input_bar_bg = (255, 255, 255)

        primary_accent = adjust_lightness(primary_raw, min(0.45, max(0.35, get_luminance(*primary_raw))))
        secondary_accent = adjust_lightness(secondary_raw, min(0.48, max(0.35, get_luminance(*secondary_raw))))
        accent_hover = adjust_lightness(primary_accent, max(0.2, get_luminance(*primary_accent) - 0.08))

        text_primary = (24, 28, 35) if not config.contrast_boost else (0, 0, 0)
        text_secondary = (105, 115, 130)
        text_link = primary_accent
        separator_line = (228, 232, 240)
        
        input_bar_text = (24, 28, 35)
        input_bar_hint = (150, 160, 175)

        if config.bubble_style == "accent":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = (255, 255, 255)
            in_bubble_text = text_primary
        elif config.bubble_style == "tinted":
            out_bubble_bg = blend_colors((255, 255, 255), primary_accent, 0.22)
            out_bubble_text = (20, 25, 35)
            in_bubble_bg = (255, 255, 255)
            in_bubble_text = text_primary
        elif config.bubble_style == "contrast":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = blend_colors((255, 255, 255), secondary_accent, 0.25)
            in_bubble_text = text_primary
        else: # minimal
            out_bubble_bg = (235, 240, 248)
            out_bubble_text = text_primary
            in_bubble_bg = (255, 255, 255)
            in_bubble_text = text_primary

    # Compute time & reply bar colors
    in_bubble_time = blend_colors(in_bubble_text, in_bubble_bg, 0.40)
    in_bubble_reply_bar = primary_accent

    out_bubble_time = blend_colors(out_bubble_text, out_bubble_bg, 0.35)
    out_bubble_reply_bar = blend_colors(out_bubble_text, (255, 255, 255), 0.2)

    send_button = primary_accent
    unread_badge_bg = primary_accent
    unread_badge_text = get_best_text_color(unread_badge_bg)

    return ResolvedThemePalette(
        mode=mode,
        bg_color=bg_color,
        bg_surface=bg_surface,
        bg_elevated=bg_elevated,
        topbar_bg=topbar_bg,
        dialogs_bg=dialogs_bg,
        primary_accent=primary_accent,
        secondary_accent=secondary_accent,
        accent_hover=accent_hover,
        in_bubble_bg=in_bubble_bg,
        in_bubble_text=in_bubble_text,
        in_bubble_time=in_bubble_time,
        in_bubble_reply_bar=in_bubble_reply_bar,
        out_bubble_bg=out_bubble_bg,
        out_bubble_text=out_bubble_text,
        out_bubble_time=out_bubble_time,
        out_bubble_reply_bar=out_bubble_reply_bar,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_link=text_link,
        send_button=send_button,
        unread_badge_bg=unread_badge_bg,
        unread_badge_text=unread_badge_text,
        separator_line=separator_line,
        input_bar_bg=input_bar_bg,
        input_bar_text=input_bar_text,
        input_bar_hint=input_bar_hint
    )
