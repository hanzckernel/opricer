# from data import models
# from algo import pde
import numpy as np
import datetime


class Small:

    def __init__(self, leg):
        self.leg = leg

    @classmethod
    def add_leg(cls):
        cls.leg += 1
        return cls.leg


a = Small(1)
a.add_leg()
