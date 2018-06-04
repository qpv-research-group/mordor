__author__ = 'A. M. Telford & D. Alonso-Álvarez'

import numpy as np
from tkinter import messagebox


class DummyZA:
    """
    Dummy Impedance Analyser Unit and template for other ZA
    """
    def __init__(self, address='GPIB::20', name='Dummy ZA', info=None):
        """ Constructor of the device class. Add here whatever initialisation routing needed by the SMU.
        Usual things are:
            - Open the device (ESSENTIAL!!!)
            - Reset it to some default values
            - Ask for its name
            - Enable it for remote use

        :param address: Port where the device is connected
        """
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)


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


    def set_za_function(self, fixed):
        """ Sets the functionality of the source, what to bias and how to do it.

        :param fixed: variable indicating whethe rbias or frequency are fixed
        :return: None
        """

        self.fixed = fixed


    def setup_measurement(self, plot_format, options):
        """ Sets up the scan.
        """

    def measure(self, options):
        """ Starts the scan.
        """


    def return_data(self):
        """ Generate random data for testing.

        :return: the generated data, a tuple with two vectors: voltage and current
        """

        totalPoints = 100
        # Get the data.
        # Here we just simulate some random data. two points for DC or a large number for a sweep
        data = np.random.rand(3*totalPoints)
        data = np.array(data, dtype=np.float32).reshape((-1, 3))

        return data[:, 0], data[:, 1], data[:, 2]


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
        
    def abort_sweep(self):
        pass

class New(DummyZA):
    """ Standarised name for the DummyZA class"""
    pass

