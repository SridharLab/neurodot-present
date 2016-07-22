import pygame
import sys
import random
import itertools

import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, FixationCross, TextDisplay, DoubleCheckerBoardFlasher, UserEscape, run_start_sequence, run_stop_sequence
from subprocess import call

pl.DEBUG = False

RETURN_SCREEN_SIZE = "1920x1200"
#RETURN_REFRESH_RATE = 60
SCREEN_SIZE = "800x600"
REFRESH_RATE = 75

def system_set_resolution(screen_size  = None,
                          refresh_rate = None,
                         ):
    if sys.platform.startswith("linux"):
        cmd = ["xrandr"]
        if not screen_size is None:
            cmd.extend(["-s","%s" % screen_size])
        if not refresh_rate is None:
            cmd.extend(["-r","%s" % refresh_rate])
        call(cmd)

if __name__ == "__main__":
    NUM_TRIALS   = 2
    FLASH_RATES  = [19,23] #Hz
    VSYNC_VALUES = [1,2,3]
    # BLOCKS       = 3
    # REPITITIONS  = 3
    CHECKERBOARD_NROWS = 16
    CHECKERBOARD_SIZE  = 0.5/CHECKERBOARD_NROWS
    CUE_DURATION   = 2
    FLASH_DURATION = 20 #seconds
    PAUSE_DURATION_RANGE = (2.0,5.0)

    try:
        #ensure that video mode is at the maxium FPS
        #system_set_resolution(refresh_rate  = "144")

        pygame.init()

        # hide mouse
        pygame.mouse.set_visible(False)

        #get the smallest resolution window
        #display_mode = (1920, 1080)
        display_mode = pygame.display.list_modes()[-1] #(640,480), hopefully
        FC = FixationCross()

        #TD = TextDisplay(display_mode = display_mode)
        #TD.setup_textDisplay(screen_bgColor = 'neutral-gray')

        #note only make one instance of a Screen object or else memory requirements will be high
        # use setup functions to change the display parameters during experiment
        DCBF = DoubleCheckerBoardFlasher(display_mode = display_mode)
        pauseScreen = Screen(color = "neutral-gray", fixation_cross = FC, display_mode = display_mode)
        flash_rates_cycle = itertools.cycle([(FLASH_RATES[0],FLASH_RATES[1],1),(FLASH_RATES[1],FLASH_RATES[0],3)])

        trial_conditions = []
        for i in range(NUM_TRIALS//2):
            rateL, rateR, vsync_value_base = flash_rates_cycle.next()
            trial_conditions.append(("L",rateL, rateR, vsync_value_base))
            trial_conditions.append(("R",rateL, rateR, vsync_value_base + 1))

        #randomize the trials
        random.shuffle(trial_conditions)

        #start sequence
        run_start_sequence(display_mode = display_mode)

        for side, rateL, rateR, vsync_value in trial_conditions:
            DCBF.setup_checkerboards(nrows = CHECKERBOARD_NROWS,
                                     width = CHECKERBOARD_SIZE,
                                     flash_rate_left = rateL,
                                     flash_rate_right = rateR,
                                     #show_fixation_dot = True
                                    )

            #TD.run(text_content = side, duration = CUE_DURATION)
            DCBF.run(duration = FLASH_DURATION, vsync_value = vsync_value)
            pause_duration = random.uniform(*PAUSE_DURATION_RANGE)
            pauseScreen.run(duration = pause_duration, vsync_value = 0)

    except UserEscape as exc:
        print exc
    finally:
        #stop sequence
        run_stop_sequence(display_mode = display_mode)
        pygame.quit()
        #system_set_resolution(screen_size  = "1920x1200")

    sys.exit()
