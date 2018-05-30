__author__ = 'D. Alonso-Álvarez'

import os
import numpy as np

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from Devices import device_manager


class Batch(object):
    """ Base class for the batch mode in spectroscopy experiments """

    def __init__(self, root, devman, fileheader='', mode='Dummy'):
        """ Constructor of the Batch class

        :param root: The main window of the program
        :param devman: Device manager
        :param mode: The type of batch to be done (default='Dummy')
        :return: None
        """
        self.root = root
        self.dm = devman
        self.ready = False
        self.count = 0
        self.batch_length = 0
        self.path = os.path.expanduser('~')
        self.data_file = None

        self.interface()

        if mode == 'IV':
            from Experiments.iv_batch import IV_batch
            self.batch_data = IV_batch(self, self.dm, fileheader=fileheader)
            self._batch_ready = self.batch_data.batch_ready
            self._batch_proceed = self.batch_data.batch_proceed
            self._batch_wrapup = self.batch_data.batch_wrapup
            self.mode = mode

        elif mode == 'Temperature':
            self.window.withdraw()
            messagebox.showinfo(message='{0} batch mode not implemented, yet.'.format(mode))
            self.mode = 'Dummy'

        elif mode == 'Time':
            from Experiments.time_batch import Time_batch
            self.batch_data = Time_batch(self, fileheader=fileheader)
            self._batch_ready = self.batch_data.batch_ready
            self._batch_proceed = self.batch_data.batch_proceed
            self._batch_wrapup = self.batch_data.batch_wrapup
            self.mode = mode

        else:
            self.window.withdraw()
            self.mode = 'Dummy'

    def null(self, *args, **kwargs):
        """ Empty function that does nothing

        :return: None
        """
        pass

    def quit(self):
        """ Destroys this object

        :return: None
        """
        self.window.destroy()

    def show(self):
        """ Shows the batch window

        :return: None
        """
        if self.mode is not 'Dummy':
            self.window.update()
            self.window.deiconify()

    def create_menu_bar(self):
        """ Creates the menu bar and the elements within

        :return: None
        """
        self.menubar = tk.Menu(self.window)
        self.window['menu'] = self.menubar

        self.menu_hardware = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_hardware, label='Hardware')

        # Hardware menu
        self.menu_hardware.add_command(label='Hardware configuration', command=self.dm.show)
        self.menu_hardware.add_separator()

    def interface(self):
        """ Creates the graphical interface for the batch

        :return: None
        """

        self.window = tk.Toplevel(self.root.window)
        self.window.title('Batch window')
        self.window.protocol('WM_DELETE_WINDOW', self.batch_cancel)  # We hide it rather than quiting it
        self.window.option_add('*tearOff', False)  # Prevents tearing the menus
        self.window.lift(self.root.window)  # Brings the hardware window to the top

        self.create_menu_bar()

        # Here we will add the corresponding batch interface, dependent on what si the batch about
        self.control_frame = ttk.Frame(master=self.window, padding=(15, 15, 15, 0))
        self.control_frame.grid(column=0, row=0, sticky=tk.NSEW)
        self.control_frame.columnconfigure(0, weight=1)

        # Here we will add the corresponding batch control (see below)
        self.batch_frame = ttk.Frame(master=self.window, padding=(15, 15, 15, 0))
        self.batch_frame.grid(column=0, row=1, sticky=tk.NSEW)
        self.control_frame.columnconfigure(0, weight=1)

        # Save widgets ---------------------------------
        save_frame = ttk.Labelframe(self.batch_frame, text='Save:', padding=(0, 5, 0, 15))
        save_frame.columnconfigure(0, weight=1)
        save_frame.grid(column=0, row=0, sticky=tk.NSEW)

        self.root_var = tk.StringVar()
        self.root_var.set('ID')
        ttk.Label(save_frame, text='Sample ID: ').grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(save_frame, width=10, textvariable=self.root_var).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))

        self.meas_var = tk.StringVar()
        self.meas_var.set('meas')
        ttk.Label(save_frame, text='Measurement: ').grid(column=0, row=1, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(save_frame, width=10, textvariable=self.meas_var).grid(column=1, row=1, sticky=(tk.E, tk.W, tk.S))

        self.comment_var = tk.StringVar()
        self.comment_var.set('')
        ttk.Label(save_frame, text='Comments: ').grid(column=0, row=2, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(save_frame, width=10, textvariable=self.comment_var).grid(column=1, row=2, sticky=(tk.E, tk.W, tk.S))

        self.suffix_var = tk.IntVar()
        self.suffix_var.set(1)
        ttk.Label(save_frame, text='Suffix: ').grid(column=0, row=52, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(save_frame, text="Batch variable", variable=self.suffix_var, value=0).grid(column=0, row=53, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(save_frame, text="Consecutive numbers", variable=self.suffix_var, value=1).grid(column=1, row=53, sticky=(tk.E, tk.W, tk.S))

        # run widgets ---------------------------------
        run_frame = ttk.Labelframe(self.batch_frame, text='Run:', padding=(0, 5, 0, 15))
        run_frame.columnconfigure(0, weight=1)
        run_frame.columnconfigure(1, weight=1)
        run_frame.columnconfigure(2, weight=1)
        run_frame.grid(column=0, row=1, sticky=tk.NSEW)

        ttk.Button(master=run_frame, width=7, text='Cancel', command=self.batch_cancel).grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Button(master=run_frame, width=7, text='Clear', command=self.batch_clear).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Button(master=run_frame, width=7, text='Ready!', command=self.batch_ready).grid(column=2, row=0, sticky=(tk.E, tk.W, tk.S))

        # Batch list widgets
        list_frame = ttk.Frame(self.window, padding=(0, 15, 15, 15))
        list_frame.grid(column=1, row=0, rowspan=3, sticky=tk.NSEW)
        list_frame.rowconfigure(0, weight=1)

        self.batch_list = tk.Listbox(master=list_frame)
        batch_list_scroll = ttk.Scrollbar(master=list_frame, orient=tk.VERTICAL, command=self.batch_list.yview)
        self.batch_list.configure(yscrollcommand=batch_list_scroll.set)
        self.batch_list.grid(column=0, row=0, sticky=(tk.NSEW))
        batch_list_scroll.grid(column=1, row=0, sticky=(tk.NS))

    def disable(self):
        """ Dissables the batch mode.

        :return: None
        """
        self.ready = False
        messagebox.showinfo(message='Batch mode disabled')

    def populate_batch_list(self, new_list):
        """ Fills the batch list with the bias steps that will be done

        :param new_list: The list of steps to be done
        :return: None
        """
        self.batch_list.delete(0, tk.END)
        for name in new_list:
            self.batch_list.insert(tk.END, name)

    def update_batch_list(self, last=False):
        """ Updates the color of the elements of the list.

        - Red = done
        - Green = in process
        - Black = not done yet

        :param last: flag indicating if this one is the last element
        :return: None
        """
        if self.count > 0:
            self.batch_list.itemconfig(self.count-1, fg='red')

        if last:
            return

        self.batch_list.itemconfig(self.count, fg='green')

    def batch_clear(self):
        """ Clears the batch list and disables the batch

        :return: None
        """
        self.ready = False
        self.batch_list.delete(0, tk.END)

    def batch_cancel(self):
        """ Cancels the creation of the batch

        :return: None
        """
        self.batch_clear()

        # Finally, we hide this window
        self.window.withdraw()

    def save_batch_data(self, new_data):
        """ Saves the data associate to each step of the batch. The data is append to the end of an existing file.

        :param new_data: The data to append
        :return: None
        """

        with open(self.data_file, 'a') as f:
            f.writelines("%s\t" % i for i in new_data)
            f.write('\n')

    def get_rootname(self):

        sampleid = self.root_var.get()
        meas = self.meas_var.get()
        comment = self.comment_var.get()

        if sampleid == '' or meas == '':
            messagebox.showinfo(message='Sample ID and Measurement fields can not be empty.')
            return ''
        else:
            if comment != '':
                rootname = sampleid + '_' + meas + '_' + comment
            else:
                rootname = sampleid + '_' + meas

            return rootname

    def batch_ready(self):
        """ Not used. It will be overwritten by the batch specific functions. However. it needs to exists in order to
        create the interface
        """
        self._batch_ready()

    def batch_proceed(self):
        """ Not used. It will be overwritten by the batch specific functions. However. it needs to exists in order to
        create the interface
        """
        self._batch_proceed()

    def batch_wrapup(self, data):
        """ Not used. It will be overwritten by the batch specific functions. However. it needs to exists in order to
        create the interface
        """
        self._batch_wrapup(data)

if __name__ == '__main__':

    root = tk.Tk()
    dm = device_manager.Devman(root)
    b = Batch(root, dm)
    root.mainloop()


