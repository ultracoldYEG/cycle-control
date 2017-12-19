from PyQt5.QtCore import *


class ProcedureModel(QAbstractTableModel):
    def __init__(self , controller, parent = None, **kwargs):
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