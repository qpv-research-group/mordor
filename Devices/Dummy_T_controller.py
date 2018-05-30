__author__ = 'Diego Alonso-Álvarez'

# Libraries
import datetime

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

from tkinter import messagebox, ttk
import tkinter as tk
from tkinter import filedialog

import numpy as np
import time

# Class definition
class Dummy_T_controller(object):
    def __init__(self, port='COM9', name='Dummy T controller', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.setPoint = 300
        self.temperature = (2*np.random.rand()-1) + self.setPoint

    def close(self):
        pass

    def getVersion(self):
        return 'Dummy T controller'

    def getTemp(self):
        self.temperature = (2 * np.random.rand() - 1) + self.setPoint
        return self.temperature

    def getSP(self):
        return self.setPoint

    def setSP(self, value):
        self.setPoint = value
        pass

    def setHeater(self, value):
        pass


class New(Dummy_T_controller):
    """ Standarised name for the Dummy_monochromator class"""
    pass


# Class definition
class T_controller:
    """ Some text
    """
    def __init__(self, master=None):

        self.control = Dummy_T_controller(port=None)
        print(self.control.getVersion())

        self.recording = False
        self.heater_on = False
        self.ramp = 300

        self.master = master
        self.create_interface()

    def _quit(self):
        self.control.close()
        self.TC_window.quit()

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
            self.updateSetpoint()
            self.update_refresh_time()
            time.sleep(1)

        newT = self.control.getTemp()
        newSP = self.control.setPoint
        self.temp_var.set('{0:.2f}'.format(newT))

        self.time_array.append(datetime.datetime.now())
        self.setpoint_array.append(newSP)
        self.temperature_array.append(newT)

        # if we are in a ramp, we update the setpoint
        if abs(self.setpoint - newSP) > 0:
            delta = self.time_array[-1] - self.time_ini
            newSP = self.temp_ini + self.ramp * min(delta.seconds, self.time_to_SP)
            self.countdown_var.set(self.time_to_SP - delta.seconds)
            self.control.setSP(newSP)

        self.update_plot(self.time_array, self.setpoint_array, self.temperature_array)

        if self.recording:
            self.master.after(self.refresh_time, self.record)

    def update_plot(self, x, y1, y2):

        self.T_plot.lines[0].set_xdata(x)
        self.T_plot.lines[0].set_ydata(y1)
        self.T_plot.lines[1].set_xdata(x)
        self.T_plot.lines[1].set_ydata(y2)

        self.T_plot.set_xbound(lower=x[0], upper=x[-1])
        self.T_plot.set_ybound(lower=np.min(y2), upper=np.max(y2))

        self.canvas.draw()

    def update_refresh_time(self):
        self.refresh_time = int(float(self.refresh_time_var.get()) * 1000)

    def updateSetpoint(self):
        self.time_ini = datetime.datetime.now()
        self.temp_ini = self.control.setPoint
        self.setpoint = self.setpoint_var.get()

        ramp = self.ramp_var.get()
        if ramp == 0:
            ramp = 1

        self.ramp = abs(float(ramp) / 60) * (-1) ** (self.setpoint < self.temp_ini)
        self.time_to_SP = (self.setpoint - self.temp_ini) / self.ramp

    def saveRecord(self):

        f = filedialog.asksaveasfile(defaultextension='txt')

        if f is not None:
            for i in range(len(self.time_array)):
                savedata = self.time_array[i].isoformat() + '\t' + \
                           '{0:.2f}'.format(self.temperature_array[i]) + '\t' + \
                           '{0:.2f}'.format(self.setpoint_array[i]) + '\n'
                f.write(savedata)
            f.close()

    def create_interface(self):

        # Top level elements
        self.TC_window = tk.Toplevel(self.master)
        self.TC_window.geometry('+100+100')
        self.TC_window.resizable(False, False)
        self.TC_window.protocol('WM_DELETE_WINDOW', self._quit)  # Used to force a "safe closing" of the program
        self.TC_window.option_add('*tearOff', False)  # Prevents tearing the menus
        self.TC_window.title('Barad-dûr: Mordor\'s temperature controller')

        # Creates the main frame
        plot_frame = ttk.Frame(master=self.TC_window, padding=(5, 5, 5, 5))
        control_frame = ttk.Frame(master=self.TC_window, padding=(15, 15, 15, 15))
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
        self.heater_var = tk.StringVar()
        self.heater_var.set('Enable heater')
        self.ramp_var = tk.StringVar()
        self.ramp_var.set(5.0)
        self.countdown_var = tk.IntVar()
        self.countdown_var.set(300)
        self.refresh_time_var = tk.StringVar()
        self.refresh_time_var.set(1)
        self.visualize_min_var = tk.IntVar()
        self.visualize_min_var.set(60)
        self.visualize_var = tk.IntVar()
        self.visualize_var.set(0)

        # Create the elements in the control panel
        # Temperature frame
        temp_frame = ttk.Labelframe(control_frame, text='Temperature (K):', padding=(5, 5, 5, 15))
        temp_frame.grid(column=0, row=0, sticky=(tk.NSEW))
        temp_frame.rowconfigure(1, weight=1)
        temp_frame.columnconfigure(0, weight=1)

        ttk.Label(master=temp_frame, textvariable=self.temp_var, anchor=tk.CENTER).grid(column=0, row=0,
                                                                                        sticky=tk.EW)
        ttk.Button(master=temp_frame, width=10, text='Record', command=self.start_recording).grid(column=0, row=1,
                                                                                                  sticky=tk.EW)

        # Set frame
        set_frame = ttk.Labelframe(master=control_frame, text='Set:', padding=(5, 5, 5, 15))
        set_frame.grid(column=0, row=1, sticky=(tk.NSEW))
        set_frame.rowconfigure(1, weight=1)
        set_frame.columnconfigure(0, weight=1)

        ttk.Label(master=set_frame, text="Set point (K):").grid(column=0, row=0, sticky=tk.EW)
        ttk.Label(master=set_frame, text="Ramp rate (K/min):").grid(column=0, row=1, sticky=tk.EW)
        ttk.Label(master=set_frame, text="Countdown (s):").grid(column=0, row=2, sticky=tk.EW)

        ttk.Entry(master=set_frame, width=10, textvariable=self.setpoint_var).grid(column=1, row=0, sticky=tk.EW)
        ttk.Entry(master=set_frame, width=10, textvariable=self.ramp_var).grid(column=1, row=1, sticky=tk.EW)
        ttk.Label(master=set_frame, textvariable=self.countdown_var).grid(column=1, row=2, sticky=tk.E)

        ttk.Button(master=set_frame, width=10, text='Set', command=self.updateSetpoint).grid(column=1, row=3,
                                                                                             sticky=tk.EW)
        ttk.Button(master=set_frame, width=10, textvariable=self.heater_var, command=self.enable_heater).grid(
            column=0, row=3, sticky=tk.EW)

        # Visualize frame
        visuialize_frame = ttk.Labelframe(master=control_frame, text='Visualize:', padding=(5, 5, 5, 15))
        visuialize_frame.grid(column=0, row=2, sticky=(tk.NSEW))
        visuialize_frame.rowconfigure(1, weight=1)
        visuialize_frame.columnconfigure(0, weight=1)

        ttk.Button(master=visuialize_frame, width=10, text="Refresh time (s):", command=self.update_refresh_time) \
            .grid(column=0, row=0, sticky=tk.EW)
        ttk.Entry(master=visuialize_frame, width=10, textvariable=self.refresh_time_var).grid(column=1, row=0,
                                                                                              sticky=tk.EW)

        # ttk.Radiobutton(master=visuialize_frame, text="All", variable=self.visualize_var, value=0).grid(column=0, row=1, sticky=tk.EW)
        # ttk.Radiobutton(master=visuialize_frame, text="Last (min):", variable=self.visualize_var, value=1).grid(column=0, row=2, sticky=tk.EW)
        # ttk.Entry(master=visuialize_frame, width=10, textvariable=self.visualize_min_var).grid(column=1, row=2, sticky=tk.EW)

        ttk.Button(master=visuialize_frame, width=10, text='Save T record', command=self.saveRecord).grid(column=0,
                                                                                                          row=3,
                                                                                                          columnspan=2,
                                                                                                          sticky=tk.EW)

        # These commands give the control to the HW window. I am not sure what they do exactly.
        self.TC_window.lift(self.master)  # Brings the hardware window to the top
        self.TC_window.transient(self.master)  # ?

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


# Testing
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    test = T_controller(master=root)
    root.mainloop()
