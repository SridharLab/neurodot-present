# -*- coding: utf-8 -*-
from __future__ import print_function

import os, time
from collections import OrderedDict

import numpy as np

import OpenGL.GL as gl
import OpenGL.GLU as glu
import ctypes



#local imports
from common import SETTINGS,COLORS, SCREEN_LB, SCREEN_LT, SCREEN_RB, SCREEN_RT,\
                   Quad, UserEscape, write_frame_to_png, enable_VBI_sync_osx

from fixation_cross import FixationCross

#delay configurable class loading
import neurodot_present


class Screen:
    @classmethod
    def with_pygame_display(cls,
                            display_mode = None,
                            constrain_aspect = True,
                            debug = SETTINGS['debug'],
                            hide_mouse = True,
                            VBI_sync_osx = True,
                            use_joysticks = None,
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

        # hide mouse
        if hide_mouse:
            pygame.mouse.set_visible(False)

        # OSX: enable vsync/VBI sync/syncing frame buffer swaps to screen refresh
        if VBI_sync_osx:
            enable_VBI_sync_osx()

        return cls(width = w,
                   height = h,
                   constrain_aspect = constrain_aspect,
                   display_surface = surf,
                   run_mode = 'pygame_display',
                   use_joysticks = use_joysticks
                  )
    @classmethod
    def with_opengl_texture(cls,
                            debug = SETTINGS['debug'],
                           ):
        # see http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-14-render-to-texture/
        # The framebuffer, which regroups 0, 1, or more textures, and 0 or 1 depth buffer.
        FramebufferName = gl.GLuint(0)
        gl.glGenFramebuffers(1, ctypes.byref(FramebufferName))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, FramebufferName)

        # The texture we're going to render to
        renderedTexture = gl.GLuint(0)
        gl.glGenTextures(1, ctypes.byref(renderedTexture))

        # "Bind" the newly created texture : all future texture functions will modify this texture
        gl.glBindTexture(gl.GL_TEXTURE_2D, renderedTexture)

        # Give an empty image to OpenGL ( the last "0" )
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, 1024, 768, 0,gl.GL_RGB, gl.GL_UNSIGNED_BYTE, 0)

        # Poor filtering. Needed !
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

        # Set "renderedTexture" as our colour attachement #0
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, renderedTexture, 0);

        # Set the list of draw buffers.
        DrawBuffers = gl.GLenum * 1               #gl.GLenum DrawBuffers[1]
        DrawBuffers[0] = gl.GL_COLOR_ATTACHMENT0  #  = {gl.GL_COLOR_ATTACHMENT0};
        gl.glDrawBuffers(1, DrawBuffers); # "1" is the size of DrawBuffers


        return cls(width = w,
                   height = h,
                   constrain_aspect = constrain_aspect,
                   display_surface = surf,
                   run_mode = 'open_gltexture',
                  )

    @classmethod  # something isn't right with coordinates when you use a psychopy window
    def with_psychopy_window(cls,
                             display_mode = None,
                             constrain_aspect = True,
                             #debug = DEBUG,
                             hide_mouse = True,
                            ):
        import psychopy.visual
        import pygame
        window = psychopy.visual.Window(fullscr = True,
                                        winType = 'pygame',
                                        units = 'pix',
                                        waitBlanking = True,
                                        checkTiming = True,
                                       )
        if display_mode is None:
            #default to first mode
            display_mode = pygame.display.list_modes()[0]
        w, h = display_mode

        return cls(width = w,
                   height = h,
                   constrain_aspect = constrain_aspect,
                   display_surface = window,
                   run_mode = 'psychopy_window',
                  )

    def __init__(self,
                 width,
                 height,
                 constrain_aspect = True,
                 display_surface = None,
                 run_mode = None,
                 use_joysticks = None,
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

        #detect and initialize joysticks
        if use_joysticks:
            import pygame
            pygame.joystick.init()
            joystick_nums = []
            if use_joysticks is True: #initialize all possible joysticks
                joystick_nums = range(pygame.joystick.get_count())
            else:                     #assume we were given a sequence of ints
                joystick_nums = use_joysticks
            self.joysticks = OrderedDict()
            # For each joystick
            for i in joystick_nums:
                self.joysticks[i] = js = pygame.joystick.Joystick(i)
                js.init()

    def setup(self,
              background_color = "black",
              vsync_value  = None,
              vsync_patch  = "bottom-right",
              fixation_cross = None,
              exit_keys = None,
             ):

        self.background_color = COLORS.get(background_color, background_color)

        self.vsync_value = vsync_value
        if vsync_patch == "bottom-right":
            VsyncPatch = neurodot_present.get_class_VsyncPatch()
            #define the vsync patch as being in the bottom right corner
            self.vsync_patch = VsyncPatch.make_bottom_right(screen_bottom = self.screen_bottom,
                                                            screen_right  = self.screen_right)
        else:
            self.vsync_patch = vsync_patch
        self.fixation_cross = fixation_cross
        self.exit_value = None
        if exit_keys is None:
            exit_keys = []
        self.exit_keys = exit_keys
        
    def start_rendering(self):
        #gl.glShadeModel(gl.GL_SMOOTH)
        r,g,b = self.background_color
        gl.glClearColor(r,g,b,1.0)
        gl.glClearDepth(1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT )
        gl.glHint(gl.GL_PERSPECTIVE_CORRECTION_HINT, gl.GL_NICEST)
        gl.glDisable(gl.GL_DEPTH_TEST)

        #configure the display perspective
        # Fill the entire graphics window!
        gl.glViewport(0, 0, self.screen_width, self.screen_height)
        # Set the projection matrix... our "view"
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        #project to a 2D perspective
        glu.gluOrtho2D(self.screen_left, self.screen_right, self.screen_bottom, self.screen_top)
        self.ready_to_render = True
        
    def render_before(self):
        #prepare rendering model
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_TEXTURE_2D)
            
    def render_after(self):
        if not self.fixation_cross is None:
            self.fixation_cross.render()
        #render the vsync patch
        if not self.vsync_patch is None:
            #print("vsync_patch.render: %s" % self.vsync_value)
            self.vsync_patch.render()

    def render(self):
        self.render_before()
        self.render_after()

    def start_time(self, t):
        self.t0 = t
        self.vsync_patch.start_time(t, vsync_value = self.vsync_value)

    def update(self, t, dt):
        self.vsync_patch.update(t,dt)
    
        # ensure rendering and display flipping will occur
        self.ready_to_render = True

    def run(self, run_mode = None, **kwargs):
        #check to see if run mode default was determined
        if run_mode is None:
            run_mode = self.run_mode

        if run_mode is None:
            raise ValueError("no run_mode was specified, try instantiating Screen object from classmethod Screen.with_pygame_display")
        elif run_mode == "pygame_display":
            self.pygame_display_loop(**kwargs)
        elif run_mode == "psychopy_window":
            self.psychopy_display_loop(**kwargs)
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
        #print("pygame_display_loop: vsync_value: %s" % vsync_value)
        #error check any passed vsync_values
        if not vsync_value is None:
            vsync_value = int(vsync_value)
            assert( 0 <= vsync_value <= 16)
            self.vsync_value = vsync_value

        clock = pygame.time.Clock()
        t      = time.time()
        last_t = t
        is_running = True
        self.start_time(t)
        self.start_rendering()
        #render the scene to the buffer
        self.render()
        while is_running:
            t = time.time()
            dt = t - last_t
            #dt = clock.tick_busy_loop(display_loop_rate)/1e3 #more accurate than tick, but uses more CPU resources
            #t = pygame.time.get_ticks()/1e3 #convert milliseconds to seconds
            #print(t,dt)

            #update the scene model
            self.update(t, dt)

            if self.ready_to_render:
                #render the scene to the buffer
                self.render()
                #show the scene
                pygame.display.flip()
                #gl.glFinish()

            #handle outstanding events
            is_running = self.pygame_handle_events(mask_user_escape = mask_user_escape)
            if t - self.t0 > duration and not duration is None:
                is_running = False
            #update last time
            last_t = t

        #now wait until the user presses escape
        if wait_on_user_escape:
            is_waiting = True
            try:
                while is_waiting:
                    is_waiting = self.pygame_handle_events(mask_user_escape = False) #ignore mask request which would get you stuck in FULLSCREEN!
            except UserEscape:# as exc:
                pass

    def pygame_recording_loop(self,
                              duration = 5,
                              frame_rate = 60,
                              vsync_value = None,
                              recording_name = "screen",
                              show = False,
                            ):
        import pygame

        #error check any passed vsync_values
        if not vsync_value is None:
            vsync_value = int(vsync_value)
            assert( 0 <= vsync_value <= 16)
        self.vsync_value = vsync_value

        w, h = (self.screen_width, self.screen_height)
        t  = 0.0
        dt = 1.0/frame_rate
        is_running = True
        frame_num  = 0
        total_frames = frame_rate*duration
        self.start_time(t)
        #render the scene to the buffer
        self.render()
        progress_dt = 10.0
        realtime0 = time.time()
        progress_time_last = realtime0
        while is_running:
            realtime = time.time()
            if (realtime - progress_time_last) > progress_dt:
                progress_time_last = realtime
                percent_complete = 100*float(frame_num)/total_frames
                print("%d%% complete (%d s)" % (percent_complete, realtime - realtime0))
            #record the scene
            pixel_data = gl.glReadPixels(0,0,w,h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
            write_frame_to_png("frame", frame_num, w, h, data = pixel_data, outdir=recording_name)
            #show the scene
            if show:
                pygame.display.flip()
            #generate time step
            t += dt
            #handle outstanding events
            is_running = self.pygame_handle_events()
            if t - self.t0 > duration and not duration is None:
                is_running = False
            #update the scene model
            self.update(t, dt)
            #render the scene to the buffer
            self.render()
            frame_num += 1

    def psychopy_display_loop(self,
                            duration = 5,
                            display_loop_rate = 60,
                            vsync_value = None,
                            wait_on_user_escape = False,
                            mask_user_escape    = False,
                           ):

        #error check any passed vsync_values
        if not vsync_value is None:
            vsync_value = int(vsync_value)
            assert( 0 <= vsync_value <= 16)
        self.vsync_value = vsync_value

        t      = time.time()
        last_t = t
        is_running = True
        self.start_time(t)

        #render the scene to the buffer
        self.render()
        while is_running:
            t = time.time()
            dt = t - last_t
            #dt = clock.tick_busy_loop(display_loop_rate)/1e3 #more accurate than tick, but uses more CPU resources
            #t = pygame.time.get_ticks()/1e3 #convert milliseconds to seconds
            #print(t,dt)

            #update the scene model
            self.update(t, dt)

            if self.ready_to_render:
                pass
                #render the scene to the buffer
            self.render()
                #show the scene
            self.display_surface.flip()

            #handle outstanding events
            is_running = self.pygame_handle_events(mask_user_escape = mask_user_escape)
            if t - self.t0 > duration and not duration is None:
                is_running = False
            #update last time
            last_t = t

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
                for key in self.exit_keys:
                    if (event.key == key):
                        self.exit_value = event.key
                        return False
        return True


def run_start_sequence(fixation_cross = None,
                       default_screen_color = "black",
                       start_screen_color = "green",
                       background_color = "neutral-gray",
                       **kwargs):
    if fixation_cross is None:
        fixation_cross = FixationCross()
    #instantiate screens
    default_SCR = Screen.with_pygame_display(**kwargs)
    default_SCR.setup(background_color = background_color,fixation_cross = fixation_cross)
    start_SCR = Screen.with_pygame_display(**kwargs)
    start_SCR.setup(background_color = start_screen_color,fixation_cross = fixation_cross)
    #run sequence
    default_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    start_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)  #begins the start frame
    default_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    default_SCR.run(duration = 1, vsync_value = 5, mask_user_escape = True)  #starts the recording
    default_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)

def run_stop_sequence(fixation_cross = None, 
                      default_screen_color = "black",
                      stop_screen_color = "red",
                      background_color = "neutral-gray",
                      **kwargs):
    #instantiate screens
    default_SCR = Screen.with_pygame_display(**kwargs)
    default_SCR.setup(background_color = background_color, fixation_cross = fixation_cross)
    stop_SCR   = Screen.with_pygame_display(**kwargs)
    stop_SCR.setup(background_color = stop_screen_color, fixation_cross = fixation_cross)
    #run sequence
    default_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)
    default_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    stop_SCR.run(duration = 1, vsync_value = 5, mask_user_escape = True)
    stop_SCR.run(duration = 0, vsync_value = 0, wait_on_user_escape = True)

################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    S = Screen.with_pygame_display()
    S.setup(background_color = "blue")
    S.run(duration = 1, vsync_value = 13)
    run_start_sequence()
    run_stop_sequence()

