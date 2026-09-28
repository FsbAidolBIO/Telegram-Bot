"""
Wallpaper processing and generation module for Telegram themes.
Provides crisp, full-screen wallpaper scaling with zero distortion and zero unwanted blur.
"""

from typing import Tuple, Optional
import io
from PIL import Image, ImageFilter, ImageDraw, ImageOps
import numpy as np
from theme_engine.palette import ResolvedThemePalette


def generate_wallpaper(
    base_image: Optional[Image.Image],
    palette: ResolvedThemePalette,
    mode: str = "original",
    width: int = 1080,
    height: int = 1920
) -> Image.Image:
    """
    Generate crisp, full-screen wallpaper with exact aspect ratio and zero distortion.
    """
    if base_image is None or mode == "solid":
        # Solid color background
        return Image.new("RGB", (width, height), palette.bg_color)

    img = base_image.convert("RGB")

    if mode == "original":
        # Clean, crisp original image covering full screen without ANY blur or borders
        return ImageOps.fit(
            img,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )

    elif mode == "dimmed":
        # Full-screen original image with subtle darkening for improved message readability
        cropped = ImageOps.fit(
            img,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )
        overlay_color = (0, 0, 0) if palette.mode in ("dark", "amoled") else (255, 255, 255)
        alpha = 0.35 if palette.mode in ("dark", "amoled") else 0.25
        overlay = Image.new("RGB", (width, height), overlay_color)
        return Image.blend(cropped, overlay, alpha)

    elif mode == "blurred":
        # Gaussian blur effect
        cropped = ImageOps.fit(
            img,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )
        blurred = cropped.filter(ImageFilter.GaussianBlur(radius=28))
        overlay_color = palette.bg_color
        alpha = 0.35 if palette.mode in ("dark", "amoled") else 0.20
        overlay = Image.new("RGB", (width, height), overlay_color)
        return Image.blend(blurred, overlay, alpha)

    elif mode == "gradient":
        # Smooth dual-tone gradient
        return create_smooth_gradient(
            width, height,
            color1=palette.primary_accent,
            color2=palette.secondary_accent,
            color3=palette.bg_color,
            is_dark=palette.mode in ("dark", "amoled")
        )

    # Fallback to original cover
    return ImageOps.fit(
        img,
        (width, height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5)
    )


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
    sw, sh = 256, 455
    y, x = np.mgrid[0:sh, 0:sw]
    
    diag = (x / sw * 0.6 + y / sh * 0.4)
    
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


def get_wallpaper_jpeg_bytes(wallpaper_img: Image.Image, quality: int = 92) -> bytes:
    """Convert PIL image to high quality JPEG bytes."""
    bio = io.BytesIO()
    wallpaper_img.save(bio, format="JPEG", quality=quality, optimize=True)
    return bio.getvalue()
