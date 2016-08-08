from __future__ import print_function, division
import pygame
import OpenGL.GL as gl
import numpy as np

import neurodot_present as npr

class TrueBrightnessPatch:
    def __init__(self,
                 width, # OpenGL units
                 height, # OpenGL units
                 pix_w, # OpenGL units
                 pix_h, # OpenGL units
                 bright_linewidth = 1, # pixels
                 dark_linewidth = 1, # pixels
                 color_channel = 'RGB'
                ):
        self.width = width
        self.height = height
        self.pix_h = pix_h
        self.pix_w = pix_w

        # get linewidths in OpenGL's coordinates
        self.bright_linewidth = bright_linewidth * pix_h
        self.dark_linewidth = dark_linewidth * pix_h

        # get bright colors for different color channels
        if color_channel == 'RGB':
            self.bright_color = (1.0, 1.0, 1.0)
        if color_channel == 'R':
            self.bright_color = (1.0, 0.0, 0.0)
        if color_channel == 'G':
            self.bright_color = (0.0, 1.0, 0.0)
        if color_channel == 'B':
            self.bright_color = (0.0, 0.0, 1.0)
        self.dark_color = (0.0, 0.0, 0.0)

        # get number of dark or bright lines that must be displayed
        self.num_lines = int(height / ((dark_linewidth + bright_linewidth) * pix_h))

        # initialize display_list_index as None so render() will create a display list on its first call
        self.display_list_index = None

    def render(self):
        # make or render display list
        if self.display_list_index is None:
            self.display_list_index = gl.glGenLists(1)
            gl.glNewList(self.display_list_index, gl.GL_COMPILE)

            gl.glDisable(gl.GL_LIGHTING)

            # render lines
            for i in range(0, self.num_lines + 1):
                ypos = i * (self.bright_linewidth + self.dark_linewidth)

                # render bright line
                gl.glColor3f(*self.bright_color)
                gl.glRectf(0, ypos, self.width, ypos + self.bright_linewidth)

                # render dark line
                gl.glColor3f(*self.dark_color)
                gl.glRectf(0, ypos + self.bright_linewidth, self.width, ypos + self.bright_linewidth + self.dark_linewidth)

            gl.glEnable(gl.GL_LIGHTING)
            gl.glEndList()
            gl.glCallList(self.display_list_index)

        else:
            gl.glCallList(self.display_list_index)

class TestPatch:
    def __init__(self,
                 width, # OpenGL units
                 height, # OpenGL units
                ):
        self.width = width
        self.height = height
        self.color = (0.0, 0.0, 0.0)  # will be set when GammaUtility.update() is called

    def render(self):
        gl.glDisable(gl.GL_LIGHTING)
        gl.glColor3f(*self.color)
        gl.glRectf(0, 0, self.width, self.height)
        gl.glEnable(gl.GL_LIGHTING)

class GammaUtility(npr.Screen):
    def setup(self,
              bot_left,
              top_right,
              bright_linewidth = 1,
              dark_linewidth = 1,
              background_color = 'black',
              color_bits = 8,
              color_channel = 'RGB',
              print_output = True
             ):
        npr.Screen.setup(self, background_color = background_color)
        
        self.bot_left = bot_left
        self.top_right = top_right
        self.color_channel = color_channel
        self.print_output = print_output

        # get pixel widths and heights in OpenGL coordinates
        self.pix_h = (2.0 * self.screen_top) / self.screen_height
        self.pix_w = (2.0 * self.screen_right) / self.screen_width

        # get width and height of ref+test patch
        self.width = top_right[0] - bot_left[0]
        self.height = top_right[1] - bot_left[1]

        # get increment quantities for changing test patch color
        self.color_bits = color_bits
        self.color_levels = [level for level in np.linspace(1.0, 0.0, 2**color_bits)]
        self.color_index = 0
        self.test_color_current = self.color_levels[self.color_index]

        self.standard_patch = TrueBrightnessPatch(width = self.width/2.0,
                                                  height = self.height,
                                                  pix_w = self.pix_w,
                                                  pix_h = self.pix_h,
                                                  bright_linewidth = bright_linewidth,
                                                  dark_linewidth = dark_linewidth,
                                                  color_channel = color_channel
                                                 )
        self.test_patch = TestPatch(width = self.width/2.0,
                                    height = self.height,
                                    )

    def update(self, t, dt):
        self.ready_to_render = True  # ensure things get rendered

        # get next color
        if self.color_index > 2**self.color_bits - 1:
            # ensure index doesn't go above bounds
            self.color_index = 2**self.color_bits - 1
        elif self.color_index < 0:
            # ensure index doesn't go below bounds
            self.color_index = 0
        else:
            # update color if index is within bounds
            self.test_color_current = self.color_levels[self.color_index]

        # modify test patch's appropriate RGB values
        if self.color_channel == 'RGB':
            self.test_patch.color = (self.test_color_current, self.test_color_current, self.test_color_current)
        if self.color_channel == 'R':
            self.test_patch.color = (self.test_color_current, 0.0, 0.0)
        if self.color_channel == 'G':
            self.test_patch.color = (0.0, self.test_color_current, 0.0)
        if self.color_channel == 'B':
            self.test_patch.color = (0.0, 0.0, self.test_color_current)

    def render(self):
        # do some general OpenGL stuff
        npr.Screen.render(self)

        # translate to position of reference patch and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.bot_left[0], self.bot_left[1], 0.0)
        self.standard_patch.render()

        # translate to position of test patch and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.bot_left[0] + self.width/2.0, self.bot_left[1], 0.0)
        self.test_patch.render()

    def pygame_handle_events(self, **kwargs):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    #self.print_data()  # could delete this so that info only printed on enter
                    raise npr.UserEscape

                # print info if enter pressed
                if event.key == pygame.K_RETURN:
                    self.print_data()
                    return False

                # K_DOWN cases (decreasing brightness)
                if event.key == pygame.K_DOWN:
                    mods = pygame.key.get_mods()

                    if mods & pygame.KMOD_SHIFT and mods & pygame.KMOD_CTRL:
                        # change very coarsley (by an eigth of the intensity range)
                        self.color_index += int(2**self.color_bits / 8)

                    elif mods & pygame.KMOD_CTRL:
                        # change coarsley (by a 32nd of the intensity range)
                        self.color_index += int(2**self.color_bits / 32)

                    else:
                        self.color_index += 1

                # K_UP cases (increasing brightness)
                if event.key == pygame.K_UP:
                    mods = pygame.key.get_mods()

                    if mods & pygame.KMOD_SHIFT and mods & pygame.KMOD_CTRL:
                        # change very coarsley (by an eigth of the intensity range)
                        self.color_index -= int(2**self.color_bits / 8)

                    elif mods & pygame.KMOD_CTRL:
                        # change coarsley (by a 32nd of the intensity range)
                        self.color_index -= int(2**self.color_bits / 32)

                    else:
                        self.color_index -= 1
                        
            # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
            elif event.type == pygame.JOYBUTTONDOWN:
                print("Joystick button pressed: %r" % event.button)
            

        return True
        

    def run(self, **kwargs):
        # loop rate set too high so that it should run effectively as fast as python is capable of looping
        npr.Screen.run(self, display_loop_rate = 10000, **kwargs)

    def print_data(self):
        if self.print_output:
            print('Final [0,1] intensity:', self.test_color_current)
            print('Final', self.color_bits, 'bit intensity:', 2**self.color_bits - self.color_index)

################################################################################
"""
Ed Eskew
2016-08-03

Directions:
With the screen far enough away that the lines on the left patch are indistinguishable, use the Up/Down arrow keys to
adjust the brightness of the right patch until it appears equal to the left.  Use the CTRL modifier for a more coarse
adjustment, and Shift+CTRL for very coarse.  Press "Return" to record the current intensity of the test patch and
advance to the next reference patch.  Press "Escape" to exit the program without doing anything.
"""

if __name__ == '__main__':
    import math
    import sys
    import os
    import shelve
    import matplotlib.pyplot as plt
    from scipy import interpolate

    bot_left = (-0.50, -0.25)
    top_right = (0.50, 0.25)
    color_channel    = 'RGB' # can be RGB or R, G, or B alone
    brightness_ratios = [(1,6),(1,5),(1,4),(1,3),(1,2),(1,1),(2,1),(3,1)]  # (bright, dark)[(3,2),(3,1),(4,1),(5,1),(6,1)]#
    monitor_name = 'benq'

    gammaUtility = GammaUtility.with_pygame_display( use_joysticks = True,
                                                     debug = True,
                                                    )

    display_output = True
    inputs = []
    for brightness in brightness_ratios:
        gammaUtility.setup(bot_left = bot_left,
                       top_right = top_right,
                       bright_linewidth = brightness[0],
                       dark_linewidth = brightness[1],
                       background_color = 'black',
                       color_bits = 8,
                       color_channel = color_channel,
                       print_output = False,
                      )
        try:
            gammaUtility.run(duration = None)
            inputs.append(gammaUtility.test_color_current)
        except npr.UserEscape:
            display_output = False
            break
    pygame.quit()

    if display_output:
        # get intensity values for each reference ratio
        ref_values = [vals[0] / sum(vals) for vals in brightness_ratios]

        # we know that ref_values[i]**gamma = output_brightness[i]
        gamma_values = [math.log(inputs[i], ref_values[i]) for i in range(0, len(inputs))]

        # hardcoded example values so I don't have to do the experiment every time
        #inputs = [0.28627450980392155, 0.32156862745098036, 0.36862745098039218, 0.44705882352941173, 0.56470588235294117, 0.76078431372549016, 0.88627450980392153, 0.9137254901960784]
        #gamma_values = [0.6427861556800382, 0.6332012289478619, 0.6200728559818146, 0.5807317113470583, 0.5201564295946632, 0.39444059467173037, 0.2977532307266597, 0.31362778647893835]

        # get cubic spline function for this info
        x_range = np.linspace(0.0, 1.0, 100)
        gam_func = interpolate.interp1d(inputs, gamma_values, kind = 'linear', fill_value="extrapolate", bounds_error=False)
        interp_gams = [gam_func(x) for x in x_range]

        # pyplot stuff
        fig = plt.figure(1)
        ax1 = fig.add_subplot(111)
        ax1.scatter(inputs, gamma_values)
        ax1.plot(x_range, interp_gams)
        ax1.grid(True)
        ax1.set_xlabel('Input Intensity')
        ax1.set_ylabel('Gamma')
        ax1.set_title('Input RGB Intensity vs. Gamma Factor')
        #plt.xticks([round(out, 3) for out in inputs])
        #plt.yticks([round(gam, 3) for gam in gamma_values])
        plt.show()

        print('Final input intensities:')
        print(inputs)
        print('Gamma values:')
        print(gamma_values)

        # check if calibrations folder exists, make it if not
        home = os.path.expanduser('~')
        npPath = os.path.sep.join((home, '.neurodot_present'))
        calPath = os.path.sep.join((home,'.neurodot_present', 'calibrations'))
        if not os.path.isdir(npPath):
            os.mkdir(npPath)
        if not os.path.isdir(calPath):
            os.mkdir(calPath)

        # shelve needed values
        dbPath = os.path.sep.join((home, '.neurodot_present', 'calibrations', monitor_name))
        db = shelve.open(dbPath)
        db['input_intensities'] = inputs
        db['gamma_values'] = gamma_values
        db.close()

        sys.exit()














