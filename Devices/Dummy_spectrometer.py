__author__ = 'diego'

# Libraries
import time
import random
import numpy as np
from tkinter import messagebox


# Class definition
class Dummy_spectrometer:

    def __init__(self, port=None, name='Dummy spectrometer', info=None):

        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.integration_time = 300
        self.max_integration_time = 100
        self.min_wavelength = 0.3

    def update_integration_time(self, new_time):
        """ Updates the integration time in the spectrometer based on the selection in the program
        :param new_time: the new integration time selected in the program
        :return:
        """
        num = int(np.ceil(new_time/self.max_integration_time))
        self.integration_time = int(new_time*1.0/num)

        print('Integration time: {} ms'.format(new_time))
        time.sleep(0.2)

        return new_time

    def measure(self):
        wl = np.arange(150, 1100, 0.2)
        out = np.zeros_like(wl)
        n = max(int(self.integration_time/10.), 1)
        for i in range(0, n):
            out = out + np.random.random_sample(len(wl))

        time.sleep(self.integration_time/1000.)
        return wl, out/n

    def close(self):
        pass

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(Dummy_spectrometer):
    """ Standarised name for the Dummy_spectrometer class"""
    pass

# Testing
if __name__ == "__main__":
    test = New('COM4')
    print(test.measure())