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

class CheckerBoardFlasherScreen(Screen):
    def setup(self,
              nrows,
              check_width = None,
              check_color1 = 'white',
              check_color2 = 'black',
              screen_background_color = 'neutral-gray',
              fixation_dot_color = None,
              flash_rate = DEFAULT_FLASH_RATE,
              #rate_compensation = None,
              vsync_patch = "bottom-right",
              vsync_value = None,
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
        self.CB1 = CheckerBoard(nrows, check_width, color1 = check_color1, color2 = check_color2, fixation_dot_color = fixation_dot_color)
        self.CB2 = CheckerBoard(nrows, check_width, color1 = check_color2, color2 = check_color1, fixation_dot_color = fixation_dot_color) #reversed pattern
        self.CB_cycle = itertools.cycle((self.CB1,self.CB2))

        # set time-related attributes
        self._last_CB_change_time = None
        self.flash_rate  = flash_rate
        self.flash_interval = 1.0/flash_rate
        #self.rate_compensation = rate_compensation

        # get useful coordinate values for checkerboard rendering locations
        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)

    def start_time(self,t):
        # get start time and set current CB objects (and their change times)
        Screen.start_time(self,t)
        self._last_CB_change_time = t
        self._current_CB = self.CB_cycle.next()

    def render(self):
        # do general OpenGL stuff 
        Screen.render_before(self)
        # translate to position of left board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xC, self.yC, 0.0)
        self._current_CB.render()
        # do FixationCross and Vsync Patch if needed
        Screen.render_after(self)

    def update(self, t, dt):
        Screen.update(self, t, dt) #important, this handles vsync updates
        
        #we need to render if the vsync patch is ready
        self.ready_to_render = self.vsync_patch.ready_to_render

        # otherwise, only update a checkerboard if its flash_interval has elapsed
        if (t - self._last_CB_change_time) >= self.flash_interval:
            self._last_CB_change_time = t
            self._current_CB = self.CB_cycle.next()
            self.ready_to_render = True

    def run(self, **kwargs):
        # loop rate set too high so it should run effectively as fast as python is capable of looping
        Screen.run(self, display_loop_rate = 10000, **kwargs)

################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    import sys
    
    #ensure that video mode is at the maxium FPS
    if sys.platform.startswith("linux"):
        from subprocess import call
        call(["xrandr","-r","144"])

    import neurodot_present
    neurodot_present.settings['vsync_version'] = 2
    CBFscreen = CheckerBoardFlasherScreen.with_pygame_display(
                                                              #display_mode = (512,512),
                                                              #debug = True
                                                             )
    CBFscreen.setup(nrows = 64, 
                    flash_rate = 20,
                    )
    CBFscreen.run(duration = 1.0, vsync_value = 0)
    #CBFscreen.run(duration = 5.0, vsync_value = 1)
    #CBFscreen.run(duration = 5.0, vsync_value = 2)
    #CBFscreen.run(duration = 5.0, vsync_value = 3)
    while True:
        for i in range(14):
            CBFscreen.run(duration = 1.0, vsync_value = i)
   
#    CBFscreen.run(duration = 5.0, vsync_value = 5)
#    CBFscreen.run(duration = 5.0, vsync_value = 6)
#    CBFscreen.run(duration = 5.0, vsync_value = 7)
#    CBFscreen.run(duration = 5.0, vsync_value = 8)
#    CBFscreen.run(duration = 5.0, vsync_value = 9)
#    CBFscreen.run(duration = 5.0, vsync_value = 10)
#    CBFscreen.run(duration = 5.0, vsync_value = 11)
#    CBFscreen.run(duration = 5.0, vsync_value = 12)
#    CBFscreen.run(duration = 5.0, vsync_value = 13)
#    CBFscreen.run(duration = 5.0, vsync_value = 14)
#    CBFscreen.run(duration = 5.0, vsync_value = 15)
#    CBFscreen.run(duration = 5.0, vsync_value = 16)
    #CBF.pygame_recording_loop(duration = 10.0, frame_rate = 2000, recording_name = "CBF")
