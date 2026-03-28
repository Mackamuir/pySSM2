#!/usr/bin/env python3
"""
Standalone dashboard preview with simulated gauge data.
Run from the project root: python preview_dashboard.py
"""

import sys
import os
import math
import time

# Add src to path so gui package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pygame
from gui.dashboard import Dashboard, GAUGE_CONFIG

WIDTH = 800
HEIGHT = 480


def fake_data(t):
    """Generate smoothly animated gauge values using sine waves."""
    return {
        'Boost Pressure':    -14 + 36 * max(0, math.sin(t * 0.4)) ** 2 * 0.7,
        'Coolant Temperature': 75 + 30 * math.sin(t * 0.15),
        'Battery Voltage':   13.2 + 1.2 * math.sin(t * 0.3),
        'Air Fuel Ratio':    14.7 + 2.5 * math.sin(t * 0.5),
        'Fuel Consumption':  8 + 6 * abs(math.sin(t * 0.2)),
        'Vehicle Speed':     60,
    }


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("pySSM2 Dashboard Preview")

    dash = Dashboard(WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    start = time.time()
    last = start

    running = True
    while running:
        now = time.time()
        t = now - start
        dt = now - last
        last = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                dash = Dashboard(event.w, event.h)

        dash.update(fake_data(t))
        dash.draw(screen, t, dt)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == '__main__':
    main()
