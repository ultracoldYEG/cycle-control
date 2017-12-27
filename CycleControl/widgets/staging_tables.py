from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QCursor
from PyQt5 import QtCore

from CycleControl.helpers import *

class HardwareTable(QTableWidget):
    def __init__(self, controller, gui):
        super(HardwareTable, self).__init__()
        self.gui = gui
        self.controller = controller
        self.insertColumn(0)
        self.insertColumn(1)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('Duration'))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.data_menu)
        self.cellChanged.connect(self.cell_changed_handler)
        self.fixedColumnNum = 2
        self.colors = []

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
                    return board, i
        return None, None

    def insert_row(self, row):
        pass

    def redraw_row(self, row):
        self.removeRow(row)
        self.insert_row(row)

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
        if len(self.selectedIndexes()) > 1:
            set_to = menu.addAction("Set cells to...")
        selectedItem = menu.exec_(QCursor.pos())
        row = self.currentRow()
        if selectedItem == new_row_pre:
            self.gui.insert_inst_handler(self.gui.clip_inst_number(row))
        elif selectedItem == new_row_aft:
            self.gui.insert_inst_handler(self.gui.clip_inst_number(row + 1))
        elif selectedItem == copy_row:
            self.gui.copy_inst_handler(self.gui.clip_inst_number(row))
        elif selectedItem == paste_row_pre:
            self.gui.paste_inst_handler(self.gui.clip_inst_number(row))
        elif selectedItem == paste_row_aft:
            self.gui.paste_inst_handler(self.gui.clip_inst_number(row + 1))
        elif selectedItem == del_row:
            self.gui.remove_inst_handler(self.gui.clip_inst_number(row))
        elif len(self.selectedIndexes()) > 1 and selectedItem == set_to:
            dialog = SetToWindow()
            dialog.exec_()
            if not dialog.cancelled:
                self.set_cells_to_handler(dialog.result)

    def cell_changed_handler(self, row, col):
        if self.gui.updating.lock:
            return
        with self.gui.updating:
            self.update_inst(row, col)
            self.gui.redraw_inst_row(row)


class AnalogTable(HardwareTable):
    def __init__(self, controller, gui):
        super(AnalogTable, self).__init__(controller, gui)
        self.insertColumn(2)
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Stepsize'))
        self.fixedColumnNum = 3
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]

    def redraw_cols(self):
        self.clear_all()
        n = self.fixedColumnNum
        colors = [QColor(200,200,255), QColor(255,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]
        for i, board in enumerate(self.controller.hardware.ni_boards):
            color = colors[i % 2]
            for channel in board.channels:
                if channel.enabled:
                    self.insertColumn(n)
                    self.setHorizontalHeaderItem(n, QTableWidgetItem(channel.label))
                    self.colors.append(color)
                    n += 1

    def update_inst(self, row, col):
        item = self.item(row, col)
        inst = self.controller.proc_params.instructions[row]

        if item:
            item = item.text()
            if col == 0:
                inst.name = item
            elif col == 1:
                inst.duration = item
            elif col == 2:
                inst.stepsize = item
            elif col > 2:
                board, num = self.get_channel_by_col(col, self.controller.hardware.ni_boards)
                id = board.id

                if self.is_valid_input(item, col):
                    inst.analog_functions.get(id)[num] = str(item)
                else:
                    message = 'Bad input at: ('+str(row)+', '+str(col)+').'
                    dialog = WarningWindow(message)
                    dialog.exec_()
                    print message

    def is_valid_input(self, item, col):
        board, num = self.get_channel_by_col(col, self.controller.hardware.ni_boards)
        channel = board.channels[num]
        lims = (channel.min, channel.max)
        try:
            val = float(item)
            if val < lims[0] or val > lims[1]:
                return False
            return True
        except:
            pass
        for stat_var in self.controller.proc_params.static_variables:
            if stat_var.name == item:
                val = float(stat_var.default)
                if val < lims[0] or val > lims[1]:
                    return False
        for dyn_var in self.controller.proc_params.dynamic_variables:
            if dyn_var.name == item:
                edge_cases = [float(dyn_var.start), float(dyn_var.end), float(dyn_var.default)]
                if any([val < lims[0] or val > lims[1] for val in edge_cases]):
                    return False
        return True

    def insert_row(self, row):
        self.insertRow(row)
        inst = self.controller.proc_params.instructions[row]
        for col in range((self.columnCount())):
            if col == 0:
                new_string = inst.name
            elif col == 1:
                new_string = str(inst.duration)
            elif col == 2:
                new_string = str(inst.stepsize)
            else:
                board, num = self.get_channel_by_col(col, self.controller.hardware.ni_boards)
                id = board.id
                new_string = inst.analog_functions.get(id)[num]

            item = QTableWidgetItem(new_string)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)

    def set_cells_to_handler(self, val):
        for index in self.selectedIndexes():
            row = index.row()
            col = index.column()
            item = QTableWidgetItem(val)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)


class NovatechTable(HardwareTable):
    def __init__(self, controller, gui):
        super(NovatechTable, self).__init__(controller, gui)
        self.insertColumn(2)
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Stepsize'))
        self.fixedColumnNum = 3
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]

    def redraw_cols(self):
        self.clear_all()
        n = self.fixedColumnNum
        colors = [QColor(200,200,255), QColor(255,200,200), QColor(200,255,200), QColor(200,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]
        for i, board in enumerate(self.controller.hardware.novatechs):
            for j, channel in enumerate(board.channels):
                color = colors[j % 4]
                if channel.enabled:
                    for param in ['Amp', 'Freq', 'Phase']:
                        self.insertColumn(n)
                        self.setHorizontalHeaderItem(n, QTableWidgetItem(board.id + ' '+ str(j) + ' ' + param))
                        self.colors.append(color)
                        n += 1

    def update_inst(self, row, col):
        item = self.item(row, col)
        inst = self.controller.proc_params.instructions[row]

        if item:
            item = item.text()
            if col == 0:
                inst.name = item
            elif col == 1:
                inst.duration = item
            elif col == 2:
                inst.stepsize = item
            elif col > 2:
                col2 = (col - self.fixedColumnNum) / 3 + self.fixedColumnNum
                rem = (col - self.fixedColumnNum) % 3
                board, num = self.get_channel_by_col(col2, self.controller.hardware.novatechs)
                id = board.id
                inst.novatech_functions.get(id)[3*num+rem] = str(item)

    def insert_row(self, row):
        self.insertRow(row)
        inst = self.controller.proc_params.instructions[row]
        for col in range((self.columnCount())):
            if col == 0:
                new_string = inst.name
            elif col == 1:
                new_string = str(inst.duration)
            elif col == 2:
                new_string = str(inst.stepsize)
            else:
                col2 = (col - self.fixedColumnNum) / 3 + self.fixedColumnNum
                rem = (col - self.fixedColumnNum) % 3
                board, num = self.get_channel_by_col(col2, self.controller.hardware.novatechs)
                id = board.id
                new_string = inst.novatech_functions.get(id)[3*num + rem]

            item = QTableWidgetItem(new_string)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)

    def set_cells_to_handler(self, val):
        for index in self.selectedIndexes():
            row = index.row()
            col = index.column()
            item = QTableWidgetItem(val)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)


class DigitalTable(HardwareTable):
    def __init__(self, controller, gui):
        super(DigitalTable, self).__init__(controller, gui)
        self.colors = [QColor(255,255,255), QColor(255,255,255)]

    def redraw_cols(self):
        self.clear_all()
        n = self.fixedColumnNum
        colors = [QColor(200,200,255), QColor(255,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255)]
        header = self.horizontalHeader()
        for i, board in enumerate(self.controller.hardware.pulseblasters):
            color = colors[i % 2]
            for j, channel in enumerate(board.channels):
                if channel.enabled:
                    self.insertColumn(n)
                    self.setHorizontalHeaderItem(n, QTableWidgetItem(str(j)))
                    self.setColumnWidth(n, 25)
                    header.setSectionResizeMode(n, QHeaderView.Fixed)
                    self.colors.append(color)
                    n += 1

    def update_inst(self, row, col):
        item = self.item(row, col)
        inst = self.controller.proc_params.instructions[row]

        if item:
            item = item.text()
            if col == 0:
                inst.name = item
            elif col == 1:
                inst.duration = item
            self.redraw_row(row)

    def insert_row(self, row):
        self.insertRow(row)
        inst = self.controller.proc_params.instructions[row]

        for col in range(self.columnCount()):
            if col == 0:
                self.setItem(row, col, QTableWidgetItem(inst.name))

            elif col == 1:
                self.setItem(row, col, QTableWidgetItem(str(inst.duration)))

            else:
                board, num = self.get_channel_by_col(col, self.controller.hardware.pulseblasters)
                id = board.id
                state = bool(int(inst.digital_pins.get(id)[num]))
                self.setCellWidget(row, col, TableCheckBox(self, row, col, state))
            self.setRowHeight(row, 25)
        self.update_cb_rows()

    def update_cb_rows(self):
        for col in range(self.fixedColumnNum, self.columnCount()):
            for row in range(self.rowCount()):
                self.cellWidget(row, col).row = row

    def update_digital(self, row, col, state):
        inst = self.controller.proc_params.instructions[row]
        board, num = self.get_channel_by_col(col, self.controller.hardware.pulseblasters)
        id = board.id
        digits = inst.digital_pins.get(id)
        if state:
            inst.digital_pins.update([(id, digits[:num] + '1' + digits[num + 1:])])
        else:
            inst.digital_pins.update([(id, digits[:num] + '0' + digits[num + 1:])])

    def set_cells_to_handler(self, val):
        for index in self.selectedIndexes():
            row = index.row()
            col = index.column()
            if col <= 1:
                item = QTableWidgetItem(val)
                item.setBackground(self.colors[col])
                self.setItem(row, col, item)
                self.setRowHeight(row, 25)
            else:
                state = val.lower() not in ['', '0', 'off', 'none', 'null', 'nan', 'undef', 'undefined']
                widget = self.cellWidget(row, col)
                widget.cb.setCheckState(bool_to_checkstate(state))
                self.update_digital(row, col, state)


class TableCheckBox(QWidget):
    def __init__(self, table, row, col, state):
        QWidget.__init__(self)
        self.table = table
        self.row = row
        self.col = col
        self.cb = QCheckBox()
        self.cb.setCheckState(bool_to_checkstate(state))
        if (col - 2) % 8 < 4:
            self.cb.setStyleSheet(load_stylesheet('digital_cb_light.qss'))
        else:
            self.cb.setStyleSheet(load_stylesheet('digital_cb_dark.qss'))
        self.cb.clicked.connect(self.update_instruction)
        layout = QHBoxLayout(self)
        layout.addWidget(self.cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(2, 0, 0, 0)

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
