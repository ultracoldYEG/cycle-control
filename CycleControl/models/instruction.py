from PyQt5.QtCore import *
from PyQt5.QtGui import *

import copy

from CycleControl.objects.instruction import *
from CycleControl.helpers import *


class DigitalProxyModel(QSortFilterProxyModel):
    def filterAcceptsColumn(self, col, index):
        pb_count = sum((board.num_active() for board in self.sourceModel().controller.hardware.pulseblasters))
        if col <= 2 + pb_count:
            return True
        return False


class AnalogProxyModel(QSortFilterProxyModel):
    def filterAcceptsColumn(self, col, index):
        pb_count = sum((board.num_active() for board in self.sourceModel().controller.hardware.pulseblasters))
        ni_count = sum((board.num_active() for board in self.sourceModel().controller.hardware.ni_boards))
        if col <= 2:
            return True
        if col > 2 + pb_count and col <= 2 + pb_count + ni_count:
            return True
        return False


class NovatechProxyModel(QSortFilterProxyModel):
    def filterAcceptsColumn(self, col, index):
        pb_count = sum((board.num_active() for board in self.sourceModel().controller.hardware.pulseblasters))
        ni_count = sum((board.num_active() for board in self.sourceModel().controller.hardware.ni_boards))
        if col <= 2:
            return True
        if col > 2 + pb_count + ni_count:
            return True
        return False


class InstructionsModel(QAbstractTableModel):
    def __init__(self , controller, parent = None, **kwargs):
        QAbstractItemModel.__init__(self, parent)
        self.controller = controller

    @property
    def instructions(self):
        return self.controller.proc_params.instructions

    def rowCount(self, parent = None, *args, **kwargs):
        return len(self.instructions)

    def columnCount(self, parent=None, *args, **kwargs):
        count = 3
        for hardware_type in [self.controller.hardware.pulseblasters, self.controller.hardware.ni_boards, self.controller.hardware.novatechs]:
            for board in hardware_type:
                count += board.num_active()
        return count

    def get_channel_by_col(self, col, boards):
        for board in boards:
            for i, channel in enumerate(board.channels):
                if channel.enabled:
                    col -= 1
                if col == -1:
                    return board, i
        return None, None

    def data(self, index, role=None):
        row = index.row()
        col = index.column()
        inst = self.instructions[row]

        pb_count = sum((board.num_active() for board in self.controller.hardware.pulseblasters))
        ni_count = sum((board.num_active() for board in self.controller.hardware.ni_boards))
        nova_count = sum((board.num_active() for board in self.controller.hardware.novatechs))

        if role in (Qt.DisplayRole, Qt.EditRole):
            if col == 0:
                return inst.name
            elif col == 1:
                return inst.duration
            elif col == 2:
                return inst.stepsize

            col -= 3


            if col < pb_count:
                return

            col -= pb_count

            if col < ni_count:
                board, num = self.get_channel_by_col(col, self.controller.hardware.ni_boards)
                id = board.id
                return inst.analog_functions.get(id)[num]

            col -= ni_count

            if col < nova_count:
                col2 = col / 3
                rem = col % 3
                board, num = self.get_channel_by_col(col2, self.controller.hardware.novatechs)
                id = board.id
                return inst.novatech_functions.get(id)[3 * num + rem]

        if role == Qt.CheckStateRole:
            if col < 3:
                return
            col -= 3

            if col < pb_count:
                board, num = self.get_channel_by_col(col, self.controller.hardware.pulseblasters)
                id = board.id
                return bool_to_checkstate(inst.digital_pins.get(id)[num])

        if role == Qt.SizeHintRole:
            print col
            if col > 2 and col < pb_count + 2:
                return QSize(24,24)

    def insert_new_instruction(self, row):
        self.insertRow(row)

    def remove_instruction(self, row):
        self.removeRow(row)

    def copy_instruction(self, loc):
        self.controller.clipboard = copy.deepcopy(self.controller.proc_params.instructions[loc])

    def paste_instruction(self, idx):
        self.beginInsertRows(QModelIndex(), idx, idx)
        inst = copy.deepcopy(self.controller.clipboard)
        self.controller.proc_params.instructions.insert(idx, inst)
        self.endInsertRows()
        return True

    def setData(self, index, val, role=None):
        row = index.row()
        col = index.column()
        inst = self.instructions[row]

        pb_count = sum((board.num_active() for board in self.controller.hardware.pulseblasters))
        ni_count = sum((board.num_active() for board in self.controller.hardware.ni_boards))
        nova_count = sum((board.num_active() for board in self.controller.hardware.novatechs))

        if role == Qt.EditRole:
            if col == 0:
                inst.name = val
                return True
            elif col == 1:
                inst.duration = val
                return True
            elif col == 2:
                inst.stepsize = val
                return True

            col -= 3

            if col < pb_count:
                return True

            col -= pb_count

            if col < ni_count:
                board, num = self.get_channel_by_col(col, self.controller.hardware.ni_boards)
                id = board.id
                inst.analog_functions.get(id)[num] = val
                return True

            col -= ni_count

            if col < nova_count:
                col2 = col / 3
                rem = col % 3
                board, num = self.get_channel_by_col(col2, self.controller.hardware.novatechs)
                id = board.id
                inst.novatech_functions.get(id)[3 * num + rem] = val
                return True

            self.dataChanged.emit(index, index)

        if role == Qt.CheckStateRole:
            if col < 3:
                return
            col -= 3

            if col < pb_count:
                board, num = self.get_channel_by_col(col, self.controller.hardware.pulseblasters)
                id = board.id
                inst.digital_pins.get(id)[num] = bool(val)
                return True

        return True

    def insertRows(self, row, count, parent=None, *args, **kwargs):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i in range(row, row + count):
            self.create_instruction(i)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None, *args, **kwargs):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for i in range(row, row + count):
            self.delete_instruction(i)
        self.endRemoveRows()
        return True

    def create_instruction(self, idx):
        inst = Instruction(
            hardware = self.controller.hardware,
            name = 'Instruction ' + str(idx + 1)
        )
        self.controller.proc_params.instructions.insert(idx, inst)

    def delete_instruction(self, idx):
        if self.controller.proc_params.instructions:
            del self.controller.proc_params.dynamic_variables[idx]

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable


class VariablesModel(QAbstractTableModel):
    def __init__(self , controller, parent = None):
        QAbstractItemModel.__init__(self, parent)
        self.controller = controller

    @property
    def vars(self):
        return []

    def rowCount(self, parent = None, *args, **kwargs):
        return len(self.vars)

    def new_variable(self):
        self.insertRow(self.rowCount())

    def remove_variable(self, idx):
        self.removeRow(idx)

    def insertRows(self, row, count, parent=None, *args, **kwargs):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i in range(row, row + count):
            self.create_variable(i)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None, *args, **kwargs):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for i in range(row, row + count):
            self.delete_variable(i)
        self.endRemoveRows()
        return True


class DynamicVariablesModel(VariablesModel):
    @property
    def vars(self):
        return self.controller.proc_params.dynamic_variables

    def columnCount(self, parent=None, *args, **kwargs):
        return 6

    def data(self, index, role = None):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.vars[index.row()][index.column()]

        if role == Qt.BackgroundRole and self.vars[index.row()].send:
            return QColor(140,255,100)

    def setData(self, index, val, role = None):
        if role == Qt.EditRole:
            self.vars[index.row()][index.column()] = val
            self.dataChanged.emit(index, index)
            return True

    def create_variable(self, idx):
        dyn_var = DynamicProcessVariable(
            name = 'dynamic_variable_{0}'.format(idx)
        )
        self.controller.proc_params.dynamic_variables.append(dyn_var)

    def delete_variable(self, idx):
        if self.controller.proc_params.dynamic_variables:
            del self.controller.proc_params.dynamic_variables[idx]


class StaticVariablesModel(VariablesModel):
    @property
    def vars(self):
        return self.controller.proc_params.static_variables

    def columnCount(self, parent=None, *args, **kwargs):
        return 2

    def data(self, index, role = None):
        if role == Qt.DisplayRole:
            return self.vars[index.row()][index.column()]

    def setData(self, index, val, role = None):
        if role == Qt.EditRole:
            self.vars[index.row()][index.column()] = val
            return True

    def remove_variable(self, row):
        self.removeRow(row)

    def create_variable(self, idx, parent=None, *args, **kwargs):
        stat_var = StaticProcessVariable(
            name = 'static_variable_{0}'.format(idx)
        )
        self.controller.proc_params.static_variables.append(stat_var)

    def delete_variable(self, idx):
        if self.controller.proc_params.static_variables:
            del self.controller.proc_params.static_variables[idx]

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable