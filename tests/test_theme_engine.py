"""
Unit tests for the Telegram Theme Engine.
"""

import unittest
import io
import json
from PIL import Image, ImageDraw
from theme_engine.color_extractor import (
    extract_palette_from_image,
    detect_image_brightness,
    rgb_to_hex,
    hex_to_rgb,
    get_luminance,
    get_best_text_color,
    get_color_name,
    shift_temperature,
    ExtractedColor
)
from theme_engine.palette import ThemeConfig, build_palette
from theme_engine.wallpaper_generator import generate_wallpaper, get_wallpaper_jpeg_bytes
from theme_engine.android_generator import generate_android_theme, to_argb_int
from theme_engine.desktop_generator import generate_desktop_theme, generate_desktop_palette_text
from theme_engine.preview_generator import render_preview_to_bytes
from theme_engine.palette_card_generator import generate_palette_card_bytes
from theme_engine.json_exporter import export_theme_to_json
from handlers.session_manager import SessionManager


class TestThemeEngine(unittest.TestCase):
    def setUp(self):
        self.img = Image.new("RGB", (500, 700), color=(20, 30, 45))
        draw = ImageDraw.Draw(self.img)
        draw.rectangle([(40, 40), (200, 200)], fill=(255, 120, 0))
        draw.ellipse([(220, 40), (450, 300)], fill=(0, 200, 255))
        draw.rectangle([(100, 350), (400, 600)], fill=(230, 230, 240))

    def test_color_conversions(self):
        self.assertEqual(rgb_to_hex(255, 0, 128), "#ff0080")
        self.assertEqual(hex_to_rgb("#ff0080"), (255, 0, 128))
        self.assertEqual(hex_to_rgb("ff0080"), (255, 0, 128))
        self.assertTrue(len(get_color_name((0, 200, 255))) > 0)

    def test_temperature_shift(self):
        warm = shift_temperature((100, 100, 100), 0.2)
        self.assertGreater(warm[0], 100)
        cool = shift_temperature((100, 100, 100), -0.2)
        self.assertGreater(cool[2], 100)

    def test_luminance_and_contrast(self):
        lum_white = get_luminance(255, 255, 255)
        lum_black = get_luminance(0, 0, 0)
        self.assertAlmostEqual(lum_white, 1.0, places=2)
        self.assertAlmostEqual(lum_black, 0.0, places=2)
        self.assertEqual(get_best_text_color((0, 0, 0)), (255, 255, 255))
        self.assertEqual(get_best_text_color((255, 255, 255)), (20, 20, 24))

    def test_palette_extraction(self):
        palette = extract_palette_from_image(self.img, num_colors=6)
        self.assertGreaterEqual(len(palette), 3)
        for c in palette:
            self.assertTrue(c.hex.startswith("#"))
            self.assertEqual(len(c.hex), 7)
            self.assertGreaterEqual(c.vibrancy, 0.0)

    def test_theme_modes(self):
        colors = extract_palette_from_image(self.img)
        
        cfg_dark = ThemeConfig(mode="dark")
        pal_dark = build_palette(colors, cfg_dark)
        self.assertEqual(pal_dark.mode, "dark")
        self.assertLess(get_luminance(*pal_dark.bg_color), 0.35)
        
        cfg_light = ThemeConfig(mode="light")
        pal_light = build_palette(colors, cfg_light)
        self.assertEqual(pal_light.mode, "light")
        self.assertGreater(get_luminance(*pal_light.bg_color), 0.80)
        
        cfg_amoled = ThemeConfig(mode="amoled")
        pal_amoled = build_palette(colors, cfg_amoled)
        self.assertEqual(pal_amoled.mode, "amoled")
        self.assertEqual(pal_amoled.bg_color, (0, 0, 0))

    def test_wallpaper_variations(self):
        colors = extract_palette_from_image(self.img)
        palette = build_palette(colors, ThemeConfig(mode="dark"))
        
        for w_mode in ["original", "dimmed", "blurred", "gradient", "solid"]:
            wall = generate_wallpaper(self.img, palette, mode=w_mode, width=400, height=600)
            self.assertEqual(wall.size, (400, 600))
            jpeg_data = get_wallpaper_jpeg_bytes(wall)
            self.assertGreater(len(jpeg_data), 100)

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

    def test_session_manager(self):
        sm = SessionManager(ttl_seconds=60)
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        
        session = sm.create_session(user_id=12345, image_bytes=bio.getvalue())
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, 12345)
        
        retrieved = sm.get_session(12345)
        self.assertEqual(retrieved, session)
        
        session.config.cycle_mode()
        self.assertIn(session.config.mode, ["dark", "light", "amoled"])


if __name__ == "__main__":
    unittest.main()
