__author__ = 'Andrew M. Telford & Diego Alonso-Álvarez'

# Libraries
import datetime

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

from tkinter import messagebox, ttk
import tkinter as tk
from tkinter import filedialog

import numpy as np
import time

from serial import Serial

# Class definition
class Dummy_T_UNSW(object):
    def __init__(self, port='COM4', name='Lakeshore 336', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.device = "Dummy"

        self.setPoint = 300
        self.temperature = 300

        print(self.getID())

    def close(self):
        self.device.close()

    def getID(self):
        return ("Dummy T Controller")

    def getTemp(self):
        self.temperature = self.setPoint
        return self.temperature

    def getSP(self):
        self.setPoint = self.temperature
        return self.setPoint

    def setSP(self, value):
        self.setPoint = value

    def setHeater(self, value):
        pass


class New(Dummy_T):
    """ Standarised name for the Lakeshore336 class"""
    pass


# Testing
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    test = T_controller(master=root)
    root.mainloop()
