#Mocks the functions in the National Instruments C library

import time

DAQmx_Val_Volts = 1.0
DAQmx_Val_Rising = 'rising'
DAQmx_Val_FiniteSamps = 'finite'
DAQmx_Val_GroupByChannel = 'channel'
DAQmx_Val_FromCustomScale = 'custom'

class TaskHandle(object):
    def __init__(self, id):
        self.lock = False

    def run(self):
        self.instructions = []
        self.activated = False
        self.devices = []
        self.units = []
        self.custom_units = ''
        self.volt_limits = []
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
    print 'DAQmx STARTED: ' + ''.join([' ' + str(x) for x in taskHandle.devices])

def DAQmxStopTask(taskHandle):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.activated = False
    print 'DAQmx STOPPED: ' + ''.join([' ' + str(x) for x in taskHandle.devices])

def DAQmxClearTask(taskHandle):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.__init__(0)

def DAQmxCreateAOVoltageChan(taskHandle, devices, name , low_bound, high_bound, units, custom_scale_name):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    if taskHandle.activated:
        print 'DAQmx ERROR: cant program while active'
        return

    taskHandle.devices.append(devices)
    taskHandle.units.append(units)
    taskHandle.volt_limits.append([low_bound, high_bound])

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
    print 'DAQmx programmed: ' + ''.join([' ' + str(x) for x in taskHandle.devices])

def DAQmxWaitUntilTaskDone(taskHandle, delay):
    if taskHandle.lock:
        print 'DAQmx ERROR: locked'
        return
    taskHandle.lock = True
    time.sleep(delay)
    taskHandle.lock = False

def DAQmxGetSysScales(buffer_string, buffer):
    sample_output = 'TEST_SCALE, TEST_SCALE2\x00'
    return sample_output + buffer_string[len(sample_output):]

def DAQmxSetAOCustomScaleName(taskHandle, channel, name):
    taskHandle.custom_units = name
