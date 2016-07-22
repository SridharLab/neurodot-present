# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import pygame
import OpenGL.GL as gl
import OpenGL.GLU as glu
import numpy as np
import itertools
import fractions
import copy

from . import resources


DEBUG = False

COLORS = {
    'black'   : (0.0,0.0,0.0),
    'red'     : (1.0,0.0,0.0),
    'green'   : (0.0,1.0,0.0),
    'blue'    : (0.0,0.0,1.0),
    'cyan'    : (0.0,1.0,1.0),
    'magenta' : (1.0,0.0,1.0),
    'yellow'  : (1.0,1.0,0.0),
    'white'   : (1.0,1.0,1.0),
    'neutral-gray': (0.75,0.75,0.75)
}

SCREEN_LT = np.array((-1.0, 1.0))
SCREEN_LB = np.array((-1.0,-1.0))
SCREEN_RB = np.array(( 1.0,-1.0))
SCREEN_RT = np.array(( 1.0, 1.0))

LARGE_WIDTH = 0.5 #fraction of total screen length

VSYNC_PATCH_WIDTH_DEFAULT  = 0.225
VSYNC_PATCH_HEIGHT_DEFAULT = 0.225

DEFAULT_FLASH_RATE = 17 #Hz


def bell(blocking=False):
    pygame.mixer.init()
    bell_sound = pygame.mixer.Sound(resources.get_bellpath("bell.wav"))
    ch = bell_sound.play()
    if blocking:
        while ch.get_busy():
            pygame.time.delay(100)

class UserEscape(Exception):
    def __init__(self, msg = "User stopped the sequence"):
        Exception.__init__(self, msg)

class Quad:
    def __init__(self, lt, lb, rb, rt, color = COLORS['white']):
        self.vertices = np.array((lt,lb,rb,rt))
        self.color = color
    def render(self):
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_LIGHTING)
        try:
            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(*self.color)
            for v in self.vertices:
                gl.glVertex2f(*tuple(v))
            gl.glEnd()
        finally:
            gl.glEnable(gl.GL_LIGHTING)

class FixationCross:
    def __init__(self,
                 position = (0,0),
                 size      = 0.1,
                 thickness = 0.01,
                 color = 'white',
                 ):
        self.position = position
        self.size  = size
        self.thickness = thickness
        self.color = COLORS[color]
        self.vertices = [#horizontal beam
                         (position[0] - size/2.0, position[1] + thickness/2),  #left-top
                         (position[0] - size/2.0, position[1] - thickness/2),  #left-bottom
                         (position[0] + size/2.0, position[1] - thickness/2),  #right-bottom
                         (position[0] + size/2.0, position[1] + thickness/2),  #right-top
                         #vertical beam
                         (position[0] - thickness/2, position[1] + size/2.0),  #left-top
                         (position[0] - thickness/2, position[1] - size/2.0),  #left-bottom
                         (position[0] + thickness/2, position[1] - size/2.0),  #right-bottom
                         (position[0] + thickness/2, position[1] + size/2.0),  #right-top
                        ]

    def render(self):
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

class Sprite:
    def __init__(self):
        pass

    # functions for converting between coordinate systems
    def cart2pol(self, x, y):
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        return(r, theta)

    def pol2cart(self, r, theta):
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        return(x, y)

    def update():
        raise NotImplementedError("update method must be overridden in Sprite subclass")

    def render():
        raise NotImplementedError("render method must be overridden in Sprite subclass")

class AnimatedFixationCross(Sprite):
    def __init__(self,
                 use_polar_coords = False,
                 position_initial = [0,0],
                 velocity = None,
                 position_final = None,
                 movement_duration = 1,  # time to move from position_initial to position_final, seconds
                 dt_threshold = 0.001,  # shortest allowed time between updates and between renders
                 size      = 0.1,
                 thickness = 0.01,
                 color = 'white',
                 ):
        Sprite.__init__(self)
        self.use_polar_coords = use_polar_coords
        self.position_initial = position_initial
        self.position_final = position_final
        self.movement_duration = movement_duration
        self.dt_threshold = dt_threshold
        self.size = size
        self.thickness = thickness
        self.color = COLORS[color]

        # check if velocity was specified or if it must be calculated from initial and final positions
        if not velocity == None:
            self.velocity = velocity

        elif not position_final == None:
            self.position_diff = np.array(np.subtract(position_final, position_initial)) # difference vector between initial and final positions
            self.velocity = self.position_diff / movement_duration

        else:
            raise AttributeError('Must specify either velocity or position_final of AnimatedFixationCross')

        self.reset()

    # reset initial values
    def reset(self):
        self.position_current = copy.deepcopy(self.position_initial)
        self.time_since_update = None
        self.time_since_render = None
        self.has_rendered = False # this keeps track of if render() has been called

    # update render position (velocity is vector in OpenGL style coorinates/timestep)
    def update(self, time = 0, velocity = None):

        # if update() has not been run, set time_since_update to current time
        if self.time_since_update == None:
            self.time_since_update = time

        # get length of time between this and last update() call
        deltaT = time - self.time_since_update

        # option to set different velocity value at update() call
        if not velocity == None:
            self.velocity = velocity

        size = self.size
        thickness = self.thickness
        position = self.position_current
        position[0] = position[0] + self.velocity[0] * deltaT
        position[1] = position[1] + self.velocity[1] * deltaT
        self.position_current = copy.deepcopy(position)

        if self.use_polar_coords:
            position[0], position[1] = self.pol2cart(position[0], position[1])

        self.vertices = [#horizontal beam
                         (position[0] - size/2.0, position[1] + thickness/2),  #left-top
                         (position[0] - size/2.0, position[1] - thickness/2),  #left-bottom
                         (position[0] + size/2.0, position[1] - thickness/2),  #right-bottom
                         (position[0] + size/2.0, position[1] + thickness/2),  #right-top
                         #vertical beam
                         (position[0] - thickness/2, position[1] + size/2.0),  #left-top
                         (position[0] - thickness/2, position[1] - size/2.0),  #left-bottom
                         (position[0] + thickness/2, position[1] - size/2.0),  #right-bottom
                         (position[0] + thickness/2, position[1] + size/2.0),  #right-top
                         ]
        self.time_since_update = time  # set time_since_update to current time

    def render(self, time = 0):

        # if render() has not been run, set time_since_render so that method will run
        if self.time_since_render == None:
            self.time_since_render = time + self.dt_threshold

        # only run update method if dt_threshold has been exceeded
        if time - self.time_since_render >= self.dt_threshold:
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
            self.time_since_render = time

class VsyncPatch:
    def __init__(self, left, bottom, width, height,
                 on_color  = COLORS['white'],
                 off_color = COLORS['black'],
                 ):
        self.vertices = np.array(((left      , bottom),
                                  (left+width, bottom),           #right bottom
                                  (left+width, bottom + height),  #right top
                                  (left      , bottom + height),  #left  top
                                  ))
        self.left   = left
        self.bottom = bottom
        self.width  = width
        self.height = height
        self.on_color  = on_color
        self.off_color = off_color

    def compute_bit_colors(self, value):
        bit_colors = []
        if value & 0b0001:  #bit0,  also the vsync trigger bit
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if value & 0b0010:  #bit1
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if value & 0b0100:  #bit2
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if value & 0b1000:  #bit3
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        return bit_colors

    def render(self, value):
        left, bottom, width, height = (self.left,self.bottom,self.width,self.height)
        bit_colors = self.compute_bit_colors(value)
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_LIGHTING)

        try:
            #bit 0, sub square at bottom/right corner, also the vsync trigger bit
            gl.glColor3f(*bit_colors[0])
            gl.glRectf(left + width/2.0, bottom,  left + width, bottom + height/2.0) #left,bottom -> right,top
            #bit 1, sub square at bottom/left corner
            gl.glColor3f(*bit_colors[1])
            gl.glRectf(left, bottom,left + width/2.0, bottom + height/2.0) #left,bottom -> right,top
            #bit 2, sub square at top/left corner
            gl.glColor3f(*bit_colors[2])
            gl.glRectf(left, bottom + height/2.0,left + width/2.0, bottom + height) #left,bottom -> right,top
            #bit 3, sub square at top/right corner
            gl.glColor3f(*bit_colors[3])
            gl.glRectf(left + width/2.0, bottom + height/2.0,left + width, bottom + height) #left,bottom -> right,top
        finally:
            gl.glEnable(gl.GL_LIGHTING)

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
        #print("Before set_mode")
        self.display_surface = pygame.display.set_mode(display_mode,
                                                       pygame.OPENGL
                                                       | pygame.DOUBLEBUF
                                                       | pygame.HWSURFACE
                                                       | fullscreen_flag_value,
                                                       #| pygame.NOFRAME
                                                       #8 #bits per pixel
                                                      )
        self.display_mode = display_mode
        #print("After set_mode")
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

class AnimatedScreen(Screen):
    def __init__(self,
                 color = "white",
                 display_mode = None,
                 vsync_patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                 vsync_patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                 constrain_aspect = True,
                 **kwargs
                 ):
        Screen.__init__(self,
                        color = color,
                        display_mode = display_mode,
                        constrain_aspect = constrain_aspect,
                        vsync_patch_width  = vsync_patch_width,
                        vsync_patch_height = vsync_patch_height,
                       )
        self.setup_AnimatedScreen(**kwargs)

    # sprite_obj must inherit from Sprite
    def setup_AnimatedScreen(self, sprite_list, screen_bgColor = "white", fixation_cross = None, vsync_value = 0):

        self.fixation_cross = fixation_cross
        self.vsync_value = vsync_value
        self.vsync_value = vsync_value
        self.screen_bgColor = COLORS[screen_bgColor]
        self.sprite_list = sprite_list

    def run(self,
            duration = None,
            vsync_value = 0,
            wait_on_user_escape = False,
            mask_user_escape = False,
            ):

        # duration param can be used to set a minimum run time (though sprites will not move after their movement duration is up)
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
            gl.glClearColor(self.screen_bgColor[0], self.screen_bgColor[1], self.screen_bgColor[2], 1.0)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            # call update() and render() for sprites, get render flags
            render_flags = []
            for sprite in self.sprite_list:

                sprite.has_rendered = False # reset sprite's render flag
                if t - t0 < sprite.movement_duration:

                    sprite.update(time = t)  # update sprite's coordinates
                    sprite.render(time = t)  # attempt to render sprite
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
            is_running = self.handle_events(mask_user_escape = mask_user_escape)

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

def run_start_sequence(fixation_cross = None, **kwargs):
    if fixation_cross is None:
        fixation_cross = FixationCross()
    #instantiate screens
    black_SCR = Screen(color = "black",fixation_cross = fixation_cross, **kwargs)
    green_SCR = Screen(color = "green",fixation_cross = fixation_cross, **kwargs)
    #run sequence
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    green_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)  #begins the start frame
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    black_SCR.run(duration = 1, vsync_value = 5, mask_user_escape = True)  #starts the recording
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)

def run_stop_sequence(fixation_cross = None, **kwargs):
    #instantiate screens
    black_SCR = Screen(color = "black", fixation_cross = fixation_cross, **kwargs)
    red_SCR = Screen(color = "red", fixation_cross = fixation_cross, **kwargs)
    #run sequence
    black_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    red_SCR.run(duration = 0, vsync_value = 5, wait_on_user_escape = True)

class CheckerBoard:
    def __init__(self,
                 nrows,
                 width = 1.0,
                 height = None,
                 color1 = COLORS['white'],
                 color2 = COLORS['black'],
                 show_fixation_dot = False
                 ):
        self.nrows = int(nrows)
        self.width = width
        if height is None:
            height = width
        self.height = height
        self.color1 = color1
        self.color2 = color2
        self.show_fixation_dot = show_fixation_dot

        # flag for checking if render method has been called (and OpenGl display list created)
        self.has_rendered = False

    def render(self):

        # create openGL list if render has not yet been called
        if not self.has_rendered:
            w = self.width
            h = self.height
            color1 = self.color1
            color2 = self.color2
            board_width = w * self.nrows
            board_height = h * self.nrows
            #gl.glDisable(gl.GL_LIGHTING)

            self.glListIndex = gl.glGenLists(1)
            gl.glNewList(self.glListIndex, gl.GL_COMPILE) # begin OpengGL list
            try:
                for x in range(0, self.nrows):
                    for y in range(0, self.nrows):
                        if (x + y) % 2 == 0:
                            gl.glColor3f(*color1)
                        else:
                            gl.glColor3f(*color2)
                        gl.glRectf(w*x, h*y, w*(x + 1), h*(y + 1))

                if self.show_fixation_dot:
                    gl.glColor3f(*COLORS['red'])
                    gl.glTranslatef(board_width / 2.0, board_height / 2.0, 0)
                    glu.gluDisk(glu.gluNewQuadric(), 0, 0.005, 45, 1)

            finally:
                pass
                #gl.glEnable(gl.GL_LIGHTING)
            gl.glEndList()  # end OpenGL list
            self.has_rendered = True

        # display checkerboard
        gl.glDisable(gl.GL_LIGHTING)
        gl.glCallList(self.glListIndex)
        gl.glEnable(gl.GL_LIGHTING)

    def __del__(self):
        gl.glDeleteLists(self.glListIndex, 1)

class CheckerBoardFlasher(Screen):
    def __init__(self,
                 display_mode = None,
                 flash_rate = DEFAULT_FLASH_RATE,
                 vsync_patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                 vsync_patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                 constrain_aspect = True,
                 ):
        Screen.__init__(self,
                        color = "black",
                        display_mode = display_mode,
                        constrain_aspect = constrain_aspect,
                        vsync_patch_width  = vsync_patch_width,
                        vsync_patch_height = vsync_patch_height,
                       )
        self.flash_rate = flash_rate


    def setup_checkerboard(self,
                           nrows,
                           width = None,
                           color1 = 'white',
                           color2 = 'black',
                           screen_bgColor = 'neutral-gray',
                           show_fixation_dot = False,
                           vsync_value = None
                           ):
        #run colors through filter to catch names and convert to RGB
        color1 = COLORS.get(color1, color1)
        color2 = COLORS.get(color2, color2)
        if width is None:
            width = 2.0/nrows #fill whole screen
        self.board_width = width*nrows
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows,width, color1 = color1, color2 = color2, show_fixation_dot = show_fixation_dot)
        self.CB2 = CheckerBoard(nrows,width, color1 = color2, color2 = color1, show_fixation_dot = show_fixation_dot) #reversed pattern
        self.screen_bgColor = COLORS[screen_bgColor]
        self.vsync_value = vsync_value

    def run(self, duration = 5, vsync_value = None):
        duration *= 1e3 #convert to milliseconds

        #white/black alterning for intermediate signals
        CB_cycle = itertools.cycle((self.CB1,self.CB2))

        if vsync_value is None and not self.vsync_value is None:
            vsync_value = self.vsync_value
        elif vsync_value is None:
            vsync_value = 1

        #set background color
        gl.glClearColor(self.screen_bgColor[0], self.screen_bgColor[1], self.screen_bgColor[2], 1.0)

        t0 = pygame.time.get_ticks()
        t  = pygame.time.get_ticks()
        CB = CB_cycle.next()
        is_running = True
        while is_running:
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
            #move so that board is center and render
            gl.glTranslatef(-0.5*self.board_width,-0.5*self.board_width,0.0)
            CB.render()
            #render the vsync patch
            self.vsync_patch.render(value = vsync_value)
            #show the scene
            pygame.display.flip()
            #handle outstanding events
            is_running = self.handle_events()
            if self.flash_rate > 0:
                dt = self.clock.tick_busy_loop(self.flash_rate) #more accurate than tick, but uses more CPU resources
                CB = CB_cycle.next()
            else:
                dt = self.clock.tick_busy_loop(self.render_loop_rate) #more accurate than tick, but uses more CPU resources
            t  = pygame.time.get_ticks()
            if t - t0 > duration:
                is_running = False

class DoubleCheckerBoardFlasher(Screen):
    def __init__(self,
                 display_mode = None,
                 flash_rate_left  = DEFAULT_FLASH_RATE,
                 flash_rate_right = DEFAULT_FLASH_RATE,
                 vsync_patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                 vsync_patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                 constrain_aspect = True,
                 flash_rate_util = None,
                 ):
        Screen.__init__(self,
                        color = "black",
                        display_mode = display_mode,
                        constrain_aspect = constrain_aspect,
                        vsync_patch_width  = vsync_patch_width,
                        vsync_patch_height = vsync_patch_height,
                       )
        self.flash_rate_left  = flash_rate_left
        self.flash_rate_right = flash_rate_right

        # check if util_flash_rate was specified: if so, single-check checkerboard will be displayed in center for verifying
        # frequency with vysnc device
        if not flash_rate_util == None:
            self.show_vsync_freq_util = True
            self.flash_rate_util = flash_rate_util
        else:
            self.show_vsync_freq_util = False

    def setup_checkerboards(self,
                           nrows,
                           width = 2.0 / 64.0,  # width of checks for 64x64 full screen board
                           color1 = 'white',
                           color2 = 'black',
                           screen_bgColor = 'neutral-gray',
                           show_fixation_dot = False,
                           vsync_value = None,
                           flash_rate_left = None,
                           flash_rate_right = None,
                           rate_compensation = None,
                           ):
        #run colors through filter to catch names and convert to RGB
        color1 = COLORS.get(color1, color1)
        color2 = COLORS.get(color2, color2)

        # if width is None:
        #     width = 2.0/nrows #fill whole screen
        self.board_width = width*nrows
        self.nrows = nrows

        # create checkerboard objects
        self.CB1 = CheckerBoard(nrows, width, color1 = color1, color2 = color2, show_fixation_dot = show_fixation_dot)
        self.CB2 = CheckerBoard(nrows, width, color1 = color2, color2 = color1, show_fixation_dot = show_fixation_dot) #reversed pattern
        self.CB3 = CheckerBoard(nrows, width, color1 = color1, color2 = color2, show_fixation_dot = show_fixation_dot)
        self.CB4 = CheckerBoard(nrows, width, color1 = color2, color2 = color1, show_fixation_dot = show_fixation_dot) # reversed

        # create frequency test utility checkerboard objects if needed
        if self.show_vsync_freq_util:
            self.utilCB1 = CheckerBoard(1, self.board_width, color1 = color1, color2 = color2)
            self.utilCB2 = CheckerBoard(1, self.board_width, color1 = color2, color2 = color1)

        # setup some values
        self.screen_bgColor = COLORS[screen_bgColor]
        self.vsync_value = vsync_value
        if not flash_rate_left is None:
            self.flash_rate_left  = flash_rate_left
        if not flash_rate_right is None:
            self.flash_rate_right = flash_rate_right

        self.rate_compensation = rate_compensation

        # setup coordinate values for two checkerboards
        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)
        self.xL, self.yL = (self.xC - 0.5*self.screen_right, self.yC)
        self.xR, self.yR = (self.xC + 0.5*self.screen_right, self.yC)

    def run(self, duration = 5, flash_rate_left = None, flash_rate_right = None, vsync_value = None):
        # do things for utility checkerboard if needed
        if self.show_vsync_freq_util:
            utilCB_cycle = itertools.cycle((self.utilCB1,self.utilCB2))
            utilCB = utilCB_cycle.next()
            dtUtil = 1.0 / self.flash_rate_util
            tU = time.time()

        #white/black alterning for intermediate signals
        leftCB_cycle = itertools.cycle((self.CB1,self.CB2))
        rightCB_cycle = itertools.cycle((self.CB3,self.CB4))

        # get flash rates if not specified
        if flash_rate_left is None:
            flash_rate_left = self.flash_rate_left
        if flash_rate_right is None:
            flash_rate_right = self.flash_rate_right

        #apply compenstation if specified
        if not self.rate_compensation is None:
            flash_rate_left  += self.rate_compensation
            flash_rate_right += self.rate_compensation

        # get vysnc value
        if vsync_value is None and not self.vsync_value is None:
            vsync_value = self.vsync_value
        elif vsync_value is None:
            vsync_value = 1

        #set background color
        gl.glClearColor(self.screen_bgColor[0], self.screen_bgColor[1], self.screen_bgColor[2], 1.0)

        # get particular vsync patch and leftCB/rightCB objects
        vsync_patch = self.vsync_patch
        leftCB = leftCB_cycle.next()
        rightCB = rightCB_cycle.next()

        is_running = True

        xL, yL = self.xL, self.yL # (xC - 0.5*self.screen_right, yC)
        xR, yR = self.xR, self.yR # (xC + 0.5*self.screen_right, yC)

        dtL = 1.0/flash_rate_left
        dtR = 1.0/flash_rate_right
        tL  = time.time() #time since last change
        tR  = time.time() #time since last change
        t0  = time.time()
        # t_list = []

        def render_routine():
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            #render the vsync patch
            vsync_patch.render(value = vsync_value)

            # translate to position of left board
            gl.glTranslatef(xL, yL, 0.0)
            leftCB.render()

            # translate to position of right board
            gl.glLoadIdentity()
            gl.glTranslatef(xR, yR, 0.0)
            rightCB.render()

            # render utility checkerboard if needed
            if self.show_vsync_freq_util:
                gl.glLoadIdentity()
                gl.glTranslatef(- self.board_width / 2.0, - self.board_width / 2.0, 0.0)
                utilCB.render()

            #show the scene
            pygame.display.flip()

        while is_running:
            #get fresh time
            t = time.time()
            if t > (tL + dtL):
                leftCB = leftCB_cycle.next()
                tL  = t #update change time
                render_routine()
            if t > (tR + dtR):
                rightCB = rightCB_cycle.next()
                tR  = t #update change time
                render_routine()

            # render check for utility checkerboard
            if self.show_vsync_freq_util and t > (tU + dtUtil):
                utilCB = utilCB_cycle.next()
                tU = t # update change time
                render_routine()

            # t_list.append(t)  #this is for measuring the loop delay
            #handle outstanding events
            is_running = self.handle_events()
            #print t, t0, duration
            if t - t0 > duration:
                is_running = False

        #-----------------------------------------------------------------------
        #this is for measuring the loop delay
        # import numpy as np
        # print("mean loop dt:", np.array(np.diff(t_list).mean()))
        # print("Frequency (Hz):", 1.0 / np.array(np.diff(t_list).mean()))

class TextDisplay(Screen):
    def __init__(self,
                 display_mode = None,
                 vsync_patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                 vsync_patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                 constrain_aspect = True,
                 **kwargs
                 ):
        Screen.__init__(self,
                        color = "white",
                        display_mode = display_mode,
                        constrain_aspect = constrain_aspect,
                        vsync_patch_width  = vsync_patch_width,
                        vsync_patch_height = vsync_patch_height,
                       )
        self.setup_textDisplay(**kwargs) #setup TextDisplay instance with kwargs or default parameters

    def setup_textDisplay(self,
                           text_content = "DEFAULT",
                           text_color = 'black',
                           text_bgColor = None,
                           font_size = 288,
                           font_type = None,
                           screen_bgColor = 'white',
                           vsync_value = 0,
                           ):
        #if text_bgColor is unspecified, set to same as background color (renders faster than using alpha)
        if text_bgColor == None:
            text_bgColor = screen_bgColor

        self.vsync_value = vsync_value
        self.screen_bgColor = COLORS[screen_bgColor]
        self.text_content = text_content
        self.text_color = COLORS[text_color]
        self.text_bgColor = COLORS[text_bgColor]
        self.font_size = font_size
        self.font_type = font_type

        self.textSurface = self.render_surface(self.text_content, self.font_size)

    def render_surface(self, text_content, font_size):

        # get file path for font file if it was specified
        if self.font_type is None:
            font_path = self.font_type
        else:
            font_path = resources.get_fontpath(self.font_type)

        #render textSurface from text_content
        self.font = pygame.font.Font(font_path, font_size)
        self.textSurface = self.font.render(text_content, 1, \
            [int(self.text_color[0]*255), int(self.text_color[1]*255), int(self.text_color[2]*255)], \
            [int(self.text_bgColor[0]*255), int(self.text_bgColor[1]*255), int(self.text_bgColor[2]*255)])

        #Scaling font; attempting to render text that is too wide/tall sets the raster position off screen and nothing is rendered
        if self.textSurface.get_width() > self.screen_width:
            percent_scale = float(self.screen_width) / self.textSurface.get_width()
            self.font = pygame.font.Font(font_path, int(font_size * percent_scale))
            self.textSurface = self.font.render(text_content, 1, \
                [int(self.text_color[0]*255), int(self.text_color[1]*255), int(self.text_color[2]*255)], \
                [int(self.text_bgColor[0]*255), int(self.text_bgColor[1]*255), int(self.text_bgColor[2]*255)])
            print("WARNING (TextDisplay): '", text_content, "' is too wide for screen; scaling to fit")

        if self.textSurface.get_height() > self.screen_height:
            percent_scale = float(self.screen_height) / self.textSurface.get_height()
            self.font = pygame.font.Font(font_path, int(font_size * percent_scale))
            self.textSurface = self.font.render(text_content, 1, \
                [int(self.text_color[0]*255), int(self.text_color[1]*255), int(self.text_color[2]*255)], \
                [int(self.text_bgColor[0]*255), int(self.text_bgColor[1]*255), int(self.text_bgColor[2]*255)])
            print("WARNING (TextDisplay): '", text_content, "' is too tall for screen; scaling to fit")

        return self.textSurface

    def run(self, text_content = None, duration = 5, vsync_value = None, scale_refObj = None):
        if not text_content is None:
            self.text_content = text_content
        if vsync_value is None:
            vsync_value = self.vsync_value

        duration *= 1e3 #convert to milliseconds

        t0 = pygame.time.get_ticks()
        t  = pygame.time.get_ticks()
        is_running = True

        #render textSurface
        self.textSurface = self.render_surface(self.text_content, self.font_size)

        # check if we are scaling size to match other TextDisplay obj's last run() and scale textSurface if needed
        if not scale_refObj is None:
            ref_surface = scale_refObj.render_surface(scale_refObj.text_content, scale_refObj.font_size)
            width_scale = float(ref_surface.get_width()) / float(self.textSurface.get_width())
            height_scale = float(ref_surface.get_height()) / float(self.textSurface.get_height())
            self.textSurface = pygame.transform.scale(self.textSurface, (int(width_scale * self.textSurface.get_width()), int(height_scale * self.textSurface.get_height())))

        #set background color
        gl.glClearColor(self.screen_bgColor[0], self.screen_bgColor[1], self.screen_bgColor[2], 1.0)

        #prepare some values for rendering centered text
        centerOffset_pixels = [-self.textSurface.get_width()/2, -self.textSurface.get_height()/2]
        raster_position = self.get_coords(*centerOffset_pixels)
        textData = pygame.image.tostring(self.textSurface, "RGBA", True)

        while is_running:
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            #render text
            gl.glRasterPos2d(*raster_position)
            gl.glDrawPixels(self.textSurface.get_width(), self.textSurface.get_height(), gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, textData)

            #render the vsync patch
            self.vsync_patch.render(value = vsync_value)

            #show the scene
            pygame.display.flip()

            #handle outstanding events
            is_running = self.handle_events()

            dt = self.clock.tick_busy_loop(self.render_loop_rate) #more accurate than tick, but uses more CPU resources
            t  = pygame.time.get_ticks()

            if t - t0 > duration:
                is_running = False

    def get_coords(self, xPos, yPos): #xPos, yPos in pixels with origin at center of screen
        xPos = self.screen_right * (float(xPos) / (self.screen_width/2))
        yPos = self.screen_top * (float(yPos) / (self.screen_height/2))
        return [xPos, yPos]



