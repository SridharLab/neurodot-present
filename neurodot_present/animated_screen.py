# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu


#local imports
from common import DEBUG, COLORS

from screen import Screen

class AnimatedScreen(Screen):
    def setup(self, sprite_list, **kwargs):
        """'sprite_list' is a sequence of neurodot_present.common.Sprite 
           class compatible objects
        """
        Screen.setup(self, **kwargs)
        self.sprite_list = sprite_list

    def run(self,
            duration = None,
            vsync_value = 0,
            wait_on_user_escape = False,
            mask_user_escape = False,
            ):
        """'duration' param can be used to set a minimum run time 
           (though sprites will not move after their movement duration is up)
        """
        import pygame
        
        if not duration == None:
            duration_list = [duration]
        else:
            duration_list = []

        # reset values to initials
        for sprite in self.sprite_list:
            sprite.reset()

        # get sprite duration times and set t0
        duration_list += [sprite.movement_duration for sprite in self.sprite_list]
        t0 = time.time()

        is_running = True
        while is_running:
            #get fresh time
            t = time.time()

            # clear screen
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            r,g,b = self.background_color
            gl.glClearColor(r,g,b,1.0)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            # call update() and render() for sprites, get render flags
            render_flags = []
            for sprite in self.sprite_list:

                sprite.has_rendered = False # reset sprite's render flag
                if t - t0 < sprite.movement_duration:

                    sprite.update(t = t)  # update sprite's coordinates
                    sprite.render(t= t)  # attempt to render sprite
                    render_flags.append(sprite.has_rendered) # get updated render flag

            # render fixation cross if it exists
            if not self.fixation_cross == None:
                self.fixation_cross.render()

            # flip display only if a sprite object has rendered
            if any(render_flags):
                # render vsync patch
                self.vsync_patch.render(value = vsync_value)
                pygame.display.flip()

            # handle outstanding events
            is_running = self.pygame_handle_events(mask_user_escape = mask_user_escape)

            # check if it has been long enough for duration param or maximum sprite movement_duration
            if t - t0 > max(duration_list):
                is_running = False

        if wait_on_user_escape:
            is_waiting = True
            try:
                while is_waiting:
                    is_waiting = self.handle_events(mask_user_escape = False) #ignore mask request which would get you stuck in FULLSCREEN!
            except UserEscape:
                pass
