import pygame, sys
import random
from neurodot_present.present_lib import Screen, FixationCross, CheckerBoardFlasher, bell, UserEscape, run_start_sequence, run_stop_sequence



pygame.init()

TASK_DURATION = 30  #seconds

FC = FixationCross()
try:
    #start sequence
    run_start_sequence()
    #setup task
    CBF = CheckerBoardFlasher(flash_rate=0) #no flashing
    CBF.setup_checkerboard(64)
    black_SCR = Screen(color = "black",fixation_cross = FC)
    #run sequence
    CBF.run(duration = TASK_DURATION, vsync_value = 1)
    black_SCR.run(duration = 1, vsync_value = 0)
    bell()
    black_SCR.run(duration = 5, vsync_value = 0)
    black_SCR.run(duration = TASK_DURATION, vsync_value = 2)
    black_SCR.run(duration = 1, vsync_value = 0)
    bell()
except UserEscape:
    print "User stopped the sequence"
except Exception, err:
    raise err
finally:
    #stop sequence
    run_stop_sequence()

pygame.quit()
sys.exit()
