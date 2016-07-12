import pygame
import sys
import random

import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, FixationCross, DoubleCheckerBoardFlasher, UserEscape, run_start_sequence, run_stop_sequence, bell, TextDisplay

pl.DEBUG = False

if __name__ == "__main__":

    pygame.init()
    pygame.mouse.set_visible(False)

    FLASH_RATES_LEFT  = [3,19, 5] #[16,19,23] #Hz
    FLASH_RATES_RIGHT = [3, 5,19] #[11,27,17]
    VSYNC_VALUES =      [1, 2, 3]
    BLOCKS       = 3
    REPITITIONS  = 3
    CHECKERBOARD_NROWS = 16
    FLASH_DURATION = 10       #seconds
    PAUSE_DURATION_RANGE = (1.0,5.0)

    CBF = DoubleCheckerBoardFlasher()
    CBF.setup_checkerboards(nrows = CHECKERBOARD_NROWS, show_fixation_dot = False, width = 2.0 / 32.0)#width = 2.0 / 64.0)#width = 1.0/CHECKERBOARD_NROWS)
    text = TextDisplay(font_type = 'Arial.ttf', screen_bgColor = 'neutral-gray')

    FC_center = FixationCross(color = 'black')
    FC_left = FixationCross(color = 'black', position = (CBF.xL + 0.5*CBF.board_width, 0.0))
    FC_right = FixationCross(color = 'black', position = (CBF.xR + 0.5*CBF.board_width, 0.0))

    SCR_rest = Screen(color = 'neutral-gray', fixation_cross = FC_center)
    SCR_left = Screen(color = 'neutral-gray', fixation_cross = FC_left)
    SCR_right = Screen(color = 'neutral-gray', fixation_cross = FC_right)

    stimAttrs = zip(FLASH_RATES_LEFT, FLASH_RATES_RIGHT, VSYNC_VALUES)

    try:
        #start sequence
        run_start_sequence()

        while BLOCKS > 0:
            # get reversal rates and vsync values for this block
            random.shuffle(stimAttrs)
            FRs_left = zip(*stimAttrs)[0]
            FRs_right = zip(*stimAttrs)[1]
            base_vsync_vals = zip(*stimAttrs)[2]

            for r in range(0, REPITITIONS):
                # choose left or right
                if random.choice([True, False]):
                    SCR = SCR_left
                    vsync_vals = base_vsync_vals
                    text_content = "LEFT"
                else:
                    SCR = SCR_right
                    vsync_vals = [v + len(base_vsync_vals) for v in base_vsync_vals]  # modify vsync values to show we are looking right
                    text_content = "RIGHT"

                text.run(text_content = text_content, duration = 1)
                pause_duration = random.uniform(*PAUSE_DURATION_RANGE)
                SCR.run(duration = pause_duration, vsync_value = 0)
                CBF.run(duration = FLASH_DURATION, flash_rate_left = FRs_left[r], flash_rate_right = FRs_right[r], vsync_value = vsync_vals[r])

            BLOCKS -= 1
            if not BLOCKS == 0:
                bell()
                SCR_rest.run(duration = 8, vsync_value = 0)
                bell()
                SCR_rest.run(duration = random.uniform(1.0,2.0), vsync_value = 0)

    except UserEscape as exc:
        print exc
    finally:
        #stop sequence
        run_stop_sequence()

    pygame.quit()
    sys.exit()