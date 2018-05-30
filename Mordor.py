__author__ = 'Diego Alonso-Álvarez'
__version__= '2.0_beta_4'
__email__ = 'd.alonso-alvarez@imperial.ac.uk'
__contributors__ = ['Markus Furher', 'Ture Hinrichsen', 'Jose Videira', 'Tomos Thomas', 'Thomas Wilson', 'Andrew M. Telford']

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib import gridspec
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from datetime import datetime

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from tkinter import font

import plot_utils as pu
import tools
from Experiments import Spectroscopy, IV, Temperature, Flash, CV
from Devices import device_manager

class Mordor(object):
    """ This class is the core of Mordor. It controls the ploting and saving of the data in the different experiments
    as well as ensuring that there is a safe *close* and *opening* of the program
    """

    def __init__(self, splash, experiment, devman, exp_number):
        """ Constructor of the main window and input to the program.
        """
        self.splash = splash
        self.dm = devman
        self.experiment_number = exp_number

        # Creates class variables
        self.create_class_variables()

        self.window = tk.Toplevel(self.splash.splashroot)
        self.window.title('Mordor')
        self.window.protocol('WM_DELETE_WINDOW', self._quit)      # Used to force a "safe closing" of the program
        self.window.option_add('*tearOff', False)                 # Prevents tearing the menus
        #self.window.iconbitmap(self.splash.icon)

        # Create the main visual elements
        self.make_front_end()
        self.experiment = experiment(self, self.dm)
        self.create_plot_area(self.experiment.plot_format)

        # Main loop of the program
        tools.center(self.window)

        # Check status of home directory
        self.check_home()
        self.save = Save(self.window)

    def _quit(self):
        """ Exits the program in a safe way, closing the ports and cleaning the tempdata folder.
        Only the data associated with this type of experiment (iv, spectroscopy, etc) are deleted.
        """
        q_exit = True
        if len(self.all_data_names) > 0:
            q_exit = messagebox.askyesno(message='Do you really want to leave Mordor?\nAll your unsaved efforts will be lost!!', icon='question', title='Exit?')

        if q_exit:

            for f in os.listdir(self.tempdata):
                name = f.split('.')[0]
                if self.experiment.id in name:
                    os.remove(os.path.join(self.tempdata, f))

            self.experiment.quit()
            self.window.destroy()
            self.splash.show(minus_experiment=True)

    def create_class_variables(self):
        """ Create the class variables, except the front end or plot related variables
        """

        # Define the home folders of the application
        self.home = os.path.join(os.path.expanduser("~"), '.Mordor', '')
        self.tempdata = os.path.join(self.home, 'tempdata', '')
        self.savedir = os.path.expanduser("~")

        # Add internal folders to path
        devices= os.path.join(sys.path[0], 'Devices')
        experiments = os.path.join(sys.path[0], 'Experiments')
        sys.path.append([devices, experiments])

        # Data variables
        self.all_data = []
        self.all_data_names = []
        self.selected_meas = None

    def check_home(self):
        """ Check the application home folder, creating it if doesn't exist and checking if there is data from a previous session.
        In the latter case, it offers to recover it by loading it into the application.
        """
        try:
            os.makedirs(self.home, exist_ok=True)
            os.makedirs(self.tempdata, exist_ok=True)
        except Exception:
            print('Error: The home directory can not be created.')

        if os.listdir(self.tempdata):
            q_recover = messagebox.askyesno(message='Last session was not closed properly.', detail=' Do you want to recover the data?', icon='question', title='Recover?')

            if q_recover:
                # We load the data
                try:
                    for f in os.listdir(self.tempdata):
                        name = f.split('.')[0]
                        if self.experiment.id in name:
                            self.all_data_names.append(f.split('.')[0])
                            data = np.loadtxt(os.path.join(self.tempdata, f))
                            self.all_data.append(data)

                    for name in self.all_data_names:
                        self.data_list.insert(tk.END, name)

                    if len(self.all_data_names) > 0:
                        self.replot_data()

                except Exception as err:
                    print('ERROR: The backup data could not be restored.')

            else:
                for f in os.listdir(self.tempdata):
                    name = f.split('.')[0]
                    if self.experiment.id in name:
                        os.remove(os.path.join(self.tempdata, f))
        else:
            pass

    def create_menu_bar(self):
        """ Creates the menu bar and the elements within
        """
        self.menubar = tk.Menu(self.window)
        self.window['menu'] = self.menubar

        self.menu_file = tk.Menu(self.menubar)
        self.menu_hardware = tk.Menu(self.menubar)
        self.menu_batch = tk.Menu(self.menubar)
        self.menu_help = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_hardware, label='Hardware')
        self.menubar.add_cascade(menu=self.menu_batch, label='Batch')
        self.menubar.add_cascade(menu=self.menu_help, label='Help')

        # File menus
        self.menu_file.add_command(label='New experiment', command=self.open_new_experiment)
        self.menu_file.add_command(label='Save spectra', command=self.save_scan)
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Leave Mordor', command=self._quit)

        # Hardware menu
        self.menu_hardware.add_command(label='Hardware configuration', command=self.dm.show)
        self.menu_hardware.add_separator()

        # Help menu
        self.menu_help.add_command(label='Documentation', command=self.open_documentation)

    def save_scan(self):
        """ Opens a dialog to save the selected data

        :return: None
        """
        if self.experiment.id == 'CV':
            self.experiment.update_header() ## This updates the file's header
            
        self.save.show((self.selected_meas,), (self.experiment.header,), (self.experiment.extension,))

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

    def create_plot_area(self, plot_format):
        """ Creates the plotting area. Its look and feel depends on the experiment.
        """
        ratios = plot_format['ratios']

        self.fig = plt.figure(figsize=(9, 8), dpi=72)
        gs = gridspec.GridSpec(2, 1, height_ratios=[ratios[0], ratios[1]])
        self.Ch1 = self.fig.add_subplot(gs[0], ylabel=plot_format['Ch1_ylabel'], xlabel=plot_format['xlabel'])
        self.Ch2 = self.fig.add_subplot(gs[1], ylabel=plot_format['Ch2_ylabel'], xlabel=plot_format['xlabel'])

        self.Ch1.grid(True, color='gray', axis='both')  # This is the grid of the plot, not the placing comand
        self.Ch2.grid(True, color='gray', axis='both')
        
        ## Test if optional plot settings are present in the specific experiment
        ## (e.g. these are all present in the CV experiment, but not in IV)
        if 'x_scale' in plot_format:
            self.Ch1.set_xscale(plot_format['x_scale'])   
            self.Ch2.set_xscale(plot_format['x_scale'])
        if 'Ch1_scale' in plot_format:
            self.Ch1.set_yscale(plot_format['Ch1_scale'])
        if 'Ch2_scale' in plot_format:
            self.Ch2.set_yscale(plot_format['Ch2_scale'])

        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.get_tk_widget().pack()
        self.canvas.show()

        toolbar = NavigationToolbar2TkAgg(self.canvas, self.plot_frame)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def make_front_end(self):
        """ Creates the visual elements of the main window: plot, toolbar, buttons...
        Only elements that might be needed outsie this function are defined as class (self) variables.

        :return: None
        """

        self.create_menu_bar()

        # The top-most containers. These must be packed and not grid in order to use the matplotlib toolbar
        self.plot_frame = ttk.Frame(master=self.window, padding=(5, 5, 5, 5))
        self.control_frame = ttk.Frame(master=self.window, padding=(5, 15, 0, 15))
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, expand=0)
        self.control_frame.rowconfigure(99, weight=1)

        # Data widgets ---------------------------------
        plot_manage_frame = ttk.Labelframe(self.control_frame, text='Data:', padding=(0, 5, 0, 15))
        plot_manage_frame.rowconfigure(1, weight=1)
        plot_manage_frame.columnconfigure(0, weight=1)

        self.data_list = tk.Listbox(master=plot_manage_frame)
        self.data_list.bind('<<ListboxSelect>>', self.update_data_selected)
        data_list_scroll = ttk.Scrollbar( master=plot_manage_frame, orient=tk.VERTICAL, command=self.data_list.yview)
        self.data_list.configure(yscrollcommand=data_list_scroll.set)
        clear_button = ttk.Button(master=plot_manage_frame, text='CLEAR ALL', command=self.clearAxis)
        clear_sel_button = ttk.Button(master=plot_manage_frame, text='Clear Selected', command=self.remove_selected)

        plot_manage_frame.grid(column=0, row=99, sticky=(tk.NSEW))
        self.data_list.grid(column=0, row=1, sticky=(tk.NSEW))
        data_list_scroll.grid(column=1, row=1, sticky=(tk.NS))
        clear_sel_button.grid(column=0, row=2, sticky=(tk.EW, tk.S))
        clear_button.grid(column=0, row=3, sticky=(tk.EW, tk.S))


    def clearAxis(self):
        """ Delete any previous measurements from the plots and variables. The data is not removed from the temp folder.

        :return: None
        """

        # Removes all previous plots
        n = len(self.Ch1.lines)
        for i in range(n):
            self.Ch1.lines.remove(self.Ch1.lines[0])
            self.Ch2.lines.remove(self.Ch2.lines[0])

        self.canvas.draw()

        self.all_data = []
        self.all_data_names = []
        self.selected_meas = None

        if n > 0:
            self.data_list.delete(0, last=tk.END)
            

    def prepare_meas(self, initial_data):

        # Set the color of any previous plot to black
        n = len(self.Ch1.lines)
        for i in range(n):
            plt.setp(self.Ch1.lines[i], color='k')
            plt.setp(self.Ch2.lines[i], color='k')
        
        self.Ch1.plot(initial_data[:, 0], initial_data[:, 1]+1, 'r')
        self.Ch2.plot(initial_data[:, 0], initial_data[:, 2]+1, 'r')
        # We are reading both channels simultaneously            


    def finish_meas(self, data, finish):
        """ Finish the measurement, updating some global variables, saving the data in the temp file and offering
        to save the data somewhere else
        """
        print('Finish!\n\a')        # Adds a 'beep' to the end of the meas

        self.all_data.append(data)
        self.all_data_names.append(self.experiment.id + '_' + datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
        self.selected_meas = self.all_data[-1]

        np.savetxt(self.tempdata + self.all_data_names[-1] + '.txt', self.selected_meas)
        self.data_list.insert(tk.END, self.all_data_names[-1])

        if finish:
            self.save_scan()

    def update_plot(self, data):
        """ Updates the plots with new data """

        pu.update(self.Ch1, data[:, 1], data[:, 0])
        pu.update(self.Ch2, data[:, 2], data[:, 0])

        self.canvas.draw()
        
    def update_plot_axis(self, plot_format): ## When Y labels are changed
        pu.update_labels(self.Ch1, plot_format['xlabel'], plot_format['Ch1_ylabel'])
        pu.update_labels(self.Ch2, plot_format['xlabel'], plot_format['Ch2_ylabel'])
        pu.update_yscales(self.Ch1, plot_format['Ch1_scale'])
        pu.update_yscales(self.Ch2, plot_format['Ch2_scale'])
        pu.update_xscales(self.Ch1, plot_format['x_scale'])
        pu.update_xscales(self.Ch2, plot_format['x_scale'])
        
        self.canvas.draw()

    def clear_plot(self, xtitle='X axis', ticks='on'):
        """ Removes all data from the plots, but it is not deleted from the memory, so it can be recovered """

        pu.clear(self.Ch1, xtitle=xtitle, xticks=ticks)
        pu.clear(self.Ch2, xtitle=xtitle, xticks=ticks)

    def replot_data(self, xtitle='X axis', ticks='on'):
        """ Re-plots all data from the memory """

        self.clear_plot(xtitle=xtitle, ticks=ticks)

        pu.plot_all(self.Ch1, self.all_data, idx=(0, 1), color='k')
        pu.plot_all(self.Ch2, self.all_data, idx=(0, 2), color='k')

        self.data_list.selection_clear(0, 'end')
        self.data_list.selection_set('end')
        self.data_list.see('end')
        self.update_data_selected()

        self.canvas.draw()

    def update_data_selected(self, *args):
        """ Updates the data currently selected, changing its color in the plot and makeing it available for saving.

        :param args: None usefeull, but there must be an extra variable there.
        :return: None
        """

        if len(self.all_data) == 0:
            return

        if len(self.data_list.curselection()) != 1:
            return

        j = int(self.data_list.curselection()[0])
        self.selected_meas = self.all_data[j]

        # Set the color of any previous plot to black
        n = len(self.Ch1.lines)
        for i in range(n):
            plt.setp(self.Ch1.lines[i], color='k')
            plt.setp(self.Ch2.lines[i], color='k')

        plt.setp(self.Ch1.lines[j], color='r', zorder=1000)
        plt.setp(self.Ch2.lines[j], color='r', zorder=1000)

        self.canvas.draw()

    def remove_selected(self, *args):
        j = int(self.data_list.curselection()[0])        
        if j != None:
            # Removes selected plot
            self.Ch1.lines.remove(self.Ch1.lines[j])
            self.Ch2.lines.remove(self.Ch2.lines[j])
            self.canvas.draw()

            del self.all_data[j]
            del self.all_data_names[j]
            self.selected_meas = None
            self.data_list.delete(j)
            
class Save(object):
    """ Class for saving data in a formatted way
    """

    def __init__(self, master):
        """ Constructor of the Save class

        :param master: The parent object, in this case, the Mordor  window.
        """

        self.master = master
        self.savedir = os.path.expanduser("~")
        self.create_save_window()
        self.window.withdraw()

    def show(self, data, header=(None,), extension=('txt',)):
        """ Shows the save window

        :return: None
        """

        self.data = data
        self.header = header
        self.extension = extension

        self.window.update()
        self.window.deiconify()
        tools.center(self.window)

    def create_save_window(self):
        """ Creates the front end of the save window.

        :return: None
        """

        self.window = tk.Toplevel(self.master)
        self.window.title('Save data...')
        # self.resizable(width=tk.FALSE, height=tk.FALSE)
        self.window.protocol('WM_DELETE_WINDOW', self.window.withdraw)  # We hide it rather than quiting it
        self.window.option_add('*tearOff', False)  # Prevents tearing the menus
        self.window.lift(self.master)  # Brings the save window to the top

        sel_frame = ttk.Frame(self.window, padding=(15, 15, 15, 15))
        sel_frame.rowconfigure(3, weight=1)
        sel_frame.grid(sticky=tk.NSEW)

        self.id_var = tk.StringVar()
        self.meas_var = tk.StringVar()
        self.comment_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.folder_var.set(self.savedir)

        ttk.Label(master=sel_frame, text="Sample ID:").grid(column=0, row=0, sticky=tk.EW)
        ttk.Label(master=sel_frame, text="Measurement (PL, EL...):").grid(column=0, row=1, sticky=tk.EW)
        ttk.Label(master=sel_frame, text="Comments:").grid(column=0, row=2, sticky=tk.EW)

        ttk.Entry(master=sel_frame, width=30, textvariable=self.id_var).grid(column=1, row=0, columnspan=2, sticky=tk.EW)
        ttk.Entry(master=sel_frame, width=30, textvariable=self.meas_var).grid(column=1, row=1, columnspan=2, sticky=tk.EW)
        ttk.Entry(master=sel_frame, width=30, textvariable=self.comment_var).grid(column=1, row=2, columnspan=2, sticky=tk.EW)

        ttk.Button(master=sel_frame, width=5, text='Select folder', command=self.select_folder).grid(column=0, row=3, sticky=tk.EW)
        ttk.Label(master=sel_frame, wraplength=300, textvariable=self.folder_var, justify=tk.LEFT).grid(column=1, row=3, columnspan=2, sticky=tk.EW)

        ttk.Button(master=sel_frame, width=5, text='Cancel', command=self.window.withdraw).grid(column=1, row=4, sticky=tk.EW)
        ttk.Button(master=sel_frame, width=5, text='Save', command=self.save_data).grid(column=2, row=4, sticky=tk.EW)

    def select_folder(self):

        dirname = filedialog.askdirectory(initialdir=self.savedir)

        if len(dirname) > 0:
            self.folder_var.set(dirname)
            self.savedir = dirname

    def save_data(self):

        sampleid = self.id_var.get()
        meas = self.meas_var.get()
        comment = self.comment_var.get()

        if sampleid == '' or meas == '':
            messagebox.showinfo(message='Sample ID and Measurement fields can not be empty.')
            return


        for i in range(len(self.data)):

            filename = '{0}_{1}_{2}.{3}'.format(sampleid, meas, comment, self.extension[i])

            if os.path.isfile(os.path.join(self.savedir, filename)):
                msg = 'File "{0}" already exists in this folder. Do you want to replace it?'.format(filename)
                msg = messagebox.askyesno(message=msg)
                if not msg:
                    return

            filename = os.path.join(self.savedir, filename)
            print(self.data[i].shape)
            np.savetxt(filename, self.data[i], fmt='%.4e', delimiter='\t', header=self.header[i])

        self.window.withdraw()

class Splash:
    """ This class is a experiment selector. It allows to run different instances of Mordor at the same time while keeping
    a consisten access to the hardware. It is also a nice splash screen :) .
    """

    def __init__(self):
        """ Constructor of the class.

        :return: None
        """

        self.splashroot = tk.Tk()
        self.splashroot.title('Mordor')
        self.splashroot.protocol('WM_DELETE_WINDOW', self.quit)      # Used to force a "safe closing" of the program
        self.splashroot.resizable(False, False)
        self.splashroot.option_add('*tearOff', False)  # Prevents tearing the menus
        #self.icon = os.path.join(sys.path[0], 'Graphics', 'mordor_icon.ico')
        #self.splashroot.iconbitmap(self.icon)

        # This variable keeps track of the experiments currently running.
        self.experiments = 0
        self.runing = []

        # We pre-load the Device Manager, which will be passed to each of the experiments.
        self.devman = device_manager.Devman(self.splashroot)

        # Checking the home directory
        self.check_home()


        masterframe = ttk.Frame(self.splashroot)
        masterframe.grid(column=0, row=0, sticky=tk.NSEW)

        # Add the image of the splash
        photoSplash = tk.PhotoImage(file=os.path.join('Graphics', 'splash.gif'))
        ttk.Label(masterframe, image=photoSplash).grid(column=0, row=0, sticky=tk.NSEW)

        # Set the big font style for the buttons
        style = ttk.Style()
        bigFont = font.Font(family='Helvetica', size=28, weight='bold')
        style.configure("Splash.TButton", font=bigFont, relief=tk.RAISED, padding=6)

        # Here we will add the buttons and labels
        control_frame = ttk.Frame(self.splashroot, padding=(15, 15, 15, 0))
        control_frame.grid(column=1, row=0, sticky=tk.NSEW)

        self.credits(control_frame)

        # Add the buttons, each of the associated to a different experiment.
        ttk.Button(control_frame, text='Spectroscopy', command=self.spectroscopy, style="Splash.TButton").grid(column=1, row=0, sticky=tk.NSEW)
        ttk.Button(control_frame, text='IV', command=self.iv, style="Splash.TButton").grid(column=1, row=1, sticky=tk.NSEW)
        ttk.Button(control_frame, text='Temperature', command=self.temperature, style="Splash.TButton").grid(column=1, row=2, sticky=tk.NSEW)
        ttk.Button(control_frame, text='Flash', command=self.flash, style="Splash.TButton").grid(column=1, row=3, sticky=tk.NSEW)
        ttk.Button(control_frame, text='CV', command=self.cv, style="Splash.TButton").grid(column=1, row=4, sticky=tk.NSEW)

        # Small buttons frame
        smallbuttons = ttk.Frame(control_frame)
        smallbuttons.grid(column=1, row=9, sticky=tk.SE)
        photoTools = tk.PhotoImage(file=os.path.join('Graphics', 'tools.gif'))
        tk.Button(smallbuttons, image=photoTools, command=self.devman.show, width=24, height=24, ).grid(column=2, row=0, sticky=tk.SE)
        photoHelp = tk.PhotoImage(file=os.path.join('Graphics', 'help.gif'))
        tk.Button(smallbuttons, image=photoHelp, command=self.open_documentation, width=24, height=24, ).grid(column=1, row=0, sticky=tk.SE)

        # Finally, we center the window and initiate the main loop.
        tools.center(self.splashroot)
        self.splashroot.mainloop()

    def check_home(self):
        """ Check the application home folder, creating it if doesn't exist and checking if there is data from a previous session.
        In the latter case, it offers to recover it by loading it into the application.
        """
        self.home = os.path.join(os.path.expanduser("~"), '.Mordor', '')
        self.tempdata = os.path.join(self.home, 'tempdata', '')

        try:
            os.makedirs(self.home, exist_ok=True)
            os.makedirs(self.tempdata, exist_ok=True)
        except Exception:
            print('Error: The home directory can not be created.')

    def credits(self, master):

        author = 'Mordor v{0}, by {1}\n'.format(__version__, __author__)
        mail = 'e-mail: {0}\n'.format(__email__)
        group = 'Copyright © 2015-2016\nQuantum Photovoltaics Group\nImperial College London\n\n'
        contributors = 'Contributors:'
        for i in __contributors__:
            contributors = contributors + '\n- {0}'.format(i)

        credits = author + mail + group + contributors

        ttk.Label(master, text=credits).grid(column=1, row=8, sticky=tk.S)

    def quit(self):
        """ Quit the whole program as long as there is no instance of Mordor still running

        :return: None
        """
        if self.experiments < 1:
                # for i in range(len(self.runing)):
                #     self.runing[i].destroy()
                self.devman.destroy()           # stops the device manager
                self.splashroot.destroy()       # destroys the main window
                self.splashroot.quit()          # quits the program
        else:
            self.hide()

    def hide(self):
        """ Hides the experiment selector window

        :return: None
        """
        self.splashroot.withdraw()

    def show(self, minus_experiment=False):
        """ Shows the experiment selector window

        :return: None
        """

        if minus_experiment:
            self.experiments = self.experiments - 1

        self.splashroot.update()
        self.splashroot.deiconify()

    def open_documentation(self):
        """ Opens the documentation in the web browser

        :return: None
        """
        import webbrowser
        address = 'file:' + os.path.join(sys.path[0], 'Doc', 'Mordor.html')
        webbrowser.open_new_tab(address)

    def iv(self):
        """ Creates an instance of Mordor to run IV experiments

        :return: None
        """
        self.hide()
        self.runing.append(Mordor(self, IV, self.devman, self.experiments))
        self.experiments = self.experiments + 1


    def spectroscopy(self):
        """ Creates an instance of Mordor to run Spectroscopy experiments

        :return: None
        """
        self.hide()
        self.runing.append(Mordor(self, Spectroscopy, self.devman, self.experiments))
        self.experiments = self.experiments + 1


    def temperature(self):
        """ Creates an instance of Mordor to run Spectroscopy experiments

        :return: None
        """
        self.hide()
        self.runing.append(Temperature(self, self.devman, self.experiments))
        self.experiments = self.experiments + 1

    def flash(self):
        """ Creates an instance of Mordor to run Spectroscopy experiments

        :return: None
        """
        self.hide()
        self.runing.append(Flash(self, self.devman, self.experiments, Save))
        self.experiments = self.experiments + 1
        
    def cv(self):
        """ Creates an instance of Mordor to run CV experiments

        :return: None
        """
        self.hide()
        self.runing.append(Mordor(self, CV, self.devman, self.experiments))
        self.experiments = self.experiments + 1

if __name__ == '__main__':
    splash = Splash()
