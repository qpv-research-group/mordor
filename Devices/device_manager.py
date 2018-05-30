__author__ = 'D. Alonso-Álvarez'

import configparser
import serial
import os
import importlib
import inspect

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from Devices.serial_ports import serial_ports
from Devices.visa_ports import visa_ports

import tools


# We try to import visa and use it for something. If it does not work, then we print a warning indicating that visa devices
# will not be available
try:
    import visa
    rm = visa.ResourceManager()
    is_visa = True
except OSError as err:
    print("WARNING: {0}\t VISA devices (eg. GPIB) will not be available.\n".format(err))
    is_visa = False


class Devman(tk.Toplevel):
    """ Class that gives access to all configured devices. It is defined as a Top Level window
    """

    def __init__(self, splash):
        """ Constructor of the device manager class

        :param splash: The parent object, in this case, the Mordor splash window.
        """

        self.splash = splash
        tk.Toplevel.__init__(self)

        self.resizable(width=tk.FALSE, height=tk.FALSE)

        # We load the default configuration file
        self.this_dir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        self.configured_devices = configparser.ConfigParser()
        self.configured_devices.read_file(open(os.path.join(self.this_dir, 'devices.ini')))

        # Current list of configured devices and the different type of devices
        self.current_config = self.load_last_working_config()
        self.current_config_backup = self.load_last_working_config()
        self.device_types = list(set([self.current_config[dev]['Type'] for dev in self.current_config.sections()]))
        self.device_conexions = ['Dummy', 'Serial', 'GPIB', 'Auto USB']

        # List of devices in use
        self.used_devices = []

        # And now, we create the actual window
        self.selector_window()
        self.withdraw()

    def load_last_working_config(self):
        """ Load the last working device list and port configuration from a file "hidden" in your home directory.

        :return: The list of configured devices
        """
        # We load the default configuration
        current = configparser.ConfigParser()
        current.read_file(open(os.path.join(self.this_dir, 'devices.ini')))

        # And override anything different in the custom one, if pressent
        home = os.path.join(os.path.expanduser("~"), '.Mordor', 'last_working_config.ini')
        current.read(home)
        return current

    def save_last_working_config(self):
        """ Save the current working configuration of devices and ports.
        Only devices used in this session of the program are checked, not all.

        :return: None
        """
        home = os.path.join(os.path.expanduser("~"), '.Mordor', 'last_working_config.ini')
        try:
            with open(home, 'w') as configfile:
                self.current_config.write(configfile)
        except Exception as err:
            print(err)
            print('ERROR: The current configuration could not be saved in your home folder.')

    def open_device(self, dev_name):
        """ Opens an instance of the device class corresponding to the device dev_name, as long as the device is not
        already opened. The actual opening takes place in the device module.

        :param dev_name: The name of the device
        :return: A new object of the corresponding device
        """

        device_info = self.current_config[dev_name]

        if device_info['Conexion'] is not 'Dummy':
            if dev_name in self.used_devices:
                messagebox.showinfo(message='Device {} is being used by other experiment.'.format(dev_name),
                                    detail='Close that device and try again.', title='Device ocupied!!')
                return None

        dev2open = '.' + device_info['Module']
        port = device_info['Port']

        try:
            dev = importlib.import_module(dev2open, package='Devices')
            new = dev.New(port, dev_name, device_info)
            self.used_devices.append(dev_name)
            return new
        except (OSError, ImportError) as err:
            print("ERROR: {0}\tDevice {1} could not be open.\n".format(err, device_info['Module']))
            return None

    def close_device(self, device):
        """ Closes the device, as long as it was opened.

        :return: None
        """

        if device.info['Name'] in self.used_devices:
            self.used_devices.remove(device.info['Name'])
            device.close()

    def check(self, port, dev_name):
        """ Used for checking that the device is in the selected port.

        :param port: Selected port.
        :param dev_name: Name of the device
        :return: 0 if it is, -1 otherwise or if an error occurs.
        """

        device_info = self.current_config[dev_name]

        # 'Dummies' are always OK. The port selected is ignored.
        if device_info['Conexion'] == 'Dummy':
            return 0

        # 'Auto USB' devices are tested simply by checking if, given the configuration, they can be open.
        # Depending on the device, the port might be important
        elif device_info['Conexion'] == 'Auto USB':
            try:
                dev = self.open_device(dev_name)
                if dev_name == dev.info['Name']:
                    self.close_device(dev)
                    return 0
                else:
                    return -1
            except:
                try:
                    self.used_devices.remove(dev_name)
                except:
                    pass

                return -1

        # 'Serial' devices need to be checked by asking a question to the port and checking if the answer is correct.
        elif (device_info['Conexion'] == 'Serial'):
            try:
                device = serial.Serial(port, timeout=10)
                device.write(bytes(device_info['Question/SN'] + '\r', 'UTF-8'))
                answer = device.readline(50).decode('utf-8').strip()

                if device_info['Answer'] in answer:
                    device_info['Port'] = port
                    device.close()
                    return 0
                else:
                    device.close()
                    return -1
            except:
                return -1

        # We are using a VISA connection that have to be checked on its own, as long as VISA is working
        # VISA devices need to be checked by asking a question to the port and checking if the answer is correct,
        # similar to serial ports.
        elif (device_info['Conexion']  == 'GPIB') and is_visa:
            try:
                device = rm.open_resource(port)
                answer = device.query(device_info['Question/SN'])

                if device_info['Answer'] in answer:
                    device_info['Port'] = port
                    device.close()
                    return 0
                else:
                    device.close()
                    return -1
            except:
                return -1

        # If none of the above worked, then that device is not connected to that port
        else:
            return -1

    def scan_ports(self):
        """ Finds all active serial and visa ports and returns a list with all of them

        :return: The list of available ports
        """
        serialp = serial_ports()

        if is_visa:
            visap = visa_ports()
        else:
            visap = []

        if 'None' not in (serialp + visap):
            serialp.append('None')

        self.port_entry['values'] = serialp + visap

        return serialp + visap

    def selector_window(self):
        """ Creates the front end of the hardware selector window.

        :return: None
        """

        self.title('Hardware Configuration Window')
        self.protocol('WM_DELETE_WINDOW', self.withdraw)  # We hide it rather than quiting it
        self.option_add('*tearOff', False)  # Prevents tearing the menus
        self.lift(self.splash)  # Brings the hardware window to the top

        sel_frame = ttk.Frame(self, padding=(15, 15, 15, 15))
        sel_frame.grid(sticky=tk.NSEW)
        sel_frame.rowconfigure(1, weight=1)
        sel_frame.columnconfigure(0, weight=1)

        self.info_lbl = ttk.Label(sel_frame, text='', relief='sunken', wraplength=400)
        self.info_lbl.grid(column=0, row=99, columnspan=2, sticky=(tk.EW, tk.S))

        # Hardware list widgets
        list_frame = ttk.Frame(sel_frame, padding=(0, 0, 15, 10))
        list_frame.grid(column=0, row=0, rowspan=50, sticky=tk.NSEW)
        list_frame.rowconfigure(0, weight=1)

        self.dev_list = tk.Listbox(master=list_frame)
        self.dev_list.bind('<<ListboxSelect>>', self.update_dev_selected)
        types_list_scroll = ttk.Scrollbar(master=list_frame, orient=tk.VERTICAL, command=self.dev_list.yview)
        self.dev_list.configure(yscrollcommand=types_list_scroll.set)
        self.dev_list.grid(column=1, row=0, columnspan=3, sticky=(tk.NSEW))
        types_list_scroll.grid(column=0, row=0, sticky=(tk.NS))

        for name in self.current_config.sections():
            self.dev_list.insert(tk.END, name)

        # duplicate HW widgets
        add_hw_button = ttk.Button(list_frame, text='+', width=1, command=self.add)
        add_hw_button.grid(column=1, row=1, sticky=tk.W)
        reset_hw_button = ttk.Button(list_frame, text='Reset', command=self.reset)
        reset_hw_button.grid(column=2, row=1, sticky=tk.EW)
        remove_hw_button = ttk.Button(list_frame, text='-', width=1, command=self.remove)
        remove_hw_button.grid(column=3, row=1, sticky=tk.E)

        # Information widgets
        info_frame = ttk.Frame(sel_frame, padding=(0, 0, 0, 10))
        info_frame.grid(column=1, row=0, rowspan=50, sticky=tk.NSEW)

        ttk.Label(info_frame, text='Name:', width=10).grid(column=2, row=0, sticky=(tk.W, tk.S))
        ttk.Label(info_frame, text='Module:', width=10).grid(column=2, row=1, sticky=(tk.W, tk.S))
        ttk.Label(info_frame, text='Type:', width=10).grid(column=2, row=2, sticky=(tk.W, tk.S))
        ttk.Label(info_frame, text='Conexion:', width=10).grid(column=2, row=3, sticky=(tk.W, tk.S))
        ttk.Label(info_frame, text='Question/SN:', width=10).grid(column=2, row=4, sticky=(tk.W, tk.S))
        ttk.Label(info_frame, text='Answer:', width=10).grid(column=2, row=5, sticky=(tk.W, tk.S))
        ttk.Label(info_frame, text='Port:', width=10).grid(column=2, row=6, sticky=(tk.W, tk.S))

        self.name_var = tk.StringVar()
        self.module_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.conexion_var = tk.StringVar()
        self.question_var = tk.StringVar()
        self.answer_var = tk.StringVar()
        self.port_var = tk.StringVar()

        name_entry = ttk.Entry(info_frame, width=20, textvariable=self.name_var)
        name_entry.grid(column=3, row=0, sticky=(tk.W, tk.S))

        ttk.Entry(info_frame, width=20, textvariable=self.module_var).grid(column=3, row=1, sticky=(tk.W, tk.S))
        ttk.Entry(info_frame, width=20, textvariable=self.question_var).grid(column=3, row=4, sticky=(tk.W, tk.S))
        ttk.Entry(info_frame, width=20, textvariable=self.answer_var).grid(column=3, row=5, sticky=(tk.W, tk.S))

        self.type_entry = ttk.Combobox(info_frame, width=18, textvariable=self.type_var)
        self.type_entry.grid(column=3, row=2, sticky=tk.NSEW)
        self.type_entry['values'] = self.device_types

        self.conexion_entry = ttk.Combobox(info_frame, width=18, textvariable=self.conexion_var)
        self.conexion_entry.grid(column=3, row=3, sticky=tk.NSEW)
        self.conexion_entry['values'] = self.device_conexions

        self.port_entry = ttk.Combobox(info_frame, width=18, textvariable=self.port_var)
        self.port_entry.grid(column=3, row=6, sticky=tk.NSEW)
        self.port_entry['values'] = self.scan_ports()

        # The choosing buttom, port scan button and the information ribbon
        scan_ports_button = ttk.Button(info_frame, text='Scan ports', width=10, command=self.scan_ports)
        check_button = ttk.Button(info_frame, text='Check', width=10, command=self.check_and_update)
        scan_ports_button.grid(column=2, row=7, sticky=tk.NSEW)
        check_button.grid(column=3, row=7, sticky=tk.NSEW)

    def add(self):
        """ Adds a new device to the configure hardware list using some default values. The new device will not be saved
        in the configuration file until it has been check it works (pressing the check buttom).

        :return: None
        """

        self.current_config.add_section('New device')

        self.current_config['New device']['Module'] = 'None'
        self.current_config['New device']['Type'] = 'Monochromator'
        self.current_config['New device']['Conexion'] = 'Dummy'
        self.current_config['New device']['Question/SN'] = 'None'
        self.current_config['New device']['Answer'] = 'None'
        self.current_config['New device']['Port'] = 'None'

        self.module_var.set('None')
        self.type_var.set('Monochromator')
        self.conexion_var.set('Dummy')
        self.question_var.set('None')
        self.answer_var.set('None')
        self.port_var.set('None')

        self.dev_list.insert(tk.END, 'New device')
        self.dev_list.activate(tk.END)

    def reset(self):
        """ Reset the hardware list to the configured hardware at the begining of the session, when Mordor was started.
        Since configparser objects don't allow deepcopy, we have to do it manually.

        :return: None
        """
        for section in self.current_config.sections():
            self.current_config.remove_section(section)

        for section in self.current_config_backup.sections():
            items = self.current_config_backup.items(section)
            self.current_config.add_section(section)
            for val in items:
                self.current_config.set(section, val[0], val[1])

        self.dev_list.delete(0, tk.END)
        for name in self.current_config.sections():
            self.dev_list.insert(tk.END, name)

        self.save_last_working_config()

    def remove(self):
        """ Removes the selected hardware from the configured hardware list and save the new configuration.

        :return: None
        """

        if len(self.dev_list.curselection()) != 1:
            return

        if self.dev_selected > len(self.current_config.sections()):
            return

        i = int(self.dev_list.curselection()[0])
        dev_name = self.current_config.sections()[i]

        if self.current_config.remove_section(dev_name):
            self.dev_list.delete(0, tk.END)
            for name in self.current_config.sections():
                self.dev_list.insert(tk.END, name)

        self.save_last_working_config()

    def rename_hw(self, oldname, newname):
        """ Renames the chosen hardware and updates the necessary lists. Since configparser objects don't have a "rename"
        option, we have to do it manually.

        :return: None
        """

        if self.dev_selected > len(self.current_config.sections()):
            self.dev_selected = 0

        items = self.current_config.items(oldname)
        self.current_config.remove_section(oldname)
        self.current_config.add_section(newname)
        for val in items:
            self.current_config.set(newname, val[0], val[1])

        self.dev_list.delete(0, tk.END)
        for name in self.current_config.sections():
            self.dev_list.insert(tk.END, name)

    def update_dev_selected(self, *args):
        """ Updates the data currently selected, showing the configuration options for that device

        :return: None
        """

        if len(self.current_config.sections()) == 0:
            return
        if len(self.dev_list.curselection()) != 1:
            return

        self.dev_selected = self.dev_list.curselection()[0]

        dev = self.current_config[self.current_config.sections()[self.dev_selected]]

        self.name_var.set(self.current_config.sections()[self.dev_selected])
        self.module_var.set(dev['Module'])
        self.type_var.set(dev['Type'])
        self.conexion_var.set(dev['Conexion'])
        self.question_var.set(dev['Question/SN'])
        self.answer_var.set(dev['Answer'])
        self.port_var.set(dev['Port'])

        if dev['Port'] not in self.port_entry['values']:
            self.info_lbl['text'] = 'WARNING: Default port for this device is not available. Check conexions and re-scan the ports.'
        else:
            self.info_lbl['text'] = ''

    def check_and_update(self):
        """ Checks that the current device configuration is valid. To do this, it tries to conect to it and,
        if successful, see if that is the correct device. See "check" function above. If things work, then the
        configuration is saved to the user initialization file, stored in the home directory.

        :return: None
        """

        if len(self.current_config.sections()) == 0:
            return

        dev_name = self.name_var.get()
        dev_selected = self.dev_list.get(self.dev_selected)

        if dev_name != dev_selected:
            self.rename_hw(dev_selected, dev_name)

        port = self.port_var.get()
        out = self.check(port, dev_name)

        if out == 0:
            self.current_config[dev_name]['Module'] = self.module_var.get()
            self.current_config[dev_name]['Type'] = self.type_var.get()
            self.current_config[dev_name]['Conexion'] = self.conexion_var.get()
            self.current_config[dev_name]['Question/SN'] = self.question_var.get()
            self.current_config[dev_name]['Answer'] = self.answer_var.get()
            self.current_config[dev_name]['Port'] = port

            self.save_last_working_config()

            self.info_lbl['text'] = 'Communication OK! New working configuration saved.'
        else:
            self.info_lbl['text'] = 'ERROR: This is not the port or the device is not listening.'

    def get_devices(self, filter):

        filtered_devices = [dev for dev in self.current_config.sections() if self.current_config[dev]['Type'] in filter]

        return filtered_devices

    def hide(self):
        """ Hides the experiment selector window

        :return: None
        """
        self.withdraw()

    def show(self):
        """ Shows the experiment selector window

        :return: None
        """
        self.update()
        self.deiconify()
        tools.center(self)


# Testing
if __name__ == "__main__":
    root = tk.Tk()
    devman = Devman(root)
    # devman.show()
    print(devman.open_device('Arduino'))
    # root.mainloop()
