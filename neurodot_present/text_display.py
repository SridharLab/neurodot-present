# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import pygame


#local imports
import resources
from common import DEBUG, COLORS
from screen import Screen

class TextDisplay(Screen):
    def __init__(self,
                 **kwargs
                 ):
        Screen.__init__(self, **kwargs)

    def setup(self,
              text_content = "DEFAULT",
              text_color = 'black',
              text_bgColor = None,
              font_size = 288,
              font_type = None,
              screen_background_color = 'white',
              scale_refObj = None,
              **kwargs
             ):
        Screen.setup(self,
                     background_color = screen_background_color,
                     **kwargs
                    )
        #if text_bgColor is unspecified, set to same as background color (renders faster than using alpha)
        if text_bgColor == None:
            text_bgColor = screen_background_color

        self.text_content = text_content
        self.text_color   = COLORS.get(text_color,   text_color)
        self.text_bgColor = COLORS.get(text_bgColor, text_bgColor)
        self.font_size = font_size
        self.font_type = font_type
        self.scale_refObj = scale_refObj
        
    def get_coords(self, xPos, yPos): #xPos, yPos in pixels with origin at center of screen
        xPos = self.screen_right * (float(xPos) / (self.screen_width/2))
        yPos = self.screen_top * (float(yPos) / (self.screen_height/2))
        return (xPos, yPos)

    def render(self):
        #this will draw background and vsync_patch
        Screen.render(self)
        
        # get file path for font file if it was specified
        font_path = None
        if self.font_type is None:
            font_path = self.font_type
        else:
            font_path = resources.get_fontpath(self.font_type)

        #render textSurface from text_content
        self.font = pygame.font.Font(font_path, self.font_size)
        rgb    = [int(c*255) for c in self.text_color]
        rgb_bg = [int(c*255) for c in self.text_bgColor]
        self.textSurface = self.font.render(self.text_content, 1, rgb, rgb_bg)

        #Scaling font; attempting to render text that is too wide/tall sets the raster position off screen and nothing is rendered
        if self.textSurface.get_width() > self.screen_width:
            percent_scale = float(self.screen_width) / self.textSurface.get_width()
            self.font = pygame.font.Font(font_path, int(font_size * percent_scale))
            self.textSurface = self.font.render(text_content, 1, rgb, rgb_bg)
            print("'", text_content, "' is too wide for screen; scaling to fit")

        if self.textSurface.get_height() > self.screen_height:
            percent_scale = float(self.screen_height) / self.textSurface.get_height()
            self.font = pygame.font.Font(font_path, int(font_size * percent_scale))
            self.textSurface = self.font.render(text_content, 1, rgb, rgb_bg)
            print("'", text_content, "' is too tall for screen; scaling to fit")
            
        #prepare some values for rendering centered text
        centerOffset_pixels = [-self.textSurface.get_width()/2, -self.textSurface.get_height()/2]
        raster_position = self.get_coords(*centerOffset_pixels)
        textData = pygame.image.tostring(self.textSurface, "RGBA", True)
        
        #render text
        gl.glRasterPos2d(*raster_position)
        gl.glDrawPixels(self.textSurface.get_width(), self.textSurface.get_height(), gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, textData)
        
        # check if we are scaling size to match other TextDisplay obj's last run() and scale textSurface if needed
        if not self.scale_refObj is None:
            ref_surface = scale_refObj.render_surface(scale_refObj.text_content, scale_refObj.font_size)
            width_scale = float(ref_surface.get_width()) / float(self.textSurface.get_width())
            height_scale = float(ref_surface.get_height()) / float(self.textSurface.get_height())
            new_width  = int(width_scale * self.textSurface.get_width())
            new_height = int(height_scale * self.textSurface.get_height())
            self.textSurface = pygame.transform.scale(self.textSurface, (new_width,new_height))

################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    TD = TextDisplay.with_pygame_display()
    TD.setup(font_size = 288,
             font_type = "FreeMono.ttf",
             screen_background_color = "white",
            )
    TD.run(duration = 5)
            
