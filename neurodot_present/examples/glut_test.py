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

    # gl.glFinish()
    # t_initial = time.time()

    #prepare rendering model
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    glu.gluOrtho2D(*screen_limits)

    # translate to position of left board and render
    gl.glTranslatef(xTranslateLeft, yTranslate, 0.0)
    CB_left.render()

    # translate to position of right board and render
    gl.glTranslatef(-xTranslateLeft + xTranslateRight, 0.0, 0.0)
    CB_right.render()

    #show the scene
    gl.glFinish()
    glut.glutSwapBuffers()

    gl.glFinish()
    t_final = time.time()
    render_time_list.append(t_final)#t_final - t_initial)

# idle function, will be looped through by GLUT (at the screen refresh rate) in absence of other events
def presentation():#trash_value):
    global tLeft
    global tRight
    global t_list
    global CB_left
    global CB_right
    # global idleFunc_time_list
    # global idleFunc_call_list

    # gl.glFinish()
    # t_initial = time.time()
    # idleFunc_call_list.append(time.time())

    # reset things
    render_flag = False
    append_left_time = False
    append_right_time = False
    t = time.time()

    # check if enough time has passed to rerender left checkerboard
    if t > (tLeft + dtLeft):
        CB_left = CB_cycle_left.next()
        tLeft  = t #update change time
        render_flag = True
        append_left_time = True

    # check if enough time has passed to rerender right checkerboard
    if t > (tRight + dtRight):
        CB_right = CB_cycle_right.next()
        tRight = t
        render_flag = True
        append_right_time = True

    # check if either checkerboard needs to be rendered, re-paint display
    if render_flag:
        gl.glFinish()
        glut.glutPostRedisplay() # glutPostRedisplay calls glutDisplayFunc's argument (the callback handler for window re-paint)

    # append time values to time lists for each checkerboard
    if append_left_time:
        t_list_left.append(time.time())
    if append_right_time:
        t_list_right.append(time.time())

    # # finish doing things, get time
    # gl.glFinish()
    # t_final = time.time()
    # if render_flag:
    #     idleFunc_time_list.append(t_final - t_initial)

    # check if the presentation has been running long enough yet
    if t - t0 > DURATION:
        exit_function()

    # refresh_ms = int(np.floor(1000.0 / 144.0))  # should be 16 ms for 60 Hz refresh rate
    # glut.glutTimerFunc(1, presentation, 0)

# handle key press events
def key_pressed(*args):
    if args[0] == esc_key:
        exit_function()
    else:
        sys.exit()

# things to do when window is destroyed
def exit_function():
    # print('Left checkerboard:')
    # print_freq_info(t_list_left)
    # print()
    # print('Right checkerboard:')
    # print_freq_info(t_list_right)
    # print('Mean render time:    ', np.array(render_time_list).mean())
    # print('Render variance:     ', np.var(np.array(render_time_list)))
    # print('Mean idleFunc time:  ', np.array(idleFunc_time_list).mean())
    # print('Idle variance:       ', np.var(np.array(idleFunc_time_list)))
    # print()
    # print('Mean idleFunc call time:', np.array(np.diff(idleFunc_call_list).mean()))
    # print('Mean idleFunc call frequency:', 1.0 / np.array(np.diff(idleFunc_call_list).mean()))
    frameTime = np.array(np.diff(render_time_list)).mean()
    print('Mean frame time: ', frameTime)
    print('Mean FPS:        ', 1.0/frameTime)

    #glut.glutLeaveMainLoop()
    sys.exit()

# set global objects needed for presentation
def initialize_presentation():
    global CB_cycle_left
    global CB_cycle_right
    global CB_left
    global CB_right
    global dtLeft  # period of left checkerboard
    global dtRight  # period of right checkerboard
    global tLeft  # time since left board rendered
    global tRight  # time since right board rendered
    global t0  # initial time
    global t_list_left
    global t_list_right
    global screen_limits
    global xTranslateLeft
    global xTranslateRight
    global yTranslate
    global esc_key
    global render_time_list
    global idleFunc_time_list
    global idleFunc_call_list

    # create checkerboards
    cb1 = pl.CheckerBoard(1, color1 = [1.0, 1.0, 1.0], color2 = [0.0, 0.0, 0.0], width = 0.5)
    cb2 = pl.CheckerBoard(1, color1 = [0.0, 0.0, 0.0], color2 = [1.0, 1.0, 1.0], width = 0.5)
    CB_cycle_left = itertools.cycle((cb2, cb1))
    CB_cycle_right = itertools.cycle((cb2, cb1))
    CB_left = CB_cycle_left.next()
    CB_right = CB_cycle_right.next()

    # get time variables
    dtLeft = 1.0/flash_rate_left
    dtRight = 1.0/flash_rate_right
    tLeft = tRight = t0 = time.time()  # time since last change (CB_cycle_left, CB_cycle_right), start time
    t_list_left = []
    t_list_right = []
    render_time_list = []
    idleFunc_time_list = []
    idleFunc_call_list = []

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
    glut.glutIdleFunc(presentation)     # set idle function to be called in the absence of other events
    #glut.glutTimerFunc(0, presentation, 0)
    #glut.GLUT_ACTION_ON_WINDOW_CLOSE = glut.GLUT_ACTION_CONTINUE_EXECUTION
    glut.glutFullScreen()       # put window in full screen
    glut.glutMainLoop()     # enter main events processing loop
