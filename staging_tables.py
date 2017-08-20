from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5 import QtCore
from PyQt5.QtGui import QCursor

from helpers import *

class HardwareTable(QTableWidget):
    def __init__(self, gui):
        super(HardwareTable, self).__init__()
        self.gui = gui
        self.insertColumn(0)
        self.insertColumn(1)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('Duration'))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.data_menu)
        self.cellChanged.connect(self.cell_changed_handler)
        self.fixedColumnNum = 2

    def clear_all(self):
        num = self.fixedColumnNum
        for i in range(self.columnCount()-num):
            self.removeColumn(num)
        for i in range(self.rowCount()):
            self.removeRow(0)

    def redraw_cols(self):
        pass

    def update_inst(self, row, col):
        pass

    def get_channel_by_col(self, col, boards):
        col -= self.fixedColumnNum
        for board in boards:
            for i, channel in enumerate(board.channels):
                if channel.enabled:
                    col -= 1
                if col == -1:
                    return board.board_identifier, i
        return None, None

    def insert_row(self, row):
        pass

    def redraw_row(self, row):
        self.removeRow(row)
        self.insert_row(row)

    def data_menu(self):
        menu = QMenu()
        new_row_pre = menu.addAction("Insert new instruction before")
        new_row_aft = menu.addAction("Insert new instruction after")
        del_row = menu.addAction("Remove instruction")
        selectedItem = menu.exec_(QCursor.pos())
        row = self.currentRow()
        if selectedItem == new_row_pre:
            self.gui.insert_inst_handler(self.gui.clip_inst_number(row))
        if selectedItem == new_row_aft:
            self.gui.insert_inst_handler(self.gui.clip_inst_number(row + 1))
        if selectedItem == del_row:
            self.gui.remove_inst_handler(self.gui.clip_inst_number(row))

    def cell_changed_handler(self, row, col):
        if self.gui.updating.lock:
            return
        with self.gui.updating:
            self.update_inst(row, col)
            self.gui.redraw_inst_row(row)

class AnalogTable(HardwareTable):
    def __init__(self, gui):
        super(AnalogTable, self).__init__(gui)
        self.insertColumn(2)
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Stepsize'))
        self.fixedColumnNum = 3

    def redraw_cols(self):
        self.clear_all()
        n = self.fixedColumnNum
        colors = [QColor(200,200,255), QColor(255,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]
        for i, board in enumerate(self.gui.hardware.ni_boards):
            color = colors[i % 2]
            for channel in board.channels:
                if channel.enabled:
                    self.insertColumn(n)
                    self.setHorizontalHeaderItem(n, QTableWidgetItem(channel.label))
                    self.colors.append(color)
                    n += 1

    def update_inst(self, row, col):
        item = self.item(row, col)
        inst = self.gui.proc_params.instructions[row]

        if item:
            item = item.text()
            if col == 0:
                inst.set_name(item)
            elif col == 1:
                inst.set_duration(item)
            elif col == 2:
                inst.set_stepsize(item)
            elif col > 2:
                id, num = self.get_channel_by_col(col, self.gui.hardware.ni_boards)
                inst.analog_functions.get(id)[num] = str(item)

    def insert_row(self, row):
        self.insertRow(row)
        inst = self.gui.proc_params.instructions[row]
        for col in range((self.columnCount())):
            if col == 0:
                new_string = inst.name
            elif col == 1:
                new_string = inst.duration
            elif col == 2:
                new_string = inst.stepsize
            else:
                id, num = self.get_channel_by_col(col, self.gui.hardware.ni_boards)
                new_string = inst.analog_functions.get(id)[num]

            item = QTableWidgetItem(new_string)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)

class NovatechTable(HardwareTable):
    def __init__(self, gui):
        super(NovatechTable, self).__init__(gui)
        self.insertColumn(2)
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Stepsize'))
        self.fixedColumnNum = 3

    def redraw_cols(self):
        self.clear_all()
        n = self.fixedColumnNum
        colors = [QColor(200,200,255), QColor(255,200,200), QColor(200,255,200), QColor(200,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]
        for i, board in enumerate(self.gui.hardware.novatechs):
            for j, channel in enumerate(board.channels):
                color = colors[j % 4]
                if channel.enabled:
                    for param in ['Amp', 'Freq', 'Phase']:
                        self.insertColumn(n)
                        self.setHorizontalHeaderItem(n, QTableWidgetItem(board.board_identifier + ' '+ str(j) + ' ' + param))
                        self.colors.append(color)
                        n += 1

    def update_inst(self, row, col):
        item = self.item(row, col)
        inst = self.gui.proc_params.instructions[row]

        if item:
            item = item.text()
            if col == 0:
                inst.set_name(item)
            elif col == 1:
                inst.set_duration(item)
            elif col == 2:
                inst.set_stepsize(item)
            elif col > 2:
                col2 = (col - self.fixedColumnNum) / 3 + self.fixedColumnNum
                rem = (col - self.fixedColumnNum) % 3
                id, num = self.get_channel_by_col(col2, self.gui.hardware.novatechs)
                inst.novatech_functions.get(id)[3*num+rem] = str(item)

    def insert_row(self, row):
        self.insertRow(row)
        inst = self.gui.proc_params.instructions[row]
        for col in range((self.columnCount())):
            if col == 0:
                new_string = inst.name
            elif col == 1:
                new_string = inst.duration
            elif col == 2:
                new_string = inst.stepsize
            else:
                col2 = (col - self.fixedColumnNum) / 3 + self.fixedColumnNum
                rem = (col - self.fixedColumnNum) % 3
                id, num = self.get_channel_by_col(col2, self.gui.hardware.novatechs)
                new_string = inst.novatech_functions.get(id)[3*num + rem]

            item = QTableWidgetItem(new_string)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)

class DigitalTable(HardwareTable):
    def __init__(self, gui):
        super(DigitalTable, self).__init__(gui)

    def redraw_cols(self):
        self.clear_all()
        n = self.fixedColumnNum
        colors = [QColor(200,200,255), QColor(255,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255)]
        for i, board in enumerate(self.gui.hardware.pulseblasters):
            color = colors[i % 2]
            for j, channel in enumerate(board.channels):
                if channel.enabled:
                    self.insertColumn(n)
                    self.setHorizontalHeaderItem(n, QTableWidgetItem(str(j)))
                    self.setColumnWidth(n, 25)
                    self.colors.append(color)
                    n += 1

    def update_inst(self, row, col):
        item = self.item(row, col)
        inst = self.gui.proc_params.instructions[row]

        if item:
            item = item.text()
            if col == 0:
                inst.set_name(item)
            elif col == 1:
                inst.set_duration(item)
            self.redraw_row(row)

    def insert_row(self, row):
        self.insertRow(row)
        inst = self.gui.proc_params.instructions[row]

        for col in range(self.columnCount()):
            if col == 0:
                self.setItem(row, col, QTableWidgetItem(inst.name))

            elif col == 1:
                self.setItem(row, col, QTableWidgetItem(str(inst.duration)))

            else:
                id, num = self.get_channel_by_col(col, self.gui.hardware.pulseblasters)
                state = bool(int(inst.digital_pins.get(id)[num]))
                self.setCellWidget(row, col, TableCheckBox(self, row, col, state))
            self.setRowHeight(row, 25)
        self.update_cb_rows()

    def update_cb_rows(self):
        for col in range(self.fixedColumnNum, self.columnCount()):
            for row in range(self.rowCount()):
                self.cellWidget(row, col).row = row

    def update_digital(self, row, col):
        inst = self.gui.proc_params.instructions[row]
        id, num = self.get_channel_by_col(col, self.gui.hardware.pulseblasters)
        digits = inst.digital_pins.get(id)
        if digits[num] == '1':
            inst.digital_pins.update([(id, digits[:num] + '0' + digits[num + 1:])])
        else:
            inst.digital_pins.update([(id, digits[:num] + '1' + digits[num + 1:])])


class TableCheckBox(QWidget):
    def __init__(self, table, row, col, state):
        QWidget.__init__(self)
        self.table = table
        self.row = row
        self.col = col
        cb = QCheckBox()
        cb.setCheckState(bool_to_checkstate(state))
        if (col - 2) % 8 < 4:
            cb.setStyleSheet(load_stylesheet('digital_cb_light.qss'))
        else:
            cb.setStyleSheet(load_stylesheet('digital_cb_dark.qss'))
        cb.clicked.connect(self.update_instruction)
        layout = QHBoxLayout(self)
        layout.addWidget(cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(2, 0, 0, 0)

    def update_instruction(self):
        self.table.update_digital(self.row, self.col)

