"""
Python-Arduino interface based on the project 'Python Arduino Prototyping API v2':

https://github.com/vascop/Python-Arduino-Proto-API-v2

I have just added some extra functionality to make it work easily with Mordor

The 'prototype.ino' sketch that can be found in the 'arduino sketch' folder needs to be loaded into the arduino board,
so it understands the commands sent by this script. This way of communicating with Arduino has a slower performance that
coding things directly into the Arduino, but it is much more flexible as it is only limited by what you can do in Python.
"""

import serial
import time

class Arduino(object):

    __OUTPUT_PINS = -1

    def __init__(self, port=None, name='Arduino', info=None):
        self.info = {}
        self.info['Name'] = name
        if info is not None:
            self.info.update(info)

        self.baudrate = 115200
        self.serial = serial.Serial(port, self.baudrate)

        self.digital_output = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.analog_input = [0, 1, 2, 3, 4, 5]

        self.output(self.digital_output)
        self.turnOff()

        assert 'Arduino' in self.getID()

        print('Arduino loaded!!')
        
    def __str__(self):
        return "Arduino is on port %s at %d baudrate" %(self.serial.port, self.serial.baudrate)

    def output(self, pinArray):
        self.__sendData(len(pinArray))

        if(isinstance(pinArray, list) or isinstance(pinArray, tuple)):
            self.__OUTPUT_PINS = pinArray
            for each_pin in pinArray:
                self.__sendData(each_pin)
        return True

    def getID(self):
        self.__sendData('98')
        return self.__getData()
        
    def setLow(self, pin):
        self.__sendData('0')
        self.__sendData(pin)
        return True

    def setHigh(self, pin):
        self.__sendData('1')
        self.__sendData(pin)
        return True

    def getState(self, pin):
        self.__sendData('2')
        self.__sendData(pin)
        return self.__formatPinState(self.__getData()[0])

    def analogWrite(self, pin, value):
        self.__sendData('3')
        self.__sendData(pin)
        self.__sendData(value)
        return True

    def analogRead(self, pin):
        self.__sendData('4')
        self.__sendData(pin)
        return self.__getData()

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
        while(self.__getData()[0] != "w"):
            pass
        serial_data = str(serial_data).encode('utf-8')
        self.serial.write(serial_data)

    def __getData(self):
        input_string = self.serial.readline()
        input_string = input_string.decode('utf-8')
        return input_string.strip()

    def __formatPinState(self, pinValue):
        if pinValue == '1':
            return True
        else:
            return False

    def close(self):
        self.serial.close()
        return True

class New(Arduino):
    """ Standarised name for the Arduino class"""
    pass

if __name__ == "__main__":
    b = Arduino('/dev/ttyACM0')

    # # b.serial.write(b'98')
    # data = b.serial.readline().decode('utf-8')
    # print(data)
    # #
    # pin = 2
    #
    # # b.output([])
    for i in range(100000):
        time.sleep(0.1)
        b.pulse(13, 100)
        print(i)


    # while (True):
    #     val = b.analogRead(pin)
    #     print (val)
    #     time.sleep(0.5)

    b.close()
