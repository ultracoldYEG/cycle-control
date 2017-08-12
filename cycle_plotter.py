try:
    from PyQt4.uic import loadUiType
    from PyQt4 import QtCore
    from PyQt4.QtGui import *
except:
    from PyQt5.uic import loadUiType
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from cycle import *

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
    def __init__(self, gui):
        self.gui = gui
        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(111)
        self.step = 1

        self.canvas = FigureCanvas(self.fig)
        self.gui.plot_layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self.gui.widget, coordinates=True)
        self.gui.plot_layout.addWidget(self.toolbar)
        self.toolbar.setFixedHeight(24)

        self.canvas.draw()
        self.cycle = None

        self.gui.digital_channel_combo = CheckableComboBox()
        self.gui.analog_channel_combo = CheckableComboBox()
        self.gui.novatech_channel_combo = CheckableComboBox()

        self.gui.gridLayout_10.addWidget(self.gui.digital_channel_combo, 2, 0)
        self.gui.gridLayout_10.addWidget(self.gui.analog_channel_combo, 2, 1)
        self.gui.gridLayout_10.addWidget(self.gui.novatech_channel_combo, 2, 2)

        self.gui.plot_button.clicked.connect(self.update_data)
        self.gui.cycle_plot_number.valueChanged.connect(self.update_step)
        self.update_channels()

    def update_channels(self):
        self.gui.digital_channel_combo.clear()
        self.gui.analog_channel_combo.clear()
        self.gui.novatech_channel_combo.clear()
        for i in range(3, self.gui.digital_table.columnCount()):
            name = self.gui.digital_table.horizontalHeaderItem(i).text()
            self.add_checkable_combo_item(self.gui.digital_channel_combo, name, i-3)

        for i in range(3, self.gui.analog_table.columnCount()):
            name = self.gui.analog_table.horizontalHeaderItem(i).text()
            self.add_checkable_combo_item(self.gui.analog_channel_combo, name, i - 3)

        for i in range(3, self.gui.novatech_table.columnCount()):
            name = self.gui.novatech_table.horizontalHeaderItem(i).text()
            self.add_checkable_combo_item(self.gui.novatech_channel_combo, name, i - 3)

    def update_step(self, val):
        if val <= self.gui.proc_params.steps:
            self.step = val
            self.update_data()

    def update_data(self):
        if not len(self.gui.proc_params.instructions):
            print('Put in more instructions')
            return
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.ax.grid()
        self.cycle = Cycle(self.gui.proc_params.instructions, self.gui.proc_params.get_cycle_variables(self.step - 1))
        self.cycle.create_waveforms()

        results = []
        for i in range(self.gui.digital_channel_combo.count()):
            if self.gui.digital_channel_combo.model().item(i, 0).checkState():
                results.append(i)
        self.plot_digital_channels(*results)

        results = []
        for i in range(self.gui.analog_channel_combo.count()):
            if self.gui.analog_channel_combo.model().item(i, 0).checkState():
                results.append(i)
        self.plot_analog_channels(*results)

        results = []
        for i in range(self.gui.novatech_channel_combo.count()):
            if self.gui.novatech_channel_combo.model().item(i, 0).checkState():
                results.append(i)
        self.plot_novatech_channels(*results)

        self.canvas.draw()

    def add_checkable_combo_item(self, combo, name, i):
        combo.addItem(str(name))
        item = combo.model().item(i, 0)
        item.setCheckState(QtCore.Qt.Unchecked)

    def plot_analog_channels(self, *channels):
        plot_num = len(channels)

        for i in range(plot_num):
            analog_domain = self.cycle.analog_domain
            analog_data = self.cycle.analog_data[channels[i]]
            x, y = prepare_sample_plot_data(analog_domain, analog_data)
            self.ax.plot(x, y, marker='o', markersize=2)

    def plot_novatech_channels(self, *channels):
        plot_num = len(channels)

        for i in range(plot_num):
            analog_domain = self.cycle.novatech_domain
            analog_data = self.cycle.novatech_data[channels[i]]
            x, y = prepare_sample_plot_data(analog_domain, analog_data)
            self.ax.plot(x, y, marker='o', markersize=2)

    def plot_digital_channels(self, *channels):
        plot_num = len(channels)

        for i in range(plot_num):
            digital_domain = self.cycle.digital_domain
            digital_data = [int(x[channels[i]]) for x in self.cycle.digital_data]
            x, y = prepare_sample_plot_data(digital_domain, digital_data)
            self.ax.plot(x, y, marker='o', markersize=2)


class CheckableComboBox(QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QStandardItemModel(self))

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)