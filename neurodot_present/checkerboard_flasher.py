# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import pygame
import OpenGL.GL as gl
import OpenGL.GLU as glu
import numpy as np
import itertools
import fractions
import copy

import numpy as np

#local imports
from common import SETTINGS, COLORS, VSYNC_PATCH_HEIGHT_DEFAULT, VSYNC_PATCH_WIDTH_DEFAULT, DEFAULT_FLASH_RATE
from common import UserEscape

from screen import Screen

from checkerboard import CheckerBoard

class CheckerBoardFlasher(Screen):
    def setup(self,
              nrows,
              check_width = None,
              check_color1 = 'white',
              check_color2 = 'black',
              screen_background_color = 'neutral-gray',
              show_fixation_dot = False,
              flash_rate = DEFAULT_FLASH_RATE,
              vsync_patch = None
             ):
        Screen.setup(self,
                     background_color = screen_background_color,
                     vsync_patch = vsync_patch,
                     )
        #run colors through filter to catch names and convert to RGB
        check_color1 = COLORS.get(check_color1, check_color1)
        check_color2 = COLORS.get(check_color2, check_color2)
        if check_width is None:
            check_width = 2.0/nrows #fill whole screen
        self.board_width = check_width*nrows
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows,check_width, color1 = check_color1, color2 = check_color2, show_fixation_dot = show_fixation_dot)
        self.CB2 = CheckerBoard(nrows,check_width, color1 = check_color2, color2 = check_color1, show_fixation_dot = show_fixation_dot) #reversed pattern
        #white/black alterning for intermediate signals
        self.CB_cycle = itertools.cycle((self.CB1,self.CB2))
        self._last_CB_change_time = None
        self.flash_rate     = flash_rate
        self.flash_interval = 1.0/flash_rate

    def start_time(self,t):
        Screen.start_time(self,t)
        self._last_CB_change_time = t
        self._current_CB = self.CB_cycle.next()

    def render(self):
        Screen.render(self)
        #move so that board is centered and render
        gl.glLoadIdentity()
        gl.glTranslatef(-0.5*self.board_width,-0.5*self.board_width,0.0)
        self._current_CB.render()

    def update(self, t, dt):
        #print(t,dt)
        if (t - self._last_CB_change_time) >= self.flash_interval:
            self._last_CB_change_time = t
            self._current_CB = self.CB_cycle.next()

################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    CBF = CheckerBoardFlasher.with_pygame_display(display_mode = (64,64),debug = True)
    CBF.setup(nrows = 1, flash_rate = 19)
    CBF.pygame_recording_loop(duration = 10.0, frame_rate = 2000, recording_name = "CBF")
