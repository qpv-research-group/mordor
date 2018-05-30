__author__ = 'D. Alonso-Álvarez'

import numpy as np

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from Experiments.batch_control import Batch


class Spectroscopy:
    """ Base class for spectroscopy experiments """

    def __init__(self, master, devman):

        self.master = master
        self.dm = devman
        self.id = 'spec'
        self.header = 'Wavelength (nm)\tCh-1\tCh-2'
        self.extension = 'txt'

        # Pre-load the batch, witout creating any interface
        self.batch = Batch(self.master, self.dm, fileheader=self.header)

        # Create the main variables of the class
        self.create_variables()

        # Create the interface
        self.create_interface()
        self.plot_format = {'ratios' : (3, 1),
                            'xlabel' : 'Wavelength (nm)',
                            'Ch1_ylabel' : 'Ch-1',
                            'Ch2_ylabel' : 'Ch-2',
                            'Ch1_scale' : 'linear',
                            'Ch2_scale' : 'linear'}

        # We load the dummy devices by default
        self.fill_devices()

    def quit(self):
        """ Safe closing of the devices. The devices must be closed by the Device Manager, not directly,
        so they are registered as "free".
        """

        if self.monochromator is not None:
            self.dm.close_device(self.monochromator)
        if self.adquisition is not None:
            self.dm.close_device(self.adquisition)

        self.batch.quit()

    def create_variables(self):

        # Data variables
        self.record = None
        self.background = None

        # Hardware variables
        self.monochromator = None
        self.adquisition = None

        # Adquisition variables
        self.integration_time = 300
        self.waiting_time = 100
        self.stop = True

    def create_interface(self):

        # Add elements to the menu bar
        self.create_menu_bar()

        # Creates the spectroscopy frame
        self.spectroscopy_frame = ttk.Frame(master=self.master.control_frame)
        self.spectroscopy_frame.grid(column=0, row=0, sticky=(tk.EW))
        self.spectroscopy_frame.columnconfigure(0, weight=1)

        # Hardware widgets
        hardware_frame = ttk.Labelframe(self.spectroscopy_frame, text='Selected hardware:', padding=(0, 5, 0, 15))
        hardware_frame.columnconfigure(0, weight=1)
        hardware_frame.grid(column=0, row=0, sticky=(tk.EW))

        self.mono_var = tk.StringVar()
        self.adq_var = tk.StringVar()
        self.monochromator_box = ttk.Combobox(master=hardware_frame, textvariable=self.mono_var, state="readonly")
        self.adquisition_box = ttk.Combobox(master=hardware_frame, textvariable=self.adq_var, state="readonly")

        self.monochromator_box.bind('<<ComboboxSelected>>', self.select_monochromator)
        self.adquisition_box.bind('<<ComboboxSelected>>', self.select_adquisition)

        self.monochromator_box.grid(column=0, row=0, sticky=(tk.EW))
        self.adquisition_box.grid(column=0, row=1, sticky=(tk.EW))

        # Set widgets ---------------------------------
        set_frame = ttk.Labelframe(self.spectroscopy_frame, text='Set:', padding=(0, 5, 0, 15))
        set_frame.columnconfigure(1, weight=1)

        self.GoTo_button = ttk.Button(master=set_frame, text='GoTo', command=self.goto)
        self.GoTo_entry = ttk.Entry(master=set_frame, width=10)
        self.GoTo_entry.insert(0, '700.0')
        self.integration_time_button = ttk.Button(master=set_frame, text='Integration time (ms)',
                                                  command=self.update_integration_time)
        self.integration_time_entry = ttk.Entry(master=set_frame, width=10)
        self.integration_time_entry.insert(0, '300')
        self.waiting_time_button = ttk.Button(master=set_frame, text='Waiting time (ms)',
                                              command=self.update_waiting_time)
        self.waiting_time_entry = ttk.Entry(master=set_frame, width=10)
        self.waiting_time_entry.insert(0, '100')

        set_frame.grid(column=0, row=1, sticky=(tk.EW))
        self.GoTo_button.grid(column=0, row=0, sticky=(tk.EW))
        self.GoTo_entry.grid(column=1, row=0, sticky=(tk.EW))
        self.integration_time_button.grid(column=0, row=2, sticky=(tk.EW))
        self.integration_time_entry.grid(column=1, row=2, sticky=(tk.EW))
        self.waiting_time_button.grid(column=0, row=3, sticky=(tk.EW))
        self.waiting_time_entry.grid(column=1, row=3, sticky=(tk.EW))

        # Live adquisition widgets
        live_frame = ttk.Labelframe(self.spectroscopy_frame, text='Live:', padding=(0, 5, 0, 15))
        live_frame.columnconfigure(1, weight=1)
        live_frame.columnconfigure(2, weight=1)

        self.window_live_lbl = ttk.Label(master=live_frame, text="Window (points):")
        self.window_live_entry = ttk.Entry(master=live_frame, width=10)
        self.window_live_entry.insert(0, '100')

        self.record_live_button = ttk.Button(master=live_frame, text='Record', command=self.record_live)
        self.pause_live_button = ttk.Button(master=live_frame, text='Pause', state=tk.DISABLED, command=self.pause_live)

        live_frame.grid(column=0, row=2, sticky=(tk.EW))
        self.window_live_lbl.grid(column=0, row=0, sticky=(tk.EW))
        self.window_live_entry.grid(column=1, row=0, columnspan=2, sticky=(tk.EW))
        self.record_live_button.grid(column=1, row=3, sticky=(tk.EW))
        self.pause_live_button.grid(column=2, row=3, sticky=(tk.EW))

        # Scan widgets ---------------------------------
        scan_frame = ttk.Labelframe(self.spectroscopy_frame, text='Scan:', padding=(0, 5, 0, 15))
        scan_frame.columnconfigure(0, weight=1)

        Start_lbl = ttk.Label(master=scan_frame, text="Start (nm):")
        self.Start_entry = ttk.Entry(master=scan_frame)
        self.Start_entry.insert(0, '700.0')
        Stop_lbl = ttk.Label(master=scan_frame, text="Stop (nm):")
        self.Stop_entry = ttk.Entry(master=scan_frame)
        self.Stop_entry.insert(0, '900.0')
        Step_lbl = ttk.Label(master=scan_frame, text="Step (nm):")
        self.Step_entry = ttk.Entry(master=scan_frame)
        self.Step_entry.insert(0, '5.0')

        self.scan_button = ttk.Button(master=scan_frame, text='Run', command=self.start_stop_scan, width=7)
        self.pause_button = ttk.Button(master=scan_frame, text='Pause', state=tk.DISABLED, command=self.pause_scan,
                                       width=7)

        scan_frame.grid(column=0, row=3, sticky=(tk.EW))
        Start_lbl.grid(column=0, row=0, sticky=(tk.EW))
        self.Start_entry.grid(column=1, row=0, columnspan=2, sticky=(tk.EW))
        Stop_lbl.grid(column=0, row=1, sticky=(tk.EW))
        self.Stop_entry.grid(column=1, row=1, columnspan=2, sticky=(tk.EW))
        Step_lbl.grid(column=0, row=2, sticky=(tk.EW))
        self.Step_entry.grid(column=1, row=2, columnspan=2, sticky=(tk.EW))
        self.scan_button.grid(column=1, row=3, sticky=(tk.EW))
        self.pause_button.grid(column=2, row=3, sticky=(tk.EW))

        # Background widgets
        self.background_frame = ttk.Labelframe(self.spectroscopy_frame, text='Background:', padding=(0, 5, 0, 15))
        self.background_frame.columnconfigure(0, weight=1)
        self.background_frame.columnconfigure(1, weight=1)
        self.background_button = ttk.Button(master=self.background_frame, text='Get', command=self.get_background)
        self.clear_background_button = ttk.Button(master=self.background_frame, text='Clear',
                                                  command=self.clear_background)

        self.background_frame.grid(column=0, row=4, sticky=(tk.NSEW))
        self.background_button.grid(column=0, row=0, sticky=(tk.EW, tk.S))
        self.clear_background_button.grid(column=1, row=0, sticky=(tk.EW, tk.S))

    def create_menu_bar(self):
        """ Add elememnts to the master menubar
        """

        # Hardware menu
        self.master.menu_hardware.add_command(label='Monochromator', command=lambda: self.monochromator.interface(self.master))
        self.master.menu_hardware.entryconfig("Monochromator", state="disabled")
        self.master.menu_hardware.add_command(label='Adquisition', command=lambda: self.adquisition.interface(self.master))
        self.master.menu_hardware.entryconfig("Adquisition", state="disabled")

        # Batch menu
        self.master.menu_batch.add_command(label='Disable', command=self.batch.disable)
        self.master.menu_batch.add_command(label='IV', command=lambda: self.new_batch('IV'))
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
            self.batch.quit()
            self.batch = Batch(self.master, self.dm, mode=batch_mode)

    def fill_devices(self):
        """ Fills the device selectors with the corresponding type of devices

        :return:
        """

        self.monochromator_box['values'] = self.dm.get_devices(['Monochromator'])
        self.monochromator_box.current(0)
        self.adquisition_box['values'] = self.dm.get_devices(['Lock-In', 'Spectrometer'])
        self.adquisition_box.current(0)

        self.select_monochromator()
        self.select_adquisition()

    def select_monochromator(self, *args):

        if self.monochromator is not None:
            self.dm.close_device(self.monochromator)

        dev_name = self.mono_var.get()
        self.monochromator = self.dm.open_device(dev_name)

        if self.monochromator is None:
            self.monochromator_box.current(0)
            self.monochromator = self.dm.open_device(self.mono_var.get())

        elif self.dm.current_config[dev_name]['Type'] == 'Monochromator':
            self.move = self.monochromator.move

        else:
            self.monochromator_box.current(0)
            self.monochromator = self.dm.open_device(self.mono_var.get())

        # If the device has an interface to set options, we link it to the entry in the menu
        interface = getattr(self.monochromator, "interface", None)
        if callable(interface):
            self.master.menu_hardware.entryconfig("Monochromator", state="normal")
        else:
            self.master.menu_hardware.entryconfig("Monochromator", state="disabled")

    def select_adquisition(self, *args):
        """ When the adquisition selector changes, this function updates some variables and the graphical interface
        to adapt it to the selected device.

        :param args: Dummy variable that does nothing but must exist (?)
        :return: None
        """

        if self.adquisition is not None:
            self.dm.close_device(self.adquisition)

        dev_name = self.adq_var.get()
        self.adquisition = self.dm.open_device(dev_name)

        if self.adquisition is None:
            self.adquisition_box.current(0)
            self.adquisition = self.dm.open_device(self.adq_var.get())

        elif self.dm.current_config[dev_name]['Type'] == 'Spectrometer':
            self.move = self.null
            self.prepare_scan = self.prepare_scan_spectrometer
            self.get_next_datapoint = self.mode_spectrometer
            self.start_live = self.prepare_live_spectrometer
            self.live = self.live_spectrometer
            self.background_frame.grid(column=0, row=4, sticky=(tk.NSEW))
            self.window_live_lbl.grid_forget()
            self.window_live_entry.grid_forget()
            self.monochromator_box['state'] = 'disabled'
            self.Step_entry['state'] = 'disabled'
            self.GoTo_button['state'] = 'disabled'
            self.GoTo_entry['state'] = 'disabled'

        elif self.dm.current_config[dev_name]['Type'] in ['Lock-In', 'Multimeter']:
            self.move = self.monochromator.move
            self.prepare_scan = self.prepare_scan_lockin
            self.get_next_datapoint = self.mode_lockin
            self.start_live = self.prepare_live_lockin
            self.live = self.live_lockin
            self.background_frame.grid_forget()
            self.window_live_lbl.grid(column=0, row=0, sticky=(tk.EW))
            self.window_live_entry.grid(column=1, row=0, columnspan=2, sticky=(tk.EW))
            self.monochromator_box['state'] = 'normal'
            self.Step_entry['state'] = 'normal'
            self.GoTo_button['state'] = 'normal'
            self.GoTo_entry['state'] = 'normal'

        else:
            self.adquisition_box.current(0)
            self.adquisition = self.dm.open_device(self.adq_var.get())

        interface = getattr(self.adquisition, "interface", None)
        if callable(interface):
            self.master.menu_hardware.entryconfig("Adquisition", state="normal")
        else:
            self.master.menu_hardware.entryconfig("Adquisition", state="disabled")

    def null(self, *args, **kwargs):
        """ Empty function that does nothing

        :return: None
        """
        pass

    def start_stop_scan(self):
        """ Starts and stops an scan

        :return: None
        """
        if self.stop:
            self.prepare_scan()
        else:
            self.stop = True
            self.finish_scan()

    def pause_scan(self):
        """ Pauses an scan or resumes the adquisition

        :return: None
        """
        self.stop = not self.stop

        if self.stop:
            self.pause_button['text'] = 'Resume'
        else:
            self.pause_button['text'] = 'Pause'

        self.get_next_datapoint()

    def prepare_scan_lockin(self):
        """ Any scan is divided in three stages:
        1) Prepare the conditions of the scan (this function), getting starting point, integration time and creating all relevant variables.
        2) Runing the scan, performed by a recursive function  "mode_spectrometer" or "mode_lockin"
        3) Finish the scan, where we update some variables and save the data.

        :return: None
        """
        self.update_integration_time()
        self.update_waiting_time()

        # Get the scan conditions
        self.start_wl = max(float(self.Start_entry.get()), 250)
        self.stop_wl = max(min(float(self.Stop_entry.get()), 3000), self.start_wl + 1)
        step = min(max(float(self.Step_entry.get()), self.adquisition.min_wavelength), self.stop_wl - self.start_wl)

        # # If we are in a batch, we proceed to the next point
        if self.batch.ready:
            self.batch.batch_proceed()

        self.move(self.start_wl, speed='Fast')
        print('Starting scan...')

        # Create the record array
        self.size = int(np.ceil((self.stop_wl - self.start_wl + 0.5 * step) / step))
        self.num = self.size
        self.record = np.zeros((self.size, 3))
        self.record[:, 0] = np.arange(self.start_wl, self.stop_wl + 0.5 * step, step)
        self.record[:, 1] = self.record[:, 1] * np.NaN
        self.record[:, 2] = self.record[:, 1] * np.NaN

        self.master.prepare_meas(self.record)

        self.i = 0

        self.scan_running()

        self.mode_lockin()

    def mode_lockin(self):
        """ Gets the next data point in a scan. This function depends on the adquisition device

        :return: None
        """

        if not self.stop:
            data = self.adquisition.measure()
            self.record[self.i, 1] = data[0]
            self.record[self.i, 2] = data[1]

            self.master.update_plot(self.record)

            if self.i < self.num - 1:
                self.i += 1
                self.move(self.record[self.i, 0], speed='Fast')
                self.master.window.after(int(self.integration_time + self.waiting_time), self.mode_lockin)

            else:
                self.finish_scan()

    def prepare_scan_spectrometer(self):
        """ Any scan is divided in three stages:
        1) Prepare the conditions of the scan (this function), getting starting point, integration time and creating all relevant variables.
        2) Runing the scan, performed by a recursive function "mode_spectrometer" or "mode_lockin"
        3) Finish the scan, where we update some variables and save the data.

        :return: None
        """
        self.update_integration_time()
        self.update_waiting_time()

        # We check the background is not none and offer to update it
        if self.background is None:
            meas_bg = messagebox.askyesno(message='There is no background spectrum for this integration time!',
                                              detail='Do you want to measure it now?', icon='question',
                                              title='Measure background?')

            self.get_background(meas_bg)

        # # If we are in a batch, we proceed to the next point
        if self.batch.ready:
            self.batch.batch_proceed()

        # If the integration time is too long, we have to split the adquisition in several steps,
        # otherwise the spectrometer hangs
        self.num = int(np.ceil(self.integration_time / self.adquisition.max_integration_time))

        # Here we select the wavelength range we want to record and re-shape the record array
        # Get the scan conditions
        self.start_wl = max(float(self.Start_entry.get()), 300)
        self.stop_wl = max(min(float(self.Stop_entry.get()), 2000), self.start_wl + 1)
        wl = self.adquisition.measure()[0]
        self.idx = np.where((self.start_wl <= wl) & (wl <= self.stop_wl))
        self.size = len(self.idx[0])

        # Create the record array
        self.record = np.zeros((self.size, 3))
        self.record[:, 0] = wl[self.idx]
        self.record[:, 2] = self.background[self.idx]

        self.master.prepare_meas(self.record)

        self.i = 0

        self.scan_running()

        self.mode_spectrometer()

    def mode_spectrometer(self):
        """ Gets the whole spectrum at once recorded by the spectrometer in the range selected

        :return: None
        """

        if not self.stop:
            data = self.adquisition.measure()
            intensity = data[1][self.idx] - self.background[self.idx]
            self.record[:, 1] = (intensity + self.i * self.record[:, 1]) / (self.i + 1.)

            self.master.update_plot(self.record)

            if self.i < self.num - 1:
                self.i = self.i + 1
                self.master.window.after(int(self.integration_time / self.num), self.mode_spectrometer)

            else:
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

        if self.stop or not self.batch.ready:
            # We reduce the number of counts in the batch to resume at the unfinished point if necessary
            # In other words, it repeats the last, un-finished measurement
            self.batch.count = max(self.batch.count - 1, 0)
            self.scan_stopped()

        else:
            self.prepare_scan()

    def scan_running(self):
        """ Updates the graphical interface, disable the buttoms that must be disabled during the measurement.

        :return: None
        """
        self.scan_button['text'] = 'Stop'
        self.pause_button['state'] = 'enabled'
        self.record_live_button['state'] = 'disabled'
        self.GoTo_button['state'] = 'disabled'
        self.integration_time_button['state'] = 'disabled'
        self.waiting_time_button['state'] = 'disabled'
        self.background_button['state'] = 'disabled'
        self.clear_background_button['state'] = 'disabled'
        self.stop = False

    def scan_stopped(self):
        """ Returns the graphical interface to normal once the measurement has finished.

        :return: None
        """
        self.scan_button['text'] = 'Run'
        self.pause_button['state'] = 'disabled'
        self.record_live_button['state'] = 'enabled'
        self.GoTo_button['state'] = 'enabled'
        self.integration_time_button['state'] = 'enabled'
        self.waiting_time_button['state'] = 'enabled'
        self.background_button['state'] = 'enabled'
        self.clear_background_button['state'] = 'enabled'
        self.stop = True

    def get_background(self, meas_bg=True):
        """ Gets the background when using the spectrometer, if requested.

        :parameter: meas_bg     True or False: wether to measure a background or just produce a bg with zeros
        :return: None
        """

        if meas_bg:
            self.update_integration_time()
            self.background = self.adquisition.measure()[1]
            messagebox.showinfo(message='Background taken!', detail='Press OK to continue.', title='Background taken!')
        else:
            self.background = self.adquisition.measure()[1]*0.0

    def clear_background(self):
        """ Clears the background when using the spectrometer.

        :return: None
        """
        self.background = None

    def record_live(self):
        """ Starts and stops a live recording.

        :return: None
        """
        if self.stop:
            self.stop = False
            self.record_live_button['text'] = 'Stop'
            self.pause_live_button['state'] = 'enabled'
            self.scan_button['state'] = 'disabled'
            self.background_button['state'] = 'disabled'
            self.clear_background_button['state'] = 'disabled'
            self.start_live()
        else:
            self.record_live_button['text'] = 'Record'
            self.pause_live_button['state'] = 'disabled'
            self.scan_button['state'] = 'enabled'
            self.background_button['state'] = 'enabled'
            self.clear_background_button['state'] = 'enabled'
            self.stop = True
            self.finish_live()

    def pause_live(self):
        """ Pauses a live recording or resumes the adquisition
        """
        self.stop = not self.stop

        if self.stop:
            self.pause_live_button['text'] = 'Resume'
        else:
            self.pause_live_button['text'] = 'Pause'

        self.live()

    def prepare_live_lockin(self):
        """ Prepares the lock-in live adquisition and prepare some variables
        """
        self.goto()
        self.update_integration_time()

        self.window_points = int(self.window_live_entry.get())

        self.live_data = np.zeros((self.window_points, 3))
        self.live_data[:, 0] = np.arange(self.window_points)

        # Removes all plots, but not the data, and change the horizontal axis conditions
        self.master.clear_plot(xtitle='Time', ticks='off')
        self.master.prepare_meas(self.live_data)

        self.live_lockin()

    def live_lockin(self):
        """ Runs the live lock-in adquisition
        """
        if not self.stop:
            self.live_data[:-1, 1] = self.live_data[1:, 1]
            self.live_data[:-1, 2] = self.live_data[1:, 2]

            self.live_data[-1, 1], self.live_data[-1, 2] = self.adquisition.measure()

            self.master.update_plot(self.live_data)

            self.master.window.after(self.integration_time, self.live_lockin)

    def prepare_live_spectrometer(self):
        """ Prepares the spectrometer live adquisition and prepare some variables
        """
        self.update_integration_time()

        if self.integration_time > self.adquisition.max_integration_time:
            self.integration_time = int(self.adquisition.max_integration_time)
            self.adquisition.update_integration_time(self.integration_time)

        data0, data1 = self.adquisition.measure()

        self.live_data = np.zeros((len(data0), 3))
        self.live_data[:, 0] = data0
        self.live_data[:, 1] = data1

        # Removes all plots, but not the data, and change the horizontal axis conditions
        self.master.clear_plot(xtitle='Wavelength (nm)', ticks='on')
        self.master.prepare_meas(self.live_data)

        self.live_spectrometer()

    def live_spectrometer(self):
        """ Runs the live spectrometer adquisition
        """
        if not self.stop:
            data0, data1 = self.adquisition.measure()
            self.live_data[:, 1] = data1

            self.master.update_plot(self.live_data)

            self.master.window.after(self.integration_time, self.live_spectrometer)

    def finish_live(self):
        """ Finish the live adquisition, returning the front end to the scan mode
        """
        self.master.replot_data(xtitle='Wavelength (nm)', ticks='on')

    def update_integration_time(self):
        """ Updates the integration time
        """
        old_integration_time = self.integration_time
        self.integration_time = int(self.integration_time_entry.get())

        if old_integration_time != self.integration_time:
            self.clear_background()
            self.integration_time = self.adquisition.update_integration_time(self.integration_time)
            self.integration_time_entry.delete(0, tk.END)
            self.integration_time_entry.insert(0, '%i' % self.integration_time)

    def update_waiting_time(self):
        """ Updates the waiting time
        """
        self.waiting_time = int(self.waiting_time_entry.get())

    def goto(self):
        """ Go to the specified wavelength
        """
        wl = float(self.GoTo_entry.get())
        self.move(wl, speed='Fast')
        print('Done! Wavelength = {} nm'.format(wl))
