from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QCursor
from PyQt5 import QtCore

from CycleControl.helpers import *

from PyQt5 import QtGui
from PyQt5 import QtWidgets

s = QtWidgets.QVB

class StagingTableView(QTableView):
    def __init__(self, controller, parent=None):
        super(StagingTableView, self).__init__(parent)
        self.controller = controller
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.data_menu)

    def data_menu(self):
        menu = QMenu()

        new_row_pre = menu.addAction("New instruction before")
        new_row_aft = menu.addAction("New instruction after")

        copy_row = menu.addAction("Copy instruction")

        paste_row_pre = menu.addAction("Paste new instruction before")
        paste_row_aft = menu.addAction("Paste new instruction after")

        del_row = menu.addAction("Remove instruction")

        if not self.controller.clipboard:
            paste_row_pre.setEnabled(False)
            paste_row_aft.setEnabled(False)

        set_to = None
        if len(self.selectionModel().selectedIndexes()) > 1:
            set_to = menu.addAction("Set cells to...")

        selectedItem = menu.exec_(QCursor.pos())

        row = self.selectionModel().currentIndex().row()
        model = self.model().sourceModel()
        if selectedItem is None:
            return
        elif selectedItem == new_row_pre:
            model.insert_new_instruction(row)
        elif selectedItem == new_row_aft:
            model.insert_new_instruction(row + 1)
        elif selectedItem == copy_row:
            model.copy_instruction(row)
        elif selectedItem == paste_row_pre:
            model.paste_instruction(row)
        elif selectedItem == paste_row_aft:
            model.paste_instruction(row + 1)
        elif selectedItem == del_row:
            model.remove_instruction(row)
        elif selectedItem == set_to:
            dialog = SetToWindow()
            dialog.exec_()
            if not dialog.cancelled:
                self.set_cells_to_handler(dialog.result)


class DigitalTableView(StagingTableView):
    def __int__(self, controller, parent = None):
        StagingTableView.__init__(self, controller, parent)
        self.delegate = CheckBoxDelegate(self)
        self.setItemDelegateForColumn(3, self.delegate)

    def columnWidth(self, p_int):
        if p_int > 2:
            return 50

# class TableCheckBox(QWidget):
#     def __init__(self, table, row, col, state):
#         QWidget.__init__(self)
#         self.table = table
#         self.row = row
#         self.col = col
#         self.cb = QCheckBox()
#         self.cb.setCheckState(bool_to_checkstate(state))
#         if (col - 2) % 8 < 4:
#             self.cb.setStyleSheet(load_stylesheet('digital_cb_light.qss'))
#         else:
#             self.cb.setStyleSheet(load_stylesheet('digital_cb_dark.qss'))
#         self.cb.clicked.connect(self.update_instruction)
#         layout = QHBoxLayout(self)
#         layout.addWidget(self.cb)
#         layout.setAlignment(QtCore.Qt.AlignCenter)
#         layout.setContentsMargins(2, 0, 0, 0)
#
#     def update_instruction(self):
#         self.table.update_digital(self.row, self.col, self.cb.isChecked())

class CheckBoxDelegate(QItemDelegate):
    def __init__(self, parent = None):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        print 'RAN'
        cb = QCheckBox()
        if (index.col() - 2) % 8 < 4:
            cb.setStyleSheet(load_stylesheet('digital_cb_light.qss'))
        else:
            cb.setStyleSheet(load_stylesheet('digital_cb_dark.qss'))
        # self.cb.clicked.connect(self.update_instruction)
        # layout = QHBoxLayout(self)
        # layout.addWidget(self.cb)
        # layout.setAlignment(QtCore.Qt.AlignCenter)
        # layout.setContentsMargins(2, 0, 0, 0)
        return cb

    def paint(self, painter, option, index):
        QItemDelegate.paint(self, painter, option, index)

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole).toString()
        num = self.items.index(value)
        editor.setCurrentIndex(num)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, QtCore.Qt.DisplayRole, QtCore.QVariant(value))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def update_instruction(self):
        self.table.update_digital(self.row, self.col, self.cb.isChecked())


class SetToWindow(QDialog):
    def __init__(self):
        super(SetToWindow, self).__init__()
        self.cancelled = True
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.setWindowTitle('Set Selected Cells To')

        self.val = QLineEdit()
        yes_btn = QPushButton('Yes')
        no_btn = QPushButton('Cancel')

        yes_btn.clicked.connect(self.confirm)
        no_btn.clicked.connect(self.cancel)

        self.layout.addWidget(self.val)
        self.layout.addWidget(yes_btn)
        self.layout.addWidget(no_btn)

    def confirm(self):
        self.cancelled = False
        self.result = str(self.val.text())
        self.done(0)

    def cancel(self):
        self.done(0)


class WarningWindow(QDialog):
    def __init__(self, msg = 'An error occured.'):
        super(WarningWindow, self).__init__()
        self.cancelled = True
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.setWindowTitle('Warning')

        message = QLabel(msg)
        btn = QPushButton('OK')

        btn.clicked.connect(self.close)

        self.layout.addWidget(message)
        self.layout.addWidget(btn)

    def close(self):
        self.done(0)
