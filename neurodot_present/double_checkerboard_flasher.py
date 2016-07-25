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
from common import DEBUG, COLORS, VSYNC_PATCH_HEIGHT_DEFAULT, VSYNC_PATCH_WIDTH_DEFAULT, DEFAULT_FLASH_RATE
from common import UserEscape

from screen import Screen

from checkerboard import CheckerBoard

class DoubleCheckerBoardFlasher(Screen):
    def __init__(self,
                 display_mode = None,
                 flash_rate_left  = DEFAULT_FLASH_RATE,
                 flash_rate_right = DEFAULT_FLASH_RATE,
                 vsync_patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                 vsync_patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                 constrain_aspect = True,
                 ):
        Screen.__init__(self,
                        color = "black",
                        display_mode = display_mode,
                        constrain_aspect = constrain_aspect,
                        vsync_patch_width  = vsync_patch_width,
                        vsync_patch_height = vsync_patch_height,
                       )
        self.flash_rate_left  = flash_rate_left
        self.flash_rate_right = flash_rate_right

    def setup_checkerboards(self,
                           nrows,
                           width = 2.0 / 64.0,  # width of checks for 64x64 full screen board
                           color1 = 'white',
                           color2 = 'black',
                           screen_bgColor = 'neutral-gray',
                           show_fixation_dot = False,
                           vsync_value = None,
                           flash_rate_left = None,
                           flash_rate_right = None,
                           rate_compensation = None,
                           ):
        #run colors through filter to catch names and convert to RGB
        color1 = COLORS.get(color1, color1)
        color2 = COLORS.get(color2, color2)
        # if width is None:
        #     width = 2.0/nrows #fill whole screen
        self.board_width = width*nrows
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows, width, color1 = color1, color2 = color2, show_fixation_dot = show_fixation_dot)
        self.CB2 = CheckerBoard(nrows, width, color1 = color2, color2 = color1, show_fixation_dot = show_fixation_dot) #reversed pattern
        self.CB3 = CheckerBoard(nrows, width, color1 = color1, color2 = color2, show_fixation_dot = show_fixation_dot)
        self.CB4 = CheckerBoard(nrows, width, color1 = color2, color2 = color1, show_fixation_dot = show_fixation_dot) # reversed
        self.screen_bgColor = COLORS[screen_bgColor]
        self.vsync_value = vsync_value
        if not flash_rate_left is None:
            self.flash_rate_left  = flash_rate_left
        if not flash_rate_right is None:
            self.flash_rate_right = flash_rate_right
        
        self.rate_compensation = rate_compensation

        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)
        self.xL, self.yL = (self.xC - 0.5*self.screen_right, self.yC)
        self.xR, self.yR = (self.xC + 0.5*self.screen_right, self.yC)

    def run(self, duration = 5, flash_rate_left = None, flash_rate_right = None, vsync_value = None):
        #white/black alterning for intermediate signals
        leftCB_cycle = itertools.cycle((self.CB1,self.CB2))
        rightCB_cycle = itertools.cycle((self.CB3,self.CB4))

        if flash_rate_left is None:
            flash_rate_left = self.flash_rate_left
        if flash_rate_right is None:
            flash_rate_right = self.flash_rate_right
            
        #apply compenstation if specified
        if not self.rate_compensation is None:
            flash_rate_left  += self.rate_compensation
            flash_rate_right += self.rate_compensation

        if vsync_value is None and not self.vsync_value is None:
            vsync_value = self.vsync_value
        elif vsync_value is None:
            vsync_value = 1

        #set background color
        gl.glClearColor(self.screen_bgColor[0], self.screen_bgColor[1], self.screen_bgColor[2], 1.0)


        vsync_patch = self.vsync_patch

        leftCB = leftCB_cycle.next()
        rightCB = rightCB_cycle.next()


        is_running = True

        xL, yL = self.xL, self.yL # (xC - 0.5*self.screen_right, yC)
        xR, yR = self.xR, self.yR # (xC + 0.5*self.screen_right, yC)

        dtL = 1.0/flash_rate_left
        dtR = 1.0/flash_rate_right
        tL  = time.time() #time since last change
        tR  = time.time() #time since last change
        t0  = time.time()
        # t_list = []

        def render_routine():
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
            #render the vsync patch
            vsync_patch.render(value = vsync_value)
            # translate to position of left board
            gl.glTranslatef(xL, yL, 0.0)
            leftCB.render()
            # translate to position of right board
            gl.glLoadIdentity()
            gl.glTranslatef(xR, yR, 0.0)
            rightCB.render()
            #show the scene
            pygame.display.flip()

        while is_running:
            #get fresh time
            t = time.time()
            if t > (tL + dtL):
                leftCB = leftCB_cycle.next()
                tL  = t #update change time
                render_routine()
            if t > (tR + dtR):
                rightCB = rightCB_cycle.next()
                tR  = t #update change time
                render_routine()

            # t_list.append(t)  #this is for measuring the loop delay
                #handle outstanding events
            is_running = self.handle_events()
            #print t, t0, duration
            if t - t0 > duration:
                is_running = False
        #-----------------------------------------------------------------------
        #this is for measuring the loop delay
        # import numpy as np
        # print("mean loop dt:", np.array(np.diff(t_list).mean()))
        # print("Frequency (Hz):", 1.0 / np.array(np.diff(t_list).mean()))
        
        
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    DCBF = DoubleCheckerBoardFlasher()
    DCBF.setup_checkerboards(nrows = 16)
    DCBF.run(duration = 10)

