# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu

#local imports
from common import DEBUG, COLORS, cart2pol, pol2cart
from sprites import Sprite


################################################################################
#-------------------------------------------------------------------------------
class AnimatedFixationCross(Sprite):
    def __init__(self,
                 size      = 0.1,
                 thickness = 0.01,
                 color = 'white',
                 **kwargs
                 ):
        Sprite.__init__(self, **kwargs)
        self.size = size
        self.thickness = thickness
        self.color = COLORS.get(color,color)

    
    def update(self, t = 0, v = None):
        """ update render position (velocity is vector in OpenGL style coorinates/timestep)"""
        # if update() has not been run, set time_since_update to current time
        Sprite.update(self, t = t, v = v)
        
        p1, p2 = self.position_current
        if self.use_polar_coords:
            x, y = pol2cart(p1, p2)
        else:
            x, y = (p1,p2)
        sz = self.size
        th = self.thickness
        self.vertices = [#horizontal beam
                         (x - sz/2.0, y + th/2),  #left-top
                         (x - sz/2.0, y - th/2),  #left-bottom
                         (x + sz/2.0, y - th/2),  #right-bottom
                         (x + sz/2.0, y + th/2),  #right-top
                         #vertical beam
                         (x - th/2, y + sz/2.0),  #left-top
                         (x - th/2, y - sz/2.0),  #left-bottom
                         (x + th/2, y - sz/2.0),  #right-bottom
                         (x + th/2, y + sz/2.0),  #right-top
                         ]
        self.t_since_update = t  # set time_since_update to current time

    def render(self, t = 0):
        # if render() has not been run, set time_since_render so that method will run
        if self.t_since_render == None:
            self.t_since_render = t + self.dt_threshold
        # only run update method if dt_threshold has been exceeded
        if t - self.t_since_render >= self.dt_threshold:
            gl.glLoadIdentity()
            gl.glDisable(gl.GL_LIGHTING)
            try:
                gl.glBegin(gl.GL_QUADS)
                gl.glColor3f(*self.color)
                for v in self.vertices:
                    gl.glVertex2f(*v)
                gl.glEnd()
            finally:
                gl.glEnable(gl.GL_LIGHTING)

            self.has_rendered = True
            self.t_since_render = t

################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    import sys
    import pygame
    from common import DEBUG, UserEscape
    from screen import Screen
    from animated_screen import AnimatedScreen
    from numpy import pi
    
    pygame.init()
    pygame.mouse.set_visible(False)

    try:
        # using polar coordinates and specified velocity
        aFC_left = AnimatedFixationCross(use_polar_coords = True,
                                         position_initial = [-0.5, 0],
                                         velocity = [0, -pi],
                                         movement_duration = 8,
                                         color = 'black'
                                        )
        aFC_right = AnimatedFixationCross(use_polar_coords = True,
                                          position_initial = [0.5, 0],
                                          velocity = [0, -pi],
                                          movement_duration = 8,
                                          color = 'blue'
                                         )

        # using cartesian coordinates and specified final position instead of velocity
        aFC_line_left = AnimatedFixationCross(use_polar_coords = False,
                                              position_initial = [-0.5, 0],
                                              position_final = [0.5, 0],
                                              movement_duration = 8,
                                              color = 'green'
                                             )

        # using cartesian coordinates and specified velocity
        aFC_line_right = AnimatedFixationCross(use_polar_coords = False,
                                               position_initial = [0.5, 0],
                                               velocity = [-1.0/8.0, 0],
                                               movement_duration = 8,
                                               color = 'green'
                                              )

        #configure an aminated screen to run the demos
        sprite_list = [aFC_left,
                       aFC_right,
                       aFC_line_left,
                       aFC_line_right
                      ]
        aSCR = AnimatedScreen.with_pygame_display()
        aSCR.setup(sprite_list = sprite_list,
                   background_color = 'white',
                  )

        aSCR.run(duration = 10)

    except UserEscape as exc:
        print(exc)

    pygame.quit()
    sys.exit()
