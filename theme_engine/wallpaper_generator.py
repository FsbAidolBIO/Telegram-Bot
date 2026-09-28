"""
Wallpaper processing and generation module for Telegram themes.
Provides aspect-ratio preserving scaling, anti-stretch protection,
and multiple background modes (blur, fit with blurred borders, cover, dimmed, gradient, solid).
"""

from typing import Tuple, Optional
import io
from PIL import Image, ImageFilter, ImageDraw, ImageOps
import numpy as np
from theme_engine.palette import ResolvedThemePalette


def create_fit_with_blurred_backdrop(
    image: Image.Image,
    target_width: int,
    target_height: int,
    palette: ResolvedThemePalette
) -> Image.Image:
    """
    Fits the original image completely inside (target_width, target_height) without
    ANY cropping or stretching, and fills the letterbox/pillarbox margins with a
    Gaussian-blurred and tinted version of the image.
    """
    # 1. Create blurred backdrop filling entire canvas
    backdrop = ImageOps.fit(image, (target_width, target_height), method=Image.Resampling.BILINEAR)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=40))
    
    # Apply tint to backdrop for cohesion
    tint_color = palette.bg_color
    alpha = 0.45 if palette.mode in ("dark", "amoled") else 0.30
    tint = Image.new("RGB", (target_width, target_height), tint_color)
    backdrop = Image.blend(backdrop, tint, alpha)

    # 2. Scale original image to fit within canvas preserving 100% aspect ratio
    fitted = image.copy()
    fitted.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

    # 3. Paste centered on backdrop
    pos_x = (target_width - fitted.width) // 2
    pos_y = (target_height - fitted.height) // 2

    canvas = backdrop.copy()
    canvas.paste(fitted, (pos_x, pos_y))
    return canvas


def generate_wallpaper(
    base_image: Optional[Image.Image],
    palette: ResolvedThemePalette,
    mode: str = "blurred",
    width: int = 1080,
    height: int = 1920
) -> Image.Image:
    """
    Generate or process wallpaper image according to selected mode with zero distortion.
    Returns a PIL Image in RGB format at exact (width, height) without stretching.
    """
    if base_image is None or mode == "solid":
        # Create solid color background
        return Image.new("RGB", (width, height), palette.bg_color)

    img = base_image.convert("RGB")

    if mode == "fit_blur" or mode == "fit":
        # Entire image visible without any crop or stretch, blurred edges
        return create_fit_with_blurred_backdrop(img, width, height, palette)

    elif mode == "blurred":
        # Proportional center cover + Gaussian Blur + Theme Tint
        cropped = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        blurred = cropped.filter(ImageFilter.GaussianBlur(radius=32))
        
        overlay_color = palette.bg_color
        alpha = 0.40 if palette.mode in ("dark", "amoled") else 0.25
        overlay = Image.new("RGB", (width, height), overlay_color)
        return Image.blend(blurred, overlay, alpha)

    elif mode == "dimmed":
        # Proportional center cover + Dimming overlay
        cropped = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        overlay_color = (0, 0, 0) if palette.mode in ("dark", "amoled") else (255, 255, 255)
        alpha = 0.42 if palette.mode in ("dark", "amoled") else 0.32
        overlay = Image.new("RGB", (width, height), overlay_color)
        return Image.blend(cropped, overlay, alpha)

    elif mode == "gradient":
        # Dynamic smooth dual-tone gradient
        return create_smooth_gradient(
            width, height,
            color1=palette.primary_accent,
            color2=palette.secondary_accent,
            color3=palette.bg_color,
            is_dark=palette.mode in ("dark", "amoled")
        )

    elif mode in ("original", "cover"):
        # Proportional center cover crop (ZERO stretching, perfect aspect ratio)
        return ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    # Fallback to cover
    return ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


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


def get_wallpaper_jpeg_bytes(wallpaper_img: Image.Image, quality: int = 90) -> bytes:
    """Convert PIL image to JPEG bytes for inclusion into .attheme or .tdesktop-theme."""
    bio = io.BytesIO()
    wallpaper_img.save(bio, format="JPEG", quality=quality, optimize=True)
    return bio.getvalue()
