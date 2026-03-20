"""
Main pygame application for pySSM2.
Runs as an async coroutine alongside the ECU reader and CSV writer.
"""

import asyncio
import time
import pygame
from typing import Dict, Any
from gui.dashboard import Dashboard
from gui.popup import Popup


class App:
    """
    Main pygame application with screen stack for future multi-screen support.

    Runs in the asyncio event loop by yielding between frames.
    """

    def __init__(self, latest_data, display_width=None, display_height=None,
                 fullscreen=False, target_fps=30):
        pygame.init()
        pygame.display.set_caption("pySSM2 Dashboard")

        # Auto-detect screen size if not explicitly provided
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h

        if fullscreen:
            # Always use full native resolution in fullscreen
            display_width = screen_w
            display_height = screen_h
            flags = pygame.FULLSCREEN
        else:
            # Use provided size, or fall back to screen size with a margin
            display_width = display_width or screen_w
            display_height = display_height or screen_h
            flags = pygame.RESIZABLE

        self.screen = pygame.display.set_mode((display_width, display_height), flags)
        self.latest_data = latest_data
        self.running = True
        self.target_fps = target_fps
        self.display_width = display_width
        self.display_height = display_height

        # Time tracking for animations and peak decay
        self.start_time = time.time()
        self.last_time = self.start_time

        # Screen stack: bottom is dashboard, menus push on top
        dashboard = Dashboard(display_width, display_height)
        self.screens = [dashboard]

        # Popup overlay (shown when latest_data contains '_status')
        self.popup = None
        self._last_status = None

    @property
    def active_screen(self):
        return self.screens[-1] if self.screens else None

    def push_screen(self, screen):
        """Push a new screen on top (for menus, settings, etc.)."""
        self.screens.append(screen)

    def pop_screen(self):
        """Pop back to previous screen."""
        if len(self.screens) > 1:
            return self.screens.pop()

    async def run(self):
        """Main async game loop."""
        while self.running:
            # Time tracking
            now = time.time()
            t = now - self.start_time
            dt = now - self.last_time
            self.last_time = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if len(self.screens) > 1:
                            self.pop_screen()
                        else:
                            self.running = False
                    elif event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                if event.type == pygame.VIDEORESIZE:
                    self.display_width = event.w
                    self.display_height = event.h
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE)
                    # Rebuild dashboard at new size
                    dashboard = Dashboard(event.w, event.h)
                    self.screens = [dashboard]
                if self.active_screen:
                    self.active_screen.handle_event(event)

            # Update active screen with latest ECU data
            if self.active_screen:
                self.active_screen.update(self.latest_data)

            # Render
            if self.active_screen:
                self.active_screen.draw(self.screen, t, dt)

            # Popup overlay driven by _status in latest_data
            status = self.latest_data.get('_status')
            if status:
                title = status.get('title', '')
                message = status.get('message', '')
                status_key = (title, self.display_width, self.display_height)
                if status_key != self._last_status:
                    self.popup = Popup(self.display_width, self.display_height,
                                       title=title, message=message)
                    self._last_status = status_key
                else:
                    self.popup.message = message
                self.popup.draw(self.screen, t)
            else:
                self.popup = None
                self._last_status = None

            pygame.display.flip()

            # Yield to asyncio event loop
            await asyncio.sleep(1 / self.target_fps)

        pygame.quit()


async def run_display(latest_data: Dict[str, Any], display_width=800, display_height=480,
                      fullscreen=False, target_fps=30):
    """
    Entry point coroutine for the display.
    Called from logger.py main().
    """
    app = App(
        latest_data=latest_data,
        display_width=display_width,
        display_height=display_height,
        fullscreen=fullscreen,
        target_fps=target_fps,
    )
    await app.run()
