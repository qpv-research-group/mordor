__author__ = 'D. Alonso-Álvarez'

import visa

def visa_ports():

    rm = visa.ResourceManager()
    port_list = [p for p in rm.list_resources()]

    if port_list == ['']:
        port_list = ['None']

    return port_list
