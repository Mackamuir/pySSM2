"""
Reusable popup overlay for pySSM2.

Draws a centered panel with a title, message, and animated dots
on top of whatever is currently rendered.
"""

import time
import pygame

from gui.theme import (
    BG, AQUA, AQUA_DIM, PANEL_BG, PANEL_BORDER, LABEL_COLOR,
    load_font,
)


class Popup:
    """
    A centered overlay popup that can display a title and message.

    Usage:
        popup = Popup(screen_w, screen_h, title="SCANNING", message="Looking for adapter...")
        popup.draw(surface, t)

    Update the message at any time:
        popup.message = "Trying COM3..."
    """

    def __init__(self, screen_w, screen_h, title="", message=""):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.title = title
        self.message = message

        scale = min(screen_w / 800, screen_h / 480)
        self.scale = scale

        # Popup dimensions — proportional to screen
        self.popup_w = max(200, round(400 * scale))
        self.popup_h = max(100, round(160 * scale))

        # Fonts
        self.f_title = load_font(max(10, round(22 * scale)))
        self.f_msg = load_font(max(8, round(14 * scale)))
        self.f_dots = load_font(max(8, round(14 * scale)))

        # Dimmed background overlay
        self.dim = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 160))

    def draw(self, surface, t):
        """Draw the popup centered on the surface."""
        # Dim everything behind
        surface.blit(self.dim, (0, 0))

        s = self.scale
        br = max(2, round(6 * s))

        # Popup rect centered on screen
        px = (self.screen_w - self.popup_w) // 2
        py = (self.screen_h - self.popup_h) // 2
        rect = pygame.Rect(px, py, self.popup_w, self.popup_h)

        pygame.draw.rect(surface, PANEL_BG, rect, border_radius=br)
        pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=br)

        # Title
        ts = self.f_title.render(self.title, True, AQUA)
        tr = ts.get_rect(centerx=rect.centerx, top=rect.y + round(20 * s))
        surface.blit(ts, tr)

        # Message
        ms = self.f_msg.render(self.message, True, LABEL_COLOR)
        mr = ms.get_rect(centerx=rect.centerx, centery=rect.centery + round(5 * s))
        surface.blit(ms, mr)

        # Animated dots
        dot_count = int(t * 2) % 4
        dots = "." * dot_count
        ds = self.f_dots.render(dots, True, AQUA_DIM)
        dr = ds.get_rect(centerx=rect.centerx, top=mr.bottom + round(8 * s))
        surface.blit(ds, dr)
