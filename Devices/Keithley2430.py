__author__ = 'D. Alonso-Álvarez'

import numpy as np
import visa
import time
from tkinter import messagebox


class Keithley2430:
    """ Keithley 2430 Source Measure Unit

    """
    def __init__(self, address='GPIB::20', name='Keithley 2430', info=None):
        """ Initializes the instrument
        :param rm: resource manager
        :param address: int, GPIB address, 20
        :return: None
        """
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        rm = visa.ResourceManager()
        self.device = rm.open_resource("{}".format(address))

        # Reset default values
        self.device.write("*RST")

        # Ask for the name of the device
        print(self.device.query("*IDN?"))

        # Even though this SMU accepts a continous of values for the range, we make them discrete for consiscency
        self.i_range = ['auto', '1e-9 A', '10e-9 A', '100e-9 A', '1e-6 A', '10e-6 A', '100e-6 A', '1e-3 A', '10e-3 A',
                        '100e-3 A', '1 A', '3 A']
        self.v_range = ['auto', '1 V', '2 V', '5 V', '10 V', '20 V', '40 V', '60 V', '80 V', '100 V']
        self.log_points = ['5', '10', '25', '50']
        self.int_time = ['0.2', '2', '20', '200']

        self.function = None

    def query(self, msg):
        """ Send a message to the instrument and then waits for an answer.

        :param msg: command to be executed in the instrument
        :return: the answer to that command
        """
        return self.device.query(msg)

    def write(self, msg):
        """ Send a message to the instrument

        :param msg: message to be sent to the instrument
        :return: None
        """
        self.device.write(msg)

    def close(self):
        """ Closes the connection with the instrument

        :return: None
        """
        self.device.close()

    def set_source_function(self, function, source):
        """ Sets the functionality of the source, what to bias, what to measure and a few limits.

        :param function: 'dc' or 'sweep', dc or sweep operating function
        :param source: 'v' or 'i', voltage or current source
        :return: None
        """

        source_dict = {'v':'VOLT','i':'CURR'}
        function_dict = {'dc':'FIX','sweep':'SWE'}

        try:
            source = source_dict[source.lower()]
            function = function_dict[function.lower()]
        except(KeyError):
            raise ValueError('ERROR: bad values for source and/or function')

        # We set the source and the function
        self.write(':SOUR:FUNC {0}'.format(source))
        self.write(':SOUR:{0}:MODE {1}'.format(source, function))

        self.source = source
        self.function = function

        if self.function == 'FIX':
            # This command ensures that the source is on after the measurement
            self.write(':SOUR:CLE:AUTO OFF')
        else:
            # But in sweep mode we want it to get on and off automatically
            self.write(':SOUR:CLE:AUTO ON')

        if self.source == 'VOLT':
            self.sense = 'CURR'
            self.sense_range = self.i_range
        else:
            self.sense = 'VOLT'
            self.sense_range = self.v_range

        # We disable concurrent measurements (more than one function simultaneously) and set what we are measuring
        self.write(':SENS:FUNC:CONC 0')
        self.write(':SENS:FUNC "{0}:DC"'.format(self.sense))

        # Select the data to retrieve from the source, voltage and current, otherwise the output will include the
        # resistance (not measured) the time stamp and status information
        self.write(":FORM:ELEM VOLT, CURR")

    def update_compliance(self, compliance, measRange):
        """ Updates the compliance and the measurement range.

        :param compliance: current or voltage compliance, oposite to the selected source
        :param measRange: the meas range as the index of self.i_range or self.v_range
        :return: None
        """
        # We set the compliance
        self.write(':SENS:{0}:PROT {1}'.format(self.sense, compliance))
        self.compliance = compliance

        # And the measuring range
        if self.sense_range[measRange] == 'auto':
            self.measRange = 'auto'
            self.write(':SENS:{0}:RANG:AUTO 1'.format(self.sense))
        else:
            self.measRange = float(self.sense_range[measRange].split(' ')[0])
            self.write(':SENS:{0}:RANG {1}'.format(self.sense, self.measRange))

    def update_integration_time(self, new_time):
        """ Sets the integration time. This source needs as input the integration rate, refered to the line frequency
        which is 50 Hz. We calculate it based on the selected integration time.

        :param new_time: new integration time as the index from the self.int_time list
        :return: None
        """
        self.itime = float(self.int_time[new_time])
        rate = self.itime * 50 / 1000.

        self.write(':SENS:{0}:NPLC {1}'.format(self.sense, rate))

    def update_waiting_time(self, new_time):
        """ Sets the delay time between setting a bias and starting a measurement

        :param new_time: New delay time in ms.
        :return: None
        """
        self.delay = new_time
        self.write('SOUR:DEL {0}'.format(self.delay / 1000.))

    def setup_measurement(self, function='dc', source='v', compliance=0.1, measRange=0, delay=0, intTime=0):
        """ Prepares and triggers the IV measurement.

        :param function: 'dc' or 'sweep', dc or sweep operating function
        :param source: 'v' or 'i' for voltage or current biasing, respectively
        :param compliance: meas compliance
        :param measRange: the meas range as the index of self.i_range or self.v_range
        :param delay: the delay between applying a bias and taking the meas
        :param intTime: integration time as the index from the self.int_time list
        :return: The measured data
        """

        self.set_source_function(function, source)
        self.update_compliance(compliance, measRange)
        self.update_integration_time(intTime)
        self.update_waiting_time(delay)

    def measure(self, source='v', start=0, stop=1, step=0.05, points=1, compliance=2, measRange=0, delay=0, intTime=0):
        """ Prepares and triggers the IV measurement.

        :param source: 'v' or 'i' for voltage or current biasing, respectively
        :param start: start bias
        :param stop: stop bias
        :param points: points to measure per decade in current bias mode
        :param step: step size in voltage bias mode
        :param compliance: meas compliance
        :param measRange: the meas range as the index of self.i_range or self.v_range
        :param delay: the delay between applying a bias and taking the meas
        :param intTime: integration time as the index from the self.int_time list
        :return: The estimated measuring time
        """

        # First we setup the experiment
        self.setup_measurement('sweep', source, compliance, measRange, delay, intTime)

        # We can set the sweep direction up or down according to the input in start and end voltage.
        # However, the Keithley 2430 needs start to be less than end, and then you tell which direction the sweep goes
        if float(start) > float(stop):
            start, stop = stop, start
            self.write(':SOUR:SWE:DIR DOW')
        else:
            self.write(':SOUR:SWE:DIR UP')

        if source == 'v':
            # For voltage, we always use the BEST fixed range for the bias
            self.write(':SOUR:SWE:RANG BEST')
            # and a linear staircase
            self.write(':SOUR:SWE:SPAC LIN')
            # with a fixed step size
            totalPoints = (stop-start)/step + 1
            self.write(':SOUR:SWE:POIN {0}'.format(totalPoints))
        else:
            # For current, we always use the AUTO fixed range for the bias, as it might cover may orders of magnitude
            self.write(':SOUR:SWE:RANG AUTO')
            # and a logarithmic staircase
            self.write(':SOUR:SWE:SPAC LOG')
            # with a certain number of points. Here we have to calculate the total number of points, as the input is
            # points per decade
            totalPoints = int(np.log10(float(stop)/max(1e-9, float(start))) * int(self.log_points[points]) )+1
            self.write(':SOUR:SWE:POIN {0}'.format(totalPoints))
            pass

        # Set start...
        self.write(':SOUR:{0}:START {1}'.format(self.source, start))
        # ... and stop
        self.write(':SOUR:{0}:STOP {1}'.format(self.source, stop))

        # Trigger count needs to equal the number of points in the sweep. This command queries the SMU to read the
        # number of points for the configured sweep and set them back to the source. Why we need this???
        trigger_count = self.query(":SOUR:SWE:POIN?")
        self.write(":TRIG:COUN " + trigger_count)

        # We estimate the runing time of the sweep, set the timeout time accordingly and return the control to the IV module.
        # This will wait in a "safe way" during the measurement, avoiding freezing the program
        minimumWait = 10
        measTime = int(trigger_count) * (self.itime + self.delay + minimumWait)
        # if self.measRange == 'auto':
        #     measTime = measTime * 10
        self.device.timeout = None
        print("Waiting for Keithley.\nEstimated measurement time = {:.2f} s".format(measTime/1000.))

        # Initiates the measurement. Since the source is configured to automatically turn on and off,
        # we don't need to worry about it
        self.write(":INIT")

        return measTime

    def set_bias(self, biasValue=0.0):
        """ Set a bias to the source. If the source is not turned on or the function is not set to 'dc',
        the bias will not be applied

        :param biasValue: the chosen bias
        :return: None
        """

        # First we check that the experiment has been setup for DC bias/meas
        if self.function != 'FIX':
            print('DC measurement not setup correctly. Call self.setup_experiment before setting the bias')
            return

        # The range of the bias. We always use AUTO for the bias in the one-shot mode
        self.write(':SOUR:{0}:RANG:AUTO 1'.format(self.source))

        # We set the bias
        self.write(':SOUR:{0}:LEV {1}'.format(self.source, biasValue))

        # And wait a bit
        time.sleep(self.delay)

    def get_data(self):
        """ We get the data fromt he SMU. The order is always voltage-current. The data is a string separated by commas.
        We convert the data to an array and re-shape it in two columns. Depending of being a sweep or a single meas, we just
        fetch the data or read the data (which trigers the measurement and fetch the data)

        :return: the measured data, a tuple with two vectors: voltage and current
        """
        if self.function == 'FIX':
            data = self.query(':READ?').split(",")
        else:
            data = self.query(":FETC?").split(",")

        data = np.array(data, dtype=np.float32).reshape((-1, 2))

        return data[:, 0], data[:, 1]

    def operate_off(self):
        """ Turn off the output of the SMU

        :return: None
        """
        self.write(":OUTP OFF")

    def operate_on(self):
        """ Turn on the output of the SMU

        :return: None
        """
        self.write(":OUTP ON")

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(Keithley2430):
    """ Standarised name for the Keithley2430 class"""
    pass


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    #### Configure Keithly and run sweep ####
    keith = New('GPIB::20')
    #
    keith.setup_measurement()

    keith.set_bias(0.5)
    keith.operate_on()
    data = keith.get_data()
    keith.operate_off()
    # # data = keith.run_sweep(biasStart, biasStop, biasStep, biasRange, biasDelay)
    keith.close()

    # np.savetxt('my_test_data.txt', data, delimiter='\t', header=keith.header )
    #
    # plt.semilogy(data[:,1], abs(data[:,0]))
    # plt.show()

