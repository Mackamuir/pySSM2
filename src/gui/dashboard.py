"""
pySSM2 Dashboard — aqua/cyan segmented bars, boost arc, peak hold, scanlines.

Reads from a shared `latest_data` dict each frame (populated by the ECU logger).
All drawing functions and layout are self-contained here.
"""

import math
import time
import pygame
from math import ceil

from gui.theme import (
    BG, AQUA, AQUA_MED, AQUA_DIM, AQUA_OFF,
    PANEL_BG, PANEL_BORDER, LABEL_COLOR, UNIT_COLOR,
    WARN, WARN_OFF, AQUA_PEAK, WARN_PEAK,
    load_font, make_scanlines,
)


# ============================================================================
# GAUGE CONFIGURATION
# ============================================================================
# Each entry maps an ECU data key to its display properties.
# 'bar_segs' and 'warn_frac' control the segmented bar for that gauge.

GAUGE_CONFIG = {
    'boost': {
        'key': 'Boost Pressure',
        'label': 'BOOST',
        'unit': 'PSI',
        'min': -14, 'max': 22,
        'warn': 18,
        'dp': 1,
        'bar_segs': 30,
        'warn_frac': 0.89,
        'peak_hold': 1.5,
        'peak_decay': 0.04,
    },
    'coolant': {
        'key': 'Coolant Temperature',
        'label': 'COOLANT',
        'unit': 'C',
        'min': -20, 'max': 130,
        'warn': 110,
        'dp': 0,
        'bar_segs': 18,
        'warn_frac': 0.78,
        'peak_hold': 1.5,
        'peak_decay': 0.03,
    },
    'rpm': {
        'key': 'Engine Speed',
        'label': 'ENGINE',
        'unit': 'RPM',
        'min': 0, 'max': 8000,
        'warn': 6800,
        'dp': 0,
        'bar_segs': 40,
        'warn_frac': 0.85,
        'peak_hold': 1.5,
        'peak_decay': 0.05,
    },
    'battery': {
        'key': 'Battery Voltage',
        'label': 'BATTERY',
        'unit': 'V',
        'min': 10, 'max': 16,
        'warn': 15.2,
        'dp': 1,
        'bar_segs': 14,
        'warn_frac': 0.85,
        'peak_hold': 1.5,
        'peak_decay': 0.03,
    },
    'afr': {
        'key': 'Air Fuel Ratio',
        'label': 'AIR/FUEL',
        'unit': 'AFR',
        'min': 10, 'max': 20,
        'warn': 17.5,
        'dp': 2,
        'bar_segs': 14,
        'warn_frac': 0.85,
        'peak_hold': 1.5,
        'peak_decay': 0.04,
    },
    'fuel': {
        'key': 'Fuel Consumption',
        'label': 'AVG FUEL',
        'unit': 'L/100',
        'min': 0, 'max': 30,
        'warn': 20.0,
        'dp': 1,
        'bar_segs': 14,
        'warn_frac': 0.80,
        'peak_hold': 1.5,
        'peak_decay': 0.04,
    },
}


# ============================================================================
# PEAK TRACKER
# ============================================================================

class PeakTracker:
    """Tracks the highest bar segment with a hold period then slow decay."""

    def __init__(self, hold_time=1.5, decay_rate=0.03):
        self.peak = 0.0
        self.hold_time = hold_time
        self.decay_rate = decay_rate
        self.hold_timer = 0.0

    def update(self, current_seg, dt):
        if current_seg >= self.peak:
            self.peak = float(current_seg)
            self.hold_timer = self.hold_time
        else:
            if self.hold_timer > 0:
                self.hold_timer -= dt
            else:
                self.peak = max(float(current_seg),
                                self.peak - self.decay_rate * dt * 60)
        return ceil(self.peak)


# ============================================================================
# DRAWING FUNCTIONS
# ============================================================================

def draw_bar(surf, x, y, w, h, val, mn, mx, peak_seg, segs=25, gap=2,
             warn_frac=0.8, c_on=AQUA, c_off=AQUA_OFF, c_warn=WARN, scale=1.0):
    """Draw a segmented bar with peak hold ghost segments."""
    br = max(1, round(1 * scale))
    sw = (w - gap * (segs - 1)) // segs
    ratio = max(0.0, min(1.0, (val - mn) / max(mx - mn, 0.001)))
    filled = int(ratio * segs)
    warn_start = int(warn_frac * segs)

    for i in range(segs):
        sx = x + i * (sw + gap)
        if i < filled:
            c = c_warn if i >= warn_start else c_on
        elif i < peak_seg:
            c = WARN_PEAK if i >= warn_start else AQUA_PEAK
        else:
            c = WARN_OFF if i >= warn_start else c_off
        pygame.draw.rect(surf, c, (sx, y, sw, h), border_radius=br)

    return filled


def draw_panel(surf, rect, label, val_str, unit, bar_val, bar_min, bar_max,
               fonts, peak_seg=0, warn=False, bar_segs=20, warn_frac=0.8,
               scale=1.0):
    """Draw a bordered panel with label, digital value, unit, and segmented bar."""
    f_label, f_value, f_unit = fonts
    c_val = WARN if warn else AQUA
    border = WARN if warn else PANEL_BORDER

    s = scale
    br = max(1, round(4 * s))
    inset = max(2, round(6 * s))
    bar_h = max(3, round(6 * s))
    bar_margin = max(6, round(14 * s))

    pygame.draw.rect(surf, PANEL_BG, rect, border_radius=br)
    pygame.draw.rect(surf, border, rect, 1, border_radius=br)

    ls = f_label.render(label, True, LABEL_COLOR)
    surf.blit(ls, (rect.x + inset, rect.y + round(4 * s)))

    us = f_unit.render(unit, True, UNIT_COLOR)
    surf.blit(us, (rect.right - us.get_width() - inset, rect.y + round(4 * s)))

    vs = f_value.render(val_str, True, c_val)
    vr = vs.get_rect(center=(rect.centerx, rect.y + rect.h // 2 - round(2 * s)))
    surf.blit(vs, vr)

    bar_x = rect.x + inset
    bar_w = rect.w - inset * 2
    bar_y = rect.bottom - bar_margin
    filled = draw_bar(surf, bar_x, bar_y, bar_w, bar_h, bar_val, bar_min, bar_max,
                      peak_seg, segs=bar_segs, warn_frac=warn_frac, scale=s)
    return filled


def draw_boost_display(surf, rect, val, mn, mx, warn_val, fonts, t, peak_seg=0,
                       scale=1.0):
    """Draw the large boost gauge with arc bar and overboost flash."""
    f_label, f_big, f_unit, f_small = fonts
    warn = val >= warn_val
    c_val = WARN if warn else AQUA
    s = scale

    br = max(1, round(6 * s))
    inset = max(4, round(10 * s))
    arc_thickness = max(4, round(10 * s))
    arc_margin = max(4, round(10 * s))
    arc_inset = max(10, round(30 * s))
    label_offset = max(6, round(14 * s))

    pygame.draw.rect(surf, PANEL_BG, rect, border_radius=br)
    pygame.draw.rect(surf, WARN if warn else PANEL_BORDER, rect, 1, border_radius=br)

    ls = f_label.render("BOOST", True, LABEL_COLOR)
    surf.blit(ls, (rect.x + inset, rect.y + round(6 * s)))
    us = f_unit.render("PSI", True, UNIT_COLOR)
    surf.blit(us, (rect.right - us.get_width() - inset, rect.y + round(6 * s)))

    val_str = f"{val:+.1f}" if val != 0 else " 0.0"
    vs = f_big.render(val_str, True, c_val)
    vr = vs.get_rect(center=(rect.centerx, rect.y + round(rect.h * 0.425)))
    surf.blit(vs, vr)

    # Arc bar
    arc_cx = rect.centerx
    arc_cy = rect.bottom - arc_margin
    arc_r = rect.w // 2 - arc_inset
    start_ang = 180
    total_arc = 180
    arc_segs = 30

    ratio = max(0.0, min(1.0, (val - mn) / max(mx - mn, 0.001)))
    filled = int(ratio * arc_segs)
    warn_start = int((warn_val - mn) / max(mx - mn, 0.001) * arc_segs)

    for i in range(arc_segs):
        a_s = math.radians(start_ang - i * (total_arc / arc_segs))
        a_e = math.radians(start_ang - (i + 1) * (total_arc / arc_segs) + 1)
        inner_r = arc_r - arc_thickness
        outer_r = arc_r
        if i < filled:
            c = WARN if i >= warn_start else AQUA
        elif i < peak_seg:
            c = WARN_PEAK if i >= warn_start else AQUA_PEAK
        else:
            c = WARN_OFF if i >= warn_start else AQUA_OFF

        pts = []
        for step in range(5):
            frac = step / 4
            a = a_s + (a_e - a_s) * frac
            pts.append((arc_cx + math.cos(a) * outer_r,
                        arc_cy - math.sin(a) * outer_r))
        for step in range(4, -1, -1):
            frac = step / 4
            a = a_s + (a_e - a_s) * frac
            pts.append((arc_cx + math.cos(a) * inner_r,
                        arc_cy - math.sin(a) * inner_r))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, c, pts)

    # Scale labels
    for i in range(5):
        frac = i / 4
        v = mn + (mx - mn) * frac
        a = math.radians(start_ang - frac * total_arc)
        tx = arc_cx + math.cos(a) * (arc_r + label_offset)
        ty = arc_cy - math.sin(a) * (arc_r + label_offset)
        lbl = f_small.render(f"{v:.0f}", True, AQUA_DIM)
        surf.blit(lbl, lbl.get_rect(center=(int(tx), int(ty))))

    # Overboost flash
    if warn and int(t * 3) % 2 == 0:
        ws = f_small.render("OVERBOOST", True, WARN)
        surf.blit(ws, ws.get_rect(center=(rect.centerx, rect.bottom - round(8 * s))))

    return filled


# ============================================================================
# DASHBOARD CLASS
# ============================================================================

class Dashboard:
    """
    Main dashboard screen.

    Holds fonts, peak trackers, scanline overlay, and renders all gauges
    by reading values from the shared `latest_data` dict.

    Layout is fully proportional — scales to any resolution using 800x480
    as the reference design size.
    """

    # Reference resolution (design target)
    REF_W, REF_H = 800, 480

    def __init__(self, width, height):
        self.w = width
        self.h = height

        # Scale factor relative to reference resolution
        self.scale = min(width / self.REF_W, height / self.REF_H)
        self.pad = max(4, round(8 * self.scale))

        # Fonts — sizes scale with the display
        s = self.scale
        self.f_big    = load_font(max(20, round(76 * s)))
        self.f_value  = load_font(max(14, round(44 * s)))
        self.f_label  = load_font(max(10, round(20 * s)))
        self.f_unit   = load_font(max(10, round(18 * s)))
        self.f_small  = load_font(max(10, round(15 * s)))
        self.f_footer = load_font(max(10, round(16 * s)))

        # Peak trackers (one per gauge)
        self.peaks = {}
        for name, cfg in GAUGE_CONFIG.items():
            self.peaks[name] = PeakTracker(
                hold_time=cfg['peak_hold'],
                decay_rate=cfg['peak_decay'],
            )

        # Fuel consumption journey average
        self.fuel_avg_sum = 0.0
        self.fuel_avg_count = 0

        # Scanline overlay
        self.scanlines = make_scanlines(width, height)

        # Current data reference
        self.data = {}

    def _get(self, gauge_name):
        """Get current value for a gauge from latest_data, default 0."""
        if gauge_name == 'fuel' and self.fuel_avg_count > 0:
            return self.fuel_avg_sum / self.fuel_avg_count
        cfg = GAUGE_CONFIG[gauge_name]
        val = self.data.get(cfg['key'], 0)
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    def _format(self, gauge_name, val):
        """Format a value according to the gauge's decimal places."""
        dp = GAUGE_CONFIG[gauge_name]['dp']
        if dp == 0:
            return f"{int(round(val))}"
        elif dp == 1:
            return f"{val:.1f}"
        else:
            return f"{val:.2f}"

    def _is_warn(self, gauge_name, val):
        """Check if a value is in the warning range."""
        return val >= GAUGE_CONFIG[gauge_name]['warn']

    def update(self, latest_data):
        """Store reference to latest ECU data."""
        self.data = latest_data

        # Accumulate fuel consumption for journey average (only while moving)
        speed = latest_data.get('Vehicle Speed', 0)
        try:
            speed = float(speed)
        except (TypeError, ValueError):
            speed = 0.0
        if speed > 0:
            fuel_key = GAUGE_CONFIG['fuel']['key']
            fuel_val = latest_data.get(fuel_key, 0)
            try:
                fuel_val = float(fuel_val)
            except (TypeError, ValueError):
                fuel_val = 0.0
            if fuel_val > 0:
                self.fuel_avg_sum += fuel_val
                self.fuel_avg_count += 1

    def draw(self, surface, t, dt):
        """Draw the complete dashboard onto the surface."""
        PAD = self.pad
        W, H = self.w, self.h
        s = self.scale

        surface.fill(BG)

        # Font tuples for convenience
        panel_fonts = (self.f_label, self.f_value, self.f_unit)
        boost_fonts = (self.f_label, self.f_big, self.f_unit, self.f_small)

        # ── Proportional layout ─────────────────────────────────────────
        # Top row: 41.7% of height, boost takes 52.5% of width
        top_h = round(H * 0.4167)
        boost_w = round(W * 0.525)

        # RPM row: 18.75% of height
        rpm_h = round(H * 0.1875)

        # Footer: ~4.6% of height
        foot_h = max(16, round(H * 0.046))

        # ── Top row: Boost (big) + Coolant ──────────────────────────────
        boost_val = self._get('boost')
        boost_cfg = GAUGE_CONFIG['boost']
        boost_rect = pygame.Rect(PAD, PAD, boost_w, top_h)
        boost_filled = draw_boost_display(
            surface, boost_rect, boost_val,
            boost_cfg['min'], boost_cfg['max'], boost_cfg['warn'],
            boost_fonts, t,
            peak_seg=ceil(self.peaks['boost'].peak), scale=s)
        self.peaks['boost'].update(boost_filled, dt)

        cool_val = self._get('coolant')
        cool_cfg = GAUGE_CONFIG['coolant']
        cool_x = PAD + boost_w + PAD
        cool_rect = pygame.Rect(cool_x, PAD, W - cool_x - PAD, top_h)
        cool_filled = draw_panel(
            surface, cool_rect,
            cool_cfg['label'], self._format('coolant', cool_val), cool_cfg['unit'],
            cool_val, cool_cfg['min'], cool_cfg['max'],
            panel_fonts,
            peak_seg=ceil(self.peaks['coolant'].peak),
            warn=self._is_warn('coolant', cool_val),
            bar_segs=cool_cfg['bar_segs'], warn_frac=cool_cfg['warn_frac'],
            scale=s)
        self.peaks['coolant'].update(cool_filled, dt)

        # ── Middle row: RPM full-width ──────────────────────────────────
        rpm_val = self._get('rpm')
        rpm_cfg = GAUGE_CONFIG['rpm']
        rpm_y = PAD + top_h + PAD
        rpm_rect = pygame.Rect(PAD, rpm_y, W - PAD * 2, rpm_h)
        rpm_filled = draw_panel(
            surface, rpm_rect,
            rpm_cfg['label'], self._format('rpm', rpm_val), rpm_cfg['unit'],
            rpm_val, rpm_cfg['min'], rpm_cfg['max'],
            panel_fonts,
            peak_seg=ceil(self.peaks['rpm'].peak),
            warn=self._is_warn('rpm', rpm_val),
            bar_segs=rpm_cfg['bar_segs'], warn_frac=rpm_cfg['warn_frac'],
            scale=s)
        self.peaks['rpm'].update(rpm_filled, dt)

        # ── Bottom row: Battery, AFR, Fuel ──────────────────────────────
        bot_y = rpm_y + rpm_h + PAD
        bot_h = H - bot_y - foot_h - PAD
        pw = (W - PAD * 4) // 3

        for i, name in enumerate(('battery', 'afr', 'fuel')):
            val = self._get(name)
            cfg = GAUGE_CONFIG[name]
            rect = pygame.Rect(PAD * (i + 1) + pw * i, bot_y, pw, bot_h)
            filled = draw_panel(
                surface, rect,
                cfg['label'], self._format(name, val), cfg['unit'],
                val, cfg['min'], cfg['max'],
                panel_fonts,
                peak_seg=ceil(self.peaks[name].peak),
                warn=self._is_warn(name, val),
                bar_segs=cfg['bar_segs'], warn_frac=cfg['warn_frac'],
                scale=s)
            self.peaks[name].update(filled, dt)

        # ── Footer ──────────────────────────────────────────────────────
        foot_y = H - foot_h
        pygame.draw.line(surface, PANEL_BORDER,
                         (PAD, foot_y - round(4 * s)),
                         (W - PAD, foot_y - round(4 * s)), 1)

        now = time.localtime()
        ts = f"{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"
        cs = self.f_footer.render(ts, True, AQUA_DIM)
        surf_center_y = foot_y + (foot_h - cs.get_height()) // 2
        surface.blit(cs, (W // 2 - cs.get_width() // 2, surf_center_y))

        title = self.f_footer.render("pySSM2", True, LABEL_COLOR)
        surface.blit(title, (PAD, surf_center_y))

        esc = self.f_small.render("[ESC] QUIT", True, AQUA_OFF)
        surface.blit(esc, (W - esc.get_width() - PAD, surf_center_y))

        # ── Scanlines ──────────────────────────────────────────────────
        surface.blit(self.scanlines, (0, 0))

    def handle_event(self, event):
        """Handle pygame events. Reserved for future interactivity."""
        pass
