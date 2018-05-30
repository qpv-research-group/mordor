__author__ = 'D. Alonso-Álvarez'

import os
import numpy as np

from tkinter import filedialog, messagebox

from Experiments.iv import IV

class IV_batch(IV):
    """ Base class for the batch mode in spectroscopy experiments """

    def __init__(self, master, devman, fileheader=''):
        """ Constructor of the Batch class

        :param root: The main window of the program
        :param devman: Device manager
        :param mode: The type of batch to be done (default='Dummy')
        :return: None
        """
        self.header = fileheader
        IV.__init__(self, master, devman, in_batch=True)

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

        mode = self.source_var.get()

        start = float(self.start_var.get())
        stop = float(self.stop_var.get())
        step = float(self.step_var.get())
        points = int(self.points_list['values'][int(self.points_list.current())])

        integration_time = int(self.integration_time_list.current())
        delay = int(self.waiting_time_entry.get())
        compliance = float(self.compliance_var.get())
        meas_range = self.range_list.current()

        if mode == 'v':
            self.biasList = np.arange(start, stop + 0.0001 * step, step)
        else:
            totalPoints = int(np.log10(max(stop, start) / max(1e-9, min(stop, start))) * points) + 1
            ini = np.log10(max(start, 1e-9))
            fin = np.log10(max(stop, 1e-9))
            self.biasList = np.logspace(ini, fin, totalPoints)

        self.master.count = 0
        self.master.batch_length = len(self.biasList)

        self.options = {'function': 'dc',
                        'source': mode,
                        'compliance': compliance,
                        'measRange': meas_range,
                        'delay': delay,
                        'intTime': integration_time}

        rootname = os.path.join(self.master.path, rootname)
        self.master.data_file = rootname + '.txt'
        suffix = self.master.suffix_var.get()
        if suffix == 0:
            self.filenames = [rootname + '_{0}_{1:.4e}.txt'.format(mode.upper(), bias) for bias in self.biasList]
        else:
            self.filenames = [rootname + '_{0}.txt'.format(str(i+1).zfill(3)) for i in range(self.master.batch_length)]

        self.master.populate_batch_list(['{0} = {1:.4e}'.format(mode.upper(), bias) for bias in self.biasList])

        self.master.ready = True

    def batch_proceed(self):
        """ This function is called from the main program to execute the next step in the batch.
        The voltage, current and the filename of this measuremtn are stored in the "step_info" variable.

        :return: None
        """

        if self.master.count == 0:
            self.smu.setup_measurement(**self.options)
            self.smu.operate_on()
            self.master.save_batch_data(['Voltage (V)', 'Current (A)', 'Filename'])

        bias = self.biasList[self.master.count]
        self.smu.set_bias(biasValue=bias)
        volt, curr = self.smu.get_data()

        self.step_info = [self.master.count, volt[0], curr[0], self.filenames[self.master.count]]
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
            self.smu.operate_off()

            print('IV batch completed!!\n')
