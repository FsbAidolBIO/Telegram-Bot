"""
Session management module for storing user theme states and images in memory with TTL.
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

logger = logging.getLogger(__name__)


class UserThemeSession:
    """Stores the active theme customization state for a user."""
    def __init__(self, user_id: int, image_bytes: bytes):
        self.user_id = user_id
        self.created_at = time.time()
        self.last_accessed = time.time()
        
        # Load and safely resize image (max 2560px) to prevent excessive memory usage
        raw_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        max_dim = 2560
        if max_dim < max(raw_img.width, raw_img.height):
            raw_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        
        self.original_image = raw_img
        
        # Extract initial colors
        self.extracted_colors = extract_palette_from_image(self.original_image, num_colors=8)
        self.is_image_light = detect_image_brightness(self.original_image)
        
        # Default config based on detected brightness
        initial_mode = "light" if self.is_image_light else "dark"
        self.config = ThemeConfig(mode=initial_mode, wallpaper_mode="blurred")

    def touch(self):
        """Update last accessed timestamp."""
        self.last_accessed = time.time()

    def get_palette(self) -> ResolvedThemePalette:
        """Resolve current palette with active config."""
        return build_palette(self.extracted_colors, self.config, self.is_image_light)

    def get_wallpaper(self, width: int = 1080, height: int = 1920) -> Image.Image:
        """Generate wallpaper for current setting."""
        palette = self.get_palette()
        return generate_wallpaper(
            self.original_image,
            palette,
            mode=self.config.wallpaper_mode,
            width=width,
            height=height
        )

    def set_custom_accent(self, hex_code: str) -> bool:
        """Set custom hex accent color and return success."""
        if not is_valid_hex(hex_code):
            return False
        clean_hex = hex_code.strip()
        if not clean_hex.startswith("#"):
            clean_hex = "#" + clean_hex
        self.config.custom_accent_hex = clean_hex
        # Also add to extracted colors if not present
        rgb = hex_to_rgb(clean_hex)
        custom_color = ExtractedColor(rgb, count=999)
        if not any(c.hex.lower() == clean_hex.lower() for c in self.extracted_colors):
            self.extracted_colors.insert(0, custom_color)
            self.config.accent_idx = 0
        return True


class SessionManager:
    """Manages all active user sessions with automatic expiration."""
    def __init__(self, ttl_seconds: int = 7200): # 2 hours TTL
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


# Global session manager instance
session_manager = SessionManager()
