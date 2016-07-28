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
from common import COLORS, DEBUG, VSYNC_PATCH_HEIGHT_DEFAULT, VSYNC_PATCH_WIDTH_DEFAULT, DEFAULT_FLASH_RATE
from common import UserEscape

from screen import Screen

from checkerboard import CheckerBoard

class DoubleCheckerBoardFlasher(Screen):
    def setup_checkerboards(self,
                            nrows,
                            check_width = None,
                            check_color1 = 'white',
                            check_color2 = 'black',
                            screen_background_color = 'neutral-gray',
                            show_fixation_dot = False,
                            flash_rate_left = DEFAULT_FLASH_RATE,
                            flash_rate_right = DEFAULT_FLASH_RATE,
                            #rate_compensation = None,
                            vsync_patch = None,
                           ):
        Screen.setup(self,
                     background_color = screen_background_color,
                     vsync_patch = vsync_patch,
                     )

        #run colors through filter to catch names and convert to RGB
        check_color1 = COLORS.get(check_color1, check_color1)
        check_color2 = COLORS.get(check_color2, check_color2)

        # set checkerboard-related attributes
        if check_width is None:
            check_width = 2.0/nrows #fill whole screen
        self.board_width = check_width*nrows
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows, check_width, color1 = check_color1, color2 = check_color2, show_fixation_dot = show_fixation_dot)
        self.CB2 = CheckerBoard(nrows, check_width, color1 = check_color2, color2 = check_color1, show_fixation_dot = show_fixation_dot) #reversed pattern
        self.CB_cycle_left = itertools.cycle((self.CB1,self.CB2))
        self.CB_cycle_right = itertools.cycle((self.CB1,self.CB2))

        # set time-related attributes
        self._last_CB_change_time_left = None
        self._last_CB_change_time_right = None
        self.flash_rate_left  = flash_rate_left
        self.flash_interval_left = 1.0/flash_rate_left
        self.flash_rate_right = flash_rate_right
        self.flash_interval_right = 1.0/flash_rate_right
        #self.rate_compensation = rate_compensation

        # get useful coordinate values for checkerboard rendering locations
        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)
        self.xL, self.yL = (self.xC - 0.5*self.screen_right, self.yC)
        self.xR, self.yR = (self.xC + 0.5*self.screen_right, self.yC)

    def start_time(self,t):
        # get start time and set current CB objects (and their change times)
        Screen.start_time(self,t)
        self._last_CB_change_time_left = t
        self._last_CB_change_time_right = t
        self._current_CB_left = self.CB_cycle_left.next()
        self._current_CB_right = self.CB_cycle_right.next()

    def render(self):
        # do general OpenGL stuff as well as FixationCross and Vsync Patch if needed
        Screen.render(self)

        # translate to position of left board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xL, self.yL, 0.0)
        self._current_CB_left.render()

        # translate to position of right board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xR, self.yR, 0.0)
        self._current_CB_right.render()

    def update(self, t, dt):
        self.ready_to_render = False

        # only update a checkerboard if its flash_interval has elapsed
        if (t - self._last_CB_change_time_left) >= self.flash_interval_left:
            self._last_CB_change_time_left = t
            self._current_CB_left = self.CB_cycle_left.next()
            self.ready_to_render = True

        if (t - self._last_CB_change_time_right) >= self.flash_interval_right:
            self._last_CB_change_time_right = t
            self._current_CB_right = self.CB_cycle_right.next()
            self.ready_to_render = True

    def run(self, **kwargs):
        # loop rate set too high so it should run effectively as fast as python is capable of looping
        Screen.run(self, display_loop_rate = 10000, **kwargs)


################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    flash_rate_left = 19
    flash_rate_right = 23
    pygame.init()
    display_mode = pygame.display.list_modes()[-1]
    pygame.quit()

    DCBF = DoubleCheckerBoardFlasher.with_pygame_display(
                                                         display_mode = (64,64),
                                                         debug = True
                                                        )
    DCBF.setup_checkerboards(flash_rate_left = flash_rate_left,
                             flash_rate_right = flash_rate_right,
                             check_width = 0.5,
                             screen_background_color = 'black',
                             nrows = 1
                            )
    #DCBF.run(duration = 120)
    frame_rate = 140*25
    recording_name = "DCBF"
    DCBF.pygame_recording_loop(duration = 10.0, frame_rate = frame_rate, recording_name = recording_name)
    #import subprocess
    #subprocess.call(["ffmpeg", "-framerate",str(frame_rate),"-i", CBF/CBF_%05d.png -c^C libx264 -pix_fmt yuv420p  CBF.mp4)])
    
