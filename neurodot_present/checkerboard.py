# -*- coding: utf-8 -*-
from __future__ import print_function

import OpenGL.GL as gl
import OpenGL.GLU as glu

#local imports
from common import COLORS

class CheckerBoard:
    def __init__(self,
                 nrows,
                 check_width = 1.0,
                 check_height = None,
                 color1 = COLORS['white'],
                 color2 = COLORS['black'],
                 show_fixation_dot = False
                 ):
        self.nrows = int(nrows)
        self.check_width = check_width
        if check_height is None:
            check_height = check_width
        self.check_height = check_height
        self.color1 = color1
        self.color2 = color2
        self.show_fixation_dot = show_fixation_dot

    def render(self):
        w = self.check_width
        h = self.check_height
        color1 = self.color1
        color2 = self.color2
        board_width = w * self.nrows
        board_height = h * self.nrows
        gl.glDisable(gl.GL_LIGHTING)
        try:
            for x in range(0, self.nrows):
                for y in range(0, self.nrows):
                    if (x + y) % 2 == 0:
                        gl.glColor3f(*color1)
                    else:
                        gl.glColor3f(*color2)
                    gl.glRectf(w*x, h*y, w*(x + 1), h*(y + 1))

            if self.show_fixation_dot:
                gl.glColor3f(*COLORS['red'])
                gl.glTranslatef(board_width / 2.0, board_height / 2.0, 0)
                glu.gluDisk(glu.gluNewQuadric(), 0, 0.005, 45, 1)

        finally:
            gl.glEnable(gl.GL_LIGHTING)
