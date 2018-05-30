__author__ = 'D. Alonso-Álvarez'

import numpy as np
import visa
from tkinter import messagebox


class Keithley236:
    """ Keithley 236 Source Measure Unit

    """
    def __init__(self, address='GPIB::20', name='Keithley 236', info=None):
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
        self.write("J0X")

        # Ask for the name of the device
        print(self.query("U0X"))

        # set trigger to respond to GPIB HOX commands
        self.write("T4,0,0,1X")
        # enable triggers
        self.write("R1X")

        self.i_range = ['auto', '1e-9 A', '10e-9 A', '100e-9 A', '1e-6 A', '10e-6 A', '100e-6 A', '1e-3 A', '10e-3 A', '100e-3 A']
        self.v_range = ['auto', '1.1 V', '11 V']
        self.log_points = ['5', '10', '25', '50']
        self.int_time = ['0.416', '4', '16.67', '20']

    def query(self, msg):
        """ Send a message to the instrument and then waits for an answer.

        :param msg: command to be executed in the instrument
        :return: the answer to that command
        """
        answer = self.device.query(msg)
        return answer

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
        """ Sets the functionality of the source, what to bias and how to do it.

        :param function: 'dc' or 'sweep', dc or sweep operating function
        :param source: 'v' or 'i', voltage or current source
        :return: None
        """

        source_dict = {'v':'0','i':'1'}
        function_dict = {'dc':'0','sweep':'1'}

        try:
            source = source_dict[source.lower()]
            function = function_dict[function.lower()]
        except(KeyError):
            raise ValueError('ERROR: bad values for source and/or function')

        self.write('F{0},{1}X'.format(source, function))
        self.source = source
        self.function = function

    def update_compliance(self, compliance, measRange):
        """ Updates the compliance and the measurement range.

        :param compliance: current or voltage compliance, oposite to the selected source
        :param measRange: the meas range as the index of self.i_range or self.v_range
        :return: None
        """
        self.write("L{0},{1}X".format(compliance, measRange))
        self.compliance = compliance
        self.measRange = measRange

    def update_integration_time(self, new_time):
        """ Sets the integration time.

        :param new_time: new integration time as the index from the self.int_time list
        :return: None
        """
        self.write("S{0}X".format(int(new_time)))
        self.itime = new_time

    def update_waiting_time(self, new_time):
        """ Sets the delay time between setting a bias and starting a measurement

        :param new_time: New delay time in ms.
        :return: None
        """
        self.delay = new_time

    def setup_measurement(self, function='dc', source='v', compliance=2, measRange=0, delay=0, intTime=0):
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

        # We program the sweep. We always use the AUTO fixed range for the bias, as it might cover may orders of magnitude
        if source == 'v':
            # create a linear stair sweep.
            self.write("Q1," + repr(start) + "," + repr(stop) + "," + repr(step) + ",0," + repr(self.delay) + "X")
        else:
            # create a logarithmic stair sweep.
            self.write("Q2," + repr(start) + "," + repr(stop) + "," + repr(points) + ",0," + repr(self.delay) + "X")

        # We estimate the runing time of the sweep, set the timeout time accordingly and return the control to the IV module.
        # This will wait in a "safe way" during the measurement, avoiding freezing the program
        str1 = self.query("U8X").replace("DSS", "SMS")
        self.totalPoints = int(str1.replace('SMS', ''))
        minimumWait = 10
        measTime = self.totalPoints * (self.itime + self.delay + minimumWait)
        if self.measRange == 0:
            measTime = measTime * 10
        self.device.timeout = None
        print("Waiting for Keithley.\nEstimated measurement time = {} s".format(measTime / 1000))

        # Turn on the source
        self.operate_on()
        # trigger the sweep
        self.write("H0X")

        return measTime

    def set_bias(self, biasValue=0.0):
        """ Set a bias to the source. If the source is not turned on or the function is not set to 'dc',
        the bias will not be applied

        :param biasValue: the chosen bias
        :return: None
        """
        # First we check that the experiment has been setup for DC bias/meas
        if int(self.function) != 0:
            print (self.function)
            print('DC measurement not setup correctly. Call self.setup_experiment before setting the bias')
            return

        # The range of the bias. We always use AUTO for the bias in the one-shot mode
        self.write("B{0},0,{1}X".format(biasValue, self.delay))

        # trigger the sweep
        self.write("H0X")

    def get_data(self):
        """ We get the data fromt he SMU. The order is always bias-meas, so we need to invert the output in order to
        have voltage-current, regardless of who is the bias or the meas. The data is a string separated by commas.
        We convert the data to an array and re-shape it in two columns.

        :return: the measured data, a tuple with two vectors: voltage and current
        """

        # If we are in sweep function, we have to really wait until the meas is finished. Then, we have to turn off the source.
        # In the dc function, the source is turn off externally
        if int(self.function) == 1:

            # Loop until the sweep is done. Whe check the current number of meas in the buffer. When the meas if finished,
            # this should be equal to the number of total data points
            num = -1
            while (num != self.totalPoints):
                num = int(self.query("U11X").replace('SMS', ''))

            # And then we turn the source off
            self.operate_off()

            # Get the data with no prefix and no suffix
            data = self.query("G5,2,2X").replace("\r\n", "").split(',')
        else:
            # Get the data with no prefix and no suffix
            data = self.query("G5,2,0X").replace("\r\n", "").split(',')

        data = np.array(data, dtype=np.float32).reshape((-1, 2))

        # Depending of what we are biasing, we invert the order of the output
        if int(self.source) == 0:
            return data[:, 0], data[:, 1]
        else:
            return data[:, 1], data[:, 0]

    def operate_off(self):
        """ Turn off the output of the SMU

        :return: None
        """
        self.write("N0X")

    def operate_on(self):
        """ Turn on the output of the SMU

        :return: None
        """
        self.write("N1X")

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(Keithley236):
    """ Standarised name for the Keithley236 class"""
    pass


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    #### Configure Keithly and run sweep ####
    keith = New('GPIB::3')
    #
    # Measurement conditions
    biasSource = 'v'
    voltageCompliance = 2
    currentCompliance = 1
    biasStart = 1e-9
    biasStop = 0.01
    biasStep = 1
    biasRange = 0
    biasDelay = 10
    measRange = 'auto'

    # keith.set_source_function(biasSource, 'sweep', currentCompliance, measRange)
    # data = keith.run_sweep(biasStart, biasStop, biasRange=0, biasPoints=2, mode='log')
    # keith.close()

    # keith.set_source_function('dc', biasSource)
    keith.setup_measurement(function='dc', source=biasSource, compliance=currentCompliance,
                            measRange=biasRange, delay=biasDelay, intTime=0)
    keith.set_bias(0.7)
    data = keith.get_data()
    print(data)
    keith.operate_off()
    # # data = keith.run_sweep(biasStart, biasStop, biasStep, biasRange, biasDelay)
    keith.close()

    # np.savetxt('my_test_data.txt', data, delimiter='\t', header=keith.header )
    #
    # plt.semilogy(data[:,1], abs(data[:,0]))
    # plt.show()

