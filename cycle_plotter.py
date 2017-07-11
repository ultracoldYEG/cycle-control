import matplotlib.pyplot as plt

def prepare_sample_plot_data(domain, data):
    new_domain = []
    new_data = []
    for i in range(1, len(domain)):
        new_domain.append(domain[i - 1])
        new_data.append(data[i - 1])

        new_domain.append(domain[i])
        new_data.append(data[i - 1])

    new_domain.append(domain[-1])
    new_data.append(data[-1])

    return new_domain, new_data

class CyclePlotter(object):
    def __init__(self, cycle):
        self.cycle = cycle

    def plot_analog_channels(self, *channels):
        plot_num = len(channels)

        fig = plt.figure()
        for i in range(plot_num):
            ax = fig.add_subplot(plot_num, 1, i+1)
            analog_domain = self.cycle.analog_domain
            analog_data = self.cycle.analog_data[channels[i]]
            x, y = prepare_sample_plot_data(analog_domain, analog_data)
            ax.plot(x, y, marker='o', markersize=2)
            ax.set_ylim([min(y)-1, max(y)+1])

        plt.show()

    def plot_novatech_channels(self, *channels):
        plot_num = len(channels)

        fig = plt.figure()
        for i in range(plot_num):
            ax = fig.add_subplot(plot_num, 1, i+1)
            analog_domain = self.cycle.novatech_domain
            analog_data = self.cycle.novatech_data[channels[i]]
            x, y = prepare_sample_plot_data(analog_domain, analog_data)
            ax.plot(x, y, marker='o', markersize=2)
            ax.set_ylim([min(y) - 1, max(y) + 1])
        plt.show()



    def plot_digital_channels(self, *channels):
        plot_num = len(channels)
        fig = plt.figure()
        for i in range(plot_num):
            ax = fig.add_subplot(plot_num, 1, i + 1)
            digital_domain = self.cycle.digital_domain
            digital_data = [int(x[channels[i]]) for x in self.cycle.digital_data]
            x, y = prepare_sample_plot_data(digital_domain, digital_data)
            ax.plot(x, y, marker='o', markersize=2)
            ax.set_ylim([-0.5, 1.5])

        plt.show()


