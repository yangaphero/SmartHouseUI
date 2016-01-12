# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from random import random
from itertools import product

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger as log
from kivy.graphics import Color, Rectangle

SCREENSAVER_TIMEOUT = 60
FIRST_GENERATION_DENSITY = 0.3
RESTART_EVERY = 180  # seconds
LOOP_DELAY = 0.4

CELL_SIZE = 16  # px


class ScreensaverDrawingArea(FloatLayout):
    def __init__(self, *args, **kwargs):
        super(ScreensaverDrawingArea, self).__init__(*args, **kwargs)
        self._tempr_label = None

    def restart(self):
        log.debug('Starting screensaver...')

        self._init()
        Clock.schedule_interval(self._init, RESTART_EVERY)
        self._update()
        Clock.schedule_interval(self._update, LOOP_DELAY)

    def _init(self, *args):
        self._cells_count_x = int(self.width / float(CELL_SIZE))
        self._cells_count_y = int(self.height / float(CELL_SIZE))
        self._cells = {}

        self.canvas.before.clear()

        with self.canvas.before:
            for x in range(self._cells_count_x):
                for y in range(self._cells_count_y):
                    alpha = 1 if random() < FIRST_GENERATION_DENSITY else 0
                    self._cells[(x, y)] = Color(rgba=[0.3, 0.3, 0.3, alpha])
                    Rectangle(
                        size=[CELL_SIZE, CELL_SIZE],
                        pos=[x * CELL_SIZE, y * CELL_SIZE],
                    )

    def _update(self, *args):
        to_change = {}

        for x in range(self._cells_count_x):
            for y in range(self._cells_count_y):
                cells = product(
                    [
                        x - 1 if x > 0 else self._cells_count_x - 1,
                        x,
                        x + 1 if x < self._cells_count_x - 1 else 0,
                    ],
                    [
                        y-1 if y > 0 else self._cells_count_y - 1,
                        y,
                        y + 1 if y < self._cells_count_y - 1 else 0,
                    ],
                )
                neighbours_total_life = sum(self._cells[item].a for item in cells)

                if self._cells[(x, y)].a:
                    neighbours_total_life -= 1

                    if neighbours_total_life not in [2, 3]:
                        to_change[(x, y)] = 0
                else:
                    if neighbours_total_life == 3:
                        to_change[(x, y)] = 1

        for item, value in to_change.items():
            self._cells[item].a = value

        # Updating sensors
        if not self._tempr_label:
            panels = App.get_running_app().main_screen.ids['panels']
            self._tempr_label = panels.ids['weather'].ids['temp_out']

        temp = self._tempr_label.text
        if temp and temp.isdigit():
            temp = 'Temperature: %s [sup]o[/sup]C' % temp
        else:
            temp = 'Temperature Unknown =('

        self.ids['temperature_label'].text = temp

        self.ids['time_label'].text = datetime.now().strftime('%H:%M')

    def stop(self):
        log.debug('Stopping screensaver...')
        Clock.unschedule(self._update)
        Clock.unschedule(self._init)


def reschedule_screensaver():
    Clock.unschedule(_run_screensaver)
    Clock.schedule_once(_run_screensaver, SCREENSAVER_TIMEOUT)


def _run_screensaver(*args):
    manager = IdleScreen._instance.manager
    manager.transition = FadeTransition()
    manager.current = 'idle'


class IdleScreen(Screen):
    _instance = None

    def __init__(self, *args, **kwargs):
        super(IdleScreen, self).__init__(*args, **kwargs)
        IdleScreen._instance = self
        reschedule_screensaver()

    def on_pre_enter(self, *args):
        self.ids['draw_area'].restart()

    def on_leave(self, *args):
        self.ids['draw_area'].stop()

    def on_touch_down(self, touch):
        self.manager.transition = FadeTransition()
        self.manager.current = self.manager.previous_screen_name
        return True
