from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QCursor
from PyQt5 import QtCore

from CycleControl.helpers import *
from CycleControl.mock_PyDAQmx import *


class HardwareTree(QTreeWidget):
    def __init__(self, gui):
        QTreeWidget.__init__(self)
        self.gui = gui
        self.itemChanged.connect(self.cell_changed_handler)

    def redraw(self):
        pass

    def update_hardware(self, item, col):
        pass

    def cell_changed_handler(self, item, col):
        self.update_hardware(item, col)


class DigitalTree(HardwareTree):
    def __init__(self, gui):
        HardwareTree.__init__(self, gui)
        item = QTreeWidgetItem()
        item.setData(0, QtCore.Qt.DisplayRole, 'Channel')
        item.setData(1, QtCore.Qt.DisplayRole, 'Analog Pin')
        item.setData(2, QtCore.Qt.DisplayRole, 'Novatech Pin')
        self.setHeaderItem(item)

    def update_hardware(self, item, col):
        if self.gui.updating.lock:
            return
        with self.gui.updating:
            print 'UPDATING'
            if item.parent():
                board_index = self.indexOfTopLevelItem(item.parent())
                channel = self.gui.hardware.pulseblasters[board_index].channels[int(item.text(0))]
                if col == 0:
                    channel.enabled = bool(item.checkState(col))
            else:
                board_index = self.indexOfTopLevelItem(item)
                board = self.gui.hardware.pulseblasters[board_index]
                if col == 0:
                    board.board_identifier = item.text(col)

    def redraw(self):
        with self.gui.updating:
            for i in range(self.topLevelItemCount()):
                self.takeTopLevelItem(0)
            for board in self.gui.hardware.pulseblasters:
                board_root = QTreeWidgetItem(self, [board.board_identifier])
                board_root.setData(1, QtCore.Qt.DisplayRole, board.analog_pin)
                board_root.setData(2, QtCore.Qt.DisplayRole, board.novatech_pin)
                board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
                for i, channel in enumerate(board.channels):
                    item = QTreeWidgetItem(board_root, [str(i)])
                    item.setCheckState(0, bool_to_checkstate(channel.enabled))


class AnalogTree(HardwareTree):
    def __init__(self, gui):
        HardwareTree.__init__(self, gui)
        item = QTreeWidgetItem()
        item.setData(0, QtCore.Qt.DisplayRole, 'Virtual Channel')
        item.setData(1, QtCore.Qt.DisplayRole, 'Label')
        item.setData(2, QtCore.Qt.DisplayRole, 'Min')
        item.setData(3, QtCore.Qt.DisplayRole, 'Max')
        item.setData(4, QtCore.Qt.DisplayRole, 'Scaling')
        self.setHeaderItem(item)

        self.itemDoubleClicked.connect(self.checkEdit)
        self.setEditTriggers(self.NoEditTriggers)

    def update_hardware(self, item, col):
        if self.gui.updating.lock:
            return
        with self.gui.updating:
            if item.parent():
                board_index = self.indexOfTopLevelItem(item.parent())
                channel = self.gui.hardware.ni_boards[board_index].channels[int(item.text(0))]
                if col == 0:
                    channel.enabled = bool(item.checkState(col))
                elif col == 1:
                    channel.label = item.text(col)
                elif col == 2:
                    channel.min = float(item.text(col))
                elif col == 3:
                    channel.max = float(item.text(col))
                elif col == 4:
                    channel.scaling = item.text(col)
            else:
                board_index = self.indexOfTopLevelItem(item)
                board = self.gui.hardware.ni_boards[board_index]
                if col == 0:
                    board.board_identifier = item.text(col)

    def redraw(self):
        with self.gui.updating:
            for i in range(self.topLevelItemCount()):
                self.takeTopLevelItem(0)
            for board in self.gui.hardware.ni_boards:
                board_root = QTreeWidgetItem(self, [board.board_identifier])
                board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
                for i, channel in enumerate(board.channels):
                    item = QTreeWidgetItem(board_root, [str(i)])
                    item.setData(1, QtCore.Qt.DisplayRole, channel.label)
                    item.setData(2, QtCore.Qt.DisplayRole, channel.min)
                    item.setData(3, QtCore.Qt.DisplayRole, channel.max)
                    self.setItemWidget(item, 4, ScaleComboBox(self, item))
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                    item.setCheckState(0, bool_to_checkstate(channel.enabled))

    def checkEdit(self, item, col):
        if item.parent() and col > 0:
            self.editItem(item, col)
        elif not item.parent() and col == 0:
            self.editItem(item, col)

class NovatechTree(HardwareTree):
    def __init__(self, gui):
        HardwareTree.__init__(self, gui)
        item = QTreeWidgetItem()
        item.setData(0, QtCore.Qt.DisplayRole, 'Channel')
        self.setHeaderItem(item)

    def update_hardware(self, item, col):
        if self.gui.updating.lock:
            return
        with self.gui.updating:
            if item.parent():
                board_index = self.indexOfTopLevelItem(item.parent())
                channel = self.gui.hardware.novatechs[board_index].channels[int(item.text(0))]
                if col == 0:
                    channel.enabled = bool(item.checkState(col))
            else:
                board_index = self.indexOfTopLevelItem(item)
                board = self.gui.hardware.novatechs[board_index]
                if col == 0:
                    board.board_identifier = item.text(col)

    def redraw(self):
        with self.gui.updating:
            for i in range(self.topLevelItemCount()):
                self.takeTopLevelItem(0)
            for board in self.gui.hardware.novatechs:
                board_root = QTreeWidgetItem(self, [board.board_identifier])
                board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
                for i, channel in enumerate(board.channels):
                    item = QTreeWidgetItem(board_root, [str(i)])
                    item.setCheckState(0, bool_to_checkstate(channel.enabled))


class ScaleComboBox(QComboBox):
    def __init__(self, tree, item):
        QComboBox.__init__(self)
        self.tree = tree
        self.item = item
        scales = ' ' * 10000
        result = DAQmxGetSysScales(scales, 10000)
        scales = result or scales
        scales = scales.strip().split(', ')
        self.addItem('')
        self.addItems(scales)
        self.currentTextChanged.connect(self.item_changed_handler)

        channel = self.get_channel()
        if self.findText(channel.scaling, QtCore.Qt.MatchExactly) == -1:
            channel.scaling = ''
        else:
            self.setCurrentText(channel.scaling)

    def get_channel(self):
        board_index = self.tree.indexOfTopLevelItem(self.item.parent())
        return self.tree.gui.hardware.ni_boards[board_index].channels[int(self.item.text(0))]

    def item_changed_handler(self, text):
        channel = self.get_channel()
        channel.scaling = text


