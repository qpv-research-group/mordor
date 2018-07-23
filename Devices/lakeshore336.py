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
class Lakeshore336(object):
    def __init__(self, port='COM4', name='Lakeshore 336', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.device = Serial(port,
                             baudrate=57600,
                             bytesize=7,
                             parity='E',
                             stopbits=1,
                             timeout=10)

        self.setPoint = self.getSP()
        self.temperature = self.getTemp()

        print(self.getID())

    def close(self):
        self.device.close()

    def getID(self):
        self.device.write(bytes('*IDN?\r\n', 'utf-8'))
        return self.device.readline(50).decode('utf-8').strip()

    def getTemp(self):
        self.device.write(bytes('KRDG? 1\r\n', 'utf-8'))
        self.temperature = float(self.device.readline(50).decode('utf-8').strip())
        return self.temperature

    def getSP(self):
        self.device.write(bytes('SETP? 1\r\n', 'utf-8'))
        self.setPoint = float(self.device.readline(50).decode('utf-8').strip())
        return self.setPoint

    def setSP(self, SP):
        self.setPoint = SP
        time.sleep(0.1) ## Need delay to run both commands
        self.device.write(bytes('SETP 1,'+str(self.setPoint)+'\r\n', 'utf-8'))
        time.sleep(0.1) ## Need delay to run both commands
        self.device.write(bytes('SETP 2,'+str(self.setPoint)+'\r\n', 'utf-8'))        

    def setPID(self, PID):
        time.sleep(0.1) ## Need delay to run both commands
        self.device.write(bytes('PID 1,'+PID[0]+','+PID[1]+','+PID[2]+'\r\n', 'utf-8'))
        time.sleep(0.1) ## Need delay to run both commands
        self.device.write(bytes('PID 2,'+PID[0]+','+PID[1]+','+PID[2]+'\r\n', 'utf-8'))
        
    def setHeater(self, value):
        time.sleep(0.1) ## Need delay to run both commands
        if value == 'LOW':
            self.device.write(bytes('RANGE 1,1\r\n', 'utf-8'))
            time.sleep(0.1) ## Need delay to run both commands
            self.device.write(bytes('RANGE 2,1\r\n', 'utf-8'))
        elif value == 'MED':
            self.device.write(bytes('RANGE 1,2\r\n', 'utf-8'))
            time.sleep(0.1) ## Need delay to run both commands
            self.device.write(bytes('RANGE 2,2\r\n', 'utf-8'))
        elif value == 'HIGH':
            self.device.write(bytes('RANGE 1,3\r\n', 'utf-8'))
            time.sleep(0.1) ## Need delay to run both commands
            self.device.write(bytes('RANGE 2,3\r\n', 'utf-8'))
        else:
            self.device.write(bytes('RANGE 1,0\r\n', 'utf-8'))
            time.sleep(0.1) ## Need delay to run both commands
            self.device.write(bytes('RANGE 2,0\r\n', 'utf-8'))

class New(Lakeshore336):
    """ Standarised name for the Lakeshore336 class"""
    pass


# Testing
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    test = T_controller(master=root)
    root.mainloop()
