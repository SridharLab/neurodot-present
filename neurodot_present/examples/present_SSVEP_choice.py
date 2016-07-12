import pygame
import sys
import random
import itertools

import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, FixationCross, TextDisplay, DoubleCheckerBoardFlasher, UserEscape, run_start_sequence, run_stop_sequence

pl.DEBUG = False

if __name__ == "__main__":
    #ensure that video mode is at the maxium FPS
    if sys.platform.startswith("linux"):
        from subprocess import call
        call(["xrandr","-r","144"])

    pygame.init()
    pygame.mouse.set_visible(False)

    NUM_TRIALS   = 20
    FLASH_RATES  = [19,23] #Hz
    VSYNC_VALUES = [1,2,3]
    # BLOCKS       = 3
    # REPITITIONS  = 3
    CHECKERBOARD_NROWS = 16
    CUE_DURATION   = 2
    FLASH_DURATION = 10 #seconds
    PAUSE_DURATION_RANGE = (2.0,5.0)

    FC = FixationCross()

    TD = TextDisplay()
    TD.setup_textDisplay(screen_bgColor = 'neutral-gray',)

    #note only make one instance of a Screen object or else memory requirements will be high
    # use setup functions to change the display parameters during experiment
    DCBF = DoubleCheckerBoardFlasher()

    pauseScreen = Screen(color = "neutral-gray", fixation_cross = FC)

    flash_rates_cycle = itertools.cycle([(FLASH_RATES[0],FLASH_RATES[1],1),(FLASH_RATES[1],FLASH_RATES[0],3)])

    trial_conditions = []
    for i in range(NUM_TRIALS//2):
        rateL, rateR, vsync_value_base = flash_rates_cycle.next()
        trial_conditions.append(("L",rateL, rateR, vsync_value_base))
        trial_conditions.append(("R",rateL, rateR, vsync_value_base + 1))

    #randomize the trials
    random.shuffle(trial_conditions)

    try:
        #start sequence
        run_start_sequence()

        for side, rateL, rateR, vsync_value in trial_conditions:
            DCBF.setup_checkerboards(nrows = CHECKERBOARD_NROWS,
                                     width = 2.0 / 64.0,
                                     flash_rate_left = rateL,
                                     flash_rate_right = rateR,
                                    show_fixation_dot = False,
                                    )

            TD.run(text_content = side, duration = CUE_DURATION)
            DCBF.run(duration = FLASH_DURATION, vsync_value = vsync_value)
            pause_duration = random.uniform(*PAUSE_DURATION_RANGE)
            pauseScreen.run(duration = pause_duration, vsync_value = 0)

    except UserEscape as exc:
        print exc
    finally:
        #stop sequence
        run_stop_sequence()

    pygame.quit()
    sys.exit()
