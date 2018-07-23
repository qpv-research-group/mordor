__author__ = 'A. M. Telford & D. Alonso-Álvarez'

import os
import numpy as np

from tkinter import filedialog, messagebox

from Experiments.cv import CV
from Experiments.batch_control_AMT1 import Batch

class CV_batch(CV):
    """ Base class for the batch mode in CV experiments """

    def __init__(self, master, devman, fileheader='', in_batch=True):
        """ Constructor of the CV_batch class, same as CV.__init__ but without
        assignment of device.

        :param root: The main window of the program
        :param devman: Device manager
        :param mode: The type of batch to be done (default='Dummy')
        :return: None
        """
        self.master = master
        self.dm = devman
        self.id = 'CV_batch'
		

        # Create the main variables of the class
        self.in_batch = in_batch
        self.create_variables()

        self.plot_format = {'ratios': (1, 1),
                            'xlabel': 'Frequency (Hz)',
                            'x_scale' : 'log',
                            'Ch1_ylabel': '|Z| (Ω)',
                            'Ch2_ylabel': 'Θ (°)',
                            'Ch1_scale': 'log',
                            'Ch2_scale': 'log'}
        #self.update_header()
        self.header=''
        self.extension = 'txt'
        self.batch = Batch(self.master, self.dm, fileheader=self.header)
        
        # Create the interface
        self.create_interface()
        
        # We DO NOT load the dummy devices by default
        #self.fill_devices()
        self.za = self.root.experiment.za
        
        ## HIDE UNUSED INTERFACES
        
        #self.header = fileheader
        #CV.__init__(self, master, devman, in_batch=True)
        #self.za = device
		

    def batch_ready(self):
        """ After selecting all the conditions for the batch, we arrange the last things, select the folder to save
        the data and fill the batch list. The batch is then ready to be launched.

        :return: None
        """

        rootname = self.master.get_rootname()
        if rootname == '': return

        temp = filedialog.askdirectory(initialdir=self.master.path)
        if temp == '':
            return
        else:
            self.master.path = temp

        mode = 'fixed' ## Call to fixed_var in CV experiment

        start = float(self.start_var.get())
        stop = float(self.stop_var.get())
        #step = float(self.step_var.get())
        nop = int(self.nop_var.get())

        #integration_time = int(self.integration_time_list.current())
        #delay = int(self.waiting_time_entry.get())
        #compliance = float(self.compliance_var.get())
        #meas_range = self.range_list.current()

        
        step = (stop - start)/nop
        self.valuesList = np.arange(start, stop + 0.0001 * step, step)
        #else:
        #    totalPoints = int(np.log10(max(stop, start) / max(1e-9, min(stop, start))) * points) + 1
        #    ini = np.log10(max(start, 1e-9))
        #    fin = np.log10(max(stop, 1e-9))
        #    self.biasList = np.logspace(ini, fin, totalPoints)

        self.master.count = 0
        self.master.batch_length = len(self.valuesList)

        self.options = {'fixed':   mode,
                        'start':    start,
                        'stop':     stop,
                        'nop':     nop}

        rootname = os.path.join(self.master.path, rootname)
        self.master.data_file = rootname + '.txt'
        suffix = self.master.suffix_var.get()
        if suffix == 0:
            self.filenames = [rootname + '_{0}_{1:.4e}.txt'.format(mode.upper(), bias) for bias in self.valuesList]
        else:
            self.filenames = [rootname + '_{0}.txt'.format(str(i+1).zfill(3)) for i in range(self.master.batch_length)]

        self.master.populate_batch_list(['{0} = {1:.4e}'.format(mode.upper(), bias) for bias in self.valuesList])

        self.master.ready = True

    def batch_proceed(self):
        """ This function is called from the main program to execute the next step in the batch.
        The voltage, current and the filename of this measuremtn are stored in the "step_info" variable.

        :return: None
        """

        if self.master.count == 0:
            self.za.setup_measurement(**self.options)
            self.za.operate_on()
            self.master.save_batch_data(['Voltage (V)', 'Current (A)', 'Filename'])

        fxd = self.valuesList[self.master.count]
        #self.za.set_fxd(fxdValue=fxd)
        fixed_param = self.za.get_data()

        self.step_info = [self.master.count, fixed_param[0], self.filenames[self.master.count]]
        self.step_string = 'V = {1:.3f} V\tI = {2:.4e} A\tFilename = {3}'.format(*self.step_info)

        print('Next point in batch {0}/{1}:\n\t {2}'.format(self.master.count+1, self.master.batch_length, self.step_string))

        self.master.update_batch_list()

    def batch_wrapup(self, data):
        """ After taking a measurement in the main function, this function takes the measured data and saves it
        following the convention of the batch

        :param data: data to be saved
        :return: None
        """
        self.master.save_batch_data(self.step_info)

        np.savetxt(self.filenames[self.master.count], data, fmt='%.4e', delimiter='\t',
                   header='{0}\n{1}'.format(self.step_string, self.header))

        self.master.count = self.master.count + 1
        if self.master.count == self.master.batch_length:
            self.master.update_batch_list(True)
            self.master.ready = False
            self.master.count = 0
            self.za.operate_off()

            print('IV batch completed!!\n')
