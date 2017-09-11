#from spinapi import *
#from PyDAQmx import *

from mock_spinapi import *
from mock_PyDAQmx import *
import numpy as np
import serial

class Programmer(object):
    def __init__(self, gui):
        #setUp NI board
        self.gui = gui
        self.taskHandles = {}

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
        self.update_task_handles()

    def update_task_handles(self):
        self.clear_all_task_handles()
        self.taskHandles = {}

        for board in self.gui.hardware.ni_boards:
            tasks = []
            for i, channel in enumerate(board.channels):
                if not channel.enabled:
                    tasks.append(None)
                    continue
                task = taskHandle()
                DAQmxCreateTask("", task)
                physical_channel = board.board_identifier + '/ao' + str(i) # "Dev3/ao6:7"
                DAQmxCreateAOVoltageChan(task, physical_channel, "", channel.min, channel.max, DAQmx_Val_Volts, None)
                tasks.append(task)
            self.taskHandles.update([(board.board_identifier, tasks)])
        for i in self.taskHandles.iteritems():
            print i

    def start_all_task_handles(self):
        for board, tasks in self.taskHandles.iteritems():
            for task in tasks:
                if task:
                    DAQmxStartTask(task)

    def stop_all_task_handles(self):
        for board, tasks in self.taskHandles.iteritems():
            for task in tasks:
                if task:
                    DAQmxStopTask(task)

    def clear_all_task_handles(self):
        for board, tasks in self.taskHandles.iteritems():
            for task in tasks:
                if task:
                    DAQmxStopTask(task)
                    DAQmxClearTask(task)

    def get_first_task_handle(self):
        for board, tasks in self.taskHandles.iteritems():
            for task in tasks:
                if task:
                    return task

    def program_device_handler(self, cycle):
        pb_stop()

        self.cycle = cycle
        self.cycle.create_waveforms()

        self.program_pulse_blaster()
        self.program_NI()
        #self.program_novatech()

    def program_pulse_blaster(self):
        domain = self.cycle.digital_domain

        for board, board_data in self.cycle.digital_data.iteritems():
            pb_select_board(int(board))
            pb_start_programming(PULSE_PROGRAM)
            start = pb_inst_pbonly(int(board_data[0], 2), Inst.CONTINUE, None, (domain[1] - domain[0]) * s)
            for i in range(1, len(domain)-2):
                pin_flag = int(board_data[i], 2)
                stepsize = (domain[i+1] - domain[i]) * s
                pb_inst_pbonly(pin_flag, Inst.CONTINUE, None, stepsize)

            pb_inst_pbonly(int(board_data[-2], 2), Inst.BRANCH, start, (domain[-1] - domain[-2]) * s)
            pb_stop_programming()

    def program_NI(self):
        for board, tasks in self.taskHandles.iteritems():
            analog_board_data = self.cycle.analog_data.get(board)
            for i, task in enumerate(tasks):
                if task:
                    data = np.array(analog_board_data[i], dtype=np.float64)[:-1]
                    num_samples = len(data)
                    DAQmxCfgSampClkTiming(task, "/Dev3/PFI0", 10000.0, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, num_samples)
                    DAQmxWriteAnalogF64(task, num_samples, 0, 10.0, DAQmx_Val_GroupByChannel, data, None, None)

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
        pb_start()

        if self.get_first_task_handle():
            self.start_all_task_handles()
            DAQmxWaitUntilTaskDone(self.get_first_task_handle(), self.cycle.analog_domain[-1])  # seconds
            self.stop_all_task_handles()
        else:
            time.sleep(self.cycle.analog_domain[-1])

        pb_stop()

    def stop_device_handler(self):
        self.stop_all_task_handles()
        pb_stop()
        # TODO set default values here
