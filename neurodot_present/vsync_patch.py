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
    SEGMENTS_PER_PULSE = 3

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
        self._pulse_segment_interval = 1.0/(display_rate*self.SEGMENTS_PER_PULSE)
        self._pulse_segment_color = None
        self._pulse_segment_count = None
        
    def start_time(self, t, vsync_value = 0):
        self.t0 = t
        self._last_pulse_segment_time = t
        
        if vsync_value > 0:
            #important restart color cycle
            self._pulse_segment_count = self.SEGMENTS_PER_PULSE*vsync_value
            self._pulse_segment_color = self.on_color
        else:
            self._pulse_segment_count = 0
            self._pulse_segment_color = self.off_color
        
        self.ready_to_render = True

    def update(self, t, dt):
        #only update when ready
        self.ready_to_render = False

        # only update if the pulse interval has elapsed and there are remaining segments
        if self._pulse_segment_count > 0:
            pdt = t - self._last_pulse_segment_time
            if ( pdt >= self._pulse_segment_interval):
                self._last_pulse_time = t
                rem = self._pulse_segment_count % self.SEGMENTS_PER_PULSE
                if rem == 0: #start of pulse
                    self._pulse_segment_color = self.on_color
                else: #rest of pulse is OFF, a little extra time needed to allow VSYNC signal to recover
                    self._pulse_segment_color = self.off_color
                    
                print(t, pdt, self._pulse_segment_color)
                self._pulse_segment_count -= 1
                self.ready_to_render = True

    def render(self):
        left, bottom, width, height = (self.left,self.bottom,self.width,self.height)
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_LIGHTING)

        try:
            #bit 0, sub square at bottom/right corner, also the vsync trigger bit
            gl.glColor3f(*self._pulse_segment_color)
            gl.glRectf(left + width/2.0, bottom,  left + width, bottom + height/2.0) #left,bottom -> right,top
            #bit 1, sub square at bottom/left corner
            gl.glColor3f(*self._pulse_segment_color)
            gl.glRectf(left, bottom,left + width/2.0, bottom + height/2.0) #left,bottom -> right,top
            #bit 2, sub square at top/left corner
            gl.glColor3f(*self._pulse_segment_color)
            gl.glRectf(left, bottom + height/2.0,left + width/2.0, bottom + height) #left,bottom -> right,top
            #bit 3, sub square at top/right corner
            gl.glColor3f(*self._pulse_segment_color)
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
