import pygame
import sys
import random
import itertools

#import neurodot_present.present_lib as pl
import neurodot_present.common as common
import neurodot_present.screen as screen
from neurodot_present.common import UserEscape, load_gamma_calibration
from neurodot_present.triple_checkerboard_sin_flasher import TripleCheckerBoardSinFlasher
from neurodot_present.screen import Screen
from neurodot_present.fixation_cross import FixationCross
from subprocess import call


common.DEBUG = False

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
    NUM_TRIALS   = 40
    REST_EVERY   = 10  # user will be given a 10 second break after this many trials (unless experiment is over)
    FLASH_RATES  = [19,23] # Hz
    CHECKERBOARD_NROWS = 32
    CHECK_WIDTH    = 0.5/CHECKERBOARD_NROWS
    PAUSE_DURATION = 1
    CUE_DURATION   = 1
    FLASH_DURATION = 5  # seconds
    
    #inv_gamma_func = load_gamma_calibration(monitor_name = "benq-gamer1", interp_kind = "cubic")
    #c = float(inv_gamma_func(0.5))
    c = 0.5
    inv_gamma_func = None
    NEUTRAL_GRAY =(c,c,c)




    try:
        # ensure that video mode is at the maxium FPS
        system_set_resolution(refresh_rate  = "144")

        # initialize pygame
        pygame.init()

        # hide mouse
        pygame.mouse.set_visible(False)

        # instiantiate checkerboard flasher
        DCBF = TripleCheckerBoardSinFlasher.with_pygame_display()
        DCBF.setup(nrows = CHECKERBOARD_NROWS,
                   check_width = CHECK_WIDTH,
                   
                   ) # running setup just to get coordinates for FCs

        # instantiate fixation crosses
        FC_center = FixationCross(color = 'black')
        FC_left = FixationCross(color = 'black',
                                position = (DCBF.xL + DCBF.board_width / 2.0, DCBF.yL + DCBF.board_width / 2.0)
                                )
        FC_right = FixationCross(color = 'black',
                                 position = (DCBF.xR + DCBF.board_width / 2.0, DCBF.yR + DCBF.board_width / 2.0)
                                 )

        # instantiate Screens
        pauseScreen = Screen.with_pygame_display()
        cueScreen = Screen.with_pygame_display()
        restScreen = Screen.with_pygame_display()
        flash_rates_cycle = itertools.cycle([(FLASH_RATES[0],FLASH_RATES[1],1),(FLASH_RATES[1],FLASH_RATES[0],3)])

        # get trial conditions
        trial_conditions = []
        for i in range(NUM_TRIALS//2):
            rateL, rateR, vsync_value_base = flash_rates_cycle.next()
            trial_conditions.append((FC_left, rateL, rateR, vsync_value_base))
            trial_conditions.append((FC_right, rateL, rateR, vsync_value_base + 1))

        #randomize the trials
        random.shuffle(trial_conditions)

        #start sequence
        screen.run_start_sequence()

        # begin experiment with centered fixation cross
        pauseScreen.setup(background_color = NEUTRAL_GRAY,
                          fixation_cross = FC_center,
                          )
        pauseScreen.run(duration = PAUSE_DURATION, vsync_value = 0)

        # get conditions for each trial and run
        trial_counter = 0
        for FC, rateL, rateR, vsync_value in trial_conditions:
            # setup DCBF and cue with new conditions
            DCBF.setup(nrows = CHECKERBOARD_NROWS,
                       check_width = CHECK_WIDTH,
                       flash_rate_left = rateL,
                       flash_rate_right = rateR,
                       flash_rate_center = None,
                       show_fixation_dot = True,
                       inv_gamma_func = inv_gamma_func
                      )
            cueScreen.setup(background_color = NEUTRAL_GRAY,
                            fixation_cross = FC
                            )

            # run cue and DCBF
            cueScreen.run(duration = CUE_DURATION, vsync_value = 0)
            DCBF.run(duration = FLASH_DURATION, vsync_value = vsync_value)

            # check if subjects get a rest
            trial_counter += 1
            if trial_counter%REST_EVERY == 0 and not trial_counter == NUM_TRIALS:
                common.bell()
                restScreen.setup(background_color = NEUTRAL_GRAY)
                restScreen.run(duration = 8, vsync_value = 0)
                common.bell()
                restScreen.run(duration = 2, vsync_value = 0)

            # display centered fixation cross to start next trial
            pauseScreen.run(duration = PAUSE_DURATION, vsync_value = 0)

    except UserEscape as exc:
        print exc

    except:
        raise

    finally:
        #stop sequence
        screen.run_stop_sequence()
        pygame.quit()

    sys.exit()

