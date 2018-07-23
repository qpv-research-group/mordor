__author__ = 'Andrew M. Telford & D. Alonso-Álvarez'

import os
import numpy as np
import datetime
import time

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from Devices.Dummy_T_UNSW import Dummy_T_UNSW

class Temperature_batch:
    """ Base class for the batch mode in spectroscopy experiments """

    def __init__(self, master,  fileheader=''):
        """ Constructor of the Batch class

        :param root: The main window of the program
        :param devman: Device manager
        :param mode: The type of batch to be done (default='Dummy')
        :return: None
        """
        ## Setup Lakeshore336 temperature controller
        self.T_controller = Dummy_T()
        self.master = master
        self.header = fileheader
        self.timeZero = 0

        self.create_interface()

    def create_interface(self):

        time_frame = ttk.Frame(self.master.control_frame)
        time_frame.grid(column=0, row=0, sticky=(tk.EW))
        time_frame.columnconfigure(0, weight=1)

        # Set widgets ---------------------------------
        set_frame = ttk.Labelframe(time_frame, text='Set:', padding=(0, 5, 0, 15))
        set_frame.grid(column=0, row=0, sticky=(tk.EW))
        set_frame.columnconfigure(0, weight=1)

        self.temperatureStart_var = tk.IntVar()
        self.temperatureStart_var.set('300')
        ttk.Label(set_frame, text='Temperature Start [K]: ').grid(column=0, row=0, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.temperatureStart_var).grid(column=0, row=1, sticky=(tk.EW))

        self.setPoint = self.temperatureStart_var.get()

        self.temperatureEnd_var = tk.IntVar()
        self.temperatureEnd_var.set('350')
        ttk.Label(set_frame, text='Temperature End [K]: ').grid(column=1, row=0, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.temperatureEnd_var).grid(column=1, row=1, sticky=(tk.EW))

        self.temperatureStep_var = tk.IntVar()
        self.temperatureStep_var.set('10')
        ttk.Label(set_frame, text='Temperature Step [K]: ').grid(column=2, row=0, sticky=(tk.EW))
        ttk.Entry(set_frame, width=15, textvariable=self.temperatureStep_var).grid(column=2, row=1, sticky=(tk.EW))

        # Countdown widgets ---------------------------------
        #countdown_frame = ttk.Labelframe(time_frame, text='Estimated time to next point (s):', padding=(0, 5, 0, 15))
        #countdown_frame.grid(column=0, row=1, sticky=(tk.EW))
        #countdown_frame.columnconfigure(0, weight=1)

        #self.next_var = tk.StringVar()
        #self.next_var.set('')
        #ttk.Label(countdown_frame, textvariable= self.next_var, anchor=tk.CENTER).grid(column=0, row=0, sticky=(tk.EW))


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

        start = self.temperatureStart_var.get()
        end = self.temperatureEnd_var.get()
        step = self.temperatureStep_var.get()
        steps = 1+(abs(end-start)//step)
        self.stepList = range(steps)
        self.master.count = 0
        self.master.batch_length = steps
        self.rootname = os.path.join(self.master.path, rootname)
        self.master.data_file = self.rootname + '.txt'
        self.suffix = self.master.suffix_var.get()
        self.master.populate_batch_list(['Step {0}'.format(i+1) for i in self.stepList])
        self.master.ready = True

    def batch_proceed(self):
        """ This function is called from the main program to execute the next step in the batch.
        The data and the filename of this measuremtn are stored in the "step_info" variable.

        :return: None
        """
        ## Make summary file
        if self.master.count == 0:
            self.timeZero = datetime.datetime.now()
            self.master.save_batch_data(['Step', 'Temperature (K)','Start time', 'End time', 'Duration (s)', 'Filename'])

        self.ini_time = datetime.datetime.now()


        ## Send SetTemp command to Lakeshore
        if self.master.count == 0:
            self.T_controller.setSP(self.temperatureStart_var.get())
            self.temperature = self.T_controller.getTemp()
        else:
            self.setPoint = self.setPoint + self.temperatureStep_var.get()
            self.T_controller.setSP(self.setPoint)
            self.temperature = self.T_controller.getTemp()
        print(self.setPoint)
        print(self.temperature)

        ## ADD OPC SP = Temp

        if self.suffix == 0:
            self.filename = self.rootname + '_{0}.txt'.format(self.ini_time.strftime('%y%m%d_%H-%M-%S-%f'))
        else:
            self.filename = self.rootname + '_{0}.txt'.format(str(self.master.count+1).zfill(3))

        self.step_info = [self.master.count+1, self.temperature, self.ini_time.strftime('%Y-%m-%d %H:%M:%S.%f'), self.filename]
        self.step_string = 'Step = {0} \tTemperature (K) = {1} \tIni time = {2} \tFilename = {3}'.format(*self.step_info)

        print('Next point in batch {0}/{1}:\n\t {2}'.format(self.master.count+1, self.master.batch_length, self.step_string))

        self.master.update_batch_list()

    def batch_wrapup(self, data):
        """ After taking a measurement in the main function, this function takes the measured data and saves it
        following the convention of the batch

        :param data: data to be saved
        :return: None
        """
        end_time = datetime.datetime.now()

        self.step_info.insert(-1, end_time.strftime('%Y-%m-%d %H:%M:%S.%f') )
        self.step_info.insert(-1, (end_time - self.ini_time).total_seconds() )

        self.master.save_batch_data(self.step_info)

        np.savetxt(self.filename, data, fmt='%.4e', delimiter='\t',
                   header='{0}\n{1}'.format(self.step_string, self.header))

        self.master.count = self.master.count + 1
        if self.master.count == self.master.batch_length:
            self.master.update_batch_list(True)
            self.master.ready = False
            self.master.count = 0

            print('Temperature batch completed!!\n')
