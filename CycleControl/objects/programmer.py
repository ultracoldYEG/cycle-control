# from spinapi import *
# from PyDAQmx import *

from CycleControl.mock_spinapi import *
from CycleControl.mock_PyDAQmx import *
from CycleControl.objects.instruction import *

import numpy as np
import serial
import time
from CycleControl.helpers import *

class Programmer(object):
    def __init__(self, controller):
        #setUp NI board
        self.controller = controller
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
        self.novatech_tables = {}

    def update_task_handles(self):
        self.clear_all_task_handles()
        self.taskHandles = {}

        for board in self.controller.hardware.ni_boards:
            task = TaskHandle(0)
            DAQmxCreateTask("", task)
            for i, channel in enumerate(board.channels):
                if not channel.enabled:
                    continue

                scale = DAQmx_Val_FromCustomScale if channel.scaling else DAQmx_Val_Volts
                physical_channel = board.id + '/ao' + str(i) # "Dev3/ao6:7"
                DAQmxCreateAOVoltageChan(task, physical_channel, "", channel.min, channel.max, scale, None)
                if channel.scaling:
                    DAQmxSetAOCustomScaleName(task, physical_channel, channel.scaling)
            self.taskHandles.update([(board.id, task)])

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
        timing_flags = self.cycle.timing_flags

        for board in self.controller.hardware.pulseblasters:
            board_data = self.cycle.digital_data.get(board.id)
            pb_select_board(int(board.id))
            pb_start_programming(PULSE_PROGRAM)
            timing_flag = self.convert_timing_flag(timing_flags[0])
            start = pb_inst_pbonly(int(board_data[0][::-1], 2), timing_flag, None, (domain[1] - domain[0]) * 1000 * ms)
            for i in range(1, len(domain)-2):
                pin_flag = int(board_data[i][::-1], 2)
                timing_flag = self.convert_timing_flag(timing_flags[i])
                stepsize = (domain[i+1] - domain[i]) * 1000 * ms
                pb_inst_pbonly(pin_flag, timing_flag, None, stepsize)
            pb_inst_pbonly(int(board_data[-2][::-1], 2), Inst.BRANCH, start, (domain[-1] - domain[-2]) * 1000 * ms)
            pb_stop_programming()

    def convert_timing_flag(self, timing_flag):
        if timing_flag is ContinueTimingType:
            return Inst.CONTINUE
        elif timing_flag is WaitTimingType:
            return Inst.WAIT
        else:
            raise TypeError('Invalid timing flag type')

    def program_NI(self):
        for board in self.controller.hardware.ni_boards:
            id = board.id
            analog_board_data = self.cycle.analog_data.get(id)
            task = self.taskHandles.get(id)
            data = []
            num_samples = len(force_even(analog_board_data[0][:-1]))

            for i, channel in enumerate(board.channels):
                if channel.enabled:
                    data += force_even(analog_board_data[i][:-1])

            data = np.array(data, dtype=np.float64)
            DAQmxCfgSampClkTiming(task, "/"+board.id + "/PFI0", 10000.0, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, num_samples)
            DAQmxWriteAnalogF64(task, num_samples, 0, 10.0, DAQmx_Val_GroupByChannel, data, None, None)

    def program_novatech(self):
        for board, vals in self.cycle.novatech_data.iteritems():
            out = self.get_novatech_out(0, 0, vals)
            for sample in range(len(vals[0]) - 1):
                out += self.get_novatech_out(sample, sample + 1, vals)
            out += self.get_novatech_out(sample, sample + 2, vals, state='00')
            if self.novatech_tables.get(board, None) == out:
                continue
            # with serial.Serial(board, baudrate=19200, timeout=20.0) as nova_device:
            #     nova_device.write('M 0\n'.encode('utf-8'))  # entering table writing mode
            #     nova_device.write(out.encode('utf-8'))
            #     nova_device.write('M t\n'.encode('utf-8'))  # finished writing table
            self.novatech_tables.update([(board, out)])

    def get_novatech_out(self, sample, addr, vals, state = 'FF'):
        result = ''
        addr = np.base_repr(addr, 16).zfill(4)
        for channel in range(len(vals) / 3):
            amp = np.base_repr(int(vals[3 * channel + 0][sample]), 16).zfill(4)
            freq = np.base_repr(int(vals[3 * channel + 1][sample] * 1e6 / 0.1), 16).zfill(8)
            phase = np.base_repr(int(vals[3 * channel + 2][sample]), 16).zfill(4)
            result += 't{0:1.1} {1:4.4} {2:8.8},{3:4.4},{4:4.4},{5:2.2}\n'.format(str(channel), addr, freq, phase, amp, state)
        return result

    def start_device_handler(self):
        if self.get_first_task_handle():
            self.start_all_task_handles()
            time.sleep(0.01)
            pb_start()
            DAQmxWaitUntilTaskDone(self.get_first_task_handle(), self.cycle.analog_domain[-1])  # seconds
            self.stop_all_task_handles()
        else:
            pb_start()
            time.sleep(self.cycle.analog_domain[-1])
        pb_stop()

    def stop_device_handler(self):
        self.stop_all_task_handles()
        pb_stop()

    def apply_default_setup(self):
        print 'applying default setup'
        for board, board_data in self.controller.default_setup.digital_pins.iteritems():
            pb_select_board(int(board))
            pb_start_programming(PULSE_PROGRAM)
            start = pb_inst_pbonly(int(board_data[0][::-1], 2), Inst.CONTINUE, None,  1000 * ms)
            pb_inst_pbonly(int(board_data[0][::-1], 2), Inst.BRANCH, start, 1000 * ms)
            pb_stop_programming()

        for board in self.controller.hardware.ni_boards:
            id = board.id
            analog_board_data = self.controller.default_setup.analog_functions.get(id)
            task = self.taskHandles.get(id)
            data = []
            num_samples = 1

            for i, channel in enumerate(board.channels):
                if channel.enabled:
                    data.append(float(analog_board_data[i]))

            data = np.array(data, dtype=np.float64)
            DAQmxCfgSampClkTiming(task, "/"+board.id + "/PFI0", 10000.0, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, num_samples)
            DAQmxWriteAnalogF64(task, num_samples, 0, 10.0, DAQmx_Val_GroupByChannel, data, None, None)

        for board in self.controller.hardware.novatechs:
            id = board.id
            data = self.controller.default_setup.novatech_functions.get(id) # List len 12
            # with serial.Serial(id, baudrate=19200, timeout=20.0) as nova_device:
            #     for i, channel in enumerate(board.channels):
            #         if channel.enabled:
            #
            #             amp =  'V{} {}\n'.format(i, int(data[3 * i + 0]))
            #             freq = 'F{} {:<011f}\n'.format(i, float(data[3 * i + 1]))
            #             phase = 'P{} {}\n'.format(i, int(data[3 * i + 2]))
            #
            #             nova_device.write(amp.encode('utf-8'))
            #             nova_device.write(freq.encode('utf-8'))
            #             nova_device.write(phase.encode('utf-8'))
