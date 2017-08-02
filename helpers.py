import serial
import os
from PyQt5.QtCore import Qt

ROOT_PATH = os.getcwd()

def bool_to_checkstate(bool):
    if bool:
        return Qt.Checked
    return Qt.Unchecked


def serial_ports():
    ports = ['COM%s' % (i + 1) for i in range(256)]

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def load_stylesheet(name):
    with open(os.path.join(ROOT_PATH, 'stylesheets', name), 'r') as f:
        return f.read()