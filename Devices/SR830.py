# Libraries
import serial
import time
import numpy as np
import visa
from tkinter import messagebox

debug = False
developing = False

# Class definition
class SR830:
    def __init__(self, port='GPIB::10', name='SR830', info=None):

        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        if ':' not in port:
            self.serial_comms = serial.Serial(
                port=port,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                bytesize=serial.EIGHTBITS,
                timeout = 100,
                rtscts = True,
                dsrdtr = True,
                interCharTimeout = 2*0.001*50,
                writeTimeout = 100*0.001)

            self.write = self.write_serial
            self.read = self.read_serial
            self.query = self.query_serial

        else:
            rm = visa.ResourceManager()
            self.serial_comms = rm.open_resource(port, read_termination='\r')
            self.serial_comms.timeout = 5000

            self.write = self.write_visa
            self.read = self.read_visa
            self.query = self.query_visa

        self.build_timeconstants()
        self.timeconstant = self.get_time_constant()
        self.min_wavelength = 0.05

    def build_timeconstants(self):
        self.timeconstants = []
        for p in range(-5,5):
            self.timeconstants.append(10**p)
            self.timeconstants.append(3*10**p)

        self.timeconstants = np.array(self.timeconstants)

    def write_serial(self, command):

        if debug:
            print('to device: %s' % command)

        self.serial_comms.write(bytes(command+'\r', 'UTF-8'))

    def read_serial(self, bytes_to_read=1024):
        global debug
        rawread = self.serial_comms.read(bytes_to_read).decode('utf-8')

        if debug:
            print('from lockin: %s' % rawread)

        return rawread.strip()

    def query_serial(self, command, bytes_to_read=1024, wait=None):
        self.write_serial(command)
        if wait is not None:
            time.sleep(wait)
        rawread = self.read_serial(bytes_to_read)
        return rawread

    def write_visa(self, command):
        self.serial_comms.write(command)

    def read_visa(self, command):
        rawread = self.serial_comms.read()
        return rawread

    def query_visa(self, command):
        rawread = self.serial_comms.query(command)
        return rawread

    def measure(self):
        return tuple(self.query("snap?10,11").split(","))

    def update_integration_time(self, new_time):
        """ Updates the integration time in the lockin based on the selection in the program
        :param new_time: the new integration time selected in the program
        :return:
        """
        idx = np.argmin(abs(self.timeconstants-new_time/1000.))
        command = 'OFLT ' + str(idx)
        self.write(command)

        self.timeconstant = self.get_time_constant()
        print('Integration time: {0:.2f} ms'.format(self.timeconstant*1000))
        return self.timeconstant*1000

    def get_time_constant(self):
        raw = self.query("OFLT?")
        return self.timeconstants[int(raw)]

    def close(self):
        self.serial_comms.close()

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(SR830):
    """ Standarised name for the SR830 class"""
    pass

# Testing
if __name__=="__main__":
    test = New()
    print(test.update_integration_time(0.800))


