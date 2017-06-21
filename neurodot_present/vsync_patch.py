# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy as np
import OpenGL.GL as gl
import itertools


#local imports
from common import SETTINGS, COLORS, VSYNC_PATCH_HEIGHT_DEFAULT,\
                   VSYNC_PATCH_WIDTH_DEFAULT


class VsyncPatch_Version1:
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
        self.t0 = None
        self.vsync_value = None
        self.ready_to_render = None
        
    def start_time(self, t, vsync_value = 0):
        self.t0 = t
        self.vsync_value = vsync_value
        self.ready_to_render = True

    def update(self, t, dt):
        #only update when ready
        self.ready_to_render = True

    def compute_bit_colors(self):
        bit_colors = []
        if self.vsync_value & 0b0001:  #bit0,  also the vsync trigger bit
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if self.vsync_value & 0b0010:  #bit1
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if self.vsync_value & 0b0100:  #bit2
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        if self.vsync_value & 0b1000:  #bit3
            bit_colors.append(self.on_color)
        else:
            bit_colors.append(self.off_color)
        return bit_colors

    def render(self):
        if not self.vsync_value is None:
            left, bottom, width, height = (self.left,self.bottom,self.width,self.height)
            bit_colors = self.compute_bit_colors()
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
                
    @classmethod
    #define the vsync patch as being in the bottom right corner
    def make_bottom_right(cls,
                          screen_bottom,
                          screen_right,
                          patch_width  = VSYNC_PATCH_WIDTH_DEFAULT,
                          patch_height = VSYNC_PATCH_HEIGHT_DEFAULT,
                         ):
        obj = cls(left   = screen_right - patch_width,
                  bottom = screen_bottom,
                  width  = patch_width,
                  height = patch_height
                 )
        return obj
        
class VsyncPatch_Version2:
    """  The vSync code is sent as a timing between the start of two white 
         pulses, pulse_interval = VSYNC_TIMING_BASE*VSYNC_CODE.
    """
    
    PULSE_DURATION    = 4.0/60.0 #4 frames at 60 FPS
    VSYNC_TIMING_BASE = 4.0/60.0 #4 frames at 60 FPS
    VSYNC_PATCH_WIDTH_DEFAULT   = 0.05
    VSYNC_PATCH_HEIGHT_DEFAULT  = 0.05
    VSYNC_BACKGROUND_MARGIN = 0.05

    def __init__(self, left, bottom, width, height,
                 on_color  = COLORS['white'],
                 off_color = COLORS['black'],
                 display_rate = 144, #Hz
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
        self.ready_to_render = False
        self.t0 = None
        self._patch_color = None
        self._pulse_active = False
        self._pulse_interval = None
        self._start_of_pulse_time = None
        self._end_of_pulse_time = None
        
    def start_time(self, t, vsync_value):
        self.t0 = t
        
        if vsync_value > 0:
            #begin the first pulse
            self._pulse_active = True
            self._patch_color = self.on_color
            self._pulse_interval = (vsync_value + 0.25)*self.VSYNC_TIMING_BASE
            self._start_of_pulse_time = t
            print("START:",t)
            #print("\tpulse_interval =",self._pulse_interval)
        else:
            self._patch_color = self.off_color
            self._pulse_interval = None
            self._pulse_active = False
        
        self.ready_to_render = True

    def update(self, t, dt):
        #control the pulse display when it is active
        if self._pulse_active:
            self.ready_to_render = True
            pdt = t - self._start_of_pulse_time
            if ( pdt >= self.PULSE_DURATION): #pulse period is over
                print("PULSE OFF:",t - self.t0)
                self._end_of_pulse_time = t
                self._pulse_active = False
                self._patch_color = self.off_color
        elif (not self._pulse_interval is None):
            pdt = t - self._end_of_pulse_time
            if ( pdt >= self._pulse_interval): #begin final pulse, but not too early
                print("END:",t - self.t0)
                print("pdt =", pdt)
                print("pdt/VSYNC_TIMING_BASE = %f" % (pdt/self.VSYNC_TIMING_BASE,))
                self._pulse_active = True
                self._patch_color = self.on_color
                self._pulse_interval = None #invalidate for rest of epoch
                self._start_of_pulse_time = t
                self.ready_to_render = True
        else:
            self.ready_to_render = False

    def render(self):
        left, bottom, width, height = (self.left,self.bottom,self.width,self.height)
        
        bg_margin = self.VSYNC_BACKGROUND_MARGIN
        
        

        gl.glLoadIdentity()
        gl.glDisable(gl.GL_LIGHTING)

        try:
            #draw the background which is always black
            #bit 0, sub square at bottom/right corner, also the vsync trigger bit
            gl.glColor3f(*self.off_color)
            gl.glRectf(left - bg_margin, bottom - bg_margin,  left + width + bg_margin, bottom + height + bg_margin) #left,bottom -> right,top
           
            #draw the patch
            #bit 0, sub square at bottom/right corner, also the vsync trigger bit
            gl.glColor3f(*self._patch_color)
            gl.glRectf(left, bottom,  left + width, bottom + height) #left,bottom -> right,top
        finally:
            gl.glEnable(gl.GL_LIGHTING)
                
    @classmethod
    #define the vsync patch as being in the bottom right corner
    def make_bottom_right(cls,
                          screen_bottom,
                          screen_right,
                          patch_width  = None,
                          patch_height = None,
                         ):
        if patch_width is None:
            patch_width =  cls.VSYNC_PATCH_WIDTH_DEFAULT
        if patch_height is None:
            patch_height =  cls.VSYNC_PATCH_HEIGHT_DEFAULT
            
        obj = cls(left   = screen_right - patch_width,
                  bottom = screen_bottom,
                  width  = patch_width,
                  height = patch_height
                 )
        return obj
