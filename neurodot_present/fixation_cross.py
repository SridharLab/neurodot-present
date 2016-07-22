# -*- coding: utf-8 -*-
from __future__ import print_function

import time

import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import pygame

#local imports
from common import DEBUG, COLORS, SCREEN_LB, SCREEN_LT, SCREEN_RB, SCREEN_RT
from common import UserEscape

from vsync_patch import VsyncPatch

class FixationCross:
    def __init__(self,
                 position = (0,0),
                 size      = 0.1,
                 thickness = 0.01,
                 color = 'white',
                 ):
        self.position = position
        self.size  = size
        self.thickness = thickness
        self.color = COLORS[color]
        self.vertices = [#horizontal beam
                         (position[0] - size/2.0, position[1] + thickness/2),  #left-top
                         (position[0] - size/2.0, position[1] - thickness/2),  #left-bottom
                         (position[0] + size/2.0, position[1] - thickness/2),  #right-bottom
                         (position[0] + size/2.0, position[1] + thickness/2),  #right-top
                         #vertical beam
                         (position[0] - thickness/2, position[1] + size/2.0),  #left-top
                         (position[0] - thickness/2, position[1] - size/2.0),  #left-bottom
                         (position[0] + thickness/2, position[1] - size/2.0),  #right-bottom
                         (position[0] + thickness/2, position[1] + size/2.0),  #right-top
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
            
            
