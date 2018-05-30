__author__ = 'Diego Alonso-Álvarez'

# Libraries
import datetime

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

from tkinter import filedialog, ttk
import tkinter as tk

import time
import sys
import os

import numpy as np

# Class definition
class Temperature(object):
    """ Some text
    """
    def __init__(self, splash, devman, exp_number):

        self.dm = devman
        self.experiment_number = exp_number
        self.splash = splash

        self.create_interface()

        self.recording = False
        self.heater_on = False
        self.ramp = 300

        # We load the dummy devices by default
        self.fill_devices()

    def _quit(self):
        self.dm.close_device(self.control)
        self.window.destroy()
        self.splash.show(minus_experiment=True)

    def start_recording(self):

        if not self.recording:
            self.recording = True
            self.record()
        else:
            self.recording = False

    def enable_heater(self):

        if not self.heater_on:
            self.heater_on = True
            self.heater_var.set('Disable heater')
            self.control.setHeater('ON')
        else:
            self.heater_on = False
            self.heater_var.set('Enable heater')
            self.control.setHeater('OFF')

    def record(self):

        # At the begining, we update the first elements of the arrays
        if self.temperature_array[0] == 0:
            self.time_array = [datetime.datetime.now()]
            self.setpoint_array = [self.control.getSP()]
            self.temperature_array = [self.control.getTemp()]
            # self.setpoint_var.set(self.control.setPoint)
            # self.setpoint = self.control.setPoint
            # self.updateSetpoint()
            self.update_refresh_time()
            time.sleep(1)

        newT = self.control.getTemp()
        newSP = self.control.setPoint
        self.temp_var.set('{0:.2f}'.format(newT))

        self.time_array.append(datetime.datetime.now())
        self.setpoint_array.append(newSP)
        self.temperature_array.append(newT)

        # if we are in a ramp, we update the setpoint
        if abs(self.setpoint-newSP) > 0:
            delta = self.time_array[-1] - self.time_ini
            newSP = self.temp_ini + self.ramp*min(delta.seconds, self.time_to_SP)
            self.countdown_var.set('{0:.2f}'.format(self.time_to_SP-delta.seconds))
            self.control.setSP(newSP)
            self.current_setpoint_var.set('{0:.2f}'.format(self.control.setPoint))

        self.update_plot(self.time_array, self.setpoint_array, self.temperature_array)

        if self.recording:
            self.window.after(self.refresh_time, self.record)

    def update_plot(self, x, y1, y2):

        self.T_plot.lines[0].set_xdata(x)
        self.T_plot.lines[0].set_ydata(y1)
        self.T_plot.lines[1].set_xdata(x)
        self.T_plot.lines[1].set_ydata(y2)

        self.T_plot.set_xbound(lower=x[0], upper=x[-1])
        self.T_plot.set_ybound(lower=np.min(y2), upper=np.max(y2))

        self.canvas.draw()

    def update_refresh_time(self):
        self.refresh_time = int(float(self.refresh_time_var.get())*1000)

    def reset(self):
        self.temperature_array = [0]

    def updateSetpoint(self):
        self.time_ini = datetime.datetime.now()
        self.temp_ini = self.control.setPoint
        self.setpoint = self.setpoint_var.get()

        ramp = self.ramp_var.get()
        if ramp == 0:
            ramp = 1

        self.ramp = abs(float(ramp)/60) * (-1)**(self.setpoint < self.temp_ini)
        self.time_to_SP = (self.setpoint - self.temp_ini)/self.ramp

        print('Ramp to {0:.2f}K in {1:.2f} s.\n'.format(self.setpoint, self.time_to_SP))

    def saveRecord(self):

        f = filedialog.asksaveasfile(defaultextension='txt')

        if f is not None:
            for i in range(len(self.time_array)):
                savedata = self.time_array[i].isoformat() + '\t' + \
                           '{0:.2f}'.format(self.temperature_array[i]) + '\t' +\
                           '{0:.2f}'.format(self.setpoint_array[i]) + '\n'
                f.write(savedata)
            f.close()

    def select_controller(self, *args):

        if self.control is not None:
            self.dm.close_device(self.control)

        dev_name = self.control_var.get()
        self.control = self.dm.open_device(dev_name)
        self.setpoint_var.set(self.control.getSP())
        self.setpoint = self.control.setPoint
        self.current_setpoint_var.set(self.control.setPoint)

        if self.control is None:
            self.control_box.current(0)
            self.control = self.dm.open_device(self.control_var.get())
            self.setpoint_var.set(self.control.getSP())
            self.setpoint = self.control.setPoint
            self.current_setpoint_var.set(self.control.setPoint)

    def fill_devices(self):
        """ Fills the device selectors with the corresponding type of devices

        :return:
        """

        self.control_box['values'] = self.dm.get_devices(['Temperature_controller'])
        self.control_box.current(0)

        self.control = None
        self.select_controller()

    def create_menu_bar(self):
        """ Creates the menu bar and the elements within
        """
        self.menubar = tk.Menu(self.window)
        self.window['menu'] = self.menubar

        self.menu_file = tk.Menu(self.menubar)
        self.menu_hardware = tk.Menu(self.menubar)
        self.menu_help = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_hardware, label='Hardware')
        self.menubar.add_cascade(menu=self.menu_help, label='Help')

        # File menus
        self.menu_file.add_command(label='New experiment', command=self.open_new_experiment)
        self.menu_file.add_command(label='Save record', command=self.saveRecord)
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Leave Mordor', command=self._quit)

        # Hardware menu
        self.menu_hardware.add_command(label='Hardware configuration', command=self.dm.show)
        self.menu_hardware.add_separator()

        # Help menu
        self.menu_help.add_command(label='Documentation', command=self.open_documentation)

    def open_new_experiment(self):
        """ Opens the splash screen to run a new experiment, in paralel to the current one

        :return: None
        """

        self.splash.show()

    def open_documentation(self):
        """ Opens the documentation in the web browser

        :return: None
        """
        import webbrowser
        address = 'file:' + os.path.join(sys.path[0], 'Doc', 'Mordor.html')
        webbrowser.open_new_tab(address)

    def create_interface(self):

        # Top level elements
        self.window = tk.Toplevel(self.splash.splashroot)
        self.window.geometry('+100+100')
        self.window.resizable(False, False)
        self.window.protocol('WM_DELETE_WINDOW', self._quit)  # Used to force a "safe closing" of the program
        self.window.option_add('*tearOff', False)  # Prevents tearing the menus
        self.window.title('Barad-dûr: Mordor\'s temperature controller')

        self.create_menu_bar()

        # Creates the main frame
        plot_frame = ttk.Frame(master=self.window, padding=(5, 5, 5, 5))
        control_frame = ttk.Frame(master=self.window, padding=(15, 15, 15, 15))
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, expand=0)
        control_frame.rowconfigure(99, weight=1)

        # Create plot area
        self.create_plot_area(plot_frame)

        # Create variables
        self.temp_var = tk.StringVar()
        self.temp_var.set('-')
        self.setpoint_var = tk.IntVar()
        self.setpoint_var.set(300)
        self.current_setpoint_var = tk.IntVar()
        self.current_setpoint_var.set(300)
        self.heater_var = tk.StringVar()
        self.heater_var.set('Enable heater')
        self.ramp_var = tk.StringVar()
        self.ramp_var.set(20.0)
        self.countdown_var = tk.IntVar()
        self.countdown_var.set(300)
        self.refresh_time_var = tk.StringVar()
        self.refresh_time_var.set(1)
        self.visualize_min_var = tk.IntVar()
        self.visualize_min_var.set(60)
        self.visualize_var = tk.IntVar()
        self.visualize_var.set(0)

        # Create the elements in the control panel
        # Hardware widgets
        hardware_frame = ttk.Labelframe(control_frame, text='Selected hardware:', padding=(0, 5, 0, 15))
        hardware_frame.columnconfigure(0, weight=1)
        hardware_frame.grid(column=0, row=0, sticky=(tk.EW))

        self.control_var = tk.StringVar()
        self.control_box = ttk.Combobox(master=hardware_frame, textvariable=self.control_var, state="readonly")
        self.control_box.bind('<<ComboboxSelected>>', self.select_controller)
        self.control_box.grid(column=0, row=0, sticky=(tk.EW))

        # Temperature frame
        temp_frame = ttk.Labelframe(control_frame, text='Temperature (K):', padding=(5, 5, 5, 15))
        temp_frame.grid(column=0, row=1, sticky=(tk.NSEW))
        temp_frame.rowconfigure(1, weight=1)
        temp_frame.columnconfigure(0, weight=1)

        ttk.Label(master=temp_frame, textvariable=self.temp_var, anchor=tk.CENTER).grid(column=0, row=0, sticky=tk.EW)
        ttk.Button(master=temp_frame, width=10, text='Record', command=self.start_recording).grid(column=0, row=1, sticky=tk.EW)

        # Set frame
        set_frame = ttk.Labelframe(master=control_frame, text='Set:', padding=(5, 5, 5, 15))
        set_frame.grid(column=0, row=2, sticky=(tk.NSEW))
        set_frame.rowconfigure(1, weight=1)
        set_frame.columnconfigure(0, weight=1)

        ttk.Label(master=set_frame, text="Target set point (K):").grid(column=0, row=0, sticky=tk.EW)
        ttk.Label(master=set_frame, text="Ramp rate (K/min):").grid(column=0, row=1, sticky=tk.EW)
        ttk.Label(master=set_frame, text="Countdown (s):").grid(column=0, row=2, sticky=tk.EW)
        ttk.Label(master=set_frame, text="Current set point (K):").grid(column=0, row=3, sticky=tk.EW)

        ttk.Entry(master=set_frame, width=10, textvariable=self.setpoint_var).grid(column=1, row=0, sticky=tk.EW)
        ttk.Entry(master=set_frame, width=10, textvariable=self.ramp_var).grid(column=1, row=1, sticky=tk.EW)
        ttk.Label(master=set_frame, textvariable=self.countdown_var).grid(column=1, row=2, sticky=tk.E)
        ttk.Label(master=set_frame, textvariable=self.current_setpoint_var).grid(column=1, row=3, sticky=tk.E)

        ttk.Button(master=set_frame, width=10, text='Set', command=self.updateSetpoint).grid(column=1, row=4, sticky=tk.EW)
        ttk.Button(master=set_frame, width=10, textvariable=self.heater_var, command=self.enable_heater).grid(column=0, row=4, sticky=tk.EW)

        # Visualize frame
        visuialize_frame = ttk.Labelframe(master=control_frame, text='Visualize:', padding=(5, 5, 5, 15))
        visuialize_frame.grid(column=0, row=3, sticky=(tk.NSEW))
        visuialize_frame.rowconfigure(1, weight=1)
        visuialize_frame.columnconfigure(0, weight=1)

        ttk.Button(master=visuialize_frame, width=10, text="Refresh time (s):", command=self.update_refresh_time)\
            .grid(column=0, row=0, sticky=tk.EW)
        ttk.Entry(master=visuialize_frame, width=10, textvariable=self.refresh_time_var).grid(column=1, row=0, sticky=tk.EW)
        ttk.Button(master=visuialize_frame, width=10, text='Reset record', command=self.reset).grid(column=0, row=1, columnspan=2, sticky=tk.EW)


        # ttk.Radiobutton(master=visuialize_frame, text="All", variable=self.visualize_var, value=0).grid(column=0, row=1, sticky=tk.EW)
        # ttk.Radiobutton(master=visuialize_frame, text="Last (min):", variable=self.visualize_var, value=1).grid(column=0, row=2, sticky=tk.EW)
        # ttk.Entry(master=visuialize_frame, width=10, textvariable=self.visualize_min_var).grid(column=1, row=2, sticky=tk.EW)

        # # These commands give the control to the HW window. I am not sure what they do exactly.
        # self.TC_window.lift(self.master)  # Brings the hardware window to the top
        # self.TC_window.transient(self.master)  # ?

    def create_plot_area(self, frame):
        """ Creates the plotting area and the ploting variables.
        """

        xlabel = 'Time'
        ylabel = 'Temperature (K)'

        self.time_array = [datetime.datetime.now()]
        self.temperature_array = [0]
        self.setpoint_array = [0]

        f = plt.figure(figsize=(9, 8), dpi=72)
        self.T_plot = plt.subplot(111, ylabel=ylabel, xlabel=xlabel)
        self.T_plot.grid(True, color='gray')  # This is the grid of the plot, not the placing comand

        self.T_plot.plot(self.time_array, self.setpoint_array, label='Set Point')
        self.T_plot.plot(self.time_array, self.temperature_array, 'o', label='Temperature')

        f.autofmt_xdate()
        myFmt = mdates.DateFormatter('%H:%M:%S')
        self.T_plot.xaxis.set_major_formatter(myFmt)
        self.T_plot.legend(loc='lower left')
        f.tight_layout()

        self.canvas = FigureCanvasTkAgg(f, frame)
        self.canvas.get_tk_widget().pack()
        self.canvas.show()

        toolbar = NavigationToolbar2TkAgg(self.canvas, frame)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

