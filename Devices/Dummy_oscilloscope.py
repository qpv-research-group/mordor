__author__ = 'Diego Alonso-Álvarez'

# Libraries
import numpy as np
import time

# Class definition
class Dummy_Oscilloscope(object):
    def __init__(self, port=None, name='Dummy Oscilloscope', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.sampling_rate = 10e6        # 10 MHz
        self.number_of_samples = 10000    # 10000 samples (= measuring for 1 ms)
        self.V_range = 10               # 10 V
        self.trigger_time_out = 100e-3  # 100 ms
        self.ready = False

        self.available_channels = [1, 2, 3, 4]
        self.trigger_channel = 3        # Ch-4
        self.meas_channels = [0, 1, 2, 3]  # Ch-1, Ch-2, Ch-3, Ch-4

    def set_trigger_channel(self, trig=3):
        """ Sets the number of the trigger channel.

        :param trig: the number of the trigger channel
        :return: None
        """
        assert trig < len(self.available_channels), "ERROR: Incorrect number for the trigger channel."
        self.trigger_channel = trig

    def set_meas_channel(self, meas=[0, 1, 2, 3]):
        """ Sets the measurement channels.

        :param meas: A list containing the number of the measurement channels
        :return: None
        """
        assert type(meas) is list, "ERROR: The number of meas channels must be provided in a list, even if it is just one channel."
        self.meas_channels = meas

    def set_sampling_rate(self, rate):
        """ Sets the sampling rate in Samples/second. Maximum is 10 MS/s

        :param rate: New sampling rate
        :return: None
        """
        assert rate <= 1e7, "ERROR: Maximum sampling rate of 10 MS/s exedeed"
        self.sampling_rate = rate

    def set_number_samples(self, samples):
        """ Set the number of samples to be measured. It is limitted to 125 kS per channel

        :param samples: Number of samples
        :return: None
        """
        assert samples <= 125000, "ERROR: Maximum number of samples of 125 kS exedeed"
        self.number_of_samples = int(samples)

    def trigger(self):
        """ Triggers the measurement via software, without the need of an actual triggering signal

        :return:
        """
        self.set_meas_ready()

    def set_meas_ready(self):
        """ Leaves the device ready to be triggered by some external signal at the trigger channel

        :return: None
        """
        self.ready = True

    def collect_data(self):
        """ Collects the data stored in the memory of the oscilloscope once it is ready

        :return: A 2D array with as many columns as meas channels and as many rows as samples
        """
        if not self.ready:
            print('WARNING: Oscilloscope not ready to measure.')
            data = np.zeros((self.number_of_samples, len(self.meas_channels)))
            return data

        time.sleep(0.01)
        data = np.random.rand(self.number_of_samples, len(self.meas_channels))
        self.ready = False
        return data

    def close(self):
        pass


class New(Dummy_Oscilloscope):
    """ Standarised name for the Dummy_Oscilloscope class"""
    pass


# Testing
if __name__ == '__main__':
    osci = New()
    osci.set_meas_ready()
    data = osci.collect_data()
    print(data)
