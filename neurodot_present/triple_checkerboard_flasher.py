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

class TripleCheckerBoardFlasher(Screen):
    def setup(self,
              nrows,
              nrows_center = 1,
              check_width = None,
              check_width_center = 0.5,
              check_color1 = 'white',
              check_color2 = 'black',
              screen_background_color = 'neutral-gray',
              show_fixation_dot = False,
              flash_rate_left = DEFAULT_FLASH_RATE,
              flash_rate_right = DEFAULT_FLASH_RATE,
              flash_rate_center = DEFAULT_FLASH_RATE,
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
        self.board_width_center = check_width_center * nrows_center
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows, check_width, color1 = check_color1, color2 = check_color2, show_fixation_dot = show_fixation_dot)
        self.CB2 = CheckerBoard(nrows, check_width, color1 = check_color2, color2 = check_color1, show_fixation_dot = show_fixation_dot) #reversed pattern
        self.CB1_center = CheckerBoard(nrows_center, check_width_center, color1 = check_color1, color2 = check_color2, show_fixation_dot = False)#show_fixation_dot)
        self.CB2_center = CheckerBoard(nrows_center, check_width_center, color1 = check_color2, color2 = check_color1, show_fixation_dot = False)#show_fixation_dot)
        self.CB_cycle_left = itertools.cycle((self.CB1,self.CB2))
        self.CB_cycle_right = itertools.cycle((self.CB1,self.CB2))
        self.CB_cycle_center = itertools.cycle((self.CB1_center,self.CB2_center))

        # set time-related attributes
        self._last_CB_change_time_left = None
        self._last_CB_change_time_right = None
        self._last_CB_change_time_center = None
        self.flash_rate_left  = flash_rate_left
        self.flash_interval_left = 1.0/flash_rate_left
        self.flash_rate_right = flash_rate_right
        self.flash_interval_right = 1.0/flash_rate_right
        self.flash_rate_center = flash_rate_center
        self.flash_interval_center = 1.0/flash_rate_center
        #self.rate_compensation = rate_compensation

        # get useful coordinate values for checkerboard rendering locations
        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)
        self.xL, self.yL = (self.xC - 0.7*self.screen_right, self.yC)
        self.xR, self.yR = (self.xC + 0.7*self.screen_right, self.yC)

        # some lists for checking things
        self.vals = itertools.cycle((1,0))
        self.t_list = []
        self.val_list = []
        self.vals_current = self.vals.next()

    def start_time(self,t):
        # get start time and set current CB objects (and their change times)
        Screen.start_time(self,t)
        self._last_CB_change_time_left = t
        self._last_CB_change_time_right = t
        self._last_CB_change_time_center = t
        self._current_CB_left = self.CB_cycle_left.next()
        self._current_CB_right = self.CB_cycle_right.next()
        self._current_CB_center = self.CB_cycle_center.next()

        # also used for checking things
        self.t_begin = t

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

        # render center board
        gl.glLoadIdentity()
        gl.glTranslatef(-self.board_width_center / 2.0, -self.board_width_center / 2.0, 0.0)
        self._current_CB_center.render()

    def update(self, t, dt):
        self.ready_to_render = False

        # only update a checkerboard if its flash_interval has elapsed
        if (t - self._last_CB_change_time_left) >= self.flash_interval_left:
            self._last_CB_change_time_left = t
            self._current_CB_left = self.CB_cycle_left.next()
            self.ready_to_render = True

            # checking things
            self.vals_current = self.vals.next()
        self.val_list.append(self.vals_current)
        self.t_list.append(t - self.t_begin)

        if (t - self._last_CB_change_time_right) >= self.flash_interval_right:
            self._last_CB_change_time_right = t
            self._current_CB_right = self.CB_cycle_right.next()
            self.ready_to_render = True

        if (t - self._last_CB_change_time_center) >= self.flash_interval_center:
            self._last_CB_change_time_center = t
            self._current_CB_center = self.CB_cycle_center.next()
            self.ready_to_render = True

    def run(self, **kwargs):
        # loop rate set too high so it should run effectively as fast as python is capable of looping
        Screen.run(self, display_loop_rate = 10000, **kwargs)


################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    flash_rate_left = 17
    flash_rate_right = 23
    flash_rate_center = 19
    duration = 5
    show_plot = True

    DCBF = TripleCheckerBoardFlasher.with_pygame_display(#VBI_sync_osx = False,
                                                         )
    #DCBF = TripleCheckerBoardFlasher.with_psychopy_window()
    DCBF.setup(flash_rate_left = flash_rate_left,
               flash_rate_right = flash_rate_right,
               flash_rate_center = flash_rate_center,
               check_width = 1.0 / 16.0,
               check_width_center = 0.5,
               screen_background_color = 'neutral-gray',
               nrows = 8,
               nrows_center = 1,
               show_fixation_dot = True,
              )
    DCBF.run(duration = duration)
    pygame.quit()

    if show_plot:
        t_diffs = np.diff(np.array(DCBF.t_list))
        print('Mean sample interval: ', t_diffs.mean())
        print('Mean sample frequency:', 1.0/t_diffs.mean())
        print('Sample interval STD:  ', t_diffs.std())

        import matplotlib.pyplot as plt
        import scipy.signal as scps
        # plt.subplot(2,1,1)
        plt.step(DCBF.t_list, DCBF.val_list, color = 'red', label = 'Displayed')
        time_vals = np.linspace(0, duration, duration * 720)
        val_vals = [scps.square(flash_rate_left * np.pi * t, duty = 0.5) / 2.0 + 0.5 for t in time_vals]
        plt.plot(time_vals, val_vals, color = 'blue', label = 'Ideal')
        plt.legend(loc = 'best')

        # must set ready_to_render to true in every loop for fft to work to get even sample spacing
        # note that this introduces its own error, as rendering is not as optimized
        # plt.subplot(2,1,2)
        # fft_data = abs(np.fft.rfft(DCBF.val_list))
        # fft_freqs = np.fft.rfftfreq(len(DCBF.val_list), 1.0/60)
        # plt.plot(fft_freqs, fft_data)
        # plt.show()



