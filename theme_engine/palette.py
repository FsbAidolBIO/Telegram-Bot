"""
Theme Palette generator and color logic for Telegram themes.
Handles mode switching (Dark, Light, AMOLED), chromatic chat atmosphere, bubble styling,
wallpaper focus, procedural patterns, and hue rotation.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import colorsys
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


def shift_hue(rgb: Tuple[int, int, int], degrees: int) -> Tuple[int, int, int]:
    """Shift hue of RGB color by degrees."""
    if degrees == 0:
        return rgb
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    new_h = (h + degrees / 360.0) % 1.0
    nr, ng, nb = colorsys.hls_to_rgb(new_h, l, s)
    return (int(nr * 255), int(ng * 255), int(nb * 255))


@dataclass
class ThemeConfig:
    """Settings selected by user for theme generation."""
    mode: str = "dark"               # "dark", "light", "amoled", "auto"
    accent_idx: int = 0             # Index into extracted vibrant colors
    secondary_idx: int = 1          # Index for secondary accent
    bubble_style: str = "vibrant"   # "vibrant", "dual", "soft", "glass", "minimal"
    chat_tint: str = "rich"         # "rich" (22%), "medium" (14%), "subtle" (6%), "clean" (0%)
    wallpaper_mode: str = "original"# "original", "dimmed", "blurred", "gradient", "bokeh", "waves", "topography", "synthwave", "solid"
    wallpaper_focus: str = "center" # "center", "top", "bottom"
    hue_shift_deg: int = 0          # 0 to 330 deg
    brightness_offset: int = 0      # -30 to +30 percent
    contrast_boost: bool = False
    custom_accent_hex: Optional[str] = None

    def cycle_mode(self) -> str:
        modes = ["dark", "light", "amoled"]
        next_idx = (modes.index(self.mode) + 1) % len(modes) if self.mode in modes else 0
        self.mode = modes[next_idx]
        return self.mode

    def cycle_wallpaper(self) -> str:
        wallpapers = ["original", "dimmed", "blurred", "gradient", "bokeh", "waves", "topography", "synthwave", "solid"]
        next_idx = (wallpapers.index(self.wallpaper_mode) + 1) % len(wallpapers) if self.wallpaper_mode in wallpapers else 0
        self.wallpaper_mode = wallpapers[next_idx]
        return self.wallpaper_mode

    def cycle_focus(self) -> str:
        foci = ["center", "top", "bottom"]
        next_idx = (foci.index(self.wallpaper_focus) + 1) % len(foci) if self.wallpaper_focus in foci else 0
        self.wallpaper_focus = foci[next_idx]
        return self.wallpaper_focus

    def cycle_hue(self) -> int:
        self.hue_shift_deg = (self.hue_shift_deg + 30) % 360
        return self.hue_shift_deg

    def cycle_bubble(self) -> str:
        bubbles = ["vibrant", "dual", "soft", "glass", "minimal"]
        next_idx = (bubbles.index(self.bubble_style) + 1) % len(bubbles) if self.bubble_style in bubbles else 0
        self.bubble_style = bubbles[next_idx]
        return self.bubble_style

    def cycle_chat_tint(self) -> str:
        tints = ["rich", "medium", "subtle", "clean"]
        next_idx = (tints.index(self.chat_tint) + 1) % len(tints) if self.chat_tint in tints else 0
        self.chat_tint = tints[next_idx]
        return self.chat_tint

    def cycle_accent(self, max_count: int) -> int:
        if max_count <= 0:
            return 0
        self.custom_accent_hex = None
        self.accent_idx = (self.accent_idx + 1) % max_count
        return self.accent_idx

    def set_accent_index(self, idx: int):
        self.custom_accent_hex = None
        self.accent_idx = idx


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
    Generate a full harmonized color scheme with rich chromatic atmosphere.
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

    mode = config.mode
    if mode == "auto":
        mode = "light" if is_image_light else "dark"

    vibrant_sorted = sorted(extracted_colors, key=lambda c: c.vibrancy, reverse=True)
    
    if config.custom_accent_hex:
        primary_raw = hex_to_rgb(config.custom_accent_hex)
    else:
        accent_i = config.accent_idx % len(vibrant_sorted)
        primary_raw = vibrant_sorted[accent_i].rgb

    sec_i = (config.accent_idx + 1) % len(vibrant_sorted)
    secondary_raw = vibrant_sorted[sec_i].rgb
    base_raw = extracted_colors[0].rgb

    if config.hue_shift_deg != 0:
        primary_raw = shift_hue(primary_raw, config.hue_shift_deg)
        secondary_raw = shift_hue(secondary_raw, config.hue_shift_deg)
        base_raw = shift_hue(base_raw, config.hue_shift_deg)

    tint_factors = {
        "rich": 0.22,
        "medium": 0.14,
        "subtle": 0.06,
        "clean": 0.00
    }
    tint_factor = tint_factors.get(config.chat_tint, 0.18)
    b_offset = config.brightness_offset / 100.0

    if mode == "amoled":
        bg_color = (0, 0, 0)
        bg_surface = blend_colors((16, 16, 20), primary_raw, tint_factor * 0.4)
        bg_elevated = blend_colors((26, 26, 32), primary_raw, tint_factor * 0.6)
        topbar_bg = (0, 0, 0)
        dialogs_bg = (0, 0, 0)
        input_bar_bg = bg_surface
        
        primary_accent = adjust_lightness(primary_raw, min(0.68, max(0.50, get_luminance(*primary_raw))))
        secondary_accent = adjust_lightness(secondary_raw, min(0.68, max(0.50, get_luminance(*secondary_raw))))
        accent_hover = adjust_lightness(primary_accent, min(1.0, get_luminance(*primary_accent) + 0.1))

        text_primary = (255, 255, 255)
        text_secondary = (155, 160, 175)
        text_link = primary_accent
        separator_line = blend_colors((35, 35, 42), primary_raw, 0.15)
        
        input_bar_text = (255, 255, 255)
        input_bar_hint = (125, 130, 145)

        if config.bubble_style == "vibrant":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = bg_elevated
            in_bubble_text = (245, 248, 255)
        elif config.bubble_style == "dual":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = secondary_accent
            in_bubble_text = get_best_text_color(in_bubble_bg)
        elif config.bubble_style == "soft":
            out_bubble_bg = blend_colors((35, 35, 45), primary_accent, 0.55)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = blend_colors((25, 25, 32), secondary_accent, 0.35)
            in_bubble_text = (240, 245, 255)
        elif config.bubble_style == "glass":
            out_bubble_bg = blend_colors((20, 20, 25), primary_accent, 0.40)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = (20, 20, 24)
            in_bubble_text = (240, 240, 240)
        else:
            out_bubble_bg = (32, 32, 38)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = (18, 18, 22)
            in_bubble_text = (235, 235, 235)

    elif mode == "dark":
        tinted_dark = blend_colors((18, 22, 28), base_raw, tint_factor)
        l_bg = max(0.06, min(0.28, 0.11 + b_offset))
        bg_color = adjust_lightness(tinted_dark, l_bg)
        
        bg_surface = blend_colors(bg_color, primary_raw, 0.08)
        bg_surface = blend_colors(bg_surface, (255, 255, 255), 0.07)
        bg_elevated = blend_colors(bg_surface, (255, 255, 255), 0.08)
        
        topbar_bg = bg_color
        dialogs_bg = bg_color
        input_bar_bg = bg_surface

        primary_accent = adjust_lightness(primary_raw, min(0.70, max(0.53, get_luminance(*primary_raw))))
        secondary_accent = adjust_lightness(secondary_raw, min(0.70, max(0.53, get_luminance(*secondary_raw))))
        accent_hover = adjust_lightness(primary_accent, min(0.92, get_luminance(*primary_accent) + 0.08))

        text_primary = (248, 250, 255) if not config.contrast_boost else (255, 255, 255)
        text_secondary = blend_colors((145, 158, 175), primary_accent, 0.15)
        text_link = primary_accent
        separator_line = blend_colors(bg_color, (255, 255, 255), 0.12)
        
        input_bar_text = (248, 250, 255)
        input_bar_hint = blend_colors((135, 145, 160), primary_accent, 0.15)

        if config.bubble_style == "vibrant":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = bg_elevated
            in_bubble_text = text_primary
        elif config.bubble_style == "dual":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = secondary_accent
            in_bubble_text = get_best_text_color(in_bubble_bg)
        elif config.bubble_style == "soft":
            out_bubble_bg = blend_colors(bg_color, primary_accent, 0.50)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = blend_colors(bg_color, secondary_accent, 0.28)
            in_bubble_text = text_primary
        elif config.bubble_style == "glass":
            out_bubble_bg = blend_colors(bg_color, primary_accent, 0.35)
            out_bubble_text = (255, 255, 255)
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary
        else:
            out_bubble_bg = bg_elevated
            out_bubble_text = text_primary
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary

    else:
        tinted_light = blend_colors((242, 245, 250), base_raw, tint_factor * 0.7)
        l_bg = max(0.88, min(0.98, 0.95 + b_offset))
        bg_color = adjust_lightness(tinted_light, l_bg)
        
        bg_surface = blend_colors((255, 255, 255), primary_raw, 0.04)
        bg_elevated = blend_colors(bg_surface, (0, 0, 0), 0.04)
        topbar_bg = bg_surface
        dialogs_bg = bg_surface
        input_bar_bg = bg_surface

        primary_accent = adjust_lightness(primary_raw, min(0.44, max(0.32, get_luminance(*primary_raw))))
        secondary_accent = adjust_lightness(secondary_raw, min(0.48, max(0.32, get_luminance(*secondary_raw))))
        accent_hover = adjust_lightness(primary_accent, max(0.2, get_luminance(*primary_accent) - 0.08))

        text_primary = (20, 26, 36) if not config.contrast_boost else (0, 0, 0)
        text_secondary = blend_colors((95, 110, 130), primary_accent, 0.20)
        text_link = primary_accent
        separator_line = blend_colors(bg_color, (0, 0, 0), 0.08)
        
        input_bar_text = (20, 26, 36)
        input_bar_hint = blend_colors((145, 155, 170), primary_accent, 0.15)

        if config.bubble_style == "vibrant":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary
        elif config.bubble_style == "dual":
            out_bubble_bg = primary_accent
            out_bubble_text = get_best_text_color(out_bubble_bg)
            in_bubble_bg = blend_colors(bg_surface, secondary_accent, 0.30)
            in_bubble_text = text_primary
        elif config.bubble_style == "soft":
            out_bubble_bg = blend_colors((255, 255, 255), primary_accent, 0.25)
            out_bubble_text = (20, 25, 35)
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary
        elif config.bubble_style == "glass":
            out_bubble_bg = blend_colors(bg_color, primary_accent, 0.20)
            out_bubble_text = (20, 25, 35)
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary
        else:
            out_bubble_bg = blend_colors(bg_surface, primary_accent, 0.15)
            out_bubble_text = text_primary
            in_bubble_bg = bg_surface
            in_bubble_text = text_primary

    in_bubble_time = blend_colors(in_bubble_text, in_bubble_bg, 0.40)
    in_bubble_reply_bar = primary_accent

    out_bubble_time = blend_colors(out_bubble_text, out_bubble_bg, 0.35)
    out_bubble_reply_bar = blend_colors(out_bubble_text, (255, 255, 255), 0.25)

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
