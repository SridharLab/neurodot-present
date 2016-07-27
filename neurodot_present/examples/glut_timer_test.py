from __future__ import print_function
import sys
import subprocess
import itertools
import time
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
from OpenGL._bytes import as_8_bit

import neurodot_present.present_lib as pl
#from neurodot_present.present_lib import Screen, CheckerBoard, UserEscape, VsyncPatch

"""
This differs from glut_test in that it uses the GLUT glutTimerFunc function, which sets a function that will be called after some delay.
You can set multiple glutTimerFuncs at once with differing delays, so I hoped this could be an elegant solution for displaying multiple
checkerboards.  However, the actual delay that glutTimerFunc uses is simply too inconsistent for our purposes.  If there was a way to make
this delay precise and accurate this would be an excellent solution to displaying multiple frequencies.
"""

DURATION = 60
flash_rate_left = 19  # Hz
flash_rate_right = 23

# function for getting screen resolution, stolen from stackexchange
def get_screen_resolution():
    output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',shell=True, stdout=subprocess.PIPE).communicate()[0]
    resolution = output.split()[0].split(b'x')
    resolution = [int(r) for r in resolution]
    return resolution

# get screen limits
def get_screen(screen_size, constrain_aspect = True):
    screen_width, screen_height = screen_size

    # aspect ratio correcting code scalped from present_lib.Screen
    aspect_ratio = float(screen_width)/screen_height
    left, right, bottom, top = (pl.SCREEN_LT[0],pl.SCREEN_RB[0],pl.SCREEN_RB[1],pl.SCREEN_LT[1])
    if constrain_aspect:  # Set the aspect ratio of the plot so that it is not distorted
        if screen_width <= screen_height:
            bottom /= aspect_ratio
            top    /= aspect_ratio
        else:
            aspect_ratio = float(screen_width)/screen_height
            #left, right, bottom, top
            left   *= aspect_ratio
            right  *= aspect_ratio

    return (left, right, bottom, top)

# display callback handler for window re-paint
def render_routine():
    global render_time_list
    global render_left
    global render_right

    gl.glFinish()
    ti = time.time()

    #prepare rendering model
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    glu.gluOrtho2D(*screen_limits)

    # translate to position of left board and render
    gl.glTranslatef(xTranslateLeft, yTranslate, 0.0)
    if render_left:
        CB_left.render()
        render_left = False

    # translate to position of right board and render
    gl.glTranslatef(-xTranslateLeft + xTranslateRight, 0.0, 0.0)
    if render_right:
        CB_right.render()
        render_right = False

    #show the scene
    gl.glFinish()
    glut.glutSwapBuffers()

    # get time for later mean frame time calculation
    gl.glFinish()
    tf = time.time()
    render_time_list.append(tf - ti)

def update_left_checkerboard(trash_value):
    global CB_left
    global t_list_left
    global render_left

    CB_left = CB_cycle_left.next()
    render_left = True
    glut.glutPostRedisplay()
    t_list_left.append(time.time())

    glut.glutTimerFunc(dtLeft, update_left_checkerboard, None)

def update_right_checkerboard(trash_value):
    global CB_right
    global t_list_right
    global render_right

    CB_right = CB_cycle_right.next()
    render_right = True
    glut.glutPostRedisplay()
    t_list_right.append(time.time())

    glut.glutTimerFunc(dtRight, update_right_checkerboard, None)

# handle key press events
def key_pressed(*args):
    if args[0] == esc_key:
        exit_function()
    # else:
    #     sys.exit()

# things to do when exiting
def exit_function():
    print('Left checkerboard:')
    print_freq_info(t_list_left)
    print()
    print('Right checkerboard:')
    print_freq_info(t_list_right)

    #frameTime = np.array(np.diff(render_time_list)).mean()
    render_routine_time = np.array(render_time_list).mean()
    print('Mean render_routine time:      ', render_routine_time)
    print('Mean render_routine frequency: ', 1.0/render_routine_time)

    sys.exit()

# set global objects needed for presentation
def initialize_presentation():
    global CB_cycle_left
    global CB_cycle_right
    global CB_left
    global CB_right
    global dtLeft  # period of left checkerboard
    global dtRight  # period of right checkerboard
    global t_list_left
    global t_list_right
    global screen_limits
    global xTranslateLeft
    global xTranslateRight
    global yTranslate
    global esc_key
    global render_time_list
    global render_left
    global render_right

    # create checkerboards
    cb1 = pl.CheckerBoard(1, color1 = [1.0, 1.0, 1.0], color2 = [0.0, 0.0, 0.0], width = 0.5)
    cb2 = pl.CheckerBoard(1, color1 = [0.0, 0.0, 0.0], color2 = [1.0, 1.0, 1.0], width = 0.5)
    CB_cycle_left = itertools.cycle((cb2, cb1))
    CB_cycle_right = itertools.cycle((cb2, cb1))
    CB_left = CB_cycle_left.next()
    CB_right = CB_cycle_right.next()

    # initialize render flags
    render_left = False
    render_right = False

    # get time variables
    dtLeft = int(np.floor(1000.0/flash_rate_left))
    dtRight = int(np.floor(1000.0/flash_rate_right))
    t_list_left = []
    t_list_right = []
    render_time_list = []

    # get screen size and limits for setting gluOrtho2D
    screen_size = get_screen_resolution()
    #screen_size = (1440, 878) # HARDCODED screen size because xrandr takes a bit to run on macs
    screen_limits = get_screen(screen_size = screen_size)

    # get translation quantities for glTranslatef in render_routine
    board_width = CB_left.width * CB_left.nrows
    xTranslateLeft = - board_width / 2.0 - (0.5 * screen_limits[1]) # distance from origin to where left CB renders
    xTranslateRight = - board_width / 2.0 + (0.5 * screen_limits[1]) # distance from origin to where right CB renders
    yTranslate = -board_width / 2.0

    # set value so esc key can be acted on
    esc_key = as_8_bit( '\033' )

def print_freq_info(t_list):
    #this is for measuring the loop delay
    print("mean loop dt:", np.array(np.diff(t_list).mean()))
    print("Frequency (Hz):", 1.0 / np.array(np.diff(t_list).mean()))

    # get histogram values
    bins = [0]
    bins += range(16, 40, 1)
    bins += [10000]
    freq_list = 1.0 / np.diff(t_list)
    binVals, bins = np.histogram(freq_list, bins)

    # format histogram output
    titleStr = "Bin: "
    valueStr = "n:   "
    for b in bins[1:len(bins)]:
        titleStr += "{:>8}".format(b)
    for n in binVals:
        valueStr += "{:>8}".format(n)

    # print stuff
    print("Frequency list:")
    print(freq_list)
    print()
    print("Histogram values:")
    print(titleStr)
    print(valueStr)

if __name__ == '__main__':

    initialize_presentation()       # get global objects needed for all of this to work

    glut.glutInit()
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE)      # initialize display mode as double buffering
    glut.glutCreateWindow('')        # create window
    glut.glutDisplayFunc(render_routine)        # set display callback handler for window re-paint
    glut.glutKeyboardFunc(key_pressed)      # set callback handler for keyboard events
    glut.glutTimerFunc(0, update_left_checkerboard, 0)
    glut.glutTimerFunc(0, update_right_checkerboard, 0)

    glut.glutFullScreen()       # put window in full screen
    glut.glutMainLoop()     # enter main events processing loop
