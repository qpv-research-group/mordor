__author__ = 'D. Alonso-Álvarez'

import numpy as np
from tkinter import messagebox


class DummySMU:
    """
    Dummy Source Measure Unit and template for other SMU
    """
    def __init__(self, address='GPIB::20', name='Dummy SMU', info=None):
        """ Constructor of the device class. Add here whatever initialisation routing needed by the SMU.
        Usual things are:
            - Open the device (ESENTIAL!!!)
            - Reset it to some default values
            - Asking for its name
            - Enable it for remote use

        :param address: Port where the device is conected
        """
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        # Opening the device is essential. Here is an example for a VISA-based instrument
        # rm = visa.ResourceManager()
        # self.device = rm.open_resource("{}".format(address))
        self.device = None

        self.i_range = ['auto', '1e-9 A', '10e-9 A', '100e-9 A', '1e-6 A', '10e-6 A', '100e-6 A', '1e-3 A', '10e-3 A',
                        '100e-3 A']
        self.v_range = ['auto', '1.1 V', '11 V']
        self.log_points = ['5', '10', '25', '50']
        self.int_time = ['0.416', '4', '16.67', '20']

    def query(self, msg):
        """ Send a message to the instrument and then waits for an answer. depending on the nature of the device and
        how is connected, this would look different

        :param msg: command to be executed in the instrument
        :return: the answer to that command
        """
        # Here is an example for a VISA-based instrument
        # answer = self.device.query(msg)
        answer = None
        return answer

    def write(self, msg):
        """ Send a message to the instrument

        :param msg: message to be sent to the instrument
        :return: None
        """
        # Here is an example for a VISA-based instrument
        # self.device.write(msg)
        pass

    def close(self):
        """ Closes the connection with the instrument

        :return: None
        """
        # Here is an example for a VISA-based instrument
        # self.device.close()
        pass


    def set_source_function(self, function, source):
        """ Sets the functionality of the source, what to bias and how to do it.

        :param function: 'dc' or 'sweep', dc or sweep operating function
        :param source: 'v' or 'i', voltage or current source
        :return: None
        """

        self.source = source
        self.function = function


    def update_compliance(self, compliance, measRange):
        """ Updates the compliance and the measurement range.

        :param compliance: current or voltage compliance, oposite to the selected source
        :param measRange: the meas range as the index of self.i_range or self.v_range
        :return: None
        """

        self.compliance = compliance
        self.measRange = measRange


    def update_integration_time(self, new_time):
        """ Sets the integration time.

        :param new_time: new integration time as the index from the self.int_time list
        :return: None
        """

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

        # We program the sweep.
        # We typically will use the AUTO fixed range for the bias, as it might cover may orders of magnitude


        # We estimate the runing time of the sweep, set the timeout time accordingly and return the control to the IV module.
        # This will wait in a "safe way" during the measurement, avoiding freezing the program
        self.totalPoints = 100
        minimumWait = 10
        measTime = self.totalPoints * (self.itime + self.delay + minimumWait)
        if self.measRange == 0:
            measTime = measTime * 10
        # self.device.timeout = None
        print("Waiting for Dummy.\nEstimated measurement time = {} s".format(measTime / 1000))


        # Finally, we trigger the sweep. Depending on the SMU, you might need to turn it on first


        return measTime


    def set_bias(self, biasValue=0.0):
        """ Set a bias to the source. If the source is not turned on or the function is not set to 'dc',
        the bias will not be applied

        :param biasValue: the chosen bias
        :return: None
        """

        # First we check that the experiment has been setup for DC bias/meas
        if self.function != 'dc':
            print('DC measurement not setup correctly. Call self.setup_experiment before setting the bias')
            return

        # Set the bias in the SMU

        # And triger it, if need it


    def get_data(self):
        """ We get the data fromt he SMU. Depending on the order provided by the SMU we need to invert the output to
        have voltage-current, regardless of who is the bias or the meas. We convert the data to an array and re-shape
        it in two columns.

        :return: the measured data, a tuple with two vectors: voltage and current
        """

        # If we are in sweep function, we have to really wait until the meas is finished. In some SMU this is not needed
        # as they will not response until they are finished. In others, they don't like to be bothered while measuring.
        # Then, we have to turn off the source if not done automatically. In the dc function, the source is turn off externally


        # Get the data.
        # Here we just simulate some random data. two points for DC or a large number for a sweep
        if self.function == 'dc':
            data = np.random.rand(2)
        else:
            data = np.random.rand(2*self.totalPoints)
        data = np.array(data, dtype=np.float32).reshape((-1, 2))


        # Depending of what we are biasing, we might need to invert the order of the output
        # We assume in the example that the source produces bias-meas and we want voltage-current, so we invert it
        if self.source == 0:
            return data[:, 0], data[:, 1]
        else:
            return data[:, 1], data[:, 0]

    def operate_off(self):
        """ Turn off the output of the SMU

        :return: None
        """
        pass

    def operate_on(self):
        """ Turn on the output of the SMU

        :return: None
        """
        pass

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')

class New(DummySMU):
    """ Standarised name for the DummySMU class"""
    pass


if __name__ == '__main__':
    smu = New(20)
    print (smu.i_range)
    smu.measure('v', 0, 1, 100)
