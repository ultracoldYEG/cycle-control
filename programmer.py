#from spinapi import *
#from PyDAQmx import *

from cycle_plotter import *
from mock_spinapi import *
from mock_PyDAQmx import *
import numpy as np
import serial
import threading

class Programmer(object):
    def __init__(self):
        #setUp NI board
        self.taskHandle = taskHandle()

        # Set up pulse blaster
        pb_set_debug(1)

        print("Copyright (c) 2015 SpinCore Technologies, Inc.")
        print("Using SpinAPI Library version %s" % pb_get_version())
        print("Found %d boards in the system.\n" % pb_count_boards())

        pb_select_board(0)

        if pb_init() != 0:
            print("Error initializing board: %s" % pb_get_error())
            input("Please press a key to continue.")
            exit(-1)

        pb_core_clock(100.0)


    def program_device_handler(self, cycle):
        pb_stop()

        self.cycle = cycle
        self.cycle.create_waveforms()

        self.program_pulse_blaster()
        self.program_NI()
        self.program_novatech()

    def program_pulse_blaster(self):
        domain = self.cycle.digital_domain
        data = self.cycle.digital_data

        pb_start_programming(PULSE_PROGRAM)
        start = pb_inst_pbonly(int(data[0], 2), Inst.CONTINUE, None, (domain[1] - domain[0]) * s)
        for i in range(1, len(domain)-2):
            pin_flag = int(data[i], 2)
            stepsize = (domain[i+1] - domain[i]) * s
            pb_inst_pbonly(pin_flag, Inst.CONTINUE, None, stepsize)

        pb_inst_pbonly(int(data[-2], 2), Inst.BRANCH, start, (domain[-1] - domain[-2]) * s)
        pb_stop_programming()

    def program_NI(self):
        analog_data_grouped_by_channel = [x for channel in self.cycle.analog_data for x in channel[:-1]]

        analog_data = np.array(analog_data_grouped_by_channel, dtype=np.float64)
        num_samples = int(len(analog_data) / 2)
        try:
            DAQmxStopTask(self.taskHandle)
            DAQmxClearTask(self.taskHandle)
        except:
            print('no task')

        self.taskHandle = taskHandle()

        DAQmxCreateTask("", self.taskHandle)

        DAQmxCreateAOVoltageChan(self.taskHandle, "Dev3/ao6:7", "", -5.0, 5.0, DAQmx_Val_Volts, None)
        DAQmxCfgSampClkTiming(self.taskHandle, "/Dev3/PFI0", 10000.0, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, num_samples)

        DAQmxWriteAnalogF64(self.taskHandle, num_samples, 0, 10.0, DAQmx_Val_GroupByChannel, analog_data, None, None)

    def program_novatech(self):
        nova_data = self.cycle.novatech_data
        with serial.Serial('COM1', baudrate=19200, timeout=20.0) as nova_device:
            nova_device.write('M 0\n'.encode('utf-8'))  # setting mode to table enter mode
            for sample in range(len(nova_data[0])):
                for channel in range(len(nova_data)/3):

                    addr = np.base_repr(int(sample), 16).zfill(4)
                    amp = np.base_repr(int(nova_data[3 * channel + 0][sample]), 16).zfill(4)
                    freq = np.base_repr(int(nova_data[3 * channel + 1][sample] * 1e6 / 0.1), 16).zfill(8)
                    phase = np.base_repr(int(nova_data[3 * channel + 2][sample]), 16).zfill(4)

                    #print 't{0:1.1} {1:4.4} {2:8.8},{3:4.4},{4:4.4},{5:2.2}'.format(str(channel), addr,  freq, phase, amp, '00')

                    #tn 3fff aabbccdd,eeff,gghh,ii
                    #channel , address, freq, phase, amp, dwell
                    #TODO proper dwell time setting for external triggering?

                    #convert V to dBm: dBm = 10 * log_10 ( V_RMS^2 / (50ohm * 1mW) )

    def start_device_handler(self):
        time = self.cycle.analog_domain[-1]
        thread = cycle_thread(self.taskHandle, time)
        thread.start()
        thread.join()

    def stop_device_handler(self):
        DAQmxStopTask(self.taskHandle)
        pb_stop()


class cycle_thread(threading.Thread):
    def __init__(self, taskHandle, time):
        threading.Thread.__init__(self)
        self.taskHandle = taskHandle
        self.time = time

    def run(self):
        print('activated')

        pb_start()

        DAQmxStartTask(self.taskHandle)
        DAQmxWaitUntilTaskDone(self.taskHandle, self.time) #seconds
        DAQmxStopTask(self.taskHandle)

        pb_stop()
        print('Cycle complete. Waiting for next start command..')