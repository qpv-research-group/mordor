# Libraries
import serial
import time
from tkinter import messagebox, ttk
import tkinter as tk

# Global variables
debug = False


# Class definition
class ActonSP2500i:

    def __init__(self, port, name='Acton SP2500i', info=None):

        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        # We use the serial driver
        self.serial_comms = serial.Serial(
            port=port,
            baudrate=921600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=100,
            rtscts=True,
            dsrdtr=True,
            interCharTimeout=200*0.001,
            writeTimeout=100*0.001)

        # print(self.query('MONO-EESTATUS'))

        self.current_wl = self.wavelength()
        self.current_speed = self.speed()
        self.current_mirror = self.mirror()
        self.current_grating = self.grating()

        self.mirror_options = ['FRONT', 'SIDE']
        self.grating_options = self.all_gratings()

        textstring = """ Loading {0}...
                    - Wavelength (nm) = {1}
                    - Speed (nm/min) = {2}
                    - Grating = {3}
                    - Mirror = {4} """.format(self.info['Name'],
                                               self.current_wl,
                                               self.current_speed,
                                               self.grating_options[self.current_grating],
                                               self.mirror_options[self.current_mirror])

        print(textstring)

    def close(self):
        self.serial_comms.close()

    def write(self, command, wait=None):
        global debug
    
        if debug:
            print('to device: %s' % command)
    
        self.serial_comms.write(bytes(command+'\r', 'UTF-8'))

        if wait is not None:
            time.sleep(wait)

        return 0

    def query(self, command, bytes_to_read=500, lines_to_read=1, return_line=0, wait=None):
        global debug
    
        if debug:
            print('to device: %s' % command)
    
        self.serial_comms.write(bytes(command+'\r', 'UTF-8'))

        if wait is not None:
            time.sleep(wait)

        rawread = self.serial_comms.readline(bytes_to_read).decode('utf-8')
        
        if debug:
            print('from device: %s' % str(rawread))
    
        return rawread.strip()

    def move(self, target, speed='Normal'):
        """ Go to the target wavelength at the default speed of the motor. It does not return the control to the program
        until it has confirmation that the motor has stopped.
        :param target: target wavelength
        :param speed: if speed='Fast', the maximum speed of the motor (unknown) is used.
        :return: None
        """
        global debug

        if speed == 'Fast':
            self.query("%.3f GOTO" % float(target))
        else:
            waiting_time = abs(self.current_wl-target)/self.current_speed*60.0
            self.query("%.3f >NM" % float(target))

            if debug:
                print(waiting_time)

            time.sleep(waiting_time)

        ready = int(self.query('MONO-?DONE').split(' ')[0])
        while not ready:
            time.sleep(0.05)
            ready = int(self.query('MONO-?DONE').split(' ')[0])

        self.current_wl = target
        return


    def wavelength(self, to_float=True):
        raw = self.query("?NM")

        if to_float:
            return float(raw.split(" ")[0])
        else:
            return raw.split(" ")[0]

    def speed(self, to_float=True):

        raw = self.query("?NM/MIN", wait=0.2)

        if to_float:
            return float(raw.split(" ")[0])
        else:
            return raw.split(" ")[0]

    def grating(self, to_int=True):
        raw = self.query("?GRATING")

        if to_int:
            return int(raw.split(" ")[0])-1
        else:
            return raw.split(" ")[0]

    def all_gratings(self):
        self.write("?GRATINGS")

        gratings = []
        rawread = ''
        while 'ok' not in rawread:
            rawread = self.serial_comms.readline().decode('utf-8')

            if debug:
                print('from device: %s' % str(rawread))

            if 'BLZ' in rawread:
                gratings.append(rawread.strip())

        return gratings

    def mirror(self, to_int=True):
        self.query('EXIT-MIRROR')
        raw = self.query("?MIR")

        if to_int:
            return int(raw.split(" ")[0])
        else:
            return raw.split(" ")[0]

    def set_speed(self, target):
        try:
            self.query("%.3f NM/MIN" % float(target))
            time.sleep(0.5)
            self.current_speed = self.speed()
            print ('New speed (nm/min) = {0}\n\n'.format(self.current_speed) )
        except:
            print('Error: Setting the new speed could not be completed')

    def set_grating(self, target):
        try:
            print('Changing grating...')
            self.query(str(target+1) + ' GRATING', wait=2)
            time.sleep(0.5)
            self.current_grating = self.grating()
            print('New grating = {0}\n\n'.format(self.grating_options[self.current_grating]))
            self.grating_options = self.all_gratings()
        except:
            print('Error: Setting the new grating could not be completed')

    def set_mirror(self, target):
        """ Changes the orientation of the output mirror. Sometimes ir works; sometimes it doesn't. I have not found why.
        :param target: Target mirror 'FRONT' or 'SIDE'
        :return:  None
        """
        try:
            print('Changing mirror...')
            self.query('EXIT-MIRROR')
            self.query(target)
            time.sleep(0.5)
            self.current_mirror = self.mirror()
            print('New mirror = {0}\n\n'.format(self.mirror_options[self.current_mirror]))
        except:
            print('Error: Setting the new mirror could not be completed')

    def update_config(self, window):

        grating = self.grating_var.get()
        idx = self.grating_options.index(grating)
        if idx != self.current_grating:
            self.set_grating(idx)

        mirror = self.mirror_var.get()
        idx = self.mirror_options.index(mirror)
        if idx != self.current_mirror:
            self.set_mirror(mirror)

        window.destroy()

    def interface(self, master):
        # Top level elements
        acton_window = tk.Toplevel(master.window)
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
        ttk.Button(master=config_frame, text='Update', command=lambda: self.update_config(acton_window)).grid(column=1,
                                                                                                              row=3,
                                                                                                              sticky=tk.EW)
        ttk.Button(master=config_frame, text='Cancel', command=acton_window.destroy).grid(column=2, row=3, sticky=tk.EW)

        # Create the selectors
        ttk.Label(master=config_frame, text='Grating').grid(column=0, row=0, sticky=tk.E)
        ttk.Label(master=config_frame, text='Output').grid(column=0, row=1, sticky=tk.E)

        self.grating_var = tk.StringVar()
        self.mirror_var = tk.StringVar()

        grating_entry = ttk.Combobox(master=config_frame, width=25, textvariable=self.grating_var, state='readonly')
        grating_entry.grid(column=1, row=0, columnspan=2, sticky=tk.EW)
        grating_entry['values'] = self.grating_options
        self.grating_var.set(self.grating_options[self.current_grating])

        mirror_entry = ttk.Combobox(master=config_frame, width=25, textvariable=self.mirror_var, state='readonly')
        mirror_entry.grid(column=1, row=1, columnspan=2, sticky=tk.EW)
        mirror_entry['values'] = self.mirror_options
        self.mirror_var.set(self.mirror_options[self.current_mirror])

        # These commands give the control to the HW window. I am not sure what they do exactly.
        acton_window.lift(master.window)  # Brings the hardware window to the top
        acton_window.transient(master.window)  # ?
        acton_window.grab_set()  # ?
        master.wait_window(acton_window)  # Freezes the main window until this one is closed.

    def no_quit(self):
        pass

class New(ActonSP2500i):
    """ Standarised name for the ActonSP2500i class"""
    pass

# Testing
if __name__ == '__main__':
    root = tk.Tk()
    test = New('COM4')
    test.interface(root)
    root.mainloop()
    # print(test.query('2000.0 INIT-SRATE'))
    # print(test.wavelength())
    # test.move(900.0, speed='Fast')
    # # test.set_speed(3000.0)
    # test.move(300.0)
    # print(test.wavelength())
    test.close()

