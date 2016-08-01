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

class TripleCheckerBoardSinFlasher(Screen):
    def setup(self,
              nrows,
              nrows_center = 1,
              check_width = None,
              check_width_center = 0.5,
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

        # set checkerboard-related attributes
        if check_width is None:
            check_width = 2.0/nrows #fill whole screen
        self.board_width = check_width*nrows
        self.board_width_center = check_width_center * nrows_center
        self.nrows = nrows
        self.CB_left = CheckerBoard(nrows, check_width, show_fixation_dot = show_fixation_dot)
        self.CB_right = CheckerBoard(nrows, check_width, show_fixation_dot = show_fixation_dot) #reversed pattern
        self.CB_center = CheckerBoard(nrows_center, check_width_center, show_fixation_dot = False)#show_fixation_dot)

        # set time-related attributes
        self.overall_start_time = None
        self.flash_rate_left  = flash_rate_left / 2.0  # we measure twice the actual frequency in the brain
        self.flash_rate_right = flash_rate_right / 2.0
        self.flash_rate_center = flash_rate_center / 2.0
        #self.rate_compensation = rate_compensation

        # get useful coordinate values for checkerboard rendering locations
        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)
        self.xL, self.yL = (self.xC - 0.7*self.screen_right, self.yC)
        self.xR, self.yR = (self.xC + 0.7*self.screen_right, self.yC)

        # quantities for checking things
        self.r1_list = []
        self.t_list = []

    def start_time(self,t):
        # get start time and set current CB objects (and their change times)
        Screen.start_time(self,t)
        self.overall_start_time = t

    def render(self):
        # do general OpenGL stuff as well as FixationCross and Vsync Patch if needed
        Screen.render(self)

        # translate to position of left board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xL, self.yL, 0.0)
        self.CB_left.render()

        # translate to position of right board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xR, self.yR, 0.0)
        self.CB_right.render()

        # render center board
        gl.glLoadIdentity()
        gl.glTranslatef(-self.board_width_center / 2.0, -self.board_width_center / 2.0, 0.0)
        self.CB_center.render()

    def update(self, t, dt):
        self.ready_to_render = True # render on every Screen.pygame_display_loop loop

        # update check colors on left checkerboard
        color1Left, color2Left = self.get_colors(t, self.flash_rate_left)
        self.CB_left.color1 = color1Left
        self.CB_left.color2 = color2Left

        # update check colors on right checkerboard
        color1Right, color2Right = self.get_colors(t, self.flash_rate_right)
        self.CB_right.color1 = color1Right
        self.CB_right.color2 = color2Right

        # update check colors on center checkerboard
        color1Center, color2Center = self.get_colors(t, self.flash_rate_center)
        self.CB_center.color1 = color1Center
        self.CB_center.color2 = color2Center

    def get_colors(self, t, flash_rate):
      # get elapsed time
      t = t - self.overall_start_time

      # get colors
      r1 = g1 = b1 = -1.0 * np.cos(flash_rate * 2.0 * np.pi * t) / 2.0 + 0.5  # will modulate between 0 and 1 at flash_rate Hz
      r2 = g2 = b2 = np.cos(flash_rate * 2.0 * np.pi * t) / 2.0 + 0.5
      color1 = (r1, g1, b1)
      color2 = (r2, g2, b2)

      # get some values for checking what was displayed
      if flash_rate == self.flash_rate_left:
        self.r1_list.append(r1)
        self.t_list.append(t)

      return color1, color2

    def run(self, **kwargs):
        # loop rate set too high so that it should run effectively as fast as python is capable of looping
        Screen.run(self, display_loop_rate = 10000, **kwargs)


################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    flash_rate_left =  7
    flash_rate_right = 19
    flash_rate_center = 23
    show_plot = True

    DCBF = TripleCheckerBoardSinFlasher.with_pygame_display(#VBI_sync_osx = False,
                                                         )
    #DCBF = TripleCheckerBoardFlasher.with_psychopy_window()
    DCBF.setup(flash_rate_left = flash_rate_left,
               flash_rate_right = flash_rate_right,
               flash_rate_center = flash_rate_center,
               check_width = 1.0 / 16.0,
               check_width_center = 1.0 / 16.0,
               screen_background_color = 'neutral-gray',
               nrows = 8,
               nrows_center = 8,
               show_fixation_dot = True,
              )
    DCBF.run(duration = 5)
    pygame.quit()

    if show_plot:
        import matplotlib.pyplot as plt
        plt.scatter(DCBF.t_list, DCBF.r1_list, color = 'red')
        time_vals = np.linspace(0, 5, 3600)
        trig_vals = [-1.0 * np.cos(DCBF.flash_rate_left * 2.0 * np.pi * t) / 2.0 + 0.5 for t in time_vals]
        plt.plot(time_vals, trig_vals, color = 'blue')
        plt.show()

