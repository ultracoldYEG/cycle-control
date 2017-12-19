from PyQt5.QtCore import *


class DynamicVariables(QAbstractTableModel):
    def __init__(self , parent = None, **kwargs):
        QAbstractItemModel.__init__(self, parent)
        var = DynamicProcessVariable()
        var.name='TEST'
        self.vars = kwargs.get('dynamic_variables', [var])

    def rowCount(self, parent = None, *args, **kwargs):
        return len(self.vars)

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def data(self, index, role = None):
        if role == Qt.DisplayRole:
            return self.vars[index.row()].name

    def index(self, p_int, p_int_1, parent=None, *args, **kwargs):
        return QModelIndex()