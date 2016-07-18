import pygame
import sys
import random
import time

import neurodot_present.present_lib as pl
from neurodot_present.present_lib import Screen, FixationCross, DoubleCheckerBoardFlasher, UserEscape, run_start_sequence, run_stop_sequence, bell, TextDisplay, AnimatedFixationCross, AnimatedScreen

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
    MOVEMENT_DURATION = 0.5
    FLASH_DURATION = 10       #seconds
    PAUSE_DURATION_RANGE = (3.0,4.0)

    CBF = DoubleCheckerBoardFlasher()
    CBF.setup_checkerboards(nrows = CHECKERBOARD_NROWS, show_fixation_dot = True, width = 2.0 / 32.0)#width = 2.0 / 64.0)#width = 1.0/CHECKERBOARD_NROWS)
    text = TextDisplay(font_type = 'Arial.ttf', screen_bgColor = 'neutral-gray')

    FC_center = FixationCross(color = 'black')
    FC_left = FixationCross(color = 'black', position = (CBF.xL + 0.5*CBF.board_width, 0.0))
    FC_right = FixationCross(color = 'black', position = (CBF.xR + 0.5*CBF.board_width, 0.0))
    aFC_left = AnimatedFixationCross(position_initial = [0,0],
                                     position_final = [CBF.xL + 0.5*CBF.board_width, 0.0],
                                     movement_duration = MOVEMENT_DURATION,
                                     color = 'black',
                                     dt_threshold = 0.0005,
                                     )
    aFC_right = AnimatedFixationCross(position_initial = [0,0],
                                      position_final = [CBF.xR + 0.5*CBF.board_width, 0.0],
                                      movement_duration = MOVEMENT_DURATION,
                                      color = 'black',
                                      dt_threshold = 0.0005,
                                      )

    SCR_rest = Screen(color = 'neutral-gray', fixation_cross = FC_center)
    SCR_left = Screen(color = 'neutral-gray', fixation_cross = FC_left)
    SCR_right = Screen(color = 'neutral-gray', fixation_cross = FC_right)
    aSCR_left = AnimatedScreen(screen_bgColor = 'neutral-gray', sprite_list = [aFC_left])
    aSCR_right = AnimatedScreen(screen_bgColor = 'neutral-gray', sprite_list = [aFC_right])
    aSCR_both = AnimatedScreen(screen_bgColor = 'neutral-gray', sprite_list = [aFC_left, aFC_right])

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
                    aSCR = aSCR_left
                    vsync_vals = base_vsync_vals
                    text_content = "L"
                else:
                    SCR = SCR_right
                    aSCR = aSCR_right
                    vsync_vals = [v + len(base_vsync_vals) for v in base_vsync_vals]  # modify vsync values to show we are looking right
                    text_content = "R"

                SCR_rest.run(duration = 1, vsync_value = 0)
                #text.run(text_content = text_content, duration = 0.5)

                pause_duration = random.uniform(*PAUSE_DURATION_RANGE)
                #aSCR.run(duration = pause_duration)

                t0 = time.time()
                aSCR_both.run(duration = 3)
                t1 = time.time()
                print "Animation duration:", t1 - t0

                CBF.run(duration = FLASH_DURATION, flash_rate_left = FRs_left[r], flash_rate_right = FRs_right[r], vsync_value = vsync_vals[r])
                print "Stimulus duration:", time.time() - t1

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