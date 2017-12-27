from PyQt5.QtCore import *
from PyQt5.QtGui import *

from CycleControl.objects.instruction import *
from CycleControl.helpers import *

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
        return 7

    def refresh(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, 6))

    def data(self, index, role = None):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() < 6:
                return self.vars[index.row()][index.column()]
            if index.column() == 6:
                return str(self.vars[index.row()].get_stepsize(self.controller.proc_params.steps))

        if role == Qt.BackgroundRole and self.vars[index.row()].send:
            return QColor(140,255,100)

    def setData(self, index, val, role = None):
        if role == Qt.EditRole:
            self.vars[index.row()][index.column()] = val
            self.refresh()
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
        if role in (Qt.DisplayRole, Qt.EditRole):
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


class CurrentVariablesModel(QAbstractTableModel):
    def __init__(self , var_dict, parent = None):
        QAbstractItemModel.__init__(self, parent)
        self.vars = var_dict.items()

    def rowCount(self, parent = None, *args, **kwargs):
        return len(self.vars)

    def columnCount(self, parent = None, *args, **kwargs):
        return 2

    def new_vars(self, new_var_dict):
        self.vars = new_var_dict.items()
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))

    def data(self, index, role = None):
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.vars[index.row()][index.column()]

    def setData(self, index, val, role = None):
        pass