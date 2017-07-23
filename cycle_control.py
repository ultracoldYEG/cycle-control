try:
    from PyQt4.uic import loadUiType
    from PyQt4 import QtCore
    from PyQt4.QtGui import *
except:
    from PyQt5.uic import loadUiType
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import QCursor
import sys
import os

from programmer import *
from instruction import *

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'cycle_control.ui'))

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)

        self.updating = UpdateLock(False)

        self.programmer = Programmer()

        self.procedure = Procedure(self.programmer)

        self.instructions = self.procedure.instructions
        self.dynamic_vars = self.procedure.dynamic_variables
        self.static_vars = self.procedure.static_variables

        #------ Instruction GUI ---------
        for table in [self.digital_table, self.analog_table, self.novatech_table]:
            table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.digital_table.customContextMenuRequested.connect(lambda event: self.dataTableMenu(self.digital_table))
        self.analog_table.customContextMenuRequested.connect(lambda event: self.dataTableMenu(self.analog_table))
        self.novatech_table.customContextMenuRequested.connect(lambda event: self.dataTableMenu(self.novatech_table))

        self.digital_table.itemChanged.connect(self.digital_table_change)
        self.novatech_table.itemChanged.connect(self.novatech_table_change)
        self.analog_table.itemChanged.connect(self.analog_table_change)

        for i in range(2,self.digital_table.columnCount()):
            self.digital_table.setColumnWidth(i, 25)

        # ------ Process Variables GUI ---------
        self.dyn_var_name.textEdited.connect(self.update_dynamic_var_name)
        self.dyn_var_start.editingFinished.connect(self.update_dynamic_var_start)
        self.dyn_var_end.editingFinished.connect(self.update_dynamic_var_end)
        self.dyn_var_default.editingFinished.connect(self.update_dynamic_var_default)
        self.dyn_var_log.stateChanged.connect(self.update_dynamic_var_log)
        self.dyn_var_send.stateChanged.connect(self.update_dynamic_var_send)

        self.dyn_var_list.currentRowChanged.connect(self.select_dyn_var)
        self.new_dyn_var.clicked.connect(self.new_dyn_var_handler)
        self.delete_dyn_var.clicked.connect(self.remove_current_dyn_var)

        self.stat_var_table.itemChanged.connect(self.stat_var_table_change)
        self.new_stat_var.clicked.connect(self.new_stat_var_handler)
        self.delete_stat_var.clicked.connect(self.remove_current_stat_var)

        # ------ Other GUI ---------
        self.preset_path.textChanged.connect(self.populate_load_presets)
        self.preset_path.setText(os.path.join(ROOT_PATH, "presets\\"))

        self.save_button.clicked.connect(self.save_preset_handler)
        self.load_button.clicked.connect(self.load_preset_handler)

        self.start_device_button.clicked.connect(self.start_device_handler)
        self.stop_device_button.clicked.connect(self.stop_device_handler)
        self.program_device_button.clicked.connect(self.program_device_handler)

    def dataTableMenu(self, table):
        menu = QMenu()
        new_row_pre = menu.addAction("Insert new instruction before")
        new_row_aft = menu.addAction("Insert new instruction after")
        del_row = menu.addAction("Remove instruction")
        selectedItem = menu.exec_(QCursor.pos())
        row = table.currentRow()
        if selectedItem == new_row_pre:
            self.insert_inst_handler(self.clip_inst_number(row))
        if selectedItem == new_row_aft:
            self.insert_inst_handler(self.clip_inst_number(row+1))
        if selectedItem == del_row:
            self.remove_inst_handler(self.clip_inst_number(row))

    def insert_inst_handler(self, loc):
        if self.updating.lock:
            return
        with self.updating:
            inst = Instruction()
            inst.set_name('Instruction ' + str(loc+1))

            self.instructions.insert(loc, inst)
            self.insert_row(loc)

    def remove_inst_handler(self, loc):
        if self.updating.lock or not self.instructions:
            return
        with self.updating:
            del self.instructions[loc]
            self.remove_row(loc)

    def clip_inst_number(self, num):
        #limits the number between 0 and the number of instructions
        if num < 0 or num >= len(self.instructions):
            return len(self.instructions)
        return num

    def analog_table_change(self):
        if self.updating.lock:
            return
        with self.updating:
            row = self.analog_table.currentRow()
            col = self.analog_table.currentColumn()
            item = self.analog_table.item(row, col)
            inst = self.instructions[row]

            if item:
                item = item.text()
                if col == 0:
                    inst.set_name(item)
                elif col == 1:
                    inst.set_duration(item)
                elif col == 2:
                    inst.set_stepsize(item)
                elif col > 2:
                    inst.analog_functions[col - 3] = str(item)
                self.redraw_row(row)

    def novatech_table_change(self, item):
        if self.updating.lock:
            return
        with self.updating:
            row = self.novatech_table.currentRow()
            col = self.novatech_table.currentColumn()
            inst = self.instructions[row]

            if item:
                item = item.text()
                if col == 0:
                    inst.set_name(item)
                elif col == 1:
                    inst.set_duration(item)
                elif col == 2:
                    inst.set_stepsize(item)
                elif col > 2:
                    inst.novatech_functions[col - 3] = str(item)

                self.redraw_row(row)

    def digital_table_change(self, item):
        if self.updating.lock:
            return
        with self.updating:
            row = self.digital_table.currentRow()
            col = self.digital_table.currentColumn()
            inst = self.instructions[row]

            if item:
                item=item.text()
                if col == 0:
                    inst.set_name(item)
                elif col == 1:
                    inst.set_duration(item)
                self.redraw_row(row)

    def redraw_all(self):
        self.redraw_all_inst()
        self.redraw_all_dyn_var()
        self.redraw_all_stat_var()

    def redraw_all_inst(self):
        with self.updating:
            for i in range(self.digital_table.rowCount()):
                self.remove_row(0)
            for i in range(len(self.instructions)):
                self.insert_row(i)

    def redraw_row(self, row):
        self.remove_row(row)
        self.insert_row(row)

    def insert_row(self,row):
        self.insert_digital_grid_row(row)
        self.insert_analog_table_row(row)
        self.insert_novatech_table_row(row)

    def remove_row(self,row):
        self.digital_table.removeRow(row)
        self.analog_table.removeRow(row)
        self.novatech_table.removeRow(row)

    def insert_analog_table_row(self, row):
        self.analog_table.insertRow(row)
        for col in range((self.analog_table.columnCount())):
            if col == 0:
                new_string = self.instructions[row].name

            elif col == 1:
                new_string = str(self.instructions[row].duration)

            elif col == 2:
                new_string = str(self.instructions[row].stepsize)

            else:
                new_string = str(self.instructions[row].analog_functions[col - 3])

            self.analog_table.setItem(row, col, QTableWidgetItem(new_string))
            self.analog_table.setRowHeight(row, 25)

    def insert_novatech_table_row(self, row):
        self.novatech_table.insertRow(row)
        for col in range((self.novatech_table.columnCount())):
            if col == 0:
                new_string = self.instructions[row].name

            elif col == 1:
                new_string = str(self.instructions[row].duration)

            elif col == 2:
                new_string = str(self.instructions[row].stepsize)

            else:
                new_string = str(self.instructions[row].novatech_functions[col - 3])

            self.novatech_table.setItem(row, col, QTableWidgetItem(new_string))
            self.novatech_table.setRowHeight(row, 25)

    def insert_digital_grid_row(self, row):
        inst = self.instructions[row]
        self.digital_table.insertRow(row)

        for col in range(self.digital_table.columnCount()):
            if col == 0:
                self.digital_table.setItem(row, col, QTableWidgetItem(inst.name))

            elif col == 1:
                self.digital_table.setItem(row, col, QTableWidgetItem(str(inst.duration)))

            else:
                state = bool(int(inst.digital_pins[col-2]))
                self.digital_table.setCellWidget(row, col, TableCheckBox(self, row, col, state))
            self.digital_table.setRowHeight(row, 25)

    def update_digital(self, r, c):
        c-=2
        digits = self.instructions[r].digital_pins
        if digits[c] == '1':
            self.instructions[r].set_digital_pins(digits[:c] + '0' + digits[c+1:])
        else:
            self.instructions[r].set_digital_pins(digits[:c] + '1' + digits[c+1:])

    def new_stat_var_handler(self):
        if self.updating.lock:
            return
        with self.updating:
            num = len(self.static_vars)
            stat_var = StaticProcessVariable()
            stat_var.name = 'static variable '+str(num)
            self.static_vars.append(stat_var)
            self.insert_stat_var_row(num)

    def remove_current_stat_var(self):
        if self.static_vars:
            row = self.stat_var_table.currentRow()
            del self.static_vars[row]
            self.redraw_all_stat_var()

    def stat_var_table_change(self, item):
        if self.updating.lock or not item:
            return
        with self.updating:
            row = self.stat_var_table.currentRow()
            col = self.stat_var_table.currentColumn()
            stat_var = self.static_vars[row]

            if col == 0:
                stat_var.set_name(item.text())
            elif col == 1:
                stat_var.set_default(item.text())
            self.redraw_stat_var_row(row)

    def redraw_all_stat_var(self):
        for i in range(self.stat_var_table.rowCount()):
            self.stat_var_table.removeRow(0)
        for i in range(len(self.static_vars)):
            self.insert_stat_var_row(i)

    def redraw_stat_var_row(self, row):
        self.stat_var_table.removeRow(row)
        self.insert_stat_var_row(row)

    def insert_stat_var_row(self, row):
        stat_var = self.static_vars[row]
        self.stat_var_table.insertRow(row)
        self.stat_var_table.setItem(row, 0, QTableWidgetItem(stat_var.name))
        self.stat_var_table.setItem(row, 1, QTableWidgetItem(str(stat_var.default)))

    def remove_stat_var_row(self, row):
        self.stat_var_table.removeRow(row)

    def select_dyn_var(self, row):
        if self.dynamic_vars:
            self.current_dyn_var = self.dynamic_vars[row]
            self.dyn_var_name.setText(self.current_dyn_var.name)
            self.dyn_var_start.setText(str(self.current_dyn_var.start))
            self.dyn_var_end.setText(str(self.current_dyn_var.end))
            self.dyn_var_default.setText(str(self.current_dyn_var.default))
            self.dyn_var_log.setCheckState(bool_to_checkstate(self.current_dyn_var.logarithmic))
            self.dyn_var_send.setCheckState(bool_to_checkstate(self.current_dyn_var.send))

    def new_dyn_var_handler(self):
        num = len(self.dynamic_vars)
        dyn_var = DynamicProcessVariable()
        dyn_var.name = 'dynamic variable '+str(num)
        self.dynamic_vars.append(dyn_var)
        self.insert_dyn_var(num)

    def redraw_all_dyn_var(self):
        for i in range(self.dyn_var_list.count()):
            self.dyn_var_list.takeItem(0)
        for i in range(len(self.dynamic_vars)):
            self.insert_dyn_var(i)

    def redraw_dyn_var_row(self, row):
        self.insert_dyn_var(row)
        self.dyn_var_list.takeItem(row + 1)

    def insert_dyn_var(self, row):
        dyn_var = self.dynamic_vars[row]
        self.dyn_var_list.insertItem(row, QListWidgetItem(dyn_var.name))
        self.dyn_var_list.setCurrentRow(row)

    def remove_current_dyn_var(self):
        if self.dynamic_vars:
            row = self.dyn_var_list.currentRow()
            del self.dynamic_vars[row]
            self.redraw_all_dyn_var()
            self.dyn_var_list.setCurrentRow(row)

    def update_dynamic_var_name(self, name):
        self.current_dyn_var.set_name(name)
        self.redraw_dyn_var_row(self.dyn_var_list.currentRow())

    def update_dynamic_var_start(self):
        self.current_dyn_var.set_start(str(self.dyn_var_start.text()))
        self.dyn_var_start.setText(self.current_dyn_var.start)

    def update_dynamic_var_end(self):
        self.current_dyn_var.set_end(str(self.dyn_var_end.text()))
        self.dyn_var_end.setText(self.current_dyn_var.end)

    def update_dynamic_var_default(self):
        self.current_dyn_var.set_default(str(self.dyn_var_default.text()))
        self.dyn_var_default.setText(self.current_dyn_var.default)

    def update_dynamic_var_log(self, state):
        self.current_dyn_var.set_log(state)

    def update_dynamic_var_send(self, state):
        self.current_dyn_var.set_send(state)

    def save_preset_handler(self):
        with open(str(self.preset_path.text()) + str(self.save_name.text()) + '.txt', 'w+') as f:
            f.write(self.procedure.get_save_info())

    def populate_load_presets(self):
        # remove items currently in the dropdown list
        for i in range(self.load_combo.count()):
            self.load_combo.removeItem(0)

        # repopulate the dropdown list if there are any presets
        try:
            for i in os.listdir(str(self.preset_path.text())):
                self.load_combo.addItem(i)
        except:
            print('failed to load presets')

    def load_preset_handler(self):
        parsers = iter([self.parse_inst_line, self.parse_dyn_var_line, self.parse_stat_var_line])
        parser = parsers.next()
        with open(str(self.preset_path.text()) + str(self.load_combo.currentText()), 'r') as f:
            self.procedure = Procedure(self.programmer)
            self.instructions = self.procedure.instructions
            self.dynamic_vars = self.procedure.dynamic_variables
            self.static_vars = self.procedure.static_variables
            f.next()
            for line in f:
                line = [x.strip() for x in line.split(';')]
                if line == ['']:
                    f.next()
                    parser = parsers.next()
                    continue

                parser(line)
            self.redraw_all()

    def parse_inst_line(self, line):
        inst = Instruction()

        inst.set_name(line[0])
        inst.set_duration(line[1])
        inst.set_stepsize(line[2])
        inst.set_digital_pins(line[3])
        inst.analog_functions = line[4].split(' ')
        inst.novatech_functions = line[5].split(' ')

        self.instructions.append(inst)

    def parse_dyn_var_line(self, line):
        dyn_var = DynamicProcessVariable()

        dyn_var.set_name(line[0])
        dyn_var.set_start(line[1])
        dyn_var.set_end(line[2])
        dyn_var.set_default(line[3])
        dyn_var.set_log(line[4])
        dyn_var.set_send(line[5])

        self.dynamic_vars.append(dyn_var)

    def parse_stat_var_line(self, line):
        stat_var = StaticProcessVariable()

        stat_var.set_name(line[0])
        stat_var.set_default(line[1])

        self.static_vars.append(stat_var)

    def start_device_handler(self):
        self.procedure.start_sequence()

    def stop_device_handler(self):
        self.programmer.stop_device_handler()

    def program_device_handler(self):
        self.programmer.program_device_handler(self.instructions)

class UpdateLock(object):
    def __init__(self, lock):
        self.lock = lock

    def __enter__(self):
        self.lock = True

    def __exit__(self, *args):
        self.lock = False


class TableCheckBox(QWidget):
    def __init__(self, gui, row, col, state, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        cb = QCheckBox()
        cb.setCheckState(bool_to_checkstate(state))
        if (col - 2) % 8 < 4:
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 20px; height: 20px;} 
                QCheckBox::indicator:checked {background-color: #55FF00;}
                QCheckBox::indicator:checked:hover {background-color: #BBFF00;}
                QCheckBox::indicator:unchecked {background-color: #DDDDDD;}
                QCheckBox::indicator:unchecked:hover {background-color: #AAAAAA;}
            """)
        else:
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 20px; height: 20px;} 
                QCheckBox::indicator:checked {background-color: #33DD00;}
                QCheckBox::indicator:checked:hover {background-color: #AAFF00;}
                QCheckBox::indicator:unchecked {background-color: #CCCCCC;}
                QCheckBox::indicator:unchecked:hover {background-color: #999999;}
            """)
        cb.clicked.connect(lambda: gui.update_digital(row, col))
        layout = QHBoxLayout(self)
        layout.addWidget(cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(2, 0, 0, 0)

def bool_to_checkstate(bool):
    if bool:
        return QtCore.Qt.Checked
    return QtCore.Qt.Unchecked


# **************************************************************************************
if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    main = Main()
    main.show()
    app1.exec_()
    pb_close()
    sys.exit()