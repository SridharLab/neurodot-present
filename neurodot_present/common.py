# -*- coding: utf-8 -*-
from __future__ import print_function

import os,time
from collections import OrderedDict
import pygame, pygame.image
import OpenGL.GL as gl
import OpenGL.GLU as glu
import numpy as np
import itertools
import fractions
import copy
import sys
import shelve
import scipy.interpolate

import resources

from PIL import Image

SETTINGS = OrderedDict()
SETTINGS['debug'] = False

inv_gamma = 0.43

COLORS = {
    'black'   : (0.0,0.0,0.0),
    'red'     : (1.0,0.0,0.0),
    'green'   : (0.0,1.0,0.0),
    'blue'    : (0.0,0.0,1.0),
    'cyan'    : (0.0,1.0,1.0),
    'magenta' : (1.0,0.0,1.0),
    'yellow'  : (1.0,1.0,0.0),
    'white'   : (1.0,1.0,1.0),
    'neutral-gray': (0.5**inv_gamma,0.5**inv_gamma,0.5**inv_gamma)
}

SCREEN_LT = np.array((-1.0, 1.0))
SCREEN_LB = np.array((-1.0,-1.0))
SCREEN_RB = np.array(( 1.0,-1.0))
SCREEN_RT = np.array(( 1.0, 1.0))

LARGE_WIDTH = 0.5 #fraction of total screen length

VSYNC_PATCH_WIDTH_DEFAULT  = 0.225
VSYNC_PATCH_HEIGHT_DEFAULT = 0.225

DEFAULT_FLASH_RATE = 17 #Hz

MONITOR_NAME = 'benq'

#-------------------------------------------------------------------------------
# utility functions
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

# write a png file from GL framebuffer data
def png_file_write(name, frame_num, w, h, data, outdir = None):
    im = Image.frombuffer("RGBA", (w,h), data, "raw", "RGBA", 0, 0)
    fname = "%s_%05d.png" % (name,frame_num)
    if outdir is None:
        outdir = name
    #make a directory to store the recording
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
    pathname = os.path.sep.join((outdir,fname))
    im.save(pathname)

# got this straight out of stackexchange: http://stackoverflow.com/questions/17084928/how-to-enable-vsync-in-pyopengl/34768964
def enable_VBI_sync_osx():
    if sys.platform != 'darwin':
        return
    try:
        import ctypes
        import ctypes.util
        ogl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("OpenGL"))
        v = ctypes.c_int(1)

        ogl.CGLGetCurrentContext.argtypes = []
        ogl.CGLGetCurrentContext.restype = ctypes.c_void_p

        ogl.CGLSetParameter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        ogl.CGLSetParameter.restype = ctypes.c_int

        context = ogl.CGLGetCurrentContext()

        ogl.CGLSetParameter(context, 222, ctypes.pointer(v))
    except Exception as e:
        print("Unable to set vsync mode, using driver defaults: {}".format(e))

def load_gamma_calibration(monitor_name = MONITOR_NAME, interp_kind = 'cubic', show_plot = False):
    home = os.path.expanduser('~')
    dbPath = os.path.sep.join((home, '.neurodot_present', 'calibrations', monitor_name))

    # check if calibration file has been created, otherwise shelve.open will make a new .db file
    if not os.path.isfile(dbPath):
        errorstring = str(dbPath) + 'does not exist: Create a calibration file with gamma_utility.py first.'
        raise ValueError(errorstring)

    # get data from .db file
    db = shelve.open(dbPath)
    needed_inputs = db['input_intensities']
    desired_intensity = db['desired_intensities']
    db.close()

    # get function from interp1d
    inv_gam_func = scipy.interpolate.interp1d(desired_intensity, needed_inputs, kind = interp_kind)

    # show plot if needed (this is only for checking data with ipython, will not be needed in actual implementation)
    if show_plot:
        x_range = np.linspace(0, 1, 100)
        experiment_x_vals = inv_gam_func.x
        experiment_y_vals = inv_gam_func.y
        interp_vals = [inv_gam_func(x) for x in x_range]

        import matplotlib.pyplot as plt
        fig = plt.figure(1)
        ax1 = fig.add_subplot(111)
        ax1.scatter(experiment_x_vals, experiment_y_vals)
        ax1.plot(x_range, interp_vals)
        ax1.grid(True)
        ax1.set_xlabel('Desired Brightness')
        ax1.set_ylabel('Input Intensity')
        ax1.set_title('Inverse Gamma Function')
        ax1.set_xlim(0,1)
        ax1.set_ylim(0,1)
        plt.show()

    return inv_gam_func

def correct_gamma(input_color, monitor_name = MONITOR_NAME, interp_kind = 'linear', **kwargs):
    inv_gam_func = load_gamma_calibration(monitor_name = monitor_name, interp_kind = interp_kind, **kwargs)

    return(float(inv_gam_func(input_color)))

#-------------------------------------------------------------------------------
# graphics
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

#-------------------------------------------------------------------------------
# math
# functions for converting between coordinate systems
def cart2pol(x, y):
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return(r, theta)

def pol2cart(r, theta):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return(x, y)



