from PyQt5.QtCore import *
from PyQt5.QtGui import *

from CycleControl.objects.cycle_controller import *
from CycleControl.objects.hardware import *
from CycleControl.helpers import *

class BoardsModel(QAbstractItemModel):
    def __init__(self , controller, parent = None):
        QAbstractItemModel.__init__(self, parent)
        self.controller = controller

    @property
    def boards(self):
        return self.controller.hardware.pulseblasters

    def rowCount(self, parent = None, *args, **kwargs):
        parent = parent.internalPointer()
        if parent is None:
            return len(self.boards)
        if isinstance(parent, Board):
            return parent.CHANNEL_NUM
        if isinstance(parent, Channel):
            return 0

    def columnCount(self, parent = None, *args, **kwargs):
        return 2

    def new_board(self):
        self.insertRow(self.rowCount())

    def remove_board(self, idx):
        self.removeRow(idx)

    def insertRows(self, row, count, parent=None, *args, **kwargs):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i in range(row, row + count):
            self.create_board(i)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None, *args, **kwargs):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for i in range(row, row + count):
            self.delete_board(i)
        self.endRemoveRows()
        return True

    def parent(self, index = None):
        item = index.internalPointer()
        parent = item.parent
        if isinstance(parent, Controller):
            return QModelIndex()
        return self.createIndex(parent.row, 0, parent)

    def index(self, row, col, parent=None, *args, **kwargs):
        parent_node = parent.internalPointer()
        if parent_node is None:
            return self.createIndex(row, col, self.boards[row])
        elif isinstance(parent_node, Board):
            return self.createIndex(row, col, parent_node[row])
        return QModelIndex()


class PulseBlastersModel(BoardsModel):

    @property
    def boards(self):
        return self.controller.hardware.pulseblasters

    def data(self, index, role = None):
        item = index.internalPointer()
        if isinstance(item, Board):
            return self.board_data(index, role, item)
        elif isinstance(item, Channel):
            return self.channel_data(index, role, item)

    def board_data(self, index, role, board):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return board.id

    def channel_data(self, index, role, channel):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return channel.row
            if index.column() == 1:
                return channel.label

    def setData(self, index, val, role = None):
        pass

    def create_board(self, idx):
        pb = PulseBlasterBoard(str(len(self.controller.hardware.pulseblasters)), self.controller)
        self.controller.hardware.pulseblasters.append(pb)

    def delete_board(self, idx):
        if self.controller.hardware.pulseblasters:
            del self.controller.hardware.pulseblasters[idx]

    def flags(self, index):
        item = index.internalPointer()
        if isinstance(item, Board):
            return self.board_flags(index)
        elif isinstance(item, Channel):
            return self.channel_flags(index)

    def board_flags(self, index):
        return Qt.ItemIsEditable

    def channel_flags(self, index):
        return Qt.ItemIsEditable