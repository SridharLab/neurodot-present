# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu

#local imports
from common import DEBUG, COLORS


################################################################################
class FixationCross:
    def __init__(self,
                 position = (0,0),
                 size      = 0.1,
                 thickness = 0.01,
                 color = 'white',
                 ):
        self.position = x,y = position
        self.size  = size
        self.thickness = thickness
        self.color = COLORS[color]
        self.vertices = [#horizontal beam
                         (x - size/2.0, y + thickness/2),  #left-top
                         (x - size/2.0, y - thickness/2),  #left-bottom
                         (x + size/2.0, y - thickness/2),  #right-bottom
                         (x + size/2.0, y + thickness/2),  #right-top
                         #vertical beam
                         (x - thickness/2, y + size/2.0),  #left-top
                         (x - thickness/2, y - size/2.0),  #left-bottom
                         (x + thickness/2, y - size/2.0),  #right-bottom
                         (x + thickness/2, y + size/2.0),  #right-top
                        ]

    def render(self):
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_LIGHTING)
        try:
            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(*self.color)
            for v in self.vertices:
                gl.glVertex2f(*v)
            gl.glEnd()
        finally:
            gl.glEnable(gl.GL_LIGHTING)
            
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    import pygame
    from common import DEBUG, UserEscape
    from screen import Screen
    from animated_screen import AnimatedScreen
    from numpy import pi
    
    pygame.init()
    pygame.mouse.set_visible(False)

    try:
        #setup the screen with fixation_cross
        FC = FixationCross(color = 'black')
        scr = Screen.with_pygame_display()
        scr.setup(background_color = 'white', fixation_cross = FC)
        #run the screen
        scr.run(duration = 2)

    except UserEscape as exc:
        print(exc)

    pygame.quit()
    sys.exit()
