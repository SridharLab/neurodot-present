# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu


#local imports
from common import DEBUG, COLORS, SCREEN_LB, SCREEN_LT, SCREEN_RB, SCREEN_RT
from common import Quad, UserEscape

from vsync_patch import VsyncPatch
from fixation_cross import FixationCross


class Screen:
    @classmethod
    def with_pygame_display(cls,
                            display_mode = None,
                            constrain_aspect = True,
                            debug = DEBUG
                           ):
        import pygame
        #start up pygame
        pygame.init()
        if display_mode is None:
            #default to first mode
            display_mode = pygame.display.list_modes()[0]
        w,h = display_mode
        fullscreen_flag_value = pygame.FULLSCREEN
        if debug:  #do in window while debugging
            fullscreen_flag_value = 0
        surf = pygame.display.set_mode(display_mode,
                                       pygame.OPENGL
                                       | pygame.DOUBLEBUF
                                       | pygame.HWSURFACE
                                       | fullscreen_flag_value
                                      )
        
        return cls(width = w,
                   height = h,
                   constrain_aspect = constrain_aspect,
                   display_surface = surf,
                   run_mode = 'pygame',
                  )
        
    def __init__(self,
                 width,
                 height,
                 constrain_aspect = True,
                 display_surface = None,
                 run_mode = None,
                 ):


        self.screen_width  = width
        self.screen_height = height
       
        aspect_ratio = float(width)/height
        left, right, bottom, top = (SCREEN_LT[0],SCREEN_RB[0],SCREEN_RB[1],SCREEN_LT[1])
        if constrain_aspect:  # Set the aspect ratio of the plot so that it is not distorted
            if width <= height:
                aspect_ratio = float(height)/width
                bottom /= aspect_ratio
                top    /= aspect_ratio
            else:
                left   *= aspect_ratio
                right  *= aspect_ratio
        
        self.screen_left   = left
        self.screen_right  = right
        self.screen_bottom = bottom
        self.screen_top    = top
        self.screen_corner_vertices = np.array(((left , top),
                                                (left , bottom),
                                                (right, bottom),
                                                (right, top),
                                               ))
        self.display_surface = display_surface
        self.run_mode = run_mode
        
    def setup(self,
              color = "black",
              vsync_patch  = "bottom-right",
              fixation_cross = None,
             ):
        #configure the display perspective
        # Fill the entire graphics window!
        gl.glViewport(0, 0, self.screen_width, self.screen_height)
        # Set the projection matrix... our "view"
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        #project to a 2D perspective
        glu.gluOrtho2D(self.screen_left, self.screen_right, self.screen_bottom, self.screen_top)
        
        self.color = COLORS.get(color, color)
        r,g,b = self.color
        gl.glClearColor(r,g,b,1.0)
        
        if vsync_patch == "bottom-right":
            #define the vsync patch as being in the bottom right corner
            self.vsync_patch = VsyncPatch.make_bottom_right(screen_bottom = self.screen_bottom,
                                                            screen_right  = self.screen_right)
        else:
            self.vsync_patch = vsync_patch
        
        self.fixation_cross = fixation_cross
        
    def render(self):
        #prepare rendering model
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        #self.screen_quad.render()
        if not self.fixation_cross is None:
            self.fixation_cross.render()
        #render the vsync patch
        if not self.vsync_patch is None:
            self.vsync_patch.render(value = self.vsync_value)
            
    def start_time(self, t):
        self.t0 = t

    def update(self, t, dt):
        #for the simple Screen class there is notthing to update
        pass

    def run(self, run_mode = None, **kwargs):
        #check to see if run mode default was determined
        if run_mode is None:
            run_mode = self.run_mode
    
        if run_mode is None:
            raise ValueError("no run_mode was specified, try instantiating Screen object from classmethod Screen.with_pygame_display")
        elif run_mode == "pygame":
            self.pygame_display_loop(**kwargs)
        else:
            raise ValueError("run_mode = '%s' is not valid" % run_mode)
           
    def pygame_display_loop(self,
                            duration = 5,
                            display_loop_rate = 60,
                            vsync_value = None,
                            wait_on_user_escape = False,
                            mask_user_escape    = False,
                           ):
        import pygame

        if not vsync_value is None:
            vsync_value = int(vsync_value)
            assert( 0 <= vsync_value <= 16)
            self.vsync_value = vsync_value
            
        clock = pygame.time.Clock()
        t  = pygame.time.get_ticks()/1e3 #convert milliseconds to seconds
        is_running = True
        self.start_time(t)
        while is_running:
            #render the scene to the buffer
            self.render()
            #show the scene
            pygame.display.flip()
            #handle outstanding events
            is_running = self.pygame_handle_events(mask_user_escape = mask_user_escape)
            dt = clock.tick_busy_loop(display_loop_rate)/1e3 #more accurate than tick, but uses more CPU resources
            t = pygame.time.get_ticks()/1e3 #convert milliseconds to seconds
            if t - self.t0 > duration:
                is_running = False
            #update the scene model
            self.update(t, dt)
        #now wait until the user presses escape
        if wait_on_user_escape:
            is_waiting = True
            try:
                while is_waiting:
                    is_waiting = self.pygame_handle_events(mask_user_escape = False) #ignore mask request which would get you stuck in FULLSCREEN!
            except UserEscape:# as exc:
                pass

    def pygame_handle_events(self, mask_user_escape = False):
        import pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_ESCAPE) and (not mask_user_escape):
                    raise UserEscape
        return True
        
        
def run_start_sequence(fixation_cross = None):
    if fixation_cross is None:
        fixation_cross = FixationCross()
    #instantiate screens
    black_SCR = Screen.with_pygame_display()
    black_SCR.setup(color = "black",fixation_cross = fixation_cross)
    green_SCR = Screen.with_pygame_display()
    green_SCR.setup(color = "green",fixation_cross = fixation_cross)
    #run sequence
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    green_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)  #begins the start frame
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    black_SCR.run(duration = 1, vsync_value = 5, mask_user_escape = True)  #starts the recording
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)

def run_stop_sequence(fixation_cross = None):
    #instantiate screens
    black_SCR = Screen.with_pygame_display()
    black_SCR.setup(color = "black", fixation_cross = fixation_cross)
    red_SCR   = Screen.with_pygame_display()
    red_SCR.setup(color = "red", fixation_cross = fixation_cross)
    #run sequence
    black_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    red_SCR.run(duration = 0, vsync_value = 5, wait_on_user_escape = True)
    
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    S = Screen.with_pygame_display()
    S.setup(color = "blue")
    S.run(duration = 1, vsync_value = 13)
    run_start_sequence()
    run_stop_sequence()
    
