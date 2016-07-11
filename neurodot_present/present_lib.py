# -*- coding: utf-8 -*-
import pygame
import OpenGL.GL as gl
import OpenGL.GLU as glu
import numpy as np
import itertools

import resources

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

def run_start_sequence(fixation_cross = None):
    if fixation_cross is None:
        fixation_cross = FixationCross()
    #instantiate screens
    black_SCR = Screen(color = "black",fixation_cross = fixation_cross)
    green_SCR = Screen(color = "green",fixation_cross = fixation_cross)
    #run sequence
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    green_SCR.run(duration = 1, vsync_value = 13, mask_user_escape = True)  #begins the start frame
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)
    black_SCR.run(duration = 1, vsync_value = 5, mask_user_escape = True)  #starts the recording
    black_SCR.run(duration = 1, vsync_value = 0, mask_user_escape = True)

def run_stop_sequence(fixation_cross = None):
    #instantiate screens
    black_SCR = Screen(color = "black", fixation_cross = fixation_cross)
    red_SCR = Screen(color = "red", fixation_cross = fixation_cross)
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
                 color2 = COLORS['black']
                 ):
        self.nrows = int(nrows)
        self.width = width
        if height is None:
            height = width
        self.height = height
        self.color1 = color1
        self.color2 = color2

    def render(self):
        w = self.width
        h = self.height
        color1 = self.color1
        color2 = self.color2
        gl.glDisable(gl.GL_LIGHTING)
        try:
            for x in range(0, self.nrows):
                for y in range(0, self.nrows):
                    if (x + y) % 2 == 0:
                        gl.glColor3f(*color1)
                    else:
                        gl.glColor3f(*color2)
                    gl.glRectf(w*x, h*y, w*(x + 1), h*(y + 1))
        finally:
            gl.glEnable(gl.GL_LIGHTING)

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
                           vsync_value = None
                           ):
        #run colors through filter to catch names and convert to RGB
        color1 = COLORS.get(color1, color1)
        color2 = COLORS.get(color2, color2)
        if width is None:
            width = 2.0/nrows #fill whole screen
        self.board_width = width*nrows
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows,width, color1 = color1, color2 = color2)
        self.CB2 = CheckerBoard(nrows,width, color1 = color2, color2 = color1) #reversed pattern
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
                 flash_rate_left = DEFAULT_FLASH_RATE,
                 flash_rate_right = DEFAULT_FLASH_RATE,
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
        self.flash_rate_left = flash_rate_left
        self.flash_rate_right = flash_rate_right

    def setup_checkerboards(self,
                           nrows,
                           width = 2.0 / 64.0,  # width of checks for 64x64 full screen board
                           color1 = 'white',
                           color2 = 'black',
                           screen_bgColor = 'neutral-gray',
                           vsync_value = None
                           ):
        #run colors through filter to catch names and convert to RGB
        color1 = COLORS.get(color1, color1)
        color2 = COLORS.get(color2, color2)
        # if width is None:
        #     width = 2.0/nrows #fill whole screen
        self.board_width = width*nrows
        self.nrows = nrows
        self.CB1 = CheckerBoard(nrows, width, color1 = color1, color2 = color2)
        self.CB2 = CheckerBoard(nrows, width, color1 = color2, color2 = color1) #reversed pattern
        self.CB3 = CheckerBoard(nrows, width, color1 = color1, color2 = color2)
        self.CB4 = CheckerBoard(nrows, width, color1 = color2, color2 = color1) # reversed
        self.screen_bgColor = COLORS[screen_bgColor]
        self.vsync_value = vsync_value

    def run(self, duration = 5, vsync_value = None):
        duration *= 1e3 #convert to milliseconds

        #white/black alterning for intermediate signals
        leftCB_cycle = itertools.cycle((self.CB1,self.CB2))
        rightCB_cycle = itertools.cycle((self.CB3,self.CB4))

        if vsync_value is None and not self.vsync_value is None:
            vsync_value = self.vsync_value
        elif vsync_value is None:
            vsync_value = 1

        #set background color
        gl.glClearColor(self.screen_bgColor[0], self.screen_bgColor[1], self.screen_bgColor[2], 1.0)

        t0 = pygame.time.get_ticks()
        t  = pygame.time.get_ticks()
        leftCB = leftCB_cycle.next()
        rightCB = rightCB_cycle.next()
        is_running = True

        loops = 0
        while is_running:
            #prepare rendering model
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            if loops % self.flash_rate_left == 0:
                leftCB = leftCB_cycle.next()

            if loops % self.flash_rate_right == 0:
                rightCB = rightCB_cycle.next()

            # translate left board to center and left, then render
            gl.glTranslatef(-0.5*self.board_width,-0.5*self.board_width,0.0)
            gl.glTranslatef(-0.5*self.screen_right, 0.0, 0.0)
            leftCB.render()

            # translate right board to center and right, then render
            gl.glLoadIdentity()
            gl.glTranslatef(-0.5*self.board_width,-0.5*self.board_width,0.0)
            gl.glTranslatef(0.5*self.screen_right, 0.0, 0.0)
            rightCB.render()

            self.vsync_patch.render(value = vsync_value)
            pygame.display.flip()
            dt = self.clock.tick_busy_loop(self.flash_rate_left * self.flash_rate_right)
            loops += 1

            #render the vsync patch
            #show the scene
            # pygame.display.flip()
            #handle outstanding events
            is_running = self.handle_events()
            # if self.flash_rate_left > 0:
            #     dt = self.clock.tick_busy_loop(self.flash_rate_left) #more accurate than tick, but uses more CPU resources
            #     leftCB = leftCB_cycle.next()
            # if self.flash_rate_right > 0:
            #     dt = self.clock.tick_busy_loop(self.flash_rate_right) #more accurate than tick, but uses more CPU resources
            #     rightCB = rightCB_cycle.next()
            # else:
            #     dt = self.clock.tick_busy_loop(self.render_loop_rate) #more accurate than tick, but uses more CPU resources
            t  = pygame.time.get_ticks()
            if t - t0 > duration:
                is_running = False

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
            print "'", text_content, "' is too wide for screen; scaling to fit"

        if self.textSurface.get_height() > self.screen_height:
            percent_scale = float(self.screen_height) / self.textSurface.get_height()
            self.font = pygame.font.Font(font_path, int(font_size * percent_scale))
            self.textSurface = self.font.render(text_content, 1, \
                [int(self.text_color[0]*255), int(self.text_color[1]*255), int(self.text_color[2]*255)], \
                [int(self.text_bgColor[0]*255), int(self.text_bgColor[1]*255), int(self.text_bgColor[2]*255)])
            print "'", text_content, "' is too tall for screen; scaling to fit"

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



