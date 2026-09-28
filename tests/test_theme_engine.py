"""
Unit tests for Telegram Theme Studio Engine, Procedural Wallpapers, Caching, and WCAG Contrast.
"""

import unittest
import io
import json
import time
from PIL import Image
from theme_engine.color_extractor import (
    extract_palette_from_image,
    detect_image_brightness,
    rgb_to_hex,
    hex_to_rgb,
    get_color_name,
    get_color_emoji,
    is_valid_hex,
    get_luminance,
    get_best_text_color,
    calculate_contrast_ratio,
    get_wcag_badge,
    ExtractedColor
)
from theme_engine.palette import ThemeConfig, build_palette
from theme_engine.wallpaper_generator import generate_wallpaper, get_wallpaper_jpeg_bytes
from theme_engine.android_generator import generate_android_theme
from theme_engine.desktop_generator import generate_desktop_theme, generate_desktop_palette_text
from theme_engine.preview_generator import render_preview_to_bytes
from theme_engine.palette_card_generator import generate_palette_card_bytes
from theme_engine.json_exporter import export_theme_to_json
from theme_engine.procedural_wallpapers import (
    generate_procedural_bokeh,
    generate_procedural_waves,
    generate_procedural_topography,
    generate_procedural_synthwave
)
from handlers.session_manager import SessionManager


class TestThemeEngine(unittest.TestCase):
    def setUp(self):
        self.img = Image.new("RGB", (600, 800), color=(34, 139, 34))
        for y in range(200):
            for x in range(600):
                self.img.putpixel((x, y), (255, 69, 0))

    def test_color_extraction(self):
        colors = extract_palette_from_image(self.img, num_colors=5)
        self.assertGreater(len(colors), 0)
        self.assertTrue(any("ff4500" in c.hex.lower() or "228b22" in c.hex.lower() for c in colors))

    def test_color_conversions(self):
        self.assertEqual(rgb_to_hex(255, 0, 0), "#ff0000")
        self.assertEqual(hex_to_rgb("#ff0000"), (255, 0, 0))
        self.assertTrue(is_valid_hex("#abc"))
        self.assertTrue(is_valid_hex("#aabbcc"))
        self.assertFalse(is_valid_hex("xyz"))
        self.assertTrue(len(get_color_name((0, 200, 255))) > 0)
        self.assertIn(get_color_emoji(255, 0, 0), ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚪", "⚫"])

    def test_luminance_and_contrast(self):
        lum_white = get_luminance(255, 255, 255)
        lum_black = get_luminance(0, 0, 0)
        self.assertAlmostEqual(lum_white, 1.0, places=2)
        self.assertAlmostEqual(lum_black, 0.0, places=2)
        self.assertEqual(get_best_text_color((0, 0, 0)), (255, 255, 255))
        self.assertEqual(get_best_text_color((255, 255, 255)), (20, 20, 24))

    def test_wcag_and_contrast(self):
        contrast = calculate_contrast_ratio((255, 255, 255), (0, 0, 0))
        self.assertGreaterEqual(contrast, 20.0)
        badge = get_wcag_badge(contrast)
        self.assertIn("AAA", badge)

    def test_palette_builder(self):
        colors = extract_palette_from_image(self.img)
        palette_dark = build_palette(colors, ThemeConfig(mode="dark"))
        self.assertEqual(palette_dark.mode, "dark")
        
        palette_light = build_palette(colors, ThemeConfig(mode="light"))
        self.assertEqual(palette_light.mode, "light")

        palette_amoled = build_palette(colors, ThemeConfig(mode="amoled"))
        self.assertEqual(palette_amoled.bg_color, (0, 0, 0))

    def test_procedural_wallpapers(self):
        bokeh = generate_procedural_bokeh(400, 600, (255, 0, 100), (0, 200, 255), (15, 18, 24))
        self.assertEqual(bokeh.size, (400, 600))

        waves = generate_procedural_waves(400, 600, (255, 0, 100), (0, 200, 255), (15, 18, 24))
        self.assertEqual(waves.size, (400, 600))

        topography = generate_procedural_topography(400, 600, (0, 200, 255), (15, 18, 24))
        self.assertEqual(topography.size, (400, 600))

        synthwave = generate_procedural_synthwave(400, 600, (255, 0, 128), (255, 200, 0), (10, 10, 20))
        self.assertEqual(synthwave.size, (400, 600))

    def test_wallpaper_focus_and_hue(self):
        colors = extract_palette_from_image(self.img)
        cfg = ThemeConfig(mode="dark", wallpaper_focus="top", hue_shift_deg=60)
        palette = build_palette(colors, cfg)
        wall = generate_wallpaper(self.img, palette, mode="original", width=400, height=600, focus="top")
        self.assertEqual(wall.size, (400, 600))

    def test_android_theme_generator(self):
        colors = extract_palette_from_image(self.img)
        palette = build_palette(colors, ThemeConfig(mode="dark"))
        wall = generate_wallpaper(self.img, palette, mode="original")
        
        attheme_data = generate_android_theme(palette, wall)
        self.assertIn(b"windowBackgroundWhite=", attheme_data)
        self.assertIn(b"chat_inBubble=", attheme_data)
        self.assertIn(b"chat_outBubble=", attheme_data)
        self.assertIn(b"WPS\n", attheme_data)
        self.assertIn(b"WPE\n", attheme_data)

    def test_desktop_theme_generator(self):
        colors = extract_palette_from_image(self.img)
        palette = build_palette(colors, ThemeConfig(mode="dark"))
        wall = generate_wallpaper(self.img, palette, mode="original")
        
        tdesktop_data = generate_desktop_theme(palette, wall)
        self.assertTrue(tdesktop_data.startswith(b"PK\x03\x04"))
        
        palette_text = generate_desktop_palette_text(palette)
        self.assertIn("windowBg:", palette_text)
        self.assertIn("msgInBg:", palette_text)
        self.assertIn("msgOutBg:", palette_text)

    def test_preview_renderer(self):
        colors = extract_palette_from_image(self.img)
        palette = build_palette(colors, ThemeConfig(mode="dark"))
        wall = generate_wallpaper(self.img, palette, mode="original", width=800, height=820)
        
        preview_data = render_preview_to_bytes(palette, wall, colors)
        self.assertGreater(len(preview_data), 1000)
        self.assertTrue(preview_data.startswith(b"\xff\xd8"))

    def test_palette_card_and_json(self):
        colors = extract_palette_from_image(self.img)
        palette = build_palette(colors, ThemeConfig(mode="dark"))
        
        card_png = generate_palette_card_bytes(palette, colors)
        self.assertTrue(card_png.startswith(b"\x89PNG\r\n\x1a\n"))
        
        json_str = export_theme_to_json(palette, colors)
        parsed = json.loads(json_str)
        self.assertIn("theme_colors", parsed)
        self.assertIn("css_variables", parsed)

    def test_session_manager_and_caching(self):
        sm = SessionManager(ttl_seconds=60)
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        
        session = sm.create_session(user_id=12345, image_bytes=bio.getvalue())
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, 12345)
        
        # Test preview caching speed
        t0 = time.perf_counter()
        bytes1 = session.get_rendered_preview_bytes()
        t1 = time.perf_counter()
        first_duration = t1 - t0

        t2 = time.perf_counter()
        bytes2 = session.get_rendered_preview_bytes()
        t3 = time.perf_counter()
        cached_duration = t3 - t2

        self.assertEqual(bytes1, bytes2)
        self.assertLess(cached_duration, first_duration + 0.05)


if __name__ == "__main__":
    unittest.main()
