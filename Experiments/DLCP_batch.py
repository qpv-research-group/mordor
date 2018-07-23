__author__ = 'Andrew M. Telford & D. Alonso-Álvarez'

import os
import numpy as np
import datetime
import time

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

#from Devices.Dummy_T_AMT import Dummy_T

class DLCP_batch:
    """ Base class for the batch mode in DLCP experiments """

    def __init__(self, master,  fileheader=''):
        """ Constructor of the Batch class

        :param master: the script batch_control.py
        :return: None
        """
        self.master = master
        self.header = fileheader

        self.create_interface()

    def create_interface(self):

        bias_frame = ttk.Frame(self.master.control_frame)
        bias_frame.grid(column=0, row=0, sticky=(tk.EW))
        bias_frame.columnconfigure(0, weight=1)

        # Set widgets ---------------------------------
        set_frame = ttk.Labelframe(bias_frame, text='Set:', padding=(0, 5, 0, 15))
        set_frame.grid(column=0, row=0, sticky=(tk.EW))
        set_frame.columnconfigure(0, weight=1)

        self.minAC_var = tk.DoubleVar()
        self.minAC_var.set('0.01')
        ttk.Label(set_frame, text='Min AC bias [V]: ').grid(column=0, row=0, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.minAC_var).grid(column=0, row=1, sticky=(tk.EW))

        self.maxAC_var = tk.DoubleVar()
        self.maxAC_var.set('0.1')
        ttk.Label(set_frame, text='Maximum AC bias [V]: ').grid(column=1, row=0, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.maxAC_var).grid(column=1, row=1, sticky=(tk.EW))

        self.ACstep_var = tk.DoubleVar()
        self.ACstep_var.set('0.01')
        ttk.Label(set_frame, text='AC bias step [V]: ').grid(column=2, row=0, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.ACstep_var).grid(column=2, row=1, sticky=(tk.EW))

        self.maxDC_var = tk.DoubleVar()
        self.maxDC_var.set('-0.5')
        ttk.Label(set_frame, text='Upper DC bias [V]: ').grid(column=0, row=2, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.maxDC_var).grid(column=1, row=3, sticky=(tk.EW))


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

        start = self.minAC_var.get()
        end = self.maxAC_var.get()
        step = self.ACstep_var.get()
        steps = 1+(abs(end-start)/step)

        self.stepList = range(int(steps))
        self.master.count = 0
        self.master.batch_length = steps
        self.rootname = os.path.join(self.master.path, rootname)
        self.master.data_file = self.rootname + '.txt'
        self.suffix = self.master.suffix_var.get()
        self.master.populate_batch_list(['Step {0}'.format(i+1) for i in self.stepList])
        self.master.ready = True

    def batch_proceed(self):
        """ This function is called from the main program to execute the next step in the batch.
        The data and the filename of this measurement are stored in the "step_info" variable.

        :return: None
        """
        ## Make summary file
        if self.master.count == 0:
            #self.timeZero = datetime.datetime.now()
            self.master.save_batch_data(['Step', 'AC bias [V]', 'DC bias [V]', 'Start time', 'End time', 'Duration (s)', 'Filename'])

        self.ini_time = datetime.datetime.now()

        ## Send AC/DC parameters to CV experiment
        # Include delay for transmission

        ## Calculate AC/DC biases
        if self.master.count == 0:
            self.AC = self.minAC_var.get()
        else:
            self.AC = round(self.AC + self.ACstep_var.get(), 3)
        self.DC = self.maxDC_var.get() - self.AC/2
        print("DC bias is: ", self.DC)

        ## Send AC/DC bias values to CV
        ################################

        if self.suffix == 0:
            self.filename = self.rootname + '_{0}.txt'.format(self.ini_time.strftime('%y%m%d_%H-%M-%S-%f'))
        else:
            self.filename = self.rootname + '_{0}.txt'.format(str(self.master.count+1).zfill(3))

        self.step_info = [self.master.count+1, self.AC, self.DC, self.ini_time.strftime('%Y-%m-%d %H:%M:%S.%f'), self.filename]
        self.step_string = 'Step = {0} \tStart time = {3} \tFilename = {4}'.format(*self.step_info)

        print('Next point in batch {0}/{1}:\n\t {2}'.format(self.master.count+1, self.master.batch_length, self.step_string))

        self.master.update_batch_list()

    def batch_wrapup(self, data):
        """ After taking a measurement in the main function, this function takes the measured data and saves it
        following the convention of the batch

        :param data: data to be saved
        :return: None
        """
        end_time = datetime.datetime.now()

        self.step_info.insert(-1, end_time.strftime('%Y-%m-%d %H:%M:%S.%f'))
        self.step_info.insert(-1, (end_time - self.ini_time).total_seconds())

        self.master.save_batch_data(self.step_info)

        np.savetxt(self.filename, data, fmt='%.4e', delimiter='\t',
                   header='{0}\n{1}'.format(self.step_string, self.header))

        self.master.count = self.master.count + 1
        if self.master.count == self.master.batch_length:
            self.master.update_batch_list(True)
            self.master.ready = False
            self.master.count = 0

            print('DLCP batch completed!!\n')
