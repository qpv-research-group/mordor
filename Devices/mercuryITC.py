__author__ = 'Diego Alonso-Álvarez'

# Libraries
import datetime

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

from tkinter import filedialog, ttk
import tkinter as tk

import time
import serial

import numpy as np

# Class definition
class mercuryITC(object):
    def __init__(self, port='COM9', name='Mercury iTC', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.ser = serial.Serial(port,
                                 baudrate=115200,
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=1)

        time.sleep(2)
        self.defineDevices()

        self.setPoint = self.getSP()
        self.temperature = self.getTemp()

        print(self.getVersion())

    def defineDevices(self):
        #store the device addresses in a dictionary
        self.devices = {"mb0" : "DEV:MB0.H1:HTR", "mb1" : "DEV:MB1.T1:TEMP"}

    def getVersion(self):
        string = self.readValue("*IDN?", readPrefix = "")
        return string

    def getDevices(self):
        devices = self.readValue("SYS:CAT")
        print(devices)

    def writeValue(self, value):
        self.ser.write(bytes(value + "\n", 'UTF-8'))

    def readValue(self, value, readPrefix = "READ:"):
        self.writeValue(readPrefix + value)
        string = self.ser.readline().decode('latin-1').rstrip()
        self.ser.flush()
        return string

    def setValue(self, value):
        self.writeValue("SET:" + value)
        raw = self.ser.readline().decode('latin-1').rstrip()
        return raw

    def close(self):
        self.ser.close()

    def getSignal(self, device, signal):
        """Get a signal from a device
        unitPrefixes are taken into account and the value is returned as a float.

        - device: device key for the devices dictionary
        - signal: string corresponding to a valid signal, i.e. TEMP, VOLT, CURR, RES, etc.
        """
        ans = self.readValue(self.devices[device] + ":SIG:" + signal).split(":")[-1]

        # print(ans)

        siPrefixes = {"M": 1e6, "k" : 1e3, "m" : 1e-3, "\xb5" : 1e-6, "n" : 1e-9, "p" : 1e-12}

        if ans[-2].isdigit():
            return float(ans[:-2])
        elif ans == 'N/A':
            return ans
        else:
            try:
                return float(ans[:-2])*siPrefixes[ans[-2]]
            except:
                print("Ans: ", ans)
                raise ValueError

    def getSensorInformation(self, device, includeTemperature = False):
        """Get Voltage, Current, Resistance and optionally Temperature of a device"""

        v = self.getSignal(device, "VOLT")
        c = self.getSignal(device, "CURR")
        r = self.getSignal(device, "RES")

        if includeTemperature:
            t = self.getSignal(device, "TEMP")
            return v,c,r,t
        else:
            return v,c,r

    def getTemp(self):
        device = "mb1"
        self.temperature = self.getSignal(device, 'TEMP')
        return self.temperature

    def getSP(self):
        device = "mb1"
        msg = self.devices[device]+':LOOP:TSET'
        ans = self.readValue(msg).split(":")[-1]
        self.setPoint = float(ans[:-2])
        return self.setPoint

    def setSP(self, value):
        device = "mb1"
        msg = self.devices[device]+':LOOP:TSET:'+str(value)
        msg = self.setValue(msg).split(':')
        if msg[-1] == 'VALID':
            self.setPoint = value

    def setHeater(self, value):
        device = "mb1"
        msg = self.devices[device]+':LOOP:ENAB:'+str(value)
        self.setValue(msg)
        print('Heater ON')
        if value == 'OFF':
            msg = self.devices[device]+':LOOP:HSET:'+str(0.0)
            self.setValue(msg)
            print('Heater OFF')



class New(mercuryITC):
    """ Standarised name for the Dummy_monochromator class"""
    pass


if __name__ == '__main__':
    import time

    mitc = mercuryITC('COM9')

    print(mitc.getTemp())
    mitc.setSP(315.0)
    print(mitc.getSP())
    mitc.setHeater('ON')
    time.sleep(5)
    print(mitc.getTemp())
    mitc.setHeater('OFF')

    mitc.close()