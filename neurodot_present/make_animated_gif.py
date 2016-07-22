from visvis.vvmovie.images2gif import writeGif

#!/usr/bin/env python

from PIL import Image, ImageSequence
import sys, os


FRAME_DURATION = 1.0/60.0


#frames.reverse()

from images2gif import writeGif



################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    import time
    import pygame
    import OpenGL.GL as gl
    import OpenGL.GLU as glu
    import numpy as np
    import itertools
    import fractions
    import copy


    import itertools
    from checkerboard import CheckerBoard
    from common import DEBUG, COLORS, VSYNC_PATCH_HEIGHT_DEFAULT, VSYNC_PATCH_WIDTH_DEFAULT, SCREEN_LB, SCREEN_LT, SCREEN_RB, SCREEN_RT
    out_filename = "checkerboard_flasher.gif"
    color1 = COLORS['white']
    color2 = COLORS['black']
    N_FRAMES = 600
    FRAME_DURATION = 0.1 #second
    CB1 = CheckerBoard(nrows,width, color1 = color1, color2 = color2)
    CB2 = CheckerBoard(nrows,width, color1 = color2, color2 = color1)
    #white/black alterning for intermediate signals
    CB_cycle = itertools.cycle((CB1,CB2))
    CB = CB_cycle.next()
    #setup background color
    RGB_args = COLORS['neutral-gray']
    gl.glClearColor(*RGB_args, 1.0)
    frames = []
    for n in range(N_FRAMES):
        #prepare rendering model
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        #move so that board is center and render
        gl.glTranslatef(-0.5*BOARD_WIDTH,-0.5*BOARD_WIDTH,0.0)
        CB.render()
        
        
    
    writeGif(out_filename, frames, duration=original_duration/1000.0, dither=0)
