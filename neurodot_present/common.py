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

import resources


DEBUG = False

COLORS = {
    'black'   : (0.0,0.0,0.0),
    'red'     : (1.0,0.0,0.0),
    'green'   : (0.0,1.0,0.0),
    'blue'    : (0.0,0.0,1.0),
    'cyan'    : (0.0,1.0,1.0),
    'magenta' : (1.0,0.0,1.0),
    'yellow'  : (1.0,1.0,0.0),
    'white'   : (1.0,1.0,1.0),
    'neutral-gray': (0.75,0.75,0.75)
}

SCREEN_LT = np.array((-1.0, 1.0))
SCREEN_LB = np.array((-1.0,-1.0))
SCREEN_RB = np.array(( 1.0,-1.0))
SCREEN_RT = np.array(( 1.0, 1.0))

LARGE_WIDTH = 0.5 #fraction of total screen length

VSYNC_PATCH_WIDTH_DEFAULT  = 0.225
VSYNC_PATCH_HEIGHT_DEFAULT = 0.225

DEFAULT_FLASH_RATE = 17 #Hz


def bell(blocking=False):
    pygame.mixer.init()
    bell_sound = pygame.mixer.Sound(resources.get_bellpath("bell.wav"))
    ch = bell_sound.play()
    if blocking:
        while ch.get_busy():
            pygame.time.delay(100)

class UserEscape(Exception):
    def __init__(self, msg = "User stopped the sequence"):
        Exception.__init__(self, msg)

class Quad:
    def __init__(self, lt, lb, rb, rt, color = COLORS['white']):
        self.vertices = np.array((lt,lb,rb,rt))
        self.color = color
    def render(self):
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_LIGHTING)
        try:
            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(*self.color)
            for v in self.vertices:
                gl.glVertex2f(*tuple(v))
            gl.glEnd()
        finally:
            gl.glEnable(gl.GL_LIGHTING)

class Sprite:
    def __init__(self):
        pass

    # functions for converting between coordinate systems
    def cart2pol(self, x, y):
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        return(r, theta)

    def pol2cart(self, r, theta):
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        return(x, y)

    def update():
        raise NotImplementedError("update method must be overridden in Sprite subclass")

    def render():
        raise NotImplementedError("render method must be overridden in Sprite subclass")
        

