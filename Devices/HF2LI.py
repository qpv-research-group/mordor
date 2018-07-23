# Libraries
import numpy as np
from tkinter import messagebox
import zhinst.ziPython, zhinst.utils

debug = False
developing = False

# Class definition
class HF2LI:
    def __init__(self, port=None, name='Zurich Inst HF2LI', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)
        self.integration_time = 100
        self.min_wavelength = 0.
        self.daq = zhinst.ziPython.ziDAQServer('localhost', 8005)

    def open(self, demod=[0,1,2]):
        """ Subscribes to two demodulators to exctract data.
        :param demod: list of 2 demodulator numbers (in Python numbering)
        :return: none
        """
        self.daq.subscribe('/dev1370/demods/'+str(demod[0])+'/sample')
        self.daq.subscribe('/dev1370/demods/'+str(demod[1])+'/sample')
        self.daq.subscribe('/dev1370/demods/'+str(demod[2])+'/sample')

    def measure(self):
        self.daq.sync()
        timeout = self.integration_time + 200
        raw_data = self.daq.poll(self.integration_time/1000, timeout)
        Xc = np.mean(raw_data['dev1370']['demods']['0']['sample']['x'])
        Yc = np.mean(raw_data['dev1370']['demods']['0']['sample']['y'])
        Xsum = np.mean(raw_data['dev1370']['demods']['1']['sample']['x'])
        Ysum = np.mean(raw_data['dev1370']['demods']['1']['sample']['y'])
        Xdif = np.mean(raw_data['dev1370']['demods']['2']['sample']['x'])
        Ydif = np.mean(raw_data['dev1370']['demods']['2']['sample']['y'])
        return Xc, Yc, Xsum, Ysum, Xdif, Ydif

    def update_integration_time(self, new_time):
        """ Updates the integration time in the lockin based on the selection in the program
        :param new_time: the new integration time selected in the program
        :return:
        """
        self.integration_time = new_time

        print('Integration time: {} ms'.format(self.integration_time))
        return self.integration_time


    def close(self, demod=[0,1,2]):
        self.daq.unsubscribe('/dev1370/demods/'+str(demod[0])+'/sample')
        self.daq.unsubscribe('/dev1370/demods/'+str(demod[1])+'/sample')
        self.daq.unsubscribe('/dev1370/demods/'+str(demod[2])+'/sample')

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')


class New(HF2LI):
    """ Standarised name for the HF2LI class"""
    pass

# Testing
if __name__=="__main__":
    test = New()
    print(test.update_integration_time(0.800))
