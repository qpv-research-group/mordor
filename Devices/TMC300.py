# Libraries
import visa
from tkinter import messagebox
import pyBen

debug = False
developing = False

# Class definition
class TMC300:
    def __init__(self, port=None, name='Bentham TMC300', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        ## Initialise monochromator
        pyBen.build_system_model("C:/Program Files (x86)/Bentham/SDK/Configuration Files/system.cfg")
        pyBen.load_setup("C:/Program Files (x86)/Bentham/SDK/Configuration Files/system.atr")
        pyBen.initialise()
        pyBen.park()

    def move(self, target, speed='Normal'):
        pyBen.select_wavelength(float(target),1) # 1s timeout to complete operation

    def close(self):
        pyBen.close()

    def interface(self, master):
        messagebox.showinfo(message='No specific configuration available for {0}'.format(self.info['Name']),
                            detail='Press OK to continue.', title='Device configuration')


class New(TMC300):
    """ Standarised name for the TMC300 class"""
    pass

# Testing
if __name__=="__main__":
    test = New()
    print(test.update_integration_time(0.800))
