from user_functions import *
import matplotlib.pyplot as plt
import re

FUNCTION_REGEX = r'^(\w+)\((.*)\)$'

class WaveformGenerator(object):
    def __init__(self, cycle_data):
        self.cycle_data = cycle_data
        self.instructions = cycle_data.instructions


    def generate_all_waveforms(self):
        self.generate_analog_waveform()
        self.generate_novatech_waveform()
        self.generate_digital_waveform()


    def generate_analog_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            analog_domain, analog_waveforms = self.generate_single_waveform(inst, inst.analog_functions)
            self.cycle_data.analog_domain += list(analog_domain + total_t)
            for j in range(len(analog_waveforms)):
                self.cycle_data.analog_data[j] += analog_waveforms[j]

            total_t += inst.duration

    def generate_novatech_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            novatech_domain, novatech_waveforms = self.generate_single_waveform(inst, inst.novatech_functions)
            self.cycle_data.novatech_domain += list(novatech_domain + total_t)
            for j in range(len(novatech_waveforms)):
                self.cycle_data.novatech_data[j] += novatech_waveforms[j]

            total_t += inst.duration

    def generate_digital_waveform(self):
        domain = [0.0]
        for inst in self.instructions:
            domain.append(domain[-1] + inst.duration)

        iter_pins = iter([inst.digital_pins for inst in self.instructions])
        iter_domains = [iter(domain), iter(self.cycle_data.analog_domain), iter(self.cycle_data.novatech_domain)]
        next = [x.next() for x in iter_domains]
        smallest = min(next)

        analog_pin = 2
        novatech_pin = 3

        while True:
            index = next.index(smallest)

            if index == 0:
                self.pulse_pins(smallest, iter_pins.next(), analog_pin, novatech_pin)
                next = [x.next() for x in iter_domains]
            elif index == 1:
                self.pulse_pins(smallest, self.cycle_data.digital_data[-1], analog_pin)
                next[1] = iter_domains[1].next()
            else:
                self.pulse_pins(smallest, self.cycle_data.digital_data[-1], novatech_pin)
                next[2] = iter_domains[2].next()
            smallest = min(next)
            if smallest == domain[-1]:
                self.cycle_data.digital_domain.append(smallest)
                self.cycle_data.digital_data.append(self.cycle_data.digital_data[-1])
                break


    def pulse_pins(self, domain, pin_flag, *pins):
        for i in pins:
            pin_flag = self.change_digital_pin(pin_flag, i, '1')

        self.cycle_data.digital_domain.append(domain)
        self.cycle_data.digital_data.append(pin_flag)

        for i in pins:
            pin_flag = self.change_digital_pin(pin_flag, i, '0')

        self.cycle_data.digital_domain.append(domain + 5 * 10**-6)
        self.cycle_data.digital_data.append(pin_flag)

    def change_digital_pin(self,binary_string, pin_num, new_string):
        return binary_string[:pin_num] + new_string + binary_string[pin_num + 1:]

    def generate_single_waveform(self, inst, func_strings):
        funcs = []
        all_constant = True
        for func_string in func_strings:
            result = re.match(FUNCTION_REGEX, func_string)
            if result:
                key = result.group(1)
                args = [float(x) for x in result.group(2).split(',')]
            else:
                try:
                    key = 'const'
                    args = [float(func_string)]
                except ValueError:
                    print('not a valid function: ', func_string)
                    return

            if key == 'const':
                funcs.append((constFunc, args))
            elif key == 'ramp':
                funcs.append((linFunc, args))
                all_constant = False
            elif key == 'sin':
               funcs.append((sinFunc, args))
               all_constant = False
            elif key == 'exp':
                funcs.append((expFunc, args))
                all_constant = False

        duration = inst.duration
        stepsize = inst.stepsize

        if stepsize == 0:
            stepsize = duration

        steps = np.ceil(duration / stepsize)
        
        domain = np.linspace(0.0, duration, steps, False)
        
        if all_constant:
            domain = np.array([domain[0]])
            
        if self.instructions[-1] == inst:
            domain = np.append(domain, duration)
            
        return domain, [list(func(domain, duration, *args)) for func, args in funcs]


    def plot_waveforms(self):
        fig = plt.figure()
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        for i in range(8):
            ax1.plot(*self.prepare_sample_plot_data(self.cycle_data.analog_domain, self.cycle_data.analog_data[i]), marker = 'o', markersize=4)
            ax2.plot(*self.prepare_sample_plot_data(self.cycle_data.novatech_domain, self.cycle_data.novatech_data[i]), marker = 'o', markersize=4)
        ax3.plot(*self.prepare_sample_plot_data(self.cycle_data.digital_domain, [int(x[0]) for x in self.cycle_data.digital_data]), marker = 'o', markersize=4 )
        ax3.plot(*self.prepare_sample_plot_data(self.cycle_data.digital_domain, [2+int(x[2]) for x in self.cycle_data.digital_data]), marker = 'o', markersize=4 )
        ax3.plot(*self.prepare_sample_plot_data(self.cycle_data.digital_domain, [4+int(x[3]) for x in self.cycle_data.digital_data]), marker = 'o', markersize=4)

        ax1.set_xlim([0,self.cycle_data.analog_domain[-1]])
        plt.show()

    def prepare_sample_plot_data(self, domain, data):
        new_domain = []
        new_data = []
        for i in range(1,len(domain)):
            new_domain.append(domain[i-1])
            new_data.append(data[i-1])

            new_domain.append(domain[i])
            new_data.append(data[i-1])
        new_domain.append(domain[-1])
        new_data.append(data[-1])

        return new_domain, new_data
