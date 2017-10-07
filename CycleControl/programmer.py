# from spinapi import *
# from PyDAQmx import *

from mock_spinapi import *
from mock_PyDAQmx import *
import numpy as np
import serial
import time
from helpers import *

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
            task = TaskHandle(0)
            DAQmxCreateTask("", task)
            for i, channel in enumerate(board.channels):
                if not channel.enabled:
                    continue

                physical_channel = board.board_identifier + '/ao' + str(i) # "Dev3/ao6:7"
                DAQmxCreateAOVoltageChan(task, physical_channel, "", channel.min, channel.max, DAQmx_Val_Volts, None)
                # TODO HINT custom scales - use : DAQmxCreateLinScale
                # TODO DAQmxGetSysScales( 'str', 10000)
            self.taskHandles.update([(board.board_identifier, task)])

    def start_all_task_handles(self):
        for board, task in self.taskHandles.iteritems():
            DAQmxStartTask(task)

    def stop_all_task_handles(self):
        for board, task in self.taskHandles.iteritems():
            DAQmxStopTask(task)

    def clear_all_task_handles(self):
        for board, task in self.taskHandles.iteritems():
            DAQmxStopTask(task)
            DAQmxClearTask(task)

    def get_first_task_handle(self):
        for board, task in self.taskHandles.iteritems():
            return task

    def program_device_handler(self, cycle):
        pb_stop()

        self.cycle = cycle
        self.cycle.create_waveforms()

        self.program_pulse_blaster()
        self.program_NI()
        self.program_novatech()

    def program_pulse_blaster(self):
        domain = self.cycle.digital_domain

        for board, board_data in self.cycle.digital_data.iteritems():
            pb_select_board(int(board))
            pb_start_programming(PULSE_PROGRAM)
            start = pb_inst_pbonly(int(board_data[0][::-1], 2), Inst.CONTINUE, None, (domain[1] - domain[0]) * 1000 * ms)
            for i in range(1, len(domain)-2):
                pin_flag = int(board_data[i][::-1], 2)
                stepsize = (domain[i+1] - domain[i]) * 1000 * ms
                pb_inst_pbonly(pin_flag, Inst.CONTINUE, None, stepsize)

            pb_inst_pbonly(int(board_data[-2][::-1], 2), Inst.BRANCH, start, (domain[-1] - domain[-2]) * 1000 * ms)
            pb_stop_programming()

    def program_NI(self):
        for board in self.gui.hardware.ni_boards:
            id = board.board_identifier
            analog_board_data = self.cycle.analog_data.get(id)
            task = self.taskHandles.get(id)
            data = []
            num_samples = len(force_even(analog_board_data[0][:-1]))

            for i, channel in enumerate(board.channels):
                if channel.enabled:
                    data += force_even(analog_board_data[i][:-1])

            data = np.array(data, dtype=np.float64)
            DAQmxCfgSampClkTiming(task, "/"+board.board_identifier + "/PFI0", 10000.0, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, num_samples)
            DAQmxWriteAnalogF64(task, num_samples, 0, 10.0, DAQmx_Val_GroupByChannel, data, None, None)

    def program_novatech(self):
        for board, vals in self.cycle.novatech_data.iteritems():
            print 'programming: ', board
            with serial.Serial(board, baudrate=19200, timeout=20.0) as nova_device:
                nova_device.write('M 0\n'.encode('utf-8'))  # entering table writing mode
                out = ''
                for sample in range(len(vals[0]) - 1):
                    for channel in range(len(vals)/3):
                        addr = np.base_repr(int(sample), 16).zfill(4)
                        amp = np.base_repr(int(vals[3 * channel + 0][sample]), 16).zfill(4)
                        freq = np.base_repr(int(vals[3 * channel + 1][sample] * 1e6 / 0.1), 16).zfill(8)
                        phase = np.base_repr(int(vals[3 * channel + 2][sample]), 16).zfill(4)

                        out += 't{0:1.1} {1:4.4} {2:8.8},{3:4.4},{4:4.4},{5:2.2}\n'.format(str(channel), addr,  freq, phase, amp, 'FF')

                        #tn 3fff aabbccdd,eeff,gghh,ii
                        #channel , address, freq, phase, amp, dwell
                        #convert V to dBm: dBm = 10 * log_10 ( V_RMS^2 / (50ohm * 1mW) )

                nova_device.write(out.encode('utf-8'))
                nova_device.write('M t\n'.encode('utf-8'))  # finished writing table

    def start_device_handler(self):
        if self.get_first_task_handle():
            self.start_all_task_handles()
            time.sleep(0.01)
            pb_start()
            init = time.time()
            DAQmxWaitUntilTaskDone(self.get_first_task_handle(), self.cycle.analog_domain[-1])  # seconds
            print 'that took ', (time.time() - init)
            self.stop_all_task_handles()
        else:
            pb_start()
            time.sleep(self.cycle.analog_domain[-1])
        pb_stop()

    def stop_device_handler(self):
        self.stop_all_task_handles()
        pb_stop()
        # TODO set default values here
