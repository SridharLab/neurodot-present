# see http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-14-render-to-texture/
import OpenGL.GL as gl
import OpenGL.GLU as glu
#import OpenGL.GLUT as glut

import ctypes

#from OpenGL.GL.ARB.framebuffer_object import glGenFramebuffers

#start up pygame
import pygame
pygame.init()
display_mode = None
if display_mode is None:
    #default to first mode
    display_mode = pygame.display.list_modes()[0]
w,h = display_mode

surf = pygame.display.set_mode(display_mode,
                               pygame.OPENGL
                               | pygame.DOUBLEBUF
                               | pygame.HWSURFACE
                              )
                                      
                                      
# The framebuffer, which regroups 0, 1, or more textures, and 0 or 1 depth buffer.
framebuffer = gl.glGenFramebuffers(1)
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, framebuffer)

## The texture we're going to render to
renderedTexture = gl.glGenTextures(1)

## "Bind" the newly created texture : all future texture functions will modify this texture
gl.glBindTexture(gl.GL_TEXTURE_2D, renderedTexture)

## Give an empty image to OpenGL ( the last "0" )
gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, 1024, 768, 0,gl.GL_RGB, gl.GL_UNSIGNED_BYTE, gl.GLvoidp(0))

## Poor filtering. Needed !
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

### Set "renderedTexture" as our colour attachement #0
gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D,renderedTexture, 0);

## Set the list of draw buffers.
## GLenum DrawBuffers[1] = {gl.GL_COLOR_ATTACHMENT0};
DrawBuffers_type = gl.GLenum * 1 
DrawBuffers = DrawBuffers_type(gl.GL_COLOR_ATTACHMENT0)
gl.glDrawBuffers(1, DrawBuffers); # "1" is the size of DrawBuffers


# Always check that our framebuffer is ok
if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
    raise Exception("framebuffer failed check")


# Render to our framebuffer
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, framebuffer);
gl.glViewport(0,0,1024,768); # Render on the whole framebuffer, complete from the lower left corner to the upper right

#-------------------------------------------------------------------------------
# rendering test code
import time
from neurodot_present.common import Quad
q = Quad((0.5,0.5),(0.5,0.75),(0.75,0.5),(0.75,0.75))

#prepare rendering model
gl.glClear(gl.GL_COLOR_BUFFER_BIT)
gl.glMatrixMode(gl.GL_MODELVIEW)
gl.glLoadIdentity()
q.render()

#pygame.display.flip()
time.sleep(2)



