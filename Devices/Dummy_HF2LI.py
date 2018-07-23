# Libraries
import time
import random
from tkinter import messagebox


# Class definition
class Dummy_HF2LI:

    def __init__(self, port=None, name='Dummy HF2LI', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.integration_time = 300
        self.min_wavelength = 0.

    def readTimeconstant(self):
        """ Reads the integration time selected in the lockin
        :return:
        """
        return self.integration_time

    def update_integration_time(self, new_time):
        """ Updates the integration time in the lockin based on the selection in the program
        :param new_time: the new integration time selected in the program
        :return:
        """
        self.integration_time = new_time

        print('Integration time: {} ms'.format(self.integration_time))
        return self.integration_time

    def open(self):
        pass

    def measure(self):
        return random.random(), random.random(), random.random(), random.random(), random.random(), random.random()

    def close(self):
        pass

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(Dummy_HF2LI):
    """ Standarised name for the Dummy_monochromator class"""
    pass

# Testing
if __name__ == "__main__":
    test = New('COM4')
    print(test.measure())
