# -*- coding: utf-8 -*-
from __future__ import print_function

import pygame
import OpenGL.GL as gl
import numpy as np

#local imports
from common import DEFAULT_FLASH_RATE

from screen import Screen

from checkerboard import CheckerBoard

class TripleCheckerBoardSinFlasher(Screen):
    def setup(self,
              nrows,
              nrows_center = None,
              check_width = None,
              check_width_center = None,
              screen_background_color = 'neutral-gray',
              show_fixation_dot = False,
              flash_rate_left = DEFAULT_FLASH_RATE,
              flash_rate_right = DEFAULT_FLASH_RATE,
              flash_rate_center = DEFAULT_FLASH_RATE,
              #rate_compensation = None,
              vsync_patch = 'bottom-right',
             ):
        Screen.setup(self,
                     background_color = screen_background_color,
                     vsync_patch = vsync_patch,
                     )
        # check if we are rendering center board
        if flash_rate_center == None:
            self.render_center = False
        else:
            self.render_center = True
            # unless otherwise specified, center checkerboard will be same as others
            if nrows_center == None:
                nrows_center = nrows
            if check_width_center == None:
                check_width_center = check_width

        # set checkerboard-related attributes
        if check_width is None:
            check_width = 2.0/nrows #fill whole screen
        self.board_width = check_width*nrows
        if self.render_center:
            self.board_width_center = check_width_center * nrows_center
        self.nrows = nrows
        self.CB_left = CheckerBoard(nrows, check_width, show_fixation_dot = show_fixation_dot)
        self.CB_right = CheckerBoard(nrows, check_width, show_fixation_dot = show_fixation_dot) #reversed pattern
        if self.render_center:
            self.CB_center = CheckerBoard(nrows_center, check_width_center, show_fixation_dot = False)#show_fixation_dot)

        # set time-related attributes
        self.overall_start_time = None
        self.flash_rate_left  = flash_rate_left / 2.0  # we measure twice the actual frequency in the brain
        self.flash_rate_right = flash_rate_right / 2.0
        if self.render_center:
            self.flash_rate_center = flash_rate_center / 2.0
        #self.rate_compensation = rate_compensation

        # get useful coordinate values for checkerboard rendering locations
        self.xC, self.yC = (-0.5*self.board_width,-0.5*self.board_width)
        self.xL, self.yL = (self.xC - 0.7*self.screen_right, self.yC)
        self.xR, self.yR = (self.xC + 0.7*self.screen_right, self.yC)

        # quantities for checking things
        self.r1_list = []
        self.t_list = []

    def start_time(self,t):
        # get start time and set current CB objects (and their change times)
        Screen.start_time(self,t)
        self.overall_start_time = t

    def render(self):
        # do general OpenGL stuff as well as FixationCross and Vsync Patch if needed
        Screen.render(self)

        # translate to position of left board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xL, self.yL, 0.0)
        self.CB_left.render()

        # translate to position of right board and render
        gl.glLoadIdentity()
        gl.glTranslatef(self.xR, self.yR, 0.0)
        self.CB_right.render()

        # render center board
        if self.render_center:
            gl.glLoadIdentity()
            gl.glTranslatef(-self.board_width_center / 2.0, -self.board_width_center / 2.0, 0.0)
            self.CB_center.render()

    def update(self, t, dt):
        self.ready_to_render = True # render on every Screen.pygame_display_loop loop

        # update check colors on left checkerboard
        color1Left, color2Left = self.get_colors(t, self.flash_rate_left)
        self.CB_left.color1 = color1Left
        self.CB_left.color2 = color2Left

        # update check colors on right checkerboard
        color1Right, color2Right = self.get_colors(t, self.flash_rate_right)
        self.CB_right.color1 = color1Right
        self.CB_right.color2 = color2Right

        # update check colors on center checkerboard
        if self.render_center:
            color1Center, color2Center = self.get_colors(t, self.flash_rate_center, inv_gamma=1.0)
            self.CB_center.color1 = color1Center
            self.CB_center.color2 = color2Center

    def get_colors(self, t, flash_rate,
                   shape="sin",
                   inv_gamma = 0.43,
                   ):
      # get elapsed time
      t = t - self.overall_start_time

      # get colors

      color1, color2 = (None,None)
      if shape == "sin":
          # Contrasts will go from 0 and 1 at flash_rate Hz,
          # that is the half-cycle of full contrast change
          # to which the SSVEP is sensitive.
          r1 = g1 = b1 = (-1.0 * np.cos(flash_rate * np.pi * t) / 2.0 + 0.5)
          r2 = g2 = b2 = (np.cos(flash_rate * np.pi * t) / 2.0 + 0.5)
          color1 = (r1, g1, b1)
          color2 = (r2, g2, b2)
      elif shape == "square":
          c = -1.0 * np.cos(flash_rate * np.pi * t) / 2.0 + 0.5
          if c > 0.5:
              color1 = (1.0,1.0,1.0)
              color2 = (0.0,0.0,0.0)
          else:
              color1 = (0.0,0.0,0.0)
              color2 = (1.0,1.0,1.0)
      # get some values for checking what was displayed
      if flash_rate == self.flash_rate_left:
        self.r1_list.append(r1)
        self.t_list.append(t)

      return color1, color2

    def run(self, **kwargs):
        # loop rate set too high so that it should run effectively as fast as python is capable of looping
        Screen.run(self, display_loop_rate = 10000, **kwargs)


################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    flash_rate_left =  15
    flash_rate_right = 23
    flash_rate_center = 5
    nrows = 16
    nrows_center = 1
    duration = 5
    show_plot = True

    TCBF = TripleCheckerBoardSinFlasher.with_pygame_display(#VBI_sync_osx = False,
                                                            #display_mode = (512,512),
                                                            #debug = True,
                                                         )
    #TCBF = TripleCheckerBoardFlasher.with_psychopy_window()
    TCBF.setup(flash_rate_left = flash_rate_left * 2,
               flash_rate_right = flash_rate_right * 2,
               flash_rate_center = flash_rate_center * 2,
               check_width = 0.5 / nrows,
               check_width_center = 0.5 / nrows_center,
               screen_background_color = 'neutral-gray',
               nrows = nrows,
               nrows_center = nrows_center,
               show_fixation_dot = True,
              )
    # frame_rate = 140
    # recording_name = "TCBFsin140FPS_512x512"
    # TCBF.pygame_recording_loop(duration = 10.0,
    #                            frame_rate = frame_rate,
    #                            recording_name = recording_name,
    #                            show = True,
    #                            )
    # import subprocess
    # input_format = "%s/%s_%%05d.png" % (recording_name, recording_name)
    # output_name = "%s.mp4" % recording_name
    # subprocess.call(["ffmpeg",
    #                  "-framerate",str(frame_rate),
    #                  "-i", input_format,
    #                  "-c:v", "libx264",
    #                  "-preset", "fast",  #compression rate
    #                  #"-pix_fmt", "yuv420p",
    #                  "-qp","0",              #lossless
    #                  #"-r", str(frame_rate),
    #                  output_name])

    TCBF.run(duration = duration)
    pygame.quit()

    if show_plot:
        t_diffs = np.diff(np.array(TCBF.t_list))
        print('Mean sample interval: ', t_diffs.mean())
        print('Mean sample frequency:', 1.0/t_diffs.mean())
        print('Sample interval STD:  ', t_diffs.std())

        import matplotlib.pyplot as plt
        plt.subplot(2,1,1)
        plt.scatter(TCBF.t_list, TCBF.r1_list, color = 'red', label = 'Displayed')
        time_vals = np.linspace(0, duration, duration * 720)
        trig_vals = [(-1.0 * np.cos(TCBF.flash_rate_left * 2.0 * np.pi * t) / 2.0 + 0.5) for t in time_vals]
        plt.plot(time_vals, trig_vals, color = 'blue', label = 'Ideal')
        plt.legend()#loc = 'best')

        plt.subplot(2,1,2)
        fft_data = abs(np.fft.rfft(TCBF.r1_list))
        fft_freqs = np.fft.rfftfreq(len(TCBF.r1_list), 1.0/140)
        plt.plot(fft_freqs, fft_data)
        plt.scatter(fft_freqs, fft_data)
        plt.show()


