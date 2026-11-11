"""Legacy alias module forwarding to centralized interface.theme."""

from interface.theme import HudPalette, build_stylesheet

HUD_STYLESHEET = build_stylesheet(85)

__all__ = ["HudPalette", "build_stylesheet", "HUD_STYLESHEET"]
