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

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'signal_controller.ui'))

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)

        self.programmer = Programmer()

        self.instructions = []
        self.updating = False

        self.insert_inst.clicked.connect(self.insert_inst_handler)
        self.remove_inst.clicked.connect(self.remove_inst_handler)

        self.start_device_button.clicked.connect(self.start_device_handler)
        self.stop_device_button.clicked.connect(self.stop_device_handler)
        self.program_device_button.clicked.connect(self.program_device_handler)

        self.digital_table.itemChanged.connect(self.digital_table_change)
        self.novatech_table.itemChanged.connect(self.novatech_table_change)
        self.analog_table.itemChanged.connect(self.analog_table_change)

        self.preset_path.textChanged.connect(self.populate_load_presets)
        self.preset_path.setText(os.path.join(ROOT_PATH, "presets\\"))

        self.save_button.clicked.connect(self.save_preset_handler)
        self.load_button.clicked.connect(self.load_preset_handler)

        header = self.digital_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2,self.digital_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
            self.digital_table.setColumnWidth(i, 35)

    def insert_inst_handler(self):
        insert_location = self.clip_inst_number(self.insert_inst_num.value())

        self.instructions.insert(insert_location, Instruction())

        self.instructions[insert_location].set_name('n' + str(insert_location))
        self.instructions[insert_location].set_duration(np.random.rand())
        self.instructions[insert_location].set_stepsize(0.01)

        self.insert_digital_grid_row(insert_location)
        self.insert_analog_table_row(insert_location)
        self.insert_novatech_table_row(insert_location)

    def remove_inst_handler(self):
        remove_location = self.clip_inst_number(self.remove_inst_num.value())

        del self.instructions[remove_location - 1]

        self.digital_table.removeRow(remove_location - 1)
        self.novatech_table.removeRow(remove_location - 1)
        self.analog_table.removeRow(remove_location - 1)

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


    def save_preset_handler(self):
        with open(str(self.preset_path.text()) + str(self.save_name.text()) + '.txt', 'w+') as f:
            f.write('{:>10}; {:>20}; {:>10}; {:>20}; {:>75}; {:>75}\n'.format(
                'Name',
                'Duration',
                'Stepsize',
                'Digital Pins',
                'Analog Outputs',
                'Novatech Outputs'
            ))
            for i in self.instructions:
                f.write('{:>10}; {:20.6f}; {:10.6f}; {:>20}; {:>75}; {:>75}\n'.format(
                    i.name,
                    i.duration,
                    i.stepsize,
                    i.digital_pins,
                    ''.join([x + ' ' for x in i.analog_functions]),
                    ''.join([x + ' ' for x in i.novatech_functions])
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
        with open(str(self.preset_path.text()) + str(self.load_combo.currentText()), 'r') as f:
            self.instructions = []

            for i in f:
                i = [x.strip() for x in i.split(';')]
                if i[0] == 'Name':
                    continue

                inst = Instruction()

                inst.set_name(i[0])
                inst.set_duration(i[1])
                inst.set_stepsize(i[2])
                inst.set_digital_pins(i[3])
                inst.analog_functions = i[4].split(' ')
                inst.novatech_functions = i[5].split(' ')

                self.instructions.append(inst)
            self.redraw_all()

    def start_device_handler(self):
        self.programmer.start_device_handler()

    def stop_device_handler(self):
        self.programmer.stop_device_handler()

    def program_device_handler(self):
        self.programmer.program_device_handler(self.instructions)



class TableCheckBox(QWidget):
    def __init__(self, gui, row, col, state):
        QWidget.__init__(self)
        cb = QCheckBox()
        cb.setCheckState(QtCore.Qt.Unchecked)
        if state:
            cb.setCheckState(QtCore.Qt.Checked)
        cb.setStyleSheet("QCheckBox::indicator { width: 35px; height: 35px;}")
        cb.clicked.connect(lambda: gui.update_digital(row,col))
        layout = QHBoxLayout(self)
        layout.addWidget(cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)


# **************************************************************************************
if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    main = Main()
    main.show()
    app1.exec_()
    pb_close()
    sys.exit()