# Libraries
import time
from tkinter import messagebox, ttk
import tkinter as tk


# Class definition
class Dummy_monochromator:
    """ Some text
    """

    def __init__(self, port=None, name='Dummy monochromator', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.current_wl = 700
        self.current_speed = 200
        self.current_mirror = 0
        self.current_grating = 1

        self.mirror_options = ['FRONT', 'SIDE']
        self.grating_options = ['Grating 1', 'Grating 2']

        self.grating_var = tk.StringVar()
        self.mirror_var = tk.StringVar()

    def move(self, target, speed='Normal'):
        pass

    def wavelength(self):
        time.sleep(0.1)
        return 0.

    def close(self):
        pass

    def set_grating(self, target):
        self.current_grating = target
        print('New grating = {0}'.format(self.grating_options[self.current_grating]))

    def set_mirror(self, target):
        self.current_mirror = target
        print('New mirror = {0}'.format(self.mirror_options[self.current_mirror]))

    def update_config(self, window):

        grating = self.grating_var.get()
        idx = self.grating_options.index(grating)
        if idx != self.current_grating:
            self.set_grating(idx)

        mirror = self.mirror_var.get()
        idx = self.mirror_options.index(mirror)
        if idx != self.current_mirror:
            self.set_mirror(idx)

        window.destroy()

    def interface(self, master):

        # Top level elements
        acton_window = tk.Toplevel(master)
        acton_window.geometry('+100+100')
        acton_window.resizable(False, False)
        acton_window.protocol('WM_DELETE_WINDOW', self.no_quit)  # Used to force a "safe closing" of the program
        acton_window.option_add('*tearOff', False)  # Prevents tearing the menus
        acton_window.title('Select the options:')

        # Creates the main frame
        config_frame = ttk.Frame(master=acton_window, padding=(15, 15, 15, 15))
        config_frame.grid(column=0, row=0, sticky=(tk.EW))
        config_frame.columnconfigure(0, weight=1)

        # Create the buttons
        ttk.Button(master=config_frame, text='Update', command=lambda: self.update_config(acton_window)).grid(column=1, row=3, sticky=tk.EW)
        ttk.Button(master=config_frame, text='Cancel', command=acton_window.destroy).grid(column=2, row=3, sticky=tk.EW)

        # Create the selectors
        ttk.Label(master=config_frame, text='Grating').grid(column=0, row=0, sticky=tk.E)
        ttk.Label(master=config_frame, text='Output').grid(column=0, row=1, sticky=tk.E)

        grating_entry = ttk.Combobox(master=config_frame, width=20, textvariable=self.grating_var, state='readonly')
        grating_entry.grid(column=1, row=0, columnspan=2, sticky=tk.EW)
        grating_entry['values'] = self.grating_options
        self.grating_var.set(self.grating_options[self.current_grating])

        mirror_entry = ttk.Combobox(master=config_frame, width=20, textvariable=self.mirror_var, state='readonly')
        mirror_entry.grid(column=1, row=1, columnspan=2, sticky=tk.EW)
        mirror_entry['values'] = self.mirror_options
        self.mirror_var.set(self.mirror_options[self.current_mirror])

        # These commands give the control to the HW window. I am not sure what they do exactly.
        acton_window.lift(master)  # Brings the hardware window to the top
        acton_window.transient(master)  # ?
        acton_window.grab_set()  # ?
        master.wait_window(acton_window)  # Freezes the main window until this one is closed.

    def no_quit(self):
        pass

class New(Dummy_monochromator):
    """ Standarised name for the Dummy_monochromator class"""
    pass

# Testing
if __name__ == '__main__':
    test = New('COM5')
    test.move(1000)
    test.move(400)
    print(test.wavelength())
