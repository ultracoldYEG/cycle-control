try:
    from PyQt4.uic import loadUiType
    from PyQt4 import QtCore
    from PyQt4.QtGui import *
except:
    from PyQt5.uic import loadUiType
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import *
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

        self.programmer = Programmer()

        self.procedure = Procedure()

        self.instructions = self.procedure.instructions
        self.dynamic_vars = self.procedure.dynamic_variables
        self.current_dyn_var = None

        self.updating = False

        #------ Instruction GUI ---------
        self.insert_inst.clicked.connect(self.insert_inst_handler)
        self.remove_inst.clicked.connect(self.remove_inst_handler)

        self.digital_table.itemChanged.connect(self.digital_table_change)
        self.novatech_table.itemChanged.connect(self.novatech_table_change)
        self.analog_table.itemChanged.connect(self.analog_table_change)

        self.digital_table.setAlternatingRowColors(True)
        self.novatech_table.setAlternatingRowColors(True)
        self.analog_table.setAlternatingRowColors(True)

        for i in range(2,self.digital_table.columnCount()):
            self.digital_table.setColumnWidth(i, 35)

        # ------ Process Variables GUI ---------
        self.proc_var0.textEdited.connect(self.update_dynamic_var_name)
        self.var_start0.textEdited.connect(self.update_dynamic_var_start)
        self.var_end0.textEdited.connect(self.update_dynamic_var_end)
        self.var_default0.textEdited.connect(self.update_dynamic_var_default)
        self.log_cb0.stateChanged.connect(self.update_dynamic_var_log)
        self.send_var0_cb.stateChanged.connect(self.update_dynamic_var_send)

        self.listWidget.currentRowChanged.connect(self.select_dyn_var)
        self.new_dyn_var.clicked.connect(self.new_dyn_var_handler)

        # ------ Other GUI ---------
        self.preset_path.textChanged.connect(self.populate_load_presets)
        self.preset_path.setText(os.path.join(ROOT_PATH, "presets\\"))

        self.save_button.clicked.connect(self.save_preset_handler)
        self.load_button.clicked.connect(self.load_preset_handler)

        self.start_device_button.clicked.connect(self.start_device_handler)
        self.stop_device_button.clicked.connect(self.stop_device_handler)
        self.program_device_button.clicked.connect(self.program_device_handler)

    def insert_inst_handler(self):
        if self.updating:
            return
        self.updating = True
        loc = self.clip_inst_number(self.insert_inst_num.value())

        inst = Instruction()
        inst.set_name('n' + str(loc))
        inst.set_duration(np.random.rand())
        inst.set_stepsize(0.01)

        self.instructions.insert(loc, inst)
        self.insert_row(loc)
        self.updating = False

    def remove_inst_handler(self):
        if self.updating:
            return
        self.updating = True
        loc = self.clip_inst_number(self.remove_inst_num.value())

        del self.instructions[loc - 1]

        self.remove_row(loc - 1)
        self.updating = False

    def clip_inst_number(self, num):
        #limits the number between 0 and the number of instructions
        if num < 0 or num > len(self.instructions):
            return len(self.instructions)
        return num

    def analog_table_change(self):
        if self.updating:
            return
        self.updating = True
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
        self.updating = False

    def novatech_table_change(self, item):
        if self.updating:
            return
        self.updating = True
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
        self.updating = False

    def digital_table_change(self, item):
        if self.updating:
            return
        self.updating = True
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
        self.updating = False

    def redraw_all(self):
        self.updating = True
        for i in range(self.digital_table.rowCount()):
            self.remove_row(0)
        for i in range(len(self.instructions)):
            self.insert_row(i)
        self.updating = False

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


    def update_digital(self, r, c):
        c-=2
        digits = self.instructions[r].digital_pins
        if digits[c] == '1':
            self.instructions[r].set_digital_pins(digits[:c] + '0' + digits[c+1:])
        else:
            self.instructions[r].set_digital_pins(digits[:c] + '1' + digits[c+1:])


    def select_dyn_var(self, event):
        self.current_dyn_var = self.dynamic_vars[event]
        self.proc_var0.setText(self.current_dyn_var.name)
        self.var_start0.setText(str(self.current_dyn_var.start))
        self.var_end0.setText(str(self.current_dyn_var.end))
        self.var_default0.setText(str(self.current_dyn_var.default))
        self.log_cb0.setCheckState(bool_to_checkstate(self.current_dyn_var.logarithmic))
        self.send_var0_cb.setCheckState(bool_to_checkstate(self.current_dyn_var.send))

    def new_dyn_var_handler(self):
        num = len(self.dynamic_vars)
        dyn_var = DynamicProcessVariable()
        dyn_var.name = 'dynamic variable '+str(num)
        self.dynamic_vars.append(dyn_var)
        self.listWidget.addItem(QListWidgetItem(dyn_var.name))
        self.listWidget.setCurrentRow(num)

    def add_dyn_var(self, dyn_var):
        num = len(self.dynamic_vars)
        self.dynamic_vars.append(dyn_var)
        self.listWidget.addItem(QListWidgetItem(dyn_var.name))
        self.listWidget.setCurrentRow(num)

    def update_dynamic_var_list_widget(self, name):
        row = self.listWidget.currentRow()
        self.listWidget.insertItem(row, QListWidgetItem(name))
        self.listWidget.setCurrentRow(row)
        self.listWidget.takeItem(row+1)

    def update_dynamic_var_name(self, name):
        self.current_dyn_var.set_name(name)
        self.update_dynamic_var_list_widget(name)

    def update_dynamic_var_start(self, start):
        self.current_dyn_var.set_start(start)

    def update_dynamic_var_end(self, end):
        self.current_dyn_var.set_end(end)

    def update_dynamic_var_default(self, default):
        self.current_dyn_var.set_default(default)

    def update_dynamic_var_log(self, state):
        self.current_dyn_var.set_log(state)

    def update_dynamic_var_send(self, state):
        self.current_dyn_var.set_send(state)



    def save_preset_handler(self):
        with open(str(self.preset_path.text()) + str(self.save_name.text()) + '.txt', 'w+') as f:
            inst_format = '{:>40}; {:>20}; {:>10}; {:>20}; {:>75}; {:>75}\n'
            dynamic_var_format = '{:>40}; {:>20}; {:>20}; {:>20}; {:>15}; {:>6}\n'
            f.write(inst_format.format(
                '===Instructions===       Name',
                'Duration',
                'Stepsize',
                'Digital Pins',
                'Analog Outputs',
                'Novatech Outputs'
            ))
            for i in self.instructions:
                f.write(inst_format.format(
                    i.name,
                    i.duration,
                    i.stepsize,
                    i.digital_pins,
                    ''.join([x + ' ' for x in i.analog_functions]),
                    ''.join([x + ' ' for x in i.novatech_functions])
                ))
            f.write('\n')
            f.write(dynamic_var_format.format(
                '===Dynamic Process Variables===    Name',
                'Start',
                'End',
                'Default',
                'Logarithmic',
                'Send'
            ))
            for i in self.dynamic_vars:
                f.write(dynamic_var_format.format(
                    i.name,
                    i.start,
                    i.end,
                    i.default,
                    int(i.logarithmic),
                    int(i.send)
                ))


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
        parsers = iter([self.parse_inst_line, self.parse_dyn_var_line])
        parser = parsers.next()
        with open(str(self.preset_path.text()) + str(self.load_combo.currentText()), 'r') as f:
            print dir(f)
            self.instructions = []
            self.dynamic_vars = []
            f.next()
            for i in f:
                i = [x.strip() for x in i.split(';')]
                if i == ['']:
                    f.next()
                    parser = parsers.next()
                    continue

                parser(i)
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

        self.add_dyn_var(dyn_var)

    def start_device_handler(self):
        self.programmer.start_device_handler()

    def stop_device_handler(self):
        self.programmer.stop_device_handler()

    def program_device_handler(self):
        self.programmer.program_device_handler(self.instructions)



class TableCheckBox(QWidget):
    def __init__(self, gui, row, col, state, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        cb = QCheckBox()
        cb.setCheckState(bool_to_checkstate(state))
        cb.setStyleSheet("""
            QCheckBox::indicator { width: 23px; height: 20px;} 
            QCheckBox::indicator:checked {background-color: #55FF00;}
            QCheckBox::indicator:checked:hover {background-color: #33DD00;}
            QCheckBox::indicator:unchecked {background-color: #DDDDDD;}
            QCheckBox::indicator:unchecked:hover {background-color: #AAAAAA;}
        """)
        cb.clicked.connect(lambda: gui.update_digital(row,col))
        layout = QHBoxLayout(self)
        layout.addWidget(cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(5, 0, 0, 0)

def bool_to_checkstate(bool):
    if bool:
        return QtCore.Qt.Checked
    return QtCore.Qt.Unchecked


# **************************************************************************************
if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    app1.setStyle('cleanlooks')
    main = Main()
    main.show()
    app1.exec_()
    pb_close()
    sys.exit()