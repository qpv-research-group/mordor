import time
import numpy as np
from tkinter import messagebox

try:
    import seabreeze.spectrometers as sb
except ImportError as err:
    print("ERROR: {0}\n\t Ocean Optics devices will not be available.".format(err))

# Class definition
class HR4000:

    def __init__(self, port=None, name='Ocean Optics HR4000', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        if 'Question/SN' in self.info.keys():
            self.dev = sb.Spectrometer.from_serial_number(self.info['Question/SN'])
        else:
            self.dev = sb.Spectrometer.from_serial_number()

        self.integration_time = 300
        self.max_integration_time = 100
        self.min_integration_time = 3.8
        self.min_wavelength = 0.271299657128
        self.correct_dark_counts = True
        self.correct_nonlinearity = True

        self.update_integration_time(self.integration_time)

    def update_integration_time(self, new_time):
        """ Updates the integration time in the spectrometer based on the selection in the program
        :param new_time: the new integration time selected in the program, in ms
        :return: the slected time, again in ms. Is the same as input
        """
        num = int(np.ceil(new_time/self.max_integration_time))
        self.integration_time = int(new_time*1.0/num)

        print('Integration time: {} ms'.format(new_time) )
        self.dev.integration_time_micros(self.integration_time*1000)
        time.sleep(0.2)

        return new_time

    def measure(self):
        """ Measures the signal from the spectrometer. The signal is provided as a rate: counts/s

        :return: a tupple with the wavelength (in nm) and the signal (in counts/s)
        """
        wl = self.dev.wavelengths()
        intensities = self.dev.intensities(correct_dark_counts=self.correct_dark_counts, correct_nonlinearity=self.correct_nonlinearity)

        # We filter the signal because outside this boundaries it makes no sense
        i = np.argmin(abs(wl-200))
        k = np.argmin(abs(wl-1100))

        return wl[i:k], intensities[i:k]*1000.0/self.integration_time

    def close(self):
        """ Closes the conexion to the spectrometer

        :return: None
        """
        self.dev.close()

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(HR4000):
    """ Standarised name for the HR4000 class"""
    pass

# Testing
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # test = New()
    # # print(test.dev.serial_number)
    # print(test.dev.model)
    # data = test.measure()
    # grad = np.gradient(data[0])
    # print(min(grad), max(grad))
    # # for i in range(4):
    # #     data = test.measure()
    # #     plt.plot(data[0], data[1])
    # # plt.show()
    # test.close()
#
#
devices = sb.list_devices()
print (devices)
#
# spec = sb.Spectrometer(devices[0])
#
# print(spec.serial_number)
# print(spec.model)
#
# TC = 1000000
# spec.integration_time_micros(TC)
#
# wl = spec.wavelengths()
# data = spec.intensities(correct_dark_counts=True, correct_nonlinearity=True)/TC
# plt.plot(wl, data)
# plt.show()
#
# spec.close()