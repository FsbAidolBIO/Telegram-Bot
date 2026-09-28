"""
Session management module for storing user theme states, images, and precomputed fast previews with TTL and LRU render caching.
"""

from typing import Dict, Optional, List
import time
import io
import logging
from PIL import Image
from theme_engine.color_extractor import (
    extract_palette_from_image,
    detect_image_brightness,
    ExtractedColor,
    is_valid_hex,
    hex_to_rgb
)
from theme_engine.palette import ThemeConfig, build_palette, ResolvedThemePalette
from theme_engine.wallpaper_generator import generate_wallpaper
from theme_engine.preview_generator import render_preview_to_bytes

logger = logging.getLogger(__name__)


class UserThemeSession:
    """Stores the active theme customization state for a user."""
    def __init__(self, user_id: int, image_bytes: bytes):
        self.user_id = user_id
        self.image_bytes = image_bytes
        self.created_at = time.time()
        self.last_accessed = time.time()
        
        # 1. Full uncompressed original image for final theme export (up to 4096px)
        raw_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        max_dim = 4096
        if max(raw_img.width, raw_img.height) > max_dim:
            raw_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        self.original_image = raw_img
        
        # 2. Fast preview proxy image (max 1080px) for instantaneous preview card rendering
        preview_thumb = raw_img.copy()
        preview_thumb.thumbnail((1080, 1080), Image.Resampling.BILINEAR)
        self.preview_image = preview_thumb
        
        # 3. Extract initial colors
        self.extracted_colors = extract_palette_from_image(self.preview_image, num_colors=8)
        self.is_image_light = detect_image_brightness(self.preview_image)
        
        # Default config: original image on full screen
        initial_mode = "light" if self.is_image_light else "dark"
        self.config = ThemeConfig(mode=initial_mode, wallpaper_mode="original")
        
        # 4. In-memory LRU render cache for this session (state_key -> jpeg bytes)
        self._render_cache: Dict[str, bytes] = {}

    def touch(self):
        """Update last accessed timestamp."""
        self.last_accessed = time.time()

    def get_state_key(self) -> str:
        """Compute unique cache key for current theme configuration."""
        c = self.config
        return f"{c.mode}:{c.accent_idx}:{c.custom_accent_hex}:{c.bubble_style}:{c.chat_tint}:{c.wallpaper_mode}:{c.wallpaper_focus}:{c.hue_shift_deg}:{c.brightness_offset}:{c.contrast_boost}"

    def get_palette(self) -> ResolvedThemePalette:
        """Resolve current palette with active config."""
        return build_palette(self.extracted_colors, self.config, self.is_image_light)

    def get_wallpaper(self, width: Optional[int] = None, height: Optional[int] = None, for_preview: bool = False) -> Image.Image:
        """
        Generate wallpaper.
        If for_preview=True, uses fast pre-scaled proxy image.
        If for_preview=False, uses 100% full-resolution original image.
        """
        palette = self.get_palette()
        base = self.preview_image if for_preview else self.original_image
        return generate_wallpaper(
            base,
            palette,
            mode=self.config.wallpaper_mode,
            width=width,
            height=height,
            focus=self.config.wallpaper_focus
        )

    def get_rendered_preview_bytes(self) -> bytes:
        """
        Get or compute the preview card JPEG bytes with sub-millisecond LRU caching.
        """
        key = self.get_state_key()
        if key in self._render_cache:
            return self._render_cache[key]
        
        palette = self.get_palette()
        wallpaper = self.get_wallpaper(width=800, height=820, for_preview=True)
        preview_bytes = render_preview_to_bytes(palette, wallpaper, self.extracted_colors)
        
        # LRU cache size limit: 20 renders
        if len(self._render_cache) >= 20:
            first_key = next(iter(self._render_cache))
            del self._render_cache[first_key]
            
        self._render_cache[key] = preview_bytes
        return preview_bytes

    def set_custom_accent(self, hex_code: str) -> bool:
        """Set custom hex accent color and return success."""
        if not is_valid_hex(hex_code):
            return False
        clean_hex = hex_code.strip()
        if not clean_hex.startswith("#"):
            clean_hex = "#" + clean_hex
        self.config.custom_accent_hex = clean_hex
        rgb = hex_to_rgb(clean_hex)
        custom_color = ExtractedColor(rgb, count=999)
        if not any(c.hex.lower() == clean_hex.lower() for c in self.extracted_colors):
            self.extracted_colors.insert(0, custom_color)
            self.config.accent_idx = 0
        return True


class SessionManager:
    """Manages all active user sessions with automatic expiration."""
    def __init__(self, ttl_seconds: int = 7200):
        self._sessions: Dict[int, UserThemeSession] = {}
        self.ttl_seconds = ttl_seconds

    def create_session(self, user_id: int, image_bytes: bytes) -> UserThemeSession:
        self.cleanup_expired()
        session = UserThemeSession(user_id, image_bytes)
        self._sessions[user_id] = session
        return session

    def get_session(self, user_id: int) -> Optional[UserThemeSession]:
        session = self._sessions.get(user_id)
        if session:
            if time.time() - session.last_accessed > self.ttl_seconds:
                del self._sessions[user_id]
                return None
            session.touch()
        return session

    def cleanup_expired(self):
        now = time.time()
        expired = [uid for uid, s in self._sessions.items() if now - s.last_accessed > self.ttl_seconds]
        for uid in expired:
            del self._sessions[uid]


session_manager = SessionManager()
