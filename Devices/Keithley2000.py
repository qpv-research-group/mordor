__author__ = 'D. Alonso-Álvarez'

import numpy as np
import visa
from tkinter import messagebox


options = { 'CDC' : ':current:dc',
            'CAC' : ':current:ac',
            'VDC' : ':voltage:dc',
            'VAC' : ':voltage:ac',
            'RES' : ':resistance',
            'TEMP': ':temperature',
            'FREC': ':frequency'}

# Class definition
class Keithley2000:
    def __init__(self, port='GPIB::12', name='Keithley 2000', info=None):

        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        rm = visa.ResourceManager()
        self.serial_comms = rm.open_resource(port)
        self.serial_comms.write("*rst; status:preset; *cls")
        self.meas_mode = ':current:dc'
        self.timeconstant = 300

    def set_meas_mode(self, mode='CDC'):
        self.meas_mode = options[mode]

    def measure(self):
        data = self.serial_comms.query(':measure'+self.meas_mode)
        return float(data), 0.0

    def update_integration_time(self, new_time):
        """ Updates the integration time in the lockin based on the selection in the program
        DOES NOTHING, for now
        :param new_time: the new integration time selected in the program
        :return:
        """

        self.timeconstant = new_time
        print('Integration time: {} ms'.format(self.timeconstant))
        return self.timeconstant

    def close(self):
        self.serial_comms.close()

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(Keithley2000):
    """ Standarised name for the Keithley2000 class"""
    pass

# Testing
if __name__=="__main__":
    test = New()
    print(test.measure())