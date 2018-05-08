from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QItemDelegate, QComboBox

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

    def refresh(self):
        print self.rowCount()
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))

    def rowCount(self, parent = None, *args, **kwargs):

        if parent is None:
            return len(self.boards)
        parent = parent.internalPointer()
        if parent is None:
            return len(self.boards)
        if isinstance(parent, Board):
            return parent.CHANNEL_NUM
        if isinstance(parent, Channel):
            return 0

    def columnCount(self, parent = None, *args, **kwargs):
        return 2

    def remove_board(self, index):
        item = index.internalPointer()
        if isinstance(item, Board):
            self.removeRow(index.row())

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
        if parent is None:
            return QModelIndex()
        parent_node = parent.internalPointer()
        if parent_node is None and row < len(self.boards):
            return self.createIndex(row, col, self.boards[row])
        elif isinstance(parent_node, Board):
            return self.createIndex(row, col, parent_node[row])
        return QModelIndex()

    def data(self, index, role = None):
        item = index.internalPointer()
        if isinstance(item, Board):
            return self.board_data(index, role, item)
        elif isinstance(item, Channel):
            return self.channel_data(index, role, item)

    def setData(self, index, val, role = None):
        item = index.internalPointer()
        if isinstance(item, Board):
            return self.set_board_data(index, val, role, item)
        elif isinstance(item, Channel):
            return self.set_channel_data(index, val, role, item)

    def board_data(self, index, role, board):
        raise Exception('Not implemented')

    def channel_data(self, index, role, channel):
        raise Exception('Not implemented')

    def set_board_data(self, index, val, role, board):
        raise Exception('Not implemented')

    def set_channel_data(self, index, val, role, channel):
        raise Exception('Not implemented')

    def flags(self, index):
        item = index.internalPointer()
        if isinstance(item, Board):
            return self.board_flags(index)
        elif isinstance(item, Channel):
            return self.channel_flags(index)

    def board_flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.NoItemFlags

    def channel_flags(self, index):
        if index.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        return Qt.NoItemFlags

class PulseBlastersModel(BoardsModel):
    @property
    def boards(self):
        return self.controller.hardware.pulseblasters

    def headerData(self, idx, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ['Channel', 'Label'][idx]

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
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                return bool_to_checkstate(channel.enabled)

    def set_board_data(self, index, val, role, board):
        if role == Qt.EditRole:
            if index.column() == 0:
                board.id = val
                return True

    def set_channel_data(self, index, val, role, channel):
        if role == Qt.EditRole:
            if index.column() == 1:
                channel.label = val
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                channel.enabled = bool(val)
        return True

    def create_board(self, idx):
        pb = PulseBlasterBoard(str(idx), self.controller)
        self.controller.hardware.pulseblasters.append(pb)

    def delete_board(self, idx):
        if self.controller.hardware.pulseblasters:
            del self.controller.hardware.pulseblasters[idx]


class NIBoardsModel(BoardsModel):
    @property
    def boards(self):
        return self.controller.hardware.ni_boards

    def headerData(self, idx, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ['Channel', 'Label', 'Minimum', 'Maximum', 'Scaling'][idx]

    def columnCount(self, parent = None, *args, **kwargs):
        return 5

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
            if index.column() == 2:
                return channel.min
            if index.column() == 3:
                return channel.max
            if index.column() == 4:
                return channel.scaling
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                return bool_to_checkstate(channel.enabled)

    def set_board_data(self, index, val, role, board):
        if role == Qt.EditRole:
            if index.column() == 0:
                board.id = val
                return True

    def set_channel_data(self, index, val, role, channel):
        if role == Qt.EditRole:
            if index.column() == 1:
                channel.label = val
            if index.column() == 2:
                channel.min = val
            if index.column() == 3:
                channel.max = val
            if index.column() == 4:
                channel.scaling = val
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                channel.enabled = bool(val)
        return True

    def create_board(self, idx):
        ni = NIBoard('Dev{}'.format(idx), self.controller)
        self.controller.hardware.ni_boards.append(ni)

    def delete_board(self, idx):
        if self.controller.hardware.ni_boards:
            del self.controller.hardware.ni_boards[idx]

    def channel_flags(self, index):
        if index.column() in [1, 2, 3, 4]:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        return Qt.NoItemFlags


class NovatechsModel(BoardsModel):
    @property
    def boards(self):
        return self.controller.hardware.novatechs

    def headerData(self, idx, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ['Channel', 'Label'][idx]

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
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                return bool_to_checkstate(channel.enabled)

    def set_board_data(self, index, val, role, board):
        if role == Qt.EditRole:
            if index.column() == 0:
                board.id = val
                return True

    def set_channel_data(self, index, val, role, channel):
        if role == Qt.EditRole:
            if index.column() == 1:
                channel.label = val
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                channel.enabled = bool(val)
        return True

    def create_board(self, idx):
        nova = NovatechBoard('COM{}'.format(idx), self.controller)
        self.controller.hardware.novatechs.append(nova)

    def delete_board(self, idx):
        if self.controller.hardware.novatechs:
            del self.controller.hardware.novatechs[idx]


class ComboDelegate(QItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        scales = ' ' * 10000
        result = DAQmxGetSysScales(scales, 10000)
        scales = result or scales
        scales = scales.strip().split(', ')
        combo.addItem('')
        combo.addItems(scales)
        return combo

    def setEditorData(self, editor, index):
        text = index.data()
        index = editor.findText(text)
        editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.itemText(editor.currentIndex()), role = Qt.EditRole)