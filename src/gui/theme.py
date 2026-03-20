"""
Visual theme for pySSM2 dashboard.
Aqua/cyan color scheme with DS-DIGII digital font.
"""

import pygame

# Try to import config for font path; fall back to relative path
try:
    import config
    _FONT_PATH = config.FONT_PATH
except (ImportError, AttributeError):
    import os
    _FONT_PATH = os.path.normpath(
        os.path.join('/','etc', 'pySSM2', 'assets', 'fonts', 'DS-DIGII.TTF'))

# ============================================================================
# COLORS — Aqua/cyan theme
# ============================================================================

BG              = (0, 0, 0)
AQUA            = (0, 255, 255)
AQUA_MED        = (0, 200, 220)
AQUA_DIM        = (0, 120, 140)
AQUA_OFF        = (0, 35, 42)
PANEL_BG        = (6, 14, 18)
PANEL_BORDER    = (0, 130, 150)
LABEL_COLOR     = (0, 200, 220)
UNIT_COLOR      = (0, 220, 240)
WARN            = (255, 60, 25)
WARN_OFF        = (55, 18, 10)

# Peak hold colors (higher intensity for visibility)
AQUA_PEAK       = (0, 180, 180)
WARN_PEAK       = (180, 40, 15)


# ============================================================================
# FONTS
# ============================================================================

_font_cache = {}


def load_font(size):
    """Load DS-DIGII font at given size, cached. Falls back to Consolas."""
    if size not in _font_cache:
        try:
            _font_cache[size] = pygame.font.Font(_FONT_PATH, size)
        except (FileNotFoundError, RuntimeError):
            _font_cache[size] = pygame.font.SysFont('consolas', size, bold=True)
    return _font_cache[size]


# ============================================================================
# SCANLINES — CRT overlay effect
# ============================================================================

def make_scanlines(w, h, gap=3, alpha=22):
    """Create a semi-transparent scanline overlay surface."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, gap):
        pygame.draw.line(s, (0, 0, 0, alpha), (0, y), (w, y))
    return s
