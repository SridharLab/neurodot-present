import pygame, sys
import numpy as np
import itertools


import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, FixationCross, CheckerBoardFlasher, UserEscape, run_start_sequence, run_stop_sequence

pl.DEBUG = True
################################################################################
if __name__ == "__main__":
    import random
    
    pygame.init()

    FLASH_RATES  = [16,19,23] #Hz
    VSYNC_VALUES = [1,2,3]
    BLOCKS       = 3
    REPITITIONS  = 3
    CHECKERBOARD_NROWS = 64
    FLASH_DURATION = 2       #seconds
    PAUSE_DURATION_RANGE = (2.0,5.0)
    
    FC = FixationCross()
    
    try:
        #start sequence
        run_start_sequence()
        #trials
        for b in range(BLOCKS):
            stims = REPITITIONS*zip(FLASH_RATES, VSYNC_VALUES)
            random.shuffle(stims)
            for flash_rate, vsync_value in stims:
                CBF = CheckerBoardFlasher(flash_rate=flash_rate)
                CBF.setup_checkerboard(nrows = CHECKERBOARD_NROWS)
                CBF.run(duration = FLASH_DURATION, vsync_value = vsync_value)
                SCR = Screen(color = "black", fixation_cross = FC)
                pause_duration = random.uniform(*PAUSE_DURATION_RANGE)
                SCR.run(duration = pause_duration, vsync_value = 0)
    except UserEscape as exc:
        print exc
    finally:
        #stop sequence
        run_stop_sequence()
    #exit
    print "Exiting the presentation"
    pygame.quit()
    sys.exit()
