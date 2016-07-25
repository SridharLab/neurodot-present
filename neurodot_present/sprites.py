import time
import numpy as np

from common import DEBUG, COLORS, cart2pol, pol2cart

class Sprite:
    def __init__(self,
                 use_polar_coords = False,
                 position_initial = (0,0),
                 velocity = None,
                 position_final = None,
                 movement_duration = 1.0,  # time to move from position_initial to position_final, seconds
                 dt_threshold = 0.001,  # shortest allowed time between updates and between renders
                 ):
        self.use_polar_coords  = use_polar_coords
        self.position_initial  = position_initial
        self.position_final    = position_final
        self.movement_duration = movement_duration
        self.dt_threshold      = dt_threshold
        # check if velocity was specified or if it must be calculated from initial and final positions
        if not velocity == None:
            self.velocity = velocity
        elif not position_final == None:
            self.position_diff = np.array(np.subtract(position_final, position_initial)) # difference vector between initial and final positions
            self.velocity = self.position_diff / movement_duration
        else:
            raise AttributeError('Must specify either velocity or position_final of sprite')
        self.reset()
    
    def reset(self):
        # reset initial values
        self.position_current  = self.position_initial
        self.t_since_update = None
        self.t_since_render = None
        self.has_rendered   = False # this keeps track of if render() has been called
        
    def update(self, t = 0, v = None):
        """ update render position (velocity is vector in OpenGL style coorinates/timestep)"""
        # if update() has not been run, set time_since_update to current time
        if self.t_since_update == None:
            self.t_since_update = t
        
        # get length of time between this and last update() call
        dt = t - self.t_since_update
        
        # option to set different velocity value at update() call
        if not v is None:
            self.velocity = v
        size = self.size
        thickness = self.thickness
        p1,p2 = self.position_current
        v1,v2 = self.velocity
        p1 = p1 + v1*dt
        p2 = p2 + v2*dt
        self.position_current = (p1,p2)


    def render():
        raise NotImplementedError("render method must be overridden in Sprite subclass")
        
