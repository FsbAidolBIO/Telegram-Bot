"""
Wallpaper processing and generation module for Telegram themes.
Provides original, blurred, gradient, dimmed, and solid wallpaper variants.
"""

from typing import Tuple, Optional
import io
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import numpy as np
from theme_engine.palette import ResolvedThemePalette


def generate_wallpaper(
    base_image: Optional[Image.Image],
    palette: ResolvedThemePalette,
    mode: str = "blurred",
    width: int = 1080,
    height: int = 1920
) -> Image.Image:
    """
    Generate or process wallpaper image according to selected mode.
    Returns a PIL Image in RGB format.
    """
    if base_image is None or mode == "solid":
        # Create solid color background
        img = Image.new("RGB", (width, height), palette.bg_color)
        return img

    # Resize/crop base image to target dimensions (cover aspect ratio)
    img = base_image.convert("RGB")
    img_ratio = img.width / img.height
    target_ratio = width / height

    if img_ratio > target_ratio:
        # Image is wider: crop sides
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Image is taller: crop top/bottom
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    img = img.resize((width, height), Image.Resampling.LANCZOS)

    if mode == "blurred":
        # Apply smooth Gaussian blur
        blurred = img.filter(ImageFilter.GaussianBlur(radius=32))
        
        # Apply subtle overlay to ensure chat readability
        overlay_color = palette.bg_color
        alpha = 0.40 if palette.mode in ("dark", "amoled") else 0.25
        overlay = Image.new("RGB", (width, height), overlay_color)
        img = Image.blend(blurred, overlay, alpha)

    elif mode == "dimmed":
        # Darken/brighten original image slightly for text readability
        overlay_color = (0, 0, 0) if palette.mode in ("dark", "amoled") else (255, 255, 255)
        alpha = 0.45 if palette.mode in ("dark", "amoled") else 0.35
        overlay = Image.new("RGB", (width, height), overlay_color)
        img = Image.blend(img, overlay, alpha)

    elif mode == "gradient":
        # Create a smooth dual/tri tone gradient
        img = create_smooth_gradient(
            width, height,
            color1=palette.primary_accent,
            color2=palette.secondary_accent,
            color3=palette.bg_color,
            is_dark=palette.mode in ("dark", "amoled")
        )

    # mode == "original" returns img as is (cropped & resized)
    return img


def create_smooth_gradient(
    width: int,
    height: int,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    color3: Tuple[int, int, int],
    is_dark: bool = True
) -> Image.Image:
    """
    Create a high-quality diagonal gradient image.
    """
    # Create smaller array for speed, then resize with bilinear
    sw, sh = 256, 455
    y, x = np.mgrid[0:sh, 0:sw]
    
    # Normalized diagonal coordinate 0.0 to 1.0
    diag = (x / sw * 0.6 + y / sh * 0.4)
    
    # Darken colors slightly if in dark mode so background isn't blinding
    if is_dark:
        c1 = [int(v * 0.35) for v in color1]
        c2 = [int(v * 0.25) for v in color2]
        c3 = color3
    else:
        c1 = [int(v * 0.25 + 255 * 0.75) for v in color1]
        c2 = [int(v * 0.20 + 255 * 0.80) for v in color2]
        c3 = color3

    r = (c1[0] * (1 - diag) + c2[0] * diag * 0.6 + c3[0] * diag * 0.4).clip(0, 255).astype(np.uint8)
    g = (c1[1] * (1 - diag) + c2[1] * diag * 0.6 + c3[1] * diag * 0.4).clip(0, 255).astype(np.uint8)
    b = (c1[2] * (1 - diag) + c2[2] * diag * 0.6 + c3[2] * diag * 0.4).clip(0, 255).astype(np.uint8)

    arr = np.dstack((r, g, b))
    small_img = Image.fromarray(arr, mode="RGB")
    return small_img.resize((width, height), Image.Resampling.BICUBIC)


def get_wallpaper_jpeg_bytes(wallpaper_img: Image.Image, quality: int = 88) -> bytes:
    """Convert PIL image to JPEG bytes for inclusion into .attheme or .tdesktop-theme."""
    bio = io.BytesIO()
    wallpaper_img.save(bio, format="JPEG", quality=quality, optimize=True)
    return bio.getvalue()
