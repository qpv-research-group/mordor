__author__ = 'Diego Alonso-Álvarez'

# Libraries
import numpy as np
import time

try:
    import libtiepie
except ImportError as err:
    print("ERROR: {0}\n\t HS4-DIFF Oscilloscope will not be available.".format(err))

# Class definition
class HS4_DIFF(object):
    def __init__(self, port=None, name='HS4-DIFF', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        # We look for an oscilloscope with block measurement support
        libtiepie.device_list.update()

        self.scp = None
        for item in libtiepie.device_list:
            if item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE):
                self.scp = item.open_oscilloscope()
                if self.scp.measure_modes & libtiepie.MM_BLOCK:
                    break
                else:
                    self.scp = None

        assert self.scp is not None

        self.sampling_rate = 10e5        # 10 MHz
        self.number_of_samples = 100000    # 10000 samples (= measuring for 1 ms)
        self.V_range = 5               # 10 V
        self.trigger_time_out = 200e-3  # 100 ms
        self.ready = False

        self.available_channels = [1, 2, 3, 4]
        self.trigger_channel = 3        # Ch-4
        self.meas_channels = [0, 1, 2, 3]  # Ch-1, Ch-2, Ch-3, Ch-4

        self.config_meas()
        self.config_trigger()

        print('HS4_DIFF loaded!')

    def config_meas(self):
        """ Updates the configuration of the measurement after making changes to the conditions

        :return: None
        """
        self.scp.measure_mode = libtiepie.MM_BLOCK
        self.scp.sample_frequency = self.sampling_rate
        self.scp.record_length = self.number_of_samples
        self.scp.pre_sample_ratio = 0  # ??

        for ch in self.scp.channels:
            ch.enabled = True
            ch.range = self.V_range
            ch.coupling = libtiepie.CK_DCV  # DC Volt

    def config_trigger(self):
        """ Updates the configuration of the trigger after making changes to the conditions

        :return: None
        """
        # Set trigger timeout:
        self.scp.trigger_time_out = self.trigger_time_out

        # Disable all channel trigger sources:
        for ch in self.scp.channels:
            ch.trigger.enabled = False

        # Setup channel trigger:
        ch = self.scp.channels[self.trigger_channel]
        # Enable trigger source:
        ch.trigger.enabled = True
        # Kind:
        ch.trigger.kind = libtiepie.TK_RISINGEDGE  # Rising edge
        # Level:
        ch.trigger.levels[0] = 0.001  # 50 %
        # Hysteresis:
        ch.trigger.hystereses[0] = 0.05  # 5 %

    def set_trigger_channel(self, trig=3):
        """ Sets the number of the trigger channel.

        :param trig: the number of the trigger channel
        :return: None
        """
        assert trig < len(self.available_channels), "ERROR: Incorrect number for the trigger channel."
        self.trigger_channel = trig
        self.config_trigger()

    def set_meas_channel(self, meas=[0, 1, 2, 3]):
        """ Sets the measurement channels. Useless, for now

        :param meas: A list containing the number of the measurement channels
        :return: None
        """
        assert type(meas) is list, "ERROR: The number of meas channels must be provided in a list, even if it is just one channel."
        self.meas_channels = meas
        self.config_meas()

    def set_sampling_rate(self, rate):
        """ Sets the sampling rate in Samples/second. Maximum is 10 MS/s

        :param rate: New sampling rate
        :return: None
        """
        assert rate <= 1e7, "ERROR: Maximum sampling rate of 10 MS/s exedeed"
        self.sampling_rate = rate
        self.config_meas()

    def set_number_samples(self, samples):
        """ Set the number of samples to be measured. It is limitted to 125 kS per channel

        :param samples: Number of samples
        :return: None
        """
        assert samples <= 125000, "ERROR: Maximum number of samples of 125 kS exedeed"
        self.number_of_samples = int(samples)
        self.config_meas()

    def set_meas_ready(self):
        """ Leaves the device ready to be triggered by some external signal at the trigger channel

        :return: None
        """
        self.ready = True

    def trigger(self):
        """ Triggers the measurement via software, without the need of an actual triggering signal

        :return:
        """
        self.set_meas_ready()
        self.scp.start()

    def collect_data(self):
        """ Collects the data stored in the memory of the oscilloscope once it is ready

        :return: A 2D array with as many columns as meas channels and as many rows as samples
        """
        if not self.ready:
            print('WARNING: Oscilloscope not ready to measure.')
            data = np.zeros((self.number_of_samples, len(self.meas_channels)))
            return data

        # Wait for measurement to complete:
        while not self.scp.is_data_ready:
            time.sleep(0.01)  # 10 ms delay, to save CPU time

        # Get data
        data = np.array(self.scp.get_data()).T

        self.ready = False
        return data

    def close(self):
        del self.scp


class New(HS4_DIFF):
    """ Standarised name for the HS4_DIFF class"""
    pass


# Testing
if __name__ == '__main__':
    osci = New()
    #osci.trigger()
    osci.set_meas_ready()
    data = osci.collect_data()
    print(data.shape)
