import pygame
import sys
from math import pi

import neurodot_present.present_lib as pl

pl.DEBUG = False

if __name__ == "__main__":

    pygame.init()
    pygame.mouse.set_visible(False)

    try:

        FC = pl.FixationCross(color = 'black')

        # using polar coordinates and specified velocity
        aFC_left = pl.AnimatedFixationCross(use_polar_coords = True,
                                       position_initial = [-0.5, 0],
                                       velocity = [0, -pi],
                                       movement_duration = 8,
                                       color = 'black'
                                       )
        aFC_right = pl.AnimatedFixationCross(use_polar_coords = True,
                                       position_initial = [0.5, 0],
                                       velocity = [0, -pi],
                                       movement_duration = 8,
                                       color = 'blue'
                                       )

        # using cartesian coordinates and specified final position instead of velocity
        aFC_line_left = pl.AnimatedFixationCross(use_polar_coords = False,
                                       position_initial = [-0.5, 0],
                                       position_final = [0.5, 0],
                                       movement_duration = 8,
                                       color = 'green'
                                       )

        # using cartesian coordinates and specified velocity
        aFC_line_right = pl.AnimatedFixationCross(use_polar_coords = False,
                                       position_initial = [0.5, 0],
                                       velocity = [-1.0/8.0, 0],
                                       movement_duration = 8,
                                       color = 'green'
                                       )

        scr = pl.Screen(color = 'white', fixation_cross = FC)
        aSCR = pl.AnimatedScreen(screen_bgColor = 'white', constrain_aspect = True, sprite_list = [aFC_left, aFC_right, aFC_line_left, aFC_line_right])

        scr.run(duration = 2)
        aSCR.run(duration = 10)

    except pl.UserEscape as exc:
        print exc

    pygame.quit()
    sys.exit()