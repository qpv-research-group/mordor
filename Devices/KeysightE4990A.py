__author__ = 'A. M. Telford & D. Alonso-Álvarez'

import numpy as np
from tkinter import messagebox
import visa


class KeysightE4990A:
    """
    Keysight E4990A impedance analyser class
    """
    def __init__(self, address='USB0::0x0957::0x1809::MY54101596::0::INSTR', name='Keysight E4990A', info=None):
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

        # Opening the device is essential.
        self.rm = visa.ResourceManager()
        self.device = self.rm.open_resource("{}".format(address))
        self.device.timeout = 180000 ## 180 s default timeout (e.g. for OPC?)
        
        ## Dictionary for GUI-to-machine commands translation
        
        self.translation = {'Cs (F)' : 'CS',
                            'Cp (F)' : 'CP',
                            'Rs (Ohm)' : 'RS',
                            'Rp (Ohm)' : 'RP',
                            '|Z| (Ohm)' : 'Z',
                            'Tz (deg)' : 'TZ',
			    'Zreal (Ohm)' : 'R',
			    'Zimag (Ohm)' : 'X',
                            'Idc (A)' : 'IDC',
                            'log' : 'LOGarithmic',
                            'linear' : 'LINear',
                            'up': 'UP',
                            'down':'DOWN'}

    def query(self, msg):
        """ Send a message to the instrument and then waits for an answer. depending on the nature of the device and
        how is connected, this would look different

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
        self.rm.close()

    def setup_measurement(self, plot_format, options):
        """ Prepares the measurement by setting up the scan parameters.

        :param plot_format: dictionary of setup parameters for plotting the data
        :param options: dictionary of setup parameters for the scan
        :return: None
        """
        ## Clear buffer
        self.device.write('*CLS')

        ## Set DC bias mode to Voltage
        self.device.write(':SOURce1:BIAS:MODE %s' % ('VOLTage'))
        ## Set DC current range to 1 mA
        self.device.write(':SOURce1:BIAS:RANGe %s' % ('M1')) ## 1mA
        ## DC bias constant mode ON
        self.device.write(':SOURce1:BIAS:ALC:STATe %d' % (1))
        ## DC bias monitor ON
        self.device.write(':SENSe1:DC:MEASure:ENABle %d' % (1))
        ## AC bias constant mode ON
        self.device.write(':SOURce1:ALC:STATe %d' % (1))
        self.device.write(':SOURce1:ALC:COUNt %d' % (10)) ## Number of iterations = 10
        self.device.write(':SOURce1:ALC:TOLerance %G' % (10.0)) ## target = 10%
        ## Set number of traces to 4
        self.device.write(':CALCulate1:PARameter1:COUNt %d' % (4))
        ## Turn on point averaging
        self.device.write(':SENSe1:AVERage:STATe %d' % (1))
        ## Set number of point averages
        self.device.write(':SENSe1:AVERage:COUNt %d' % (options['navg']))
        ## Set AC bias amplitude (OSC)
        self.device.write(':SOURce1:VOLTage:LEVel:IMMediate:AMPLitude %G' % (options['osc_amp']))
        ## Set sweep direction
        self.device.write(':SENSe1:SWEep:DIRection %s' % (self.translation[options['sweep_dir']]))
        ## Set sweep points
        self.device.write(':SENSe1:SWEep:POINts %d' % (options['nop']))
        
        ## Y-axis scaling (log or linear) -------------------------------------
        self.device.write(':DISPlay:WINDow1:TRACe1:Y:SPACing %s' % (self.translation[plot_format['Ch1_scale']]))
        self.device.write(':DISPlay:WINDow1:TRACe2:Y:SPACing %s' % (self.translation[plot_format['Ch2_scale']]))
        
        ## Y-axis labels      
        self.device.write(':CALCulate1:PARameter1:DEFine %s' % (self.translation[plot_format['Ch1_ylabel']]))
        self.device.write(':CALCulate1:PARameter2:DEFine %s' % (self.translation[plot_format['Ch2_ylabel']]))       
        
        
        if options['fixed'] == 'bias':
            self.device.write('SOURce1:BIAS:VOLTage:LEVel:IMMediate:AMPLitude %G' % (options['fixed_value']))
            self.device.write(':SENSe1:FREQuency:STARt %G' % (options['start']))
            self.device.write(':SENSe1:FREQuency:STOP %G' % (options['stop']))
            self.device.write(':SENSe1:SWEep:TYPE %s' % (self.translation[plot_format['x_scale']]))
            self.device.write(':CALCulate1:PARameter3:DEFine %s' % ('VAC')) ## Trace 3 = VAC
            self.device.write(':CALCulate1:PARameter4:DEFine %s' % ('IAC')) ## Trace 4 = IAC
        else:
            self.device.write(':SENSe1:FREQuency:CW %G' % (options['fixed_value']))
            self.device.write(':SOURce1:BIAS:VOLTage:STARt %G' % (options['start']))
            self.device.write(':SOURce1:BIAS:VOLTage:STOP %G' % (options['stop']))
            if plot_format['x_scale'] == 'linear':
            ## The machine has different terms for DC bias sweeps, so the
            ## translation dictionary cannot be used here
                self.device.write(':SENSe1:SWEep:TYPE %s' % ('BIAS'))
            else:
                self.device.write(':SENSe1:SWEep:TYPE %s' % ('LBIas'))
            ## The following 2 lines MUST be after setting the sweep type to Bias, otherwise an error occurs
            self.device.write(':CALCulate1:PARameter3:DEFine %s' % ('VDC')) ## Trace 3 = VDC
            self.device.write(':CALCulate1:PARameter4:DEFine %s' % ('IDC')) ## Trace 4 = IDC

    def measure(self, options):
        """ Starts and stops the measurement.
	
	:return: None
        """
	
        if options['fixed_value'] != 0:
            self.device.write(':SOURce:BIAS:STATe %s' % ('ON'))
        self.device.write(':TRIGger:SEQuence:SOURce %s' % ('BUS'))
        self.device.write(':INITiate1:CONTinuous %d' % (1))
        self.device.write(':TRIGger:SEQuence:SINGle')
        print("Waiting for Keysight E4990A...")
        self.opc = self.device.query_ascii_values('*OPC?')
        self.device.write(':SOURce:BIAS:STATe %s' % ('OFF'))

    def return_data(self):
        """ Retrieves the data from the instrument

        :return: the measured data, a tuple with three vectors, which depend on the type of measurement performed
        """
	
        ## Autoscale all traces
        self.device.write(':DISPlay:WINDow1:TRACe1:Y:SCALe:AUTO')
        self.device.write(':DISPlay:WINDow1:TRACe2:Y:SCALe:AUTO')
        self.device.write(':DISPlay:WINDow1:TRACe3:Y:SCALe:AUTO')
        self.device.write(':DISPlay:WINDow1:TRACe4:Y:SCALe:AUTO')
        
        self.device.write('CALCulate1:PARameter1:SELect') ## Select Ch1 trace
        x_data = self.device.query_ascii_values('CALCulate1:SELected:DATA:XAXis?')
        Ch1_data = self.device.query_ascii_values(':CALCulate1:SELected:DATA:FDATa?')
        Ch1_data = Ch1_data[::2] ## Skip zeroes in output data list
        self.device.write('CALCulate1:PARameter2:SELect') ## Select Ch2 trace      
        Ch2_data = self.device.query_ascii_values(':CALCulate1:SELected:DATA:FDATa?')
        Ch2_data = Ch2_data[::2] ## Skip zeroes in output data list
        data = np.column_stack((x_data, Ch1_data, Ch2_data)) ## Aggregate data
        return data[:, 0], data[:, 1], data[:, 2]


    def interface(self, master):
        """ Givces error if Mordor cannot locate a configuration file for the instrument.
	
	:return: Error - no configuration available.
	"""
	messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')
        
    def abort_sweep(self):
	""" Aborts scan.
	
	:return: None
	"""
	
        self.device.write(':ABORt')
        self.device.write(':SOURce:BIAS:STATe %s' % ('OFF'))

class New(KeysightE4990A):
    """ Standarised name for the KeysightE4990A class"""
    pass

