import pygame, sys
import itertools
import time
import OpenGL.GL as gl

import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, CheckerBoard, UserEscape, VsyncPatch

pl.DEBUG = False
################################################################################
if __name__ == "__main__":

    pygame.init()
    pygame.mouse.set_visible(True)

    DURATION = 120
    flash_rate = 19  # Hz

    scr = Screen()
    vsync_patch = VsyncPatch(left   = scr.screen_right - pl.VSYNC_PATCH_WIDTH_DEFAULT,
                                      bottom = scr.screen_bottom,
                                      width  = pl.VSYNC_PATCH_WIDTH_DEFAULT,
                                      height = pl.VSYNC_PATCH_HEIGHT_DEFAULT
                                     )
    cb1 = CheckerBoard(1, color1 = [1.0, 1.0, 1.0], color2 = [0.0, 0.0, 0.0], width = 0.5)
    cb2 = CheckerBoard(1, color1 = [0.0, 0.0, 0.0], color2 = [1.0, 1.0, 1.0], width = 0.5)
    CB_cycle = itertools.cycle((cb2, cb1))
    vvals_cycle = itertools.cycle((0, 15))

    try:
        is_running = True

        vsync_value = vvals_cycle.next()
        CB = CB_cycle.next()

        board_width = CB.width * CB.nrows

        dtc = 1.0/flash_rate
        tc  = time.time() #time since last change
        t0 = time.time()
        # t_list = []

        while is_running:
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            #get fresh time
            t = time.time()
            if t > (tc + dtc):
                vsync_value = vvals_cycle.next()
                CB = CB_cycle.next()
                tc  = t #update change time

            # render vsync patch
            vsync_patch.render(value = vsync_value)

            # translate to position of board and render
            gl.glTranslatef(-board_width / 2.0, -board_width / 2.0, 0.0)
            CB.render()

            #show the scene
            pygame.display.flip()

            # t_list.append(t)  #this is for measuring the loop delay

            #handle outstanding events
            is_running = scr.handle_events()
            #print t, t0, duration
            if t - t0 > DURATION:
                is_running = False
        #-----------------------------------------------------------------------
        #this is for measuring the loop delay
        # import numpy as np
        # print "mean loop dt:", np.array(np.diff(t_list).mean())

    except UserEscape as exc:
        print exc
    finally:
        pass
    #exit
    pygame.quit()
    sys.exit()

