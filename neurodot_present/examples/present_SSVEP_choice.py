import pygame
import sys
import random

import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, FixationCross, DoubleCheckerBoardFlasher, UserEscape, run_start_sequence, run_stop_sequence

pl.DEBUG = False

if __name__ == "__main__":
    #ensure that video mode is at the maxium FPS
    if sys.platform.startswith("linux"):
        from subprocess import call
        call(["xrandr","-r","144"])

    pygame.init()

    FLASH_RATES  = [5,23] #Hz
    VSYNC_VALUES = [1,2,3]
    # BLOCKS       = 3
    # REPITITIONS  = 3
    CHECKERBOARD_NROWS = 16
    FLASH_DURATION = 10       #seconds
    PAUSE_DURATION_RANGE = (2.0,5.0)

    FC = FixationCross()

    try:
        #start sequence
        run_start_sequence()

        CBF = DoubleCheckerBoardFlasher(flash_rate_left=FLASH_RATES[0], flash_rate_right=FLASH_RATES[1])
        CBF.setup_checkerboards(nrows = CHECKERBOARD_NROWS, width = 2.0 / 64.0)#width = 1.0/CHECKERBOARD_NROWS)
        CBF.run(duration = FLASH_DURATION, vsync_value = VSYNC_VALUES[1])

        SCR = Screen(color = "black", fixation_cross = FC)
        pause_duration = random.uniform(*PAUSE_DURATION_RANGE)
        SCR.run(duration = pause_duration, vsync_value = 0)

    except UserEscape as exc:
        print exc
    finally:
        #stop sequence
        run_stop_sequence()

    pygame.quit()
    sys.exit()
