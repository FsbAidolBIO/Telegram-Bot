"""
Telegram Desktop Theme Generator (.tdesktop-theme and .tdesktop-palette).
Packs palette colors and background into standard tdesktop theme archive.
"""

from typing import Tuple, Dict, Any, Optional
import io
import zipfile
from PIL import Image
from theme_engine.palette import ResolvedThemePalette
from theme_engine.wallpaper_generator import get_wallpaper_jpeg_bytes
from theme_engine.color_extractor import rgb_to_hex, blend_colors


def generate_desktop_palette_text(palette: ResolvedThemePalette) -> str:
    """
    Generate the colors.tdesktop-theme file content in standard Telegram Desktop format.
    Ensures nicknames are crisp noticeable white (not colored).
    """
    is_dark = palette.mode in ("dark", "amoled")

    def h(rgb: Tuple[int, int, int], a: Optional[int] = None) -> str:
        base = rgb_to_hex(*rgb)
        if a is not None:
            return f"{base}{a:02x}"
        return base

    d = {
        # Window & Basics
        "windowBg": h(palette.bg_color),
        "windowBgOver": h(palette.bg_surface),
        "windowBgRipple": h(palette.bg_elevated),
        "windowFg": h(palette.text_primary),
        "windowFgOver": h(palette.text_primary),
        "windowSubTextFg": h(palette.text_secondary),
        "windowSubTextFgOver": h(palette.text_primary),
        "windowBoldFg": h(palette.text_primary),
        "windowBoldFgOver": h(palette.text_primary),
        "windowActiveTextFg": h(palette.primary_accent),
        "windowShadowFg": "#00000040" if is_dark else "#00000018",
        "windowShadowFgFallback": "#00000060",
        
        # Top Bar
        "topBarBg": h(palette.topbar_bg),
        
        # Dialogs / Left Chat List (Nicknames are crisp noticeable white)
        "dialogsBg": h(palette.dialogs_bg),
        "dialogsBgOver": h(palette.bg_surface),
        "dialogsBgActive": h(blend_colors(palette.bg_surface, palette.primary_accent, 0.18)),
        "dialogsNameFg": h(palette.text_primary),
        "dialogsNameFgOver": h(palette.text_primary),
        "dialogsNameFgActive": h(palette.text_primary),
        "dialogsChatIconFg": h(palette.text_secondary),
        "dialogsChatIconFgOver": h(palette.text_secondary),
        "dialogsChatIconFgActive": h(palette.text_primary),
        "dialogsDateFg": h(palette.text_secondary),
        "dialogsDateFgOver": h(palette.text_secondary),
        "dialogsDateFgActive": h(palette.text_primary),
        "dialogsTextFg": h(palette.text_secondary),
        "dialogsTextFgOver": h(palette.text_secondary),
        "dialogsTextFgActive": h(palette.text_primary),
        "dialogsUnreadBg": h(palette.unread_badge_bg),
        "dialogsUnreadBgOver": h(palette.unread_badge_bg),
        "dialogsUnreadBgActive": h(palette.unread_badge_bg),
        "dialogsUnreadFg": h(palette.unread_badge_text),
        "dialogsUnreadFgOver": h(palette.unread_badge_text),
        "dialogsUnreadFgActive": h(palette.unread_badge_text),
        "dialogsUnreadBgMuted": h(palette.text_secondary),
        "dialogsUnreadBgMutedOver": h(palette.text_secondary),
        "dialogsUnreadBgMutedActive": h(palette.text_secondary),
        "dialogsUnreadFgMuted": h(palette.bg_surface),
        "dialogsUnreadFgMutedOver": h(palette.bg_surface),
        "dialogsUnreadFgMutedActive": h(palette.bg_surface),
        
        # Incoming Messages (Sender names & reply names are crisp noticeable white)
        "msgInBg": h(palette.in_bubble_bg),
        "msgInBgSelected": h(blend_colors(palette.in_bubble_bg, palette.primary_accent, 0.2)),
        "msgInFg": h(palette.in_bubble_text),
        "msgInNameFg": h(palette.text_primary),
        "msgInReplyName": h(palette.text_primary),
        "msgInDateFg": h(palette.in_bubble_time),
        "msgInDateFgSelected": h(palette.in_bubble_text),
        "msgInReplyBarColor": h(palette.in_bubble_reply_bar),
        "msgInServiceFg": h(palette.primary_accent),
        "msgInShadow": "#00000000",
        
        # Outgoing Messages
        "msgOutBg": h(palette.out_bubble_bg),
        "msgOutBgSelected": h(blend_colors(palette.out_bubble_bg, (255, 255, 255) if is_dark else (0, 0, 0), 0.15)),
        "msgOutFg": h(palette.out_bubble_text),
        "msgOutNameFg": h(palette.out_bubble_text),
        "msgOutReplyName": h(palette.out_bubble_text),
        "msgOutDateFg": h(palette.out_bubble_time),
        "msgOutDateFgSelected": h(palette.out_bubble_text),
        "msgOutReplyBarColor": h(palette.out_bubble_reply_bar),
        "msgOutServiceFg": h(palette.out_bubble_text),
        "msgOutShadow": "#00000000",
        
        # History & Composer Area
        "historyComposeAreaBg": h(palette.input_bar_bg),
        "historyComposeAreaFg": h(palette.input_bar_text),
        "historyComposeFieldPlaceholder": h(palette.input_bar_hint),
        "historySendIcon": h(palette.send_button),
        "historySendIconOver": h(palette.accent_hover),
        "historyAttach": h(palette.text_secondary),
        "historyAttachOver": h(palette.primary_accent),
        "historyToDownFg": h(palette.text_secondary),
        "historyToDownFgOver": h(palette.text_primary),
        "historyToDownBg": h(palette.bg_elevated),
        "historyToDownBgOver": h(palette.bg_surface),
        
        # Active Buttons & Controls
        "activeButtonBg": h(palette.primary_accent),
        "activeButtonBgOver": h(palette.accent_hover),
        "activeButtonBgRipple": h(palette.accent_hover),
        "activeButtonFg": h(palette.unread_badge_text),
        "activeButtonFgOver": h(palette.unread_badge_text),
        "activeLineFg": h(palette.primary_accent),
        
        # Boxes & Modals
        "boxBg": h(palette.bg_elevated),
        "boxTextFg": h(palette.text_primary),
        "boxTitleFg": h(palette.text_primary),
        "boxSearchBg": h(palette.bg_surface),
        
        # Side Bar / Settings Menu
        "sideBarBg": h(palette.bg_surface),
        "sideBarBgActive": h(blend_colors(palette.bg_surface, palette.primary_accent, 0.15)),
        "sideBarBgRipple": h(palette.bg_elevated),
        "sideBarTextFg": h(palette.text_primary),
        "sideBarTextFgActive": h(palette.primary_accent),
        "sideBarIconFg": h(palette.text_secondary),
        "sideBarIconFgActive": h(palette.primary_accent),
        
        # Scrollbars & Media
        "scrollBarBg": h(palette.text_secondary, 60),
        "scrollBarBgOver": h(palette.text_secondary, 120),
        "mediaPlayerBg": h(palette.bg_surface),
        "mediaPlayerActive": h(palette.primary_accent),
        "mediaPlayerInactive": h(palette.separator_line)
    }

    lines = ["// Telegram Desktop Theme - Generated by Arena Telegram Theme Bot"]
    for k, v in d.items():
        lines.append(f"{k}: {v};")
    lines.append("")
    return "\n".join(lines)


def generate_desktop_theme(
    palette: ResolvedThemePalette,
    wallpaper_image: Optional[Image.Image] = None,
    theme_name: str = "custom"
) -> bytes:
    """
    Generate a full .tdesktop-theme ZIP archive containing colors.tdesktop-theme and background.jpg.
    """
    palette_text = generate_desktop_palette_text(palette)
    
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("colors.tdesktop-theme", palette_text.encode("utf-8"))
        if wallpaper_image is not None:
            jpg_bytes = get_wallpaper_jpeg_bytes(wallpaper_image, quality=98, subsampling=0)
            zf.writestr("background.jpg", jpg_bytes)
            
    return bio.getvalue()
