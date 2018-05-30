"""
Python-Arduino interface based on the project 'Python Arduino Prototyping API v2':

https://github.com/vascop/Python-Arduino-Proto-API-v2

I have just added some extra functionality to make it work easily with Mordor

The 'prototype.ino' sketch that can be found in the 'arduino sketch' folder needs to be loaded into the arduino board,
so it understands the commands sent by this script. This way of communicating with Arduino has a slower performance that
coding things directly into the Arduino, but it is much more flexible as it is only limited by what you can do in Python.
"""

import time
import numpy as np

class Dummy_ADC_DAC(object):

    __OUTPUT_PINS = -1

    def __init__(self, port=None, name='Dummy ADC-DAC', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.baudrate = 115200

        self.digital_output = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.analog_input = [0, 1, 2, 3, 4, 5]

        self.pin_state = np.zeros_like(self.digital_output)
        self.pin_value = np.zeros_like(self.digital_output)

        self.output(self.digital_output)
        self.turnOff()

        assert 'Dummy ADC-DAC' in self.getID()
        
    def __str__(self):
        return "Dummy ADC-DAC is ready"

    def output(self, pinArray):
        self.__sendData(len(pinArray))

        if(isinstance(pinArray, list) or isinstance(pinArray, tuple)):
            self.__OUTPUT_PINS = pinArray
            for each_pin in pinArray:
                self.__sendData(each_pin)
        return True

    def getID(self):
        return 'Dummy ADC-DAC'
        
    def setLow(self, pin):
        self.pin_state[pin] = 0
        return True

    def setHigh(self, pin):
        self.pin_state[pin] = 1
        return True

    def getState(self, pin):
        return self.pin_state[pin]

    def analogWrite(self, pin, value):
        self.pin_value[pin] = value
        return True

    def analogRead(self, pin):
        return np.random.randint(0, 256)

    def turnOff(self):
        for each_pin in self.__OUTPUT_PINS:
            self.setLow(each_pin)
        return True

    def pulse(self, pin, length=50):
        """ Sets a digital pin output to a HIGH state for a given time. Can be used as a trigger

        :param pin: pin number
        :param length: duration of the pulse in ms
        :return:
        """
        self.setHigh(pin)
        time.sleep(length/1000)
        self.setLow(pin)
        return True

    def __sendData(self, serial_data):
        pass

    def __getData(self):
        pass

    def __formatPinState(self, pinValue):
        if pinValue == '1':
            return True
        else:
            return False

    def close(self):
        pass
        return True

class New(Dummy_ADC_DAC):
    """ Standarised name for the Dummy_ADC_DAC class"""
    pass

if __name__ == "__main__":
    b = Dummy_ADC_DAC('/dev/tty.usbmodem1421')

    # # b.serial.write(b'98')
    # data = b.serial.readline().decode('utf-8')
    # print(data)
    # #
    # pin = 2
    #
    # # b.output([])
    time.sleep(5)
    b.pulse(13, 2000)
    time.sleep(2)
    b.pulse(13, 2000)
    time.sleep(2)
    b.pulse(13, 2000)

    # while (True):
    #     val = b.analogRead(pin)
    #     print (val)
    #     time.sleep(0.5)

    b.close()
