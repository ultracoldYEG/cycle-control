import re
import serial
import os
from PyQt5.QtCore import Qt

FUNCTION_REGEX = r'^(\w+)\((.*)\)$'
ROOT_PATH = os.getcwd()

def bool_to_checkstate(bool):
    return Qt.Checked if bool else Qt.Unchecked

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

def replace_bit(bits, i, repl):
    return bits[:i] + repl + bits[i+1:]

def parse_function(string, variables):
    result = re.match(FUNCTION_REGEX, string.replace(' ', ''))
    if result:
        key = result.group(1)
        args = [parse_arg(x.strip(), variables) for x in result.group(2).split(',')]
        if any([arg is None for arg in args]):
            print('Invalid function syntax: ', string)
            return None, None
        return key, args

    args = parse_arg(string, variables)
    if args is not None:
        return 'const', [args]

    print('Invalid function syntax: ', string)
    return None, None

def parse_arg(arg, variables):
    if arg in variables:
        return variables.get(arg)
    try:
        arg = float(arg)
        return arg
    except ValueError:
        print('Couldnt parse argument ', arg)
        return None

def force_even(data):
    if len(data) % 2 == 1:
        return data[:-1]
    return data

def sterilize_string(string):
    return re.sub('[^0-9a-zA-Z_]+', '', str(string))