# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy as np
import OpenGL.GL as gl


#local imports
from common import DEBUG, COLORS, VSYNC_PATCH_HEIGHT_DEFAULT, VSYNC_PATCH_WIDTH_DEFAULT


class VsyncPatch:
    def __init__(self, left, bottom, width, height,
                 on_color  = COLORS['white'],
                 off_color = COLORS['black'],
                 ):
        self.vertices = np.array(((left      , bottom),
                                  (left+width, bottom),           #right bottom
                                  (left+width, bottom + height),  #right top
                                  (left      , bottom + height),  #left  top
                                  ))
        self.left   = left
        self.bottom = bottom
        self.width  = width
        self.height = height
        self.on_color  = on_color
        self.off_color = off_color

    def compute_bit_colors(self, value):
        bit_colors = []
        if value & 0b0001:  #bit0,  also the vsync trigger bit
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if value & 0b0010:  #bit1
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if value & 0b0100:  #bit2
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if value & 0b1000:  #bit3
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        return bit_colors

    def render(self, value):
        if not value is None:
            left, bottom, width, height = (self.left,self.bottom,self.width,self.height)
            bit_colors = self.compute_bit_colors(value)
            gl.glLoadIdentity()
            gl.glDisable(gl.GL_LIGHTING)

            try:
                #bit 0, sub square at bottom/right corner, also the vsync trigger bit
                gl.glColor3f(*bit_colors[0])
                gl.glRectf(left + width/2.0, bottom,  left + width, bottom + height/2.0) #left,bottom -> right,top
                #bit 1, sub square at bottom/left corner
                gl.glColor3f(*bit_colors[1])
                gl.glRectf(left, bottom,left + width/2.0, bottom + height/2.0) #left,bottom -> right,top
                #bit 2, sub square at top/left corner
                gl.glColor3f(*bit_colors[2])
                gl.glRectf(left, bottom + height/2.0,left + width/2.0, bottom + height) #left,bottom -> right,top
                #bit 3, sub square at top/right corner
                gl.glColor3f(*bit_colors[3])
                gl.glRectf(left + width/2.0, bottom + height/2.0,left + width, bottom + height) #left,bottom -> right,top
            finally:
                gl.glEnable(gl.GL_LIGHTING)
    @classmethod
    #define the vsync patch as being in the bottom right corner
    def make_bottom_right(cls,
                          screen_bottom,
                          screen_right,
                          patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                          patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                         ):
        obj = cls(left   = screen_right - patch_width,
                  bottom = screen_bottom,
                  width  = patch_width,
                  height = patch_height
                 )
        return obj
