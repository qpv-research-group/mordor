__author__ = 'A. M. Telford & D. Alonso-Álvarez'

import tkinter as tk
from tkinter import ttk

import numpy as np
from Experiments.batch_control import Batch
from tkinter import messagebox

class CV:
    """ Base class for impedance sweep experiments """

    def __init__(self, master, devman, in_batch=False):
        self.master = master
        self.dm = devman
        self.id = 'CV'

        # Create the main variables of the class
        self.in_batch = in_batch
        self.create_variables()

        self.plot_format = {'ratios': (1, 1),
                            'xlabel': 'Frequency (Hz)',
                            'x_scale' : 'log',
                            'Ch1_ylabel': '|Z| (Ohm)',
                            'Ch2_ylabel': 'Tz (deg)',
                            'Ch1_scale': 'log',
                            'Ch2_scale': 'linear'}
        
        top0 = 'Bias = '
        top1 = '0 V'
        col0 = self.plot_format['xlabel']
        col1 = self.plot_format['Ch1_ylabel']
        col2 = self.plot_format['Ch2_ylabel']
        self.header = str(top0)+'= '+str(top1)+'\n'+str(col0)+'\t'+str(col1)+'\t'+str(col2)
        self.header.encode('utf-8')
        
        self.extension = 'txt'
        self.batch = Batch(self.master, self.dm, fileheader=self.header) ## Dummy mode
        
        # Create the interface
        self.create_interface()
        
        # We load the dummy devices by default
        self.fill_devices()
        
    def quit(self):
        """ Safe closing of the devices. The devices must be closed by the Device Manager, not directly,
        so they are registered as "free".
        """

        if self.za is not None:
            self.dm.close_device(self.za)

        self.batch.window.destroy()

    def create_variables(self):

        # Data variables
        self.record = None

        # Hardware variables
        self.za = None

        # Acquisition variables
        self.n_averages = 10
        self.stop = True

    def create_menu_bar(self):
        """ Add elements to the master menu bar
        """

        # Hardware menu
        self.master.menu_hardware.add_command(label='ZA', command=lambda: self.za.interface(self.master))
        self.master.menu_hardware.entryconfig("ZA", state="disabled")

        # Batch menu
        if not self.in_batch:
            self.master.menu_batch.add_command(label='Disable', command=self.batch.disable)
            self.master.menu_batch.add_command(label='Temperature', command=lambda: self.new_batch('Temperature'))
            self.master.menu_batch.add_command(label='Time', command=lambda: self.new_batch('Time'))
			
    def new_batch(self, batch_mode):
        """ Shows current batch window or, if a different batch is chosen, destroys the old one and creates a new one
        for the new batch mode

        :param batch_mode: the selected type of batch
        :return: None
        """
        if self.batch.mode == batch_mode:
            self.batch.show()
        else:
            self.batch.window.destroy()
            self.batch = Batch(self.master, self.dm, fileheader=self.header, mode=batch_mode)

    def create_interface(self):

        # Add elements to the menu bar
        self.create_menu_bar()

        cv_frame = ttk.Frame(self.master.control_frame)
        cv_frame.grid(column=0, row=0, sticky=(tk.EW))
        cv_frame.columnconfigure(0, weight=1)

        # Hardware widgets
        hardware_frame = ttk.Labelframe(cv_frame, text='Selected hardware:', padding=(0, 5, 0, 15))
        hardware_frame.grid(column=0, row=0, sticky=(tk.EW))
        hardware_frame.columnconfigure(0, weight=1)

        self.za_var = tk.StringVar()
        self.za_box = ttk.Combobox(master=hardware_frame, textvariable=self.za_var, state="readonly")
        self.za_box.grid(column=0, row=0, sticky=(tk.EW))
        self.za_box.bind('<<ComboboxSelected>>', self.select_za)
        

        # Scan mode widgets ---------------------------------
        mode_frame = ttk.Labelframe(cv_frame, text='Scan mode:', padding=(0, 5, 0, 15))
        mode_frame.grid(column=0, row=1, sticky=(tk.EW))
        mode_frame.columnconfigure(1, weight=1)

        self.fixed_var = tk.StringVar()
        self.fixed_var.set('bias')
        ttk.Radiobutton(mode_frame, text="Fixed Bias", variable=self.fixed_var, value='bias', command=self.mode).grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(mode_frame, text="Fixed Frequency", variable=self.fixed_var, value='freq', command=self.mode).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))
        
        self.fixed_value_var = tk.StringVar()
        self.fixed_value_var.set('0')
        self.fixed_value_label = ttk.Label(mode_frame, text='Set bias (V): ')
        self.fixed_value_label.grid(column=0, row=1, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=mode_frame, width=10, textvariable=self.fixed_value_var).grid(column=1, row=1, sticky=(tk.E, tk.W, tk.S))
        
        self.osc_amp_var = tk.StringVar()
        self.osc_amp_var.set('0.01')
        self.osc_amp_label = ttk.Label(mode_frame, text='Set AC bias (V): ')
        self.osc_amp_label.grid(column=0, row=2, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=mode_frame, width=10, textvariable=self.osc_amp_var).grid(column=1, row=2, sticky=(tk.E, tk.W, tk.S))
        
        # Ch1 setup widgets --------------------------------
        Ch1_frame = ttk.Labelframe(cv_frame, text='Ch1 setup:', padding=(0, 5, 0, 15))
        Ch1_frame.grid(column=0, row=2, sticky=(tk.EW))
        Ch1_frame.columnconfigure(1, weight=1)
        self.Ch1_param_var = tk.StringVar()
        self.Ch1_param_var.set('Z')
        self.Ch1_scale_var = tk.StringVar()
        self.Ch1_scale_var.set('log')
        ttk.Radiobutton(Ch1_frame, text="Z", variable=self.Ch1_param_var, value='Z', command=self.channel_param).grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch1_frame, text="Cs", variable=self.Ch1_param_var, value='Cs', command=self.channel_param).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch1_frame, text="Cp", variable=self.Ch1_param_var, value='Cp', command=self.channel_param).grid(column=2, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch1_frame, text="R", variable=self.Ch1_param_var, value='R', command=self.channel_param).grid(column=3, row=0, sticky=(tk.E, tk.W, tk.S))
        self.idc_button = ttk.Radiobutton(Ch1_frame, text="Idc", variable=self.Ch1_param_var, value='Idc', command=self.channel_param)
        self.idc_button.grid(column=4, row=0, sticky=(tk.E, tk.W, tk.S))
        self.idc_button.configure(state='disabled')
        ttk.Radiobutton(Ch1_frame, text="Linear", variable=self.Ch1_scale_var, value='linear', command=self.scan_scale).grid(column=0, row=1, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch1_frame, text="Log10", variable=self.Ch1_scale_var, value='log', command=self.scan_scale).grid(column=1, row=1, sticky=(tk.E, tk.W, tk.S))      
        
        # Ch2 setup widgets --------------------------------
        Ch2_frame = ttk.Labelframe(cv_frame, text='Ch2 setup:', padding=(0, 5, 0, 15))
        Ch2_frame.grid(column=0, row=3, sticky=(tk.EW))
        Ch2_frame.columnconfigure(1, weight=1)
        self.Ch2_param_var = tk.StringVar()
        self.Ch2_param_var.set('Tz')
        self.Ch2_scale_var = tk.StringVar()
        self.Ch2_scale_var.set('linear')
        ttk.Radiobutton(Ch2_frame, text="Tz", variable=self.Ch2_param_var, value='Tz', command=self.channel_param).grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch2_frame, text="Rs", variable=self.Ch2_param_var, value='Rs', command=self.channel_param).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch2_frame, text="Rp", variable=self.Ch2_param_var, value='Rp', command=self.channel_param).grid(column=2, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(Ch2_frame, text="X", variable=self.Ch2_param_var, value='X', command=self.channel_param).grid(column=3, row=0, sticky=(tk.E, tk.W, tk.S)) 
        ttk.Radiobutton(Ch2_frame, text="Linear", variable=self.Ch2_scale_var, value='linear', command=self.scan_scale).grid(column=0, row=1, sticky=(tk.E, tk.W, tk.S))
        self.Ch2log_button = ttk.Radiobutton(Ch2_frame, text="Log10", variable=self.Ch2_scale_var, value='log', command=self.scan_scale)
        self.Ch2log_button.grid(column=1, row=1, sticky=(tk.E, tk.W, tk.S))
        self.Ch2log_button.configure(state='disabled')
		
        # Sweep setup widgets ---------------------------------
        sweep_frame = ttk.Labelframe(cv_frame, text='Sweep setup:', padding=(0, 5, 0, 15))
        sweep_frame.columnconfigure(0, weight=1)
        sweep_frame.grid(column=0, row=4, sticky=(tk.EW))

        self.sweep_start_var = tk.StringVar()
        self.sweep_start_var.set('20')
        self.sweep_start_label = ttk.Label(sweep_frame, text='Frequency start (Hz): ')
        self.sweep_start_label.grid(column=0, row=0, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=sweep_frame, width=10, textvariable=self.sweep_start_var).grid(column=1, row=0, sticky=(tk.E, tk.W, tk.S))

        self.sweep_stop_var = tk.StringVar()
        self.sweep_stop_var.set('1e07')
        self.sweep_stop_label = ttk.Label(sweep_frame, text='Frequency stop (Hz): ')
        self.sweep_stop_label.grid(column=0, row=1, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=sweep_frame, width=10, textvariable=self.sweep_stop_var).grid(column=1, row=1, sticky=(tk.E, tk.W, tk.S))

        self.x_scale_var = tk.StringVar()
        self.x_scale_var.set('log')
        ttk.Radiobutton(sweep_frame, text="Linear", variable=self.x_scale_var, value='linear', command=self.scan_scale).grid(column=0, row=2, sticky=(tk.E, tk.W, tk.S))
        self.xlog_button = ttk.Radiobutton(sweep_frame, text="Log10", variable=self.x_scale_var, value='log', command=self.scan_scale)
        self.xlog_button.grid(column=1, row=2, sticky=(tk.E, tk.W, tk.S))
		
        self.nop_var = tk.StringVar()
        self.nop_var.set('400')
        self.nop_label = ttk.Label(sweep_frame, text='Number of points: ')
        self.nop_label.grid(column=0, row=3, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=sweep_frame, width=10, textvariable=self.nop_var).grid(column=1, row=3, sticky=(tk.E, tk.W, tk.S))
        
        self.navg_var = tk.StringVar()
        self.navg_var.set('3')
        self.navg_label = ttk.Label(sweep_frame, text='Number of point averages: ')
        self.navg_label.grid(column=0, row=4, sticky=(tk.E, tk.W, tk.S))
        ttk.Entry(master=sweep_frame, width=10, textvariable=self.navg_var).grid(column=1, row=4, sticky=(tk.E, tk.W, tk.S))
        
        self.sweep_dir_var = tk.StringVar()
        self.sweep_dir_var.set('up')
        ttk.Radiobutton(sweep_frame, text="Sweep Up", variable=self.sweep_dir_var, value='up').grid(column=0, row=5, sticky=(tk.E, tk.W, tk.S))
        ttk.Radiobutton(sweep_frame, text="Sweep Down", variable=self.sweep_dir_var, value='down').grid(column=1, row=5, sticky=(tk.E, tk.W, tk.S))
  
        #self.abort_button = ttk.Button(master=sweep_frame, width=10, text='ABORT!', command=self.abort)
        #self.abort_button.grid(column=0, row=98, sticky=( tk.E, tk.SW, tk.S))        
        
        # The "Run" button is only available if not in batch mode
        if not self.in_batch:
            self.run_button = ttk.Button(master=sweep_frame, width=10, text='Run', command=self.start_stop_scan)
            self.run_button.grid(column=1, row=98, sticky=( tk.E, tk.SW, tk.S))

    def update_header(self):
        top0 = self.fixed_var.get()
        top1 = self.fixed_value_var.get()
        
        if top0 == 'bias':
            top2 = 'V'
        else:
            top2 = 'Hz'
        
        col0 = self.plot_format['xlabel']
        col1 = self.plot_format['Ch1_ylabel']
        col2 = self.plot_format['Ch2_ylabel']
        self.header = str(top0)+'= '+str(top1)+' '+str(top2)+'\n'+str(col0)+'\t'+str(col1)+'\t'+str(col2)
        self.header.encode('utf-8')
        
    def fill_devices(self):
        """ Fills the device selectors with the corresponding type of devices

        :return: None
        """
        self.za_box['values'] = self.dm.get_devices(['ZA'])
        self.za_box.current(0)

        self.select_za()

    def select_za(self, *args):
        """ When the Z analyser selector changes, this function updates some variables and the graphical interface
        to adapt it to the selected device.

        :param args: Dummy variable that does nothing but must exist (?)
        :return: None
        """

        if self.za is not None:
            self.dm.close_device(self.za)

        dev_name = self.za_var.get()
        self.za = self.dm.open_device(dev_name)

        if self.za is None:
            self.za_box.current(0)
            self.za = self.dm.open_device(self.za_var.get())

        elif self.dm.current_config[dev_name]['Type'] == 'ZA':
            pass
        ## Line required to avoid 'busy device' error
        
        else:
            self.za_box.current(0)
            self.za = self.dm.open_device(self.za_var.get())

        # If the device has an interface to set options, we link it to the entry in the menu
        interface = getattr(self.za, "interface", None)
        if callable(interface):
            self.master.menu_hardware.entryconfig("ZA", state="normal")
        else:
            self.master.menu_hardware.entryconfig("ZA", state="disabled")
			
    def refresh_buttons(self):
        if self.fixed_var.get() == 'freq':
            self.x_scale_var.set('linear')
            self.scan_scale() ## Updates plot_format, which is used to pass parameters to the device
            self.xlog_button.configure(state='disabled')
            self.idc_button.configure(state='normal')
        else:
            self.xlog_button.configure(state='normal')
            self.idc_button.configure(state='disabled')
            
        if self.Ch2_param_var.get() == 'Tz' or self.Ch2_param_var.get() == 'X':
            self.Ch2_scale_var.set('linear')
            self.scan_scale() ## Updates plot_format, which is used to pass parameters to the device
            self.Ch2log_button.configure(state='disabled')
        else:
            self.Ch2log_button.configure(state='normal')	

    def mode(self):
        """ When the bias mode is changed, this function updates some internal variables and the graphical interface

        :return: None
        """

        if self.fixed_var.get() == 'bias':
            self.sweep_start_label['text'] = 'Frequency start (Hz): '
            self.sweep_stop_label['text'] = 'Frequency stop (Hz): '
            self.sweep_start_var.set('20')
            self.sweep_stop_var.set('1e7')
            self.fixed_value_label['text'] = 'Set Bias (V): '
            self.fixed_value_var.set('0')
            self.osc_amp_var.set('0.01')
            self.plot_format['xlabel'] = 'Frequency (Hz)'
            self.Ch1_param_var.set('Z') ## Required to avoid havind Idc selected and disabled

        elif self.fixed_var.get() == 'freq':
            self.sweep_start_label['text'] = 'Bias start (V): '
            self.sweep_stop_label['text'] = 'Bias stop (V): '
            self.sweep_start_var.set('-0.5')
            self.sweep_stop_var.set('0.5')
            self.fixed_value_label['text'] = 'Set Frequency (Hz): '
            self.fixed_value_var.set('1e5')
            self.plot_format['xlabel'] = 'Bias (V)'
            self.fixed_value_var.set('1e5')
            self.osc_amp_var.set('0.01')
			
        self.refresh_buttons()	
        self.master.update_plot_axis(self.plot_format)
            
    def channel_param(self):
        """ When the channel parameters are changed, this function updates some internal variables and the graphical interface

        :return: None
        """
        ## Channel 1 labels ----------------------------------
        if self.Ch1_param_var.get() == 'Z':
            self.plot_format['Ch1_ylabel'] = '|Z| (Ohm)'
        elif self.Ch1_param_var.get() == 'Cp':
            self.plot_format['Ch1_ylabel'] = 'Cp (F)'            
        elif self.Ch1_param_var.get() == 'Cs':
            self.plot_format['Ch1_ylabel'] = 'Cs (F)'
        elif self.Ch1_param_var.get() == 'R':
            self.plot_format['Ch1_ylabel'] = 'Zreal (Ohm)'
        elif self.Ch1_param_var.get() == 'Idc':
            self.plot_format['Ch1_ylabel'] = 'Idc (A)'
        ## Channel 2 labels ----------------------------------  
        if self.Ch2_param_var.get() == 'Tz':
            self.plot_format['Ch2_ylabel'] = 'Tz (deg)'			
        elif self.Ch2_param_var.get() == 'Rp':
            self.plot_format['Ch2_ylabel'] = 'Rp (Ohm)'            
        elif self.Ch2_param_var.get() == 'Rs':
            self.plot_format['Ch2_ylabel'] = 'Rs (Ohm)'
        elif self.Ch2_param_var.get() == 'X':
            self.plot_format['Ch2_ylabel'] = 'Zimag (Ohm)'
        
        self.refresh_buttons()		
        self.master.update_plot_axis(self.plot_format)

    def scan_scale(self):
        """ When the scan scales are changed, this function updates some internal variables and the graphical interface

        :return: None
        """
         ## X-axis scale ----------------------------------
        if self.x_scale_var.get() == 'linear':
            self.plot_format['x_scale'] = 'linear'
        elif self.x_scale_var.get() == 'log':
            self.plot_format['x_scale'] = 'log'       
        ## Channel 1 scale ----------------------------------
        if self.Ch1_scale_var.get() == 'linear':
            self.plot_format['Ch1_scale'] = 'linear'
        elif self.Ch1_scale_var.get() == 'log':
            self.plot_format['Ch1_scale'] = 'log'            
        ## Channel 2 scale ----------------------------------  
        if self.Ch2_scale_var.get() == 'linear':
            self.plot_format['Ch2_scale'] = 'linear'
        elif self.Ch2_scale_var.get() == 'log':
            self.plot_format['Ch2_scale'] = 'log'
            
        self.master.update_plot_axis(self.plot_format)
        

    def start_stop_scan(self):
        """ Starts and stops a scan

        :return: None
        """
        self.run_check()        
        if False not in self.run_ok:
					
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
                else:    
                    self.run_button['state'] = 'enabled'                    
                self.finish_scan()


    def prepare_scan(self):
        """ Any scan is divided in three stages:
        1) Prepare the conditions of the scan (this function), getting starting point, integration time and creating all relevant variables.
        2) Running the scan, performed by a recursive function "get_next_datapoint"
        3) Finish the scan, where we update some variables and save the data.

        :return: None
        """
        ## If inputs are OK, fill up the options dictionary and proceed.
        self.options = {'fixed':   self.mode,
                        'fixed_value': self.fixed_value,
                        'start': self.sweep_start,
                        'stop': self.sweep_stop,
                        'nop': self.nop,
                        'navg': self.navg,
                        'osc_amp': self.osc_amp,
                        'sweep_dir': self.sweep_dir}
        
        # # If we are in a batch, we proceed to the next point
        if self.batch.ready:
            self.batch.batch_proceed()

        print('Starting scan...')

        # Create the record array. In this case it is irrelevant
        self.record = np.zeros((self.options['nop']+1, 4))
        self.record[:, 0] = np.linspace(0, 1, self.options['nop']+1)
        self.record[:, 1] = np.ones_like(self.record[:, 0])
        self.record[:, 2] = np.ones_like(self.record[:, 0])
        self.master.prepare_meas(self.record)
        self.start_scan()

    def start_scan(self):
        self.za.setup_measurement(self.plot_format, self.options)
        self.za.measure(self.options)
        self.get_data()
        

    def get_data(self):

        data0, data1, data2 = self.za.return_data()

        self.record = np.zeros((len(data0), 3))
        self.record[:, 0] = data0
        self.record[:, 1] = data1
        self.record[:, 2] = data2
		
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
            self.run_button['text'] = 'Run'
            self.run_button['state'] = 'enabled'

        else:
            self.prepare_scan()
			
    def check_inputs(self, parameter, value, min, max):
        if value < min or value > max:
            messagebox.showerror("Error", parameter+" is out of range!")
            self.run_button['state'] = 'enabled'
            self.run_ok.append(False)
        
        else:
            self.run_ok.append(True)

        
    def run_check(self):
        self.mode = self.fixed_var.get()
        self.fixed_value = float(self.fixed_value_var.get())
        self.sweep_start = float(self.sweep_start_var.get())
        self.sweep_stop = float(self.sweep_stop_var.get())
        self.nop = int(self.nop_var.get())
        self.navg = int(self.navg_var.get())        
        self.osc_amp = float(self.osc_amp_var.get())
        self.sweep_dir = self.sweep_dir_var.get()

        ## Check that inputs are within safe/correct limits
        self.run_ok = []
        if self.mode == 'bias':
            self.check_inputs('DC bias', self.fixed_value, -10, 10)
            self.check_inputs('Minimun frequency', self.sweep_start, 20, 1e7)
            self.check_inputs('Maximun frequency', self.sweep_stop, 20, 1e7)
        elif self.mode == 'freq':
            self.check_inputs('CW frequency', self.fixed_value, 20, 1e7)
            self.check_inputs('Minimun DC bias', self.sweep_start, -10, 10)
            self.check_inputs('Maximun frequency', self.sweep_stop, -10, 10)

        self.check_inputs('Number of points', self.nop, 1, 1000)
        self.check_inputs('Number of averages', self.navg, 1, 100)
        self.check_inputs('AC bias', self.osc_amp, 0.001, 1)

        
    def abort(self):
        #pass
        self.za.abort_sweep()
        self.get_data()
