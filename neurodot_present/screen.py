# -*- coding: utf-8 -*-
from __future__ import print_function

import time

import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import pygame

#local imports
from common import DEBUG, COLORS, VSYNC_PATCH_HEIGHT_DEFAULT, VSYNC_PATCH_WIDTH_DEFAULT, SCREEN_LB, SCREEN_LT, SCREEN_RB, SCREEN_RT
from common import UserEscape

from vsync_patch import VsyncPatch

class Screen:
    def __init__(self,
                 color = 'black',
                 display_mode = None,
                 constrain_aspect = True,
                 vsync_patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                 vsync_patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                 fixation_cross = None,
                 render_loop_rate = 70,
                 ):


        self.color = COLORS.get(color, color)
        self.fixation_cross = fixation_cross

        #start up pygame
        pygame.init()
        if display_mode is None:
            #default to first mode
            display_mode = pygame.display.list_modes()[0]
        w,h = display_mode
        self.screen_width  = w
        self.screen_height = h
        fullscreen_flag_value = pygame.FULLSCREEN
        if DEBUG:  #do in window while debugging
            fullscreen_flag_value = 0
        self.display_surface = pygame.display.set_mode(display_mode,
                                                       pygame.OPENGL
                                                       | pygame.DOUBLEBUF
                                                       | pygame.HWSURFACE
                                                       | fullscreen_flag_value
                                                      )
        #configure the display perspective
        # Fill the entire graphics window!
        gl.glViewport(0, 0, w, h)
        # Set the projection matrix... our "view"
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect_ratio = float(w)/h
        left, right, bottom, top = (SCREEN_LT[0],SCREEN_RB[0],SCREEN_RB[1],SCREEN_LT[1])
        if constrain_aspect:  # Set the aspect ratio of the plot so that it is not distorted
            if w <= h:
                bottom /= aspect_ratio
                top    /= aspect_ratio
            else:
                aspect_ratio = float(w)/h
                #left, right, bottom, top
                left   *= aspect_ratio
                right  *= aspect_ratio
        glu.gluOrtho2D(left, right, bottom, top)
        self.screen_left   = left
        self.screen_right  = right
        self.screen_bottom = bottom
        self.screen_top    = top
        self.screen_corner_vertices = np.array(((left , top),
                                                (left , bottom),
                                                (right, bottom),
                                                (right, top),
                                               ))

        #define the vsync patch as being in the bottom right corner
        self.vsync_patch = VsyncPatch(left   = self.screen_right - vsync_patch_width,
                                      bottom = self.screen_bottom,
                                      width  = vsync_patch_width,
                                      height = vsync_patch_height
                                     )


        self.render_loop_rate = render_loop_rate
        self.clock = pygame.time.Clock()

    def run(self,
            duration = 5,
            vsync_value = 0,
            wait_on_user_escape = False,
            mask_user_escape = False,
           ):
        duration *= 1e3 #convert to milliseconds

        scv = self.screen_corner_vertices
        screen_quad = Quad(scv[0],scv[1],scv[2],scv[3], color = self.color)
        t0 = pygame.time.get_ticks()
        t  = pygame.time.get_ticks()

        is_running = True
        while is_running:
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
            #move so that board is center and render
            #glTranslatef(-0.5*self.board_width,-0.5*self.board_width,0.0)
            screen_quad.render()
            if not self.fixation_cross is None:
                self.fixation_cross.render()
            #render the vsync patch
            self.vsync_patch.render(value = vsync_value)
            #show the scene
            pygame.display.flip()
            #handle outstanding events
            is_running = self.handle_events(mask_user_escape = mask_user_escape)
            dt = self.clock.tick_busy_loop(self.render_loop_rate) #more accurate than tick, but uses more CPU resources
            t  = pygame.time.get_ticks()
            if t - t0 > duration:
                is_running = False
        #now wait until the user presses escape
        if wait_on_user_escape:
            is_waiting = True
            try:
                while is_waiting:
                    is_waiting = self.handle_events(mask_user_escape = False) #ignore mask request which would get you stuck in FULLSCREEN!
            except UserEscape:# as exc:
                pass

    def handle_events(self, mask_user_escape = False):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_ESCAPE) and (not mask_user_escape):
                    raise UserEscape
        return True
