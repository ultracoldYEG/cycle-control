#from spinapi import *
#from PyDAQmx import *

from instruction import *
from waveformGenerator import *
from mockSpinAPI import *
from mockPyDAQmx import *
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


    def program_device_handler(self, instructions):
        pb_stop()
        if len(instructions) <= 1:
            print('Put in more instructions')
            return

        cycle_data = InstructionCycle(instructions)

        wavegen = WaveformGenerator(cycle_data)
        wavegen.generate_all_waveforms()
        wavegen.plot_waveforms()

        self.program_pulse_blaster(cycle_data)
        self.program_NI(cycle_data)
        self.program_novatech(cycle_data)

    def program_pulse_blaster(self, cycle_data):
        domain = cycle_data.digital_domain
        data = cycle_data.digital_data

        # the first pulse blaster instruction is assigned to a variable so the last instruction
        # can reference this and return to the start.
        # pb_inst_pbonly(pin flags, next instruction, instruction flag (if needed), duration)
        pb_start_programming(PULSE_PROGRAM)
        start = pb_inst_pbonly(int(data[0], 2), Inst.CONTINUE, None, (domain[1] - domain[0]) * s)

        for i in range(1, len(domain)-2):
            pin_flag = int(data[i], 2)
            stepsize = (domain[i+1] - domain[i]) * s
            pb_inst_pbonly(pin_flag, Inst.CONTINUE, None, stepsize)

        pb_inst_pbonly(int(data[-2], 2), Inst.BRANCH, start, (domain[-1] - domain[-2]) * s)
        pb_stop_programming()

    def program_NI(self, cycle_data):
        analog_data_grouped_by_channel = [x for channel in cycle_data.analog_data for x in channel[:-1]]

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

    def program_novatech(self, cycle_data):
        # example novatech programming
        # nova_device = serial.Serial('COM3', baudrate=19200, timeout=20.0)
        # nova_device.write('M 0\n'.encode('utf-8'))  # setting mode to single tone
        # nova_device.write('F0 5.0000000\n'.encode('utf-8'))  # setting frequency to a static 2MHz
        # nova_device.write('V0 20\n'.encode('utf-8'))  # setting amplitude to a fraction 20/1023 of it's maximum output
        # nova_device.close()
        return

    def start_device_handler(self):
        thread = cycle_thread(self.taskHandle)
        thread.start()


    def stop_device_handler(self):
        DAQmxStopTask(self.taskHandle)
        pb_stop()


class cycle_thread(threading.Thread):
    def __init__(self, taskHandle):
        threading.Thread.__init__(self)
        self.taskHandle = taskHandle

    def run(self):
        print('activated')

        pb_start()

        DAQmxStartTask(self.taskHandle)
        DAQmxWaitUntilTaskDone(self.taskHandle, 10.0) #seconds
        DAQmxStopTask(self.taskHandle)

        pb_stop()
        time.sleep(0.2)
        print('Cycle complete. Waiting for next start command..')