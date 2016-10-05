# -*- coding: utf-8 -*-
from __future__ import print_function

import OpenGL.GL as gl
import OpenGL.GLU as glu

#local imports
from common import COLORS

from screen import Screen

class CheckerBoard:
    def __init__(self,
                 nrows,
                 check_width = 1.0,
                 check_height = None,
                 color1 = COLORS['white'],
                 color2 = COLORS['black'],
                 fixation_dot_color = None,
                 ):
        self.nrows = int(nrows)
        if check_width is None:
            check_width = 2.0/nrows #fill whole screen
        self.check_width = check_width
        if check_height is None:
            check_height = check_width
        self.check_height = check_height
        self.board_width = check_width*nrows
        #run colors through filter to catch names and convert to RGB
        color1 = COLORS.get(color1, color1)
        color2 = COLORS.get(color2, color2)
        self.color1 = color1
        self.color2 = color2
        self.fixation_dot_color = fixation_dot_color
        self.display_list_multi = None  #for cached rendering of multiple display lists, leaving ability to change color

    def render(self):
        color1 = self.color1
        color2 = self.color2

        # create display lists if not yet done
        if self.display_list_multi is None:
            w = self.check_width
            h = self.check_height
            board_width = w * self.nrows
            board_height = h * self.nrows

            # get needed display list ints
            if self.fixation_dot_color:
                self.num_lists = 3  # include list for fixation dot
            else:
                self.num_lists = 2
            self.display_list_multi = gl.glGenLists(self.num_lists)

            # Create a display list for color 1
            try:
                gl.glNewList(self.display_list_multi, gl.GL_COMPILE)

                # render the checkerboard's color1 checks
                gl.glDisable(gl.GL_LIGHTING)
                for x in range(0, self.nrows):
                    for y in range(0, self.nrows):
                        if (x + y) % 2 == 0:
                            gl.glRectf(w*x, h*y, w*(x + 1), h*(y + 1))
            finally:
                gl.glEnable(gl.GL_LIGHTING)
                # End the display list
                gl.glEndList()

            # create a display list for color 2
            try:
                gl.glNewList(self.display_list_multi + 1, gl.GL_COMPILE)

                # render the checkerboard's color2 checks
                gl.glDisable(gl.GL_LIGHTING)
                for x in range(0, self.nrows):
                    for y in range(0, self.nrows):
                        if (x + y) % 2 == 1:
                            gl.glRectf(w*x, h*y, w*(x + 1), h*(y + 1))
            finally:
                gl.glEnable(gl.GL_LIGHTING)
                # End the display list
                gl.glEndList()

            # create list for fixation dot
            if not self.fixation_dot_color is None:
                gl.glNewList(self.display_list_multi + 2, gl.GL_COMPILE)
                gl.glDisable(gl.GL_LIGHTING)
                r, g, b = self.fixation_dot_color
                gl.glColor3f(r, g, b)
                gl.glTranslatef(board_width / 2.0, board_height / 2.0, 0)
                glu.gluDisk(glu.gluNewQuadric(), 0, 0.005, 45, 1)
                gl.glEnable(gl.GL_LIGHTING)
                gl.glEndList()

            self.show_display_lists(color1, color2)

        else:
            # render display lists
            self.show_display_lists(color1, color2)

    def show_display_lists(self, color1, color2):
        # render the color1 list:
        gl.glColor3f(*self.color1)
        gl.glCallList(self.display_list_multi)

        # render the colro2 list:
        gl.glColor3f(*self.color2)
        gl.glCallList(self.display_list_multi + 1)

        # render fixation dot
        if not self.fixation_dot_color is None:
            gl.glCallList(self.display_list_multi + 2)

    def __del__(self):
        # __del__ gets called sometimes when render() hasn't yet been run and the OpenGL list doesn't yet exist
        try:
            gl.glDeleteLists(self.display_list_multi, self.num_lists)
        except AttributeError:
            pass
            
class CheckerBoardScreen(Screen):
    def setup(self,
              nrows,
              check_width = None,
              check_color1 = 'white',
              check_color2 = 'black',
              screen_background_color = 'neutral-gray',
              fixation_dot_color = False,
              pos_x = None, 
              pos_y = None,
              vsync_value = None,
              vsync_patch = "bottom-right",
             ):
        Screen.setup(self,
                     background_color = screen_background_color,
                     vsync_value = vsync_value,
                     vsync_patch = vsync_patch,
                     )
        
        self.CB = CheckerBoard(nrows = nrows,
                               check_width = check_width,
                               color1 = check_color1,
                               color2 = check_color2,
                               fixation_dot_color = fixation_dot_color
                              )
                             
        if pos_x is None:
            pos_x = -0.5*self.CB.board_width
        if pos_y is None:
            pos_y = -0.5*self.CB.board_width
            
        self.pos_x = pos_x
        self.pos_y = pos_y

    def render(self):
        Screen.render(self)
        #move so that board is centered and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.pos_x,self.pos_y,0.0)
        self.CB.render()
        
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    CBS = Screen.with_pygame_display(debug = True)
    CBS.setup(background_color = "neutral-gray",
              vsync_value = 1
             )
    CBS.run(duration = 5)
