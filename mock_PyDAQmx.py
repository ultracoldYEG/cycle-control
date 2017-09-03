#Mocks the functions in the National Instruments C library

import time

DAQmx_Val_Volts = 1.0
DAQmx_Val_Rising = 'rising'
DAQmx_Val_FiniteSamps = 'finite'
DAQmx_Val_GroupByChannel = 'channel'

class taskHandle(object):
    def __init__(self):
        self.lock = False

    def run(self):
        self.instructions = []
        self.activated = False
        self.devices = []
        self.units = 0.0
        self.volt_limits = [0.0, 0.0]
        self.trigger_pin = ''
        self.trigger_mode = ''
        self.trigger_num = 0
        self.rate = 0
        self.loop_type = ''
        self.samples_per_channel = 0
        self.autostart = 0
        self.timeout = 100
        self.sort_type = ''

def DAQmxCreateTask(name, taskHandle):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.run()

def DAQmxStartTask(taskHandle):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return

    if taskHandle.activated:
        print 'DAQmx ERROR: cant start while active'
        return
    taskHandle.activated = True
    print 'DAQmx STARTED: ' + taskHandle.devices

def DAQmxStopTask(taskHandle):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.activated = False
    print 'DAQmx STOPPED: ' + taskHandle.devices

def DAQmxClearTask(taskHandle):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.__init__()

def DAQmxCreateAOVoltageChan(taskHandle, devices, name , low_bound, high_bound, units, custom_scale_name):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    if taskHandle.activated:
        print 'DAQmx ERROR: cant program while active'
        return

    taskHandle.devices = devices
    taskHandle.units = units
    taskHandle.volt_limits = [low_bound, high_bound]

def DAQmxCfgSampClkTiming(taskHandle, trigger_pin, rate, trigger_mode, loop_type, trigger_num):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    if taskHandle.activated:
        print 'DAQmx ERROR: cant program while active'
        return
    taskHandle.trigger_pin = trigger_pin
    taskHandle.rate = rate
    taskHandle.trigger_mode = trigger_mode
    taskHandle.loop_type = loop_type
    taskHandle.trigger_num = trigger_num

def DAQmxWriteAnalogF64(taskHandle, num_samples, autostart, timeout, sort_type, analog_data, writeArray, reserved):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    if taskHandle.activated:
        print 'DAQmx ERROR: cant program while active'
        return
    taskHandle.samples_per_channel = num_samples
    taskHandle.autostart = autostart
    taskHandle.timeout = timeout
    taskHandle.sort_type = sort_type
    taskHandle.instructions = analog_data
    print 'DAQmx programmed: ' + taskHandle.devices

def DAQmxWaitUntilTaskDone(taskHandle, delay):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.lock = True
    time.sleep(delay)
    taskHandle.lock = False