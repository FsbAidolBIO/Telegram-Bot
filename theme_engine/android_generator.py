"""
Telegram Android Theme Generator (.attheme format).
Generates compliant Android theme files with full UI color mapping and embedded wallpaper.
"""

from typing import Tuple, Dict, Any, Optional
import io
from PIL import Image
from theme_engine.palette import ResolvedThemePalette
from theme_engine.wallpaper_generator import get_wallpaper_jpeg_bytes
from theme_engine.color_extractor import blend_colors


def to_argb_int(rgb: Tuple[int, int, int], a: int = 255) -> int:
    """Convert RGB and Alpha (0-255) to 32-bit signed ARGB integer."""
    val = ((a & 0xFF) << 24) | ((rgb[0] & 0xFF) << 16) | ((rgb[1] & 0xFF) << 8) | (rgb[2] & 0xFF)
    if val >= 0x80000000:
        val -= 0x100000000
    return val


def generate_android_theme(
    palette: ResolvedThemePalette,
    wallpaper_image: Optional[Image.Image] = None,
    theme_name: str = "Custom Theme"
) -> bytes:
    """
    Generate a complete .attheme binary/text file for Telegram Android.
    """
    is_dark = palette.mode in ("dark", "amoled")
    
    # Helper to calculate color integer
    def c(rgb: Tuple[int, int, int], a: int = 255) -> int:
        return to_argb_int(rgb, a)

    # Derived colors
    divider_color = palette.separator_line
    active_overlay = (255, 255, 255) if is_dark else (0, 0, 0)
    ripple_color = c(active_overlay, 30)
    selected_bg = c(blend_colors(palette.bg_surface, palette.primary_accent, 0.15))
    
    # Bubble timestamps & checks
    in_time = palette.in_bubble_time
    out_time = palette.out_bubble_time

    # Construct complete Android theme dictionary
    theme_dict = {
        # App Bar / Action Bar
        "actionBarDefault": c(palette.topbar_bg),
        "actionBarDefaultIcon": c(palette.text_primary),
        "actionBarDefaultTitle": c(palette.text_primary),
        "actionBarDefaultSubtitle": c(palette.text_secondary),
        "actionBarDefaultSelector": ripple_color,
        "actionBarDefaultSearch": c(palette.text_primary),
        "actionBarDefaultSearchPlaceholder": c(palette.text_secondary),
        "actionBarDefaultSubmenuBackground": c(palette.bg_elevated),
        "actionBarDefaultSubmenuItem": c(palette.text_primary),
        "actionBarDefaultSubmenuItemIcon": c(palette.text_secondary),
        
        # Windows & Backgrounds
        "windowBackgroundWhite": c(palette.bg_surface),
        "windowBackgroundGray": c(palette.bg_color),
        "windowBackgroundWhiteBlackText": c(palette.text_primary),
        "windowBackgroundWhiteGrayText": c(palette.text_secondary),
        "windowBackgroundWhiteGrayText2": c(palette.text_secondary),
        "windowBackgroundWhiteLinkText": c(palette.primary_accent),
        "windowBackgroundWhiteValueText": c(palette.primary_accent),
        "windowBackgroundWhiteBlueHeader": c(palette.primary_accent),
        "windowBackgroundWhiteInputField": c(palette.text_secondary),
        "windowBackgroundWhiteInputFieldActivated": c(palette.primary_accent),
        "windowBackgroundWhiteGrayIcon": c(palette.text_secondary),
        "divider": c(divider_color),
        "listSelector": ripple_color,
        
        # Dialogs / Chat List
        "chats_name": c(palette.text_primary),
        "chats_message": c(palette.text_secondary),
        "chats_date": c(palette.text_secondary),
        "chats_actionUser": c(palette.primary_accent),
        "chats_actionMessage": c(palette.text_secondary),
        "chats_unreadCounter": c(palette.unread_badge_bg),
        "chats_unreadCounterText": c(palette.unread_badge_text),
        "chats_unreadCounterMuted": c(palette.text_secondary),
        "chats_verifiedBackground": c(palette.primary_accent),
        "chats_verifiedCheck": c(palette.bg_surface),
        "chats_pinnedOverlay": c(palette.primary_accent, 15),
        "chats_tabletSelectedOverlay": c(palette.primary_accent, 30),
        "chats_menuBackground": c(palette.bg_surface),
        "chats_menuItemText": c(palette.text_primary),
        "chats_menuItemIcon": c(palette.text_secondary),
        "chats_menuTopBackground": c(palette.bg_elevated),
        "chats_menuName": c(palette.text_primary),
        "chats_menuPhone": c(palette.text_secondary),
        
        # Chat Screen / Background
        "chat_wallpaper": c(palette.bg_color),
        
        # Incoming Messages
        "chat_inBubble": c(palette.in_bubble_bg),
        "chat_inBubbleSelected": c(blend_colors(palette.in_bubble_bg, palette.primary_accent, 0.15)),
        "chat_inText": c(palette.in_bubble_text),
        "chat_inTimeText": c(in_time),
        "chat_inSentCheck": c(palette.primary_accent),
        "chat_inReplyName": c(palette.primary_accent),
        "chat_inReplyMessageText": c(palette.in_bubble_text),
        "chat_inReplyLine": c(palette.primary_accent),
        "chat_inLinkSelection": c(palette.primary_accent, 40),
        "chat_inMenu": c(in_time),
        "chat_inViews": c(in_time),
        "chat_inAudioProgress": c(palette.primary_accent),
        "chat_inAudioSelectedProgress": c(palette.primary_accent),
        
        # Outgoing Messages
        "chat_outBubble": c(palette.out_bubble_bg),
        "chat_outBubbleSelected": c(blend_colors(palette.out_bubble_bg, (255, 255, 255) if is_dark else (0, 0, 0), 0.12)),
        "chat_outText": c(palette.out_bubble_text),
        "chat_outTimeText": c(out_time),
        "chat_outSentCheck": c(out_time),
        "chat_outSentCheckSelected": c(palette.out_bubble_text),
        "chat_outReplyName": c(palette.out_bubble_text),
        "chat_outReplyMessageText": c(palette.out_bubble_text),
        "chat_outReplyLine": c(palette.out_bubble_reply_bar),
        "chat_outLinkSelection": c((255, 255, 255), 40),
        "chat_outMenu": c(out_time),
        "chat_outViews": c(out_time),
        "chat_outAudioProgress": c(palette.out_bubble_text),
        "chat_outAudioSelectedProgress": c(palette.out_bubble_text),
        
        # Chat Input Bar
        "chat_messagePanelBackground": c(palette.input_bar_bg),
        "chat_messagePanelText": c(palette.input_bar_text),
        "chat_messagePanelHint": c(palette.input_bar_hint),
        "chat_messagePanelIcons": c(palette.text_secondary),
        "chat_messagePanelSend": c(palette.send_button),
        "chat_messagePanelVoiceBackground": c(palette.send_button),
        "chat_messagePanelShadow": c((0, 0, 0), 30),
        "chat_topPanelBackground": c(palette.input_bar_bg),
        "chat_topPanelTitle": c(palette.primary_accent),
        "chat_topPanelMessage": c(palette.text_secondary),
        "chat_topPanelLine": c(palette.primary_accent),
        "chat_topPanelClose": c(palette.text_secondary),
        "chat_unreadMessagesStartText": c(palette.primary_accent),
        "chat_unreadMessagesStartBackground": c(palette.bg_elevated),
        
        # Buttons & Controls
        "switchTrack": c(palette.separator_line),
        "switchTrackChecked": c(palette.primary_accent, 150),
        "switchThumb": c(palette.text_secondary),
        "switchThumbChecked": c(palette.primary_accent),
        "checkbox": c(palette.text_secondary),
        "checkboxCheck": c(palette.primary_accent),
        "dialogBackground": c(palette.bg_elevated),
        "dialogTextBlack": c(palette.text_primary),
        "dialogTextLink": c(palette.primary_accent),
        "dialogButton": c(palette.primary_accent),
        "dialogButtonSelector": ripple_color,
        "player_progress": c(palette.primary_accent),
        "player_progressBackground": c(palette.separator_line),
        "featuredStickers_addButton": c(palette.primary_accent),
        "featuredStickers_buttonText": c(palette.unread_badge_text),
        "avatar_backgroundBlue": c(palette.primary_accent),
        "avatar_backgroundCyan": c(palette.secondary_accent)
    }

    # Format into key=value lines
    lines = [f"{key}={val}" for key, val in theme_dict.items()]
    theme_text = "\n".join(lines) + "\n"
    output_bytes = bytearray(theme_text.encode("utf-8"))

    # If wallpaper is present, append WPS marker and JPEG data
    if wallpaper_image is not None:
        jpg_bytes = get_wallpaper_jpeg_bytes(wallpaper_image)
        output_bytes.extend(b"WPS\n")
        output_bytes.extend(jpg_bytes)

    return bytes(output_bytes)
