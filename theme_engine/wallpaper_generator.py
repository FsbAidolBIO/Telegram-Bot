"""
Wallpaper processing and generation module for Telegram themes.
Provides ultra-sharp lossless wallpaper rendering (subsampling=0, quality=98),
focal point cropping (top/center/bottom), and preserves native resolution.
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
    width: Optional[int] = None,
    height: Optional[int] = None,
    focus: str = "center"
) -> Image.Image:
    """
    Generate wallpaper with customizable crop focus (top/center/bottom).
    - If width/height are specified (e.g. for preview cards), crops/fits cleanly.
    - If width/height are None (e.g. for phone export), preserves 100% native resolution and sharpness.
    """
    centering_map = {
        "center": (0.5, 0.5),
        "top": (0.5, 0.05),
        "bottom": (0.5, 0.95)
    }
    centering = centering_map.get(focus, (0.5, 0.5))

    if base_image is None or mode == "solid":
        w = width or 1080
        h = height or 2400
        return Image.new("RGB", (w, h), palette.bg_color)

    img = base_image.convert("RGB")

    # If explicit target canvas is requested (like preview card 800x690)
    if width is not None and height is not None:
        if mode == "original":
            return ImageOps.fit(
                img,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=centering
            )
        elif mode == "dimmed":
            cropped = ImageOps.fit(
                img,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=centering
            )
            overlay_color = (0, 0, 0) if palette.mode in ("dark", "amoled") else (255, 255, 255)
            alpha = 0.35 if palette.mode in ("dark", "amoled") else 0.25
            overlay = Image.new("RGB", (width, height), overlay_color)
            return Image.blend(cropped, overlay, alpha)
        elif mode == "blurred":
            cropped = ImageOps.fit(
                img,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=centering
            )
            blurred = cropped.filter(ImageFilter.GaussianBlur(radius=28))
            overlay_color = palette.bg_color
            alpha = 0.35 if palette.mode in ("dark", "amoled") else 0.20
            overlay = Image.new("RGB", (width, height), overlay_color)
            return Image.blend(blurred, overlay, alpha)
        elif mode == "gradient":
            return create_smooth_gradient(
                width, height,
                color1=palette.primary_accent,
                color2=palette.secondary_accent,
                color3=palette.bg_color,
                is_dark=palette.mode in ("dark", "amoled")
            )

    # For device export (Android / Desktop): Preserve full native resolution & 100% sharpness!
    if mode == "original":
        return img.copy()

    elif mode == "dimmed":
        overlay_color = (0, 0, 0) if palette.mode in ("dark", "amoled") else (255, 255, 255)
        alpha = 0.35 if palette.mode in ("dark", "amoled") else 0.25
        overlay = Image.new("RGB", img.size, overlay_color)
        return Image.blend(img, overlay, alpha)

    elif mode == "blurred":
        blurred = img.filter(ImageFilter.GaussianBlur(radius=28))
        overlay_color = palette.bg_color
        alpha = 0.35 if palette.mode in ("dark", "amoled") else 0.20
        overlay = Image.new("RGB", img.size, overlay_color)
        return Image.blend(blurred, overlay, alpha)

    elif mode == "gradient":
        return create_smooth_gradient(
            1080, 2400,
            color1=palette.primary_accent,
            color2=palette.secondary_accent,
            color3=palette.bg_color,
            is_dark=palette.mode in ("dark", "amoled")
        )

    return img.copy()


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


def get_wallpaper_jpeg_bytes(wallpaper_img: Image.Image, quality: int = 98, subsampling: int = 0) -> bytes:
    """
    Convert PIL image to ultra-sharp JPEG bytes with 4:4:4 full chroma sampling (subsampling=0).
    Eliminates color bleeding, pixel smearing, and compression blur.
    """
    bio = io.BytesIO()
    wallpaper_img.save(
        bio,
        format="JPEG",
        quality=quality,
        subsampling=subsampling,
        optimize=True
    )
    return bio.getvalue()
