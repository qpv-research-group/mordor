__author__ = 'D. Alonso-Álvarez'

import tkinter as tk
from tkinter import ttk

import numpy as np
from Experiments.batch_control import Batch


class IV:
    """ Base class for IV experiments """

    def __init__(self, master, devman, in_batch=False):

        self.master = master
        self.dm = devman
        self.id = 'iv'

        # Create the main variables of the class
        self.in_batch = in_batch
        self.create_variables()

        # Pre-load the batch, witout creating any interface
        self.header = 'Voltage (V)\tAbs(Current) (A)\tCurrent (A)'
        self.extension = 'iv'
        self.batch = Batch(self.master, self.dm, fileheader=self.header)

        # Create the interface
        self.create_interface()
        self.plot_format = {'ratios': (1, 1),
                            'xlabel': 'Voltage (V)',
                            'Ch1_ylabel': 'Abs(Current) (A)',
                            'Ch2_ylabel': 'Current (A)',
                            'Ch1_scale': 'log',
                            'Ch2_scale': 'linear'}

        # We load the dummy devices by default
        self.fill_devices()

    def quit(self):
        """ Safe closing of the devices. The devices must be closed by the Device Manager, not directly,
        so they are registered as "free".
        """

        if self.smu is not None:
            self.dm.close_device(self.smu)

        self.batch.window.destroy()

    def create_variables(self):

        # Data variables
        self.record = None

        # Hardware variables
        self.smu = None

        # Adquisition variables
        self.integration_time = 300
        self.delay = 100
        self.stop = True

    def create_menu_bar(self):
        """ Add elememnts to the master menubar
        """

        # Hardware menu
        self.master.menu_hardware.add_command(label='SMU', command=lambda: self.smu.interface(self.master))
        self.master.menu_hardware.entryconfig("SMU", state="disabled")

        # Batch menu
        if not self.in_batch:
            self.master.menu_batch.add_command(label='Disable', command=self.batch.disable)
            self.master.menu_batch.add_command(label='Temperature', command=lambda: self.new_batch('Temperature'))
            self.master.menu_batch.add_command(label='Time', command=lambda: self.new_batch('Time'))

    def new_batch(self, batch_mode):
        """ Shows current batch window or, if a different batch is chosen, destroys the old one and creates a new one
        for the new batch mpde

        :param batch_mode: the selected type of batch
        :return: None
        """
        if self.batch.mode == batch_mode:
            self.batch.show()
        else:
            self.batch.window.destroy()
            self.batch = Batch(self.master, self.dm, mode=batch_mode, fileheader=self.header)

    def create_interface(self):

        # Add elements to the menu bar
        self.create_menu_bar()

        iv_frame = ttk.Frame(self.master.control_frame)
        iv_frame.grid(column=0, row=0, sticky=(tk.EW))
        iv_frame.columnconfigure(0, weight=1)

        # Hardware widgets
        hardware_frame = ttk.Labelframe(iv_frame, text='Selected hardware:', padding=(0, 5, 0, 15))
        hardware_frame.grid(column=0, row=0, sticky=(tk.EW))
        hardware_frame.columnconfigure(0, weight=1)

        self.smu_var = tk.StringVar()
        self.smu_box = ttk.Combobox(master=hardware_frame, textvariable=self.smu_var, state="readonly")
        self.smu_box.grid(column=0, row=0, sticky=(tk.EW))
        self.smu_box.bind('<<ComboboxSelected>>', self.select_smu)

        # Set widgets ---------------------------------
        set_frame = ttk.Labelframe(iv_frame, text='Set:', padding=(0, 5, 0, 15))
        set_frame.grid(column=0, row=1, sticky=(tk.EW))
        set_frame.columnconfigure(1, weight=1)

        self.integration_time_button = ttk.Button(master=set_frame, text='Integration time (ms)', command=self.update_integration_time)
        self.integration_time_list = ttk.Combobox(set_frame, state="readonly", width=10)

        self.waiting_time_button = ttk.Button(master=set_frame, text='Waiting time (ms)', command=self.update_waiting_time)
        self.waiting_time_entry = ttk.Entry(master=set_frame, width=10)
        self.waiting_time_entry.insert(0, '10')

        self.integration_time_button.grid(column=0, row=2, sticky=(tk.EW))
        self.integration_time_list.grid(column=1, row=2, sticky=(tk.EW))
        self.waiting_time_button.grid(column=0, row=3, sticky=(tk.EW))
        self.waiting_time_entry.grid(column=1, row=3, sticky=(tk.EW))

        self.source_var = tk.StringVar()
        self.source_var.set('v')
        ttk.Radiobutton(set_frame, text="Voltage (V)", variable=self.source_var, value='v', command=self.mode).grid(column=0, row=4, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(set_frame, text="Current (A)", variable=self.source_var, value='i', command=self.mode).grid(column=1, row=4, sticky=(tk.E, tk.W, tk.S))

        # Scan widgets ---------------------------------
        scan_frame = ttk.Labelframe(iv_frame, text='Scan:', padding=(0, 5, 0, 15))
        scan_frame.columnconfigure(0, weight=1)
        scan_frame.grid(column=0, row=3, sticky=(tk.EW))

        self.start_var = tk.StringVar()
        self.start_var.set('0.00')
        self.start_label = ttk.Label(scan_frame, text='Start (V): ')
        self.start_label.grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=scan_frame, width=10, textvariable=self.start_var).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))

        self.stop_var = tk.StringVar()
        self.stop_var.set('1.00')
        self.stop_label = ttk.Label(scan_frame, text='Stop (V): ')
        self.stop_label.grid(column=0, row=1, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=scan_frame, width=10, textvariable=self.stop_var).grid(column=1, row=1, sticky=(tk.E, tk.W, tk.S))

        self.step_var = tk.StringVar()
        self.step_var.set('0.05')
        self.step_label = ttk.Label(scan_frame, text='Step (V): ')
        self.step_entry = ttk.Entry(master=scan_frame, width=10, textvariable=self.step_var)

        self.points_label = ttk.Label(scan_frame, text='Points (per decade): ')
        self.points_list = ttk.Combobox(scan_frame, state="readonly", width=10)

        self.compliance_var = tk.StringVar()
        self.compliance_var.set('0.01')
        self.compliance_label = ttk.Label(scan_frame, text='Compliance (A): ')
        self.compliance_label.grid(column=0, row=3, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(scan_frame, width=10, textvariable=self.compliance_var).grid(column=1, row=3, sticky=(tk.E, tk.W, tk.S))

        # Combobox containing the available hardware
        ttk.Label(scan_frame, text='Range: ').grid(column=0, row=4, sticky=(tk.E, tk.W, tk.S))
        self.range_list = ttk.Combobox(scan_frame,  state="readonly", width=10)
        self.range_list.grid(column=1, row=4, sticky=(tk.E, tk.W, tk.S))

        # The "Run" button is only available if not in batch mode
        if not self.in_batch:
            self.run_button = ttk.Button(master=scan_frame, width=10, text='Run', command=self.start_stop_scan)
            self.run_button.grid(column=1, row=98, sticky=( tk.E, tk.W, tk.S))

    def fill_devices(self):
        """ Fills the device selectors with the corresponding type of devices

        :return: None
        """
        self.smu_box['values'] = self.dm.get_devices(['SMU'])
        self.smu_box.current(0)

        self.select_smu()

    def select_smu(self, *args):
        """ When the SMU selector changes, this function updates some variables and the graphical interface
        to adapt it to the selected device.

        :param args: Dummy variable that does nothing but must exist (?)
        :return: None
        """

        if self.smu is not None:
            self.dm.close_device(self.smu)

        dev_name = self.smu_var.get()
        self.smu = self.dm.open_device(dev_name)

        if self.smu is None:
            self.smu_box.current(0)
            self.smu = self.dm.open_device(self.smu_var.get())

        elif self.dm.current_config[dev_name]['Type'] == 'SMU':
            self.source_var.set('v')
            self.range_list['values'] = self.smu.i_range
            self.range_list.current(0)
            self.integration_time_list['values'] = self.smu.int_time
            self.integration_time_list.current(0)
            self.points_list['values'] = self.smu.log_points
            self.points_list.current(1)
            self.mode()

        else:
            self.smu_box.current(0)
            self.smu = self.dm.open_device(self.smu_var.get())

        # If the device has an interface to set options, we link it to the entry in the menu
        interface = getattr(self.smu, "interface", None)
        if callable(interface):
            self.master.menu_hardware.entryconfig("SMU", state="normal")
        else:
            self.master.menu_hardware.entryconfig("SMU", state="disabled")

    def mode(self):
        """ When the bias mode is changed, this function updates some internal variables and the graphical interface

        :return: None
        """

        if self.source_var.get() == 'v':
            self.start_label['text'] = 'Start (V): '
            self.stop_label['text'] = 'Stop (V): '
            self.compliance_label['text'] = 'Compliance (A): '
            self.range_list['values'] = self.smu.i_range
            self.start_var.set('0')
            self.stop_var.set('1')
            self.compliance_var.set('1e-3')
            self.step_label.grid(column=0, row=2, sticky=(tk.E, tk.W, tk.S))
            self.step_entry.grid(column=1, row=2, sticky=(tk.E, tk.W, tk.S))
            self.points_label.grid_forget()
            self.points_list.grid_forget()

        else:
            self.start_label['text'] = 'Start (A): '
            self.stop_label['text'] = 'Stop (A): '
            self.compliance_label['text'] = 'Compliance (V): '
            self.range_list['values'] = self.smu.v_range
            self.start_var.set('1e-9')
            self.stop_var.set('1e-3')
            self.compliance_var.set('2')
            self.points_label.grid(column=0, row=2, sticky=(tk.E, tk.W, tk.S))
            self.points_list.grid(column=1, row=2, sticky=(tk.E, tk.W, tk.S))
            self.step_label.grid_forget()
            self.step_entry.grid_forget()

    def update_integration_time(self):
        """ Sets the value of the integration time. Informtaion IS sent to the instrument.

        :return:
        """
        self.integration_time = int(self.integration_time_list.current())
        self.smu.update_integration_time(self.integration_time)
        
    def update_waiting_time(self):
        """ Sets the value of the delay between applying a bias and taking the measurement. Informtaion IS sent to the instrument.

        :return:
        """
        self.delay = int(self.waiting_time_entry.get())
        self.smu.update_waiting_time(self.delay)

    def update_compliance_and_range(self):
        """ Sets the value of the variables compliance and meas_range. Information IS NOT sent to the instrument.

        :return: None
        """
        self.compliance = float(self.compliance_var.get())
        self.meas_range = self.range_list.current()

    def start_stop_scan(self):
        """ Starts and stops an scan

        :return: None
        """
        if self.stop:
            self.stop = False

            if self.batch.ready:
                self.run_button['text'] = 'Stop batch'
            else:
                self.run_button['state'] = 'disabled'
            self.prepare_scan()
        else:
            if self.batch.ready:
                self.batch.ready = False
                self.stop = True
                self.run_button['text'] = 'Run'
                self.run_button['state'] = 'disabled'

    def prepare_scan(self):
        """ Any scan is divided in three stages:
        1) Prepare the conditions of the scan (this function), getting starting point, integration time and creating all relevant variables.
        2) Runing the scan, performed by a recursive function "get_next_datapoint"
        3) Finish the scan, where we update some variables and save the data.

        :return: None
        """
        mode = self.source_var.get()

        start = float(self.start_var.get())
        stop = float(self.stop_var.get())
        step = float(self.step_var.get())
        points = int(self.points_list.current())

        integration_time = int(self.integration_time_list.current())
        delay = int(self.waiting_time_entry.get())
        compliance = float(self.compliance_var.get())
        meas_range = self.range_list.current()

        self.options = {'source':   mode,
                        'start':    start,
                        'stop':     stop,
                        'step':     step,
                        'points':   points,
                        'compliance':compliance,
                        'measRange':meas_range,
                        'delay':    delay,
                        'intTime':  integration_time}

        # # If we are in a batch, we proceed to the next point
        if self.batch.ready:
            self.batch.batch_proceed()

        print('Starting scan...')

        # Create the record array. In this case it is irrelevant
        self.record = np.zeros((points+1, 3))
        self.record[:, 0] = np.linspace(0, 1, points+1)
        self.record[:, 1] = np.ones_like(self.record[:, 1])
        self.record[:, 2] = np.ones_like(self.record[:, 1])

        self.master.prepare_meas(self.record)
        self.start_scan()

    def start_scan(self):

        measTime = self.smu.measure(**self.options)
        self.master.window.after(int(measTime), self.get_data)

    def get_data(self):

        data0, data1 = self.smu.get_data()

        self.record = np.zeros((len(data0), 3))
        self.record[:, 0] = data0
        self.record[:, 1] = abs(data1)
        self.record[:, 2] = data1

        self.master.update_plot(self.record)
        self.finish_scan()

    def finish_scan(self):
        """ Finish the scan, updating some global variables, saving the data in the temp file and offering to save the
        data somewhere else.

        :return: None
        """

        if self.batch.ready:
            self.master.finish_meas(self.record, finish=False)
            self.batch.batch_wrapup(self.record)
        else:
            self.master.finish_meas(self.record, finish=True)
            self.stop = True

        if self.stop or not self.batch.ready:
            # We reduce the number of counts in the batch to resume at the unfinished point if necessary
            # In other words, it repeats the last, un-finished measurement
            self.batch.count = self.batch.count - 1
            self.run_button['state'] = 'enabled'

        else:
            self.prepare_scan()

