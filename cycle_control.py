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

from programmer import *
from hardware_types import *
from instruction import *
from helpers import *

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'cycle_control.ui'))

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)

        self.updating = UpdateLock(False)

        self.hardware = HardwareSetup()
        self.hardware.load_hardware_file(os.path.join(ROOT_PATH, 'hardware_presets', 'default.txt'))
        self.hardware.save_hardware_file(os.path.join(ROOT_PATH, 'hardware_presets', 'default.txt'))

        self.programmer = Programmer()

        self.procedure = Procedure(self.programmer, self)

        self.proc_params = ProcedureParameters()

        self.plotter = CyclePlotter(self)

        #------ Instruction GUI ---------
        for table in [self.digital_table, self.analog_table, self.novatech_table]:
            table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.digital_table.customContextMenuRequested.connect(lambda event: self.data_menu(self.digital_table))
        self.analog_table.customContextMenuRequested.connect(lambda event: self.data_menu(self.analog_table))
        self.novatech_table.customContextMenuRequested.connect(lambda event: self.data_menu(self.novatech_table))

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
        self.current_dyn_var = None

        self.dyn_var_list.currentRowChanged.connect(self.select_dyn_var)
        self.new_dyn_var.clicked.connect(self.new_dyn_var_handler)
        self.delete_dyn_var.clicked.connect(self.remove_current_dyn_var)

        self.stat_var_table.itemChanged.connect(self.stat_var_table_change)
        self.new_stat_var.clicked.connect(self.new_stat_var_handler)
        self.delete_stat_var.clicked.connect(self.remove_current_stat_var)


        # ------ File Management GUI ---------
        self.preset_path.textChanged.connect(self.populate_load_presets)
        self.preset_path.setText(os.path.join(ROOT_PATH, "presets\\"))

        self.save_button.clicked.connect(self.save_preset_handler)
        self.load_button.clicked.connect(self.load_preset_handler)
        self.new_procedure_button.clicked.connect(self.new_procedure_handler)

        self.load_hardware_button.clicked.connect(self.load_hardware)

        self.detect_com_button.clicked.connect(self.update_com_ports)
        self.com_ports = []

        # ------ Header GUI ---------
        self.start_device_button.clicked.connect(self.start_device_handler)
        self.stop_device_button.clicked.connect(self.stop_device_handler)
        self.update_globals_button.clicked.connect(self.update_globals_handler)

        self.worker = gui_thread(self.procedure)
        self.worker.prog_update.connect(self.update_prog)
        self.worker.text_update.connect(self.update_cycle_label)
        self.worker.file_num_update.connect(self.update_file_num)

        self.steps_num.valueChanged.connect(self.update_steps_num)
        self.persistent_cb.stateChanged.connect(self.update_persistent)
        self.cycle_delay.valueChanged.connect(self.update_cycle_delay)


    def data_menu(self, table):
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

            self.proc_params.instructions.insert(loc, inst)
            self.insert_row(loc)

    def remove_inst_handler(self, loc):
        if self.updating.lock or not self.proc_params.instructions:
            return
        with self.updating:
            del self.proc_params.instructions[loc]
            self.remove_row(loc)

    def clip_inst_number(self, num):
        # limits the number between 0 and the number of instructions
        if num < 0 or num >= len(self.proc_params.instructions):
            return len(self.proc_params.instructions)
        return num

    def analog_table_change(self):
        if self.updating.lock:
            return
        with self.updating:
            row = self.analog_table.currentRow()
            col = self.analog_table.currentColumn()
            item = self.analog_table.item(row, col)
            inst = self.proc_params.instructions[row]

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
            inst = self.proc_params.instructions[row]

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
            inst = self.proc_params.instructions[row]

            if item:
                item = item.text()
                if col == 0:
                    inst.set_name(item)
                elif col == 1:
                    inst.set_duration(item)
                self.redraw_row(row)

    def redraw_all(self):
        self.redraw_all_inst()
        self.redraw_all_dyn_var()
        self.redraw_all_stat_var()
        self.set_stepsize_text()
        self.set_proc_param_items()

    def redraw_all_inst(self):
        with self.updating:
            for i in range(self.digital_table.rowCount()):
                self.remove_row(0)
            for i in range(len(self.proc_params.instructions)):
                self.insert_row(i)

    def redraw_row(self, row):
        self.remove_row(row)
        self.insert_row(row)

    def insert_row(self, row):
        self.insert_digital_grid_row(row)
        self.insert_analog_table_row(row)
        self.insert_novatech_table_row(row)
        self.set_total_time()

    def remove_row(self, row):
        self.digital_table.removeRow(row)
        self.analog_table.removeRow(row)
        self.novatech_table.removeRow(row)
        self.set_total_time()

    def insert_analog_table_row(self, row):
        self.analog_table.insertRow(row)
        inst = self.proc_params.instructions[row]
        for col in range((self.analog_table.columnCount())):
            if col == 0:
                new_string = inst.name

            elif col == 1:
                new_string = inst.duration

            elif col == 2:
                new_string = inst.stepsize

            else:
                new_string = inst.analog_functions[col - 3]

            self.analog_table.setItem(row, col, QTableWidgetItem(new_string))
            self.analog_table.setRowHeight(row, 25)

    def insert_novatech_table_row(self, row):
        self.novatech_table.insertRow(row)
        inst = self.proc_params.instructions[row]
        for col in range((self.novatech_table.columnCount())):
            if col == 0:
                new_string = inst.name

            elif col == 1:
                new_string = inst.duration

            elif col == 2:
                new_string = inst.stepsize

            else:
                new_string = inst.novatech_functions[col - 3]

            self.novatech_table.setItem(row, col, QTableWidgetItem(new_string))
            self.novatech_table.setRowHeight(row, 25)

    def insert_digital_grid_row(self, row):
        inst = self.proc_params.instructions[row]
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
        inst = self.proc_params.instructions[r]
        c -= 2
        digits = inst.digital_pins
        if digits[c] == '1':
            inst.set_digital_pins(digits[:c] + '0' + digits[c+1:])
        else:
            inst.set_digital_pins(digits[:c] + '1' + digits[c+1:])

    def new_stat_var_handler(self):
        if self.updating.lock:
            return
        with self.updating:
            num = len(self.proc_params.static_variables)
            stat_var = StaticProcessVariable()
            stat_var.name = 'static variable '+str(num)
            self.proc_params.static_variables.append(stat_var)
            self.insert_stat_var_row(num)

    def remove_current_stat_var(self):
        if self.proc_params.static_variables:
            row = self.stat_var_table.currentRow()
            del self.proc_params.static_variables[row]
            self.redraw_all_stat_var()

    def stat_var_table_change(self, item):
        if self.updating.lock or not item:
            return
        with self.updating:
            row = self.stat_var_table.currentRow()
            col = self.stat_var_table.currentColumn()
            stat_var = self.proc_params.static_variables[row]

            if col == 0:
                stat_var.set_name(item.text())
            elif col == 1:
                stat_var.set_default(item.text())
            self.redraw_stat_var_row(row)

    def update_current_dyn_vars(self, dict):
        for i in range(self.current_vars_table.rowCount()):
            self.current_vars_table.removeRow(0)
        row = 0
        for name, value in dict.iteritems():
            self.current_vars_table.insertRow(row)
            self.current_vars_table.setItem(row, 0, QTableWidgetItem(name))
            self.current_vars_table.setItem(row, 1, QTableWidgetItem(str(value)))
            row += 1

    def redraw_all_stat_var(self):
        for i in range(self.stat_var_table.rowCount()):
            self.stat_var_table.removeRow(0)
        for i in range(len(self.proc_params.static_variables)):
            self.insert_stat_var_row(i)

    def redraw_stat_var_row(self, row):
        self.stat_var_table.removeRow(row)
        self.insert_stat_var_row(row)

    def insert_stat_var_row(self, row):
        stat_var = self.proc_params.static_variables[row]
        self.stat_var_table.insertRow(row)
        self.stat_var_table.setItem(row, 0, QTableWidgetItem(stat_var.name))
        self.stat_var_table.setItem(row, 1, QTableWidgetItem(str(stat_var.default)))

    def remove_stat_var_row(self, row):
        self.stat_var_table.removeRow(row)

    def select_dyn_var(self, row):
        if self.proc_params.dynamic_variables:
            self.current_dyn_var = self.proc_params.dynamic_variables[row]
            self.dyn_var_name.setText(self.current_dyn_var.name)
            self.dyn_var_start.setText(str(self.current_dyn_var.start))
            self.dyn_var_end.setText(str(self.current_dyn_var.end))
            self.dyn_var_default.setText(str(self.current_dyn_var.default))
            self.dyn_var_log.setCheckState(bool_to_checkstate(self.current_dyn_var.logarithmic))
            self.dyn_var_send.setCheckState(bool_to_checkstate(self.current_dyn_var.send))
            self.set_stepsize_text()

    def new_dyn_var_handler(self):
        num = len(self.proc_params.dynamic_variables)
        dyn_var = DynamicProcessVariable()
        dyn_var.name = 'dynamic variable '+str(num)
        self.proc_params.dynamic_variables.append(dyn_var)
        self.insert_dyn_var(num)

    def redraw_all_dyn_var(self):
        for i in range(self.dyn_var_list.count()):
            self.dyn_var_list.takeItem(0)
        for i in range(len(self.proc_params.dynamic_variables)):
            self.insert_dyn_var(i)

    def redraw_dyn_var_row(self, row):
        self.insert_dyn_var(row)
        self.dyn_var_list.takeItem(row + 1)

    def insert_dyn_var(self, row):
        dyn_var = self.proc_params.dynamic_variables[row]
        self.dyn_var_list.insertItem(row, QListWidgetItem(dyn_var.name))
        self.dyn_var_list.setCurrentRow(row)

    def remove_current_dyn_var(self):
        if self.proc_params.dynamic_variables:
            row = self.dyn_var_list.currentRow()
            del self.proc_params.dynamic_variables[row]
            self.redraw_all_dyn_var()
            self.dyn_var_list.setCurrentRow(row)

    def update_dynamic_var_name(self, name):
        if self.current_dyn_var:
            self.current_dyn_var.set_name(name)
            self.redraw_dyn_var_row(self.dyn_var_list.currentRow())

    def update_dynamic_var_start(self):
        if self.current_dyn_var:
            self.current_dyn_var.set_start(str(self.dyn_var_start.text()))
            self.dyn_var_start.setText(self.current_dyn_var.start)
            self.set_stepsize_text()

    def update_dynamic_var_end(self):
        if self.current_dyn_var:
            self.current_dyn_var.set_end(str(self.dyn_var_end.text()))
            self.dyn_var_end.setText(self.current_dyn_var.end)
            self.set_stepsize_text()

    def update_dynamic_var_default(self):
        if self.current_dyn_var:
            self.current_dyn_var.set_default(str(self.dyn_var_default.text()))
            self.dyn_var_default.setText(self.current_dyn_var.default)

    def update_dynamic_var_log(self, state):
        if self.current_dyn_var:
            self.current_dyn_var.set_log(state)
            self.set_stepsize_text()

    def update_dynamic_var_send(self, state):
        if self.current_dyn_var:
            self.current_dyn_var.set_send(state)

    def update_steps_num(self, val):
        self.proc_params.steps = int(val)
        self.set_stepsize_text()

    def update_persistent(self, state):
        self.proc_params.persistent = state

    def update_cycle_delay(self, val):
        self.proc_params.delay = val

    def set_stepsize_text(self):
        try:
            stepsize = self.current_dyn_var.get_stepsize(self.proc_params.steps)
            self.dyn_var_stepsize.setText(str(stepsize))
        except (ValueError, ZeroDivisionError, AttributeError):
            self.dyn_var_stepsize.setText('NaN')

    def set_total_time(self):
        self.cycle_length.setText(str(self.proc_params.get_total_time()))

    def set_proc_param_items(self):
        self.cycle_delay.setValue(self.proc_params.delay)
        self.persistent_cb.setCheckState(bool_to_checkstate(self.proc_params.persistent))
        self.steps_num.setValue(self.proc_params.steps)

    def update_prog(self, val):
        self.cycle_progress.setValue(val)

    def update_cycle_label(self, text):
        self.cycle_label.setText(text)

    def update_file_num(self, val):
        self.file_number.setText(str(val))

    def update_com_ports(self):
        self.com_ports = serial_ports()

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

    def save_preset_handler(self):
        fp = str(self.preset_path.text()) + str(self.save_name.text()) + '.txt'
        self.proc_params.save_to_file(fp)
        self.current_file.setText(str(self.save_name.text()) + '.txt')

    def load_preset_handler(self):
        fp = str(self.preset_path.text()) + str(self.load_combo.currentText())
        self.proc_params.load_from_file(fp)
        self.current_file.setText(str(self.load_combo.currentText()))
        self.redraw_all()

    def load_hardware(self):
        self.redraw_analog_hardware()

    def redraw_analog_hardware(self):
        root = self.analog_hardware_tree.invisibleRootItem()
        for board in self.hardware.ni_boards:
            board_root = QTreeWidgetItem(root, [board.board_identifier])
            board_root.setData(1, QtCore.Qt.ItemIsEditable, board.board_identifier)
            board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
            for i, channel in enumerate(board.channels):
                item = QTreeWidgetItem(board_root, [str(i)])
                item.setData(1, QtCore.Qt.ItemIsEditable, channel.label)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                item.setCheckState(0, bool_to_checkstate(channel.enabled))

    def new_procedure_handler(self):
        self.proc_params = ProcedureParameters()
        self.current_file.setText('Untitled')
        self.redraw_all()

    def start_device_handler(self):
        if self.procedure.run_lock.running:
            print 'Already running'
            return
        self.procedure.activated = True
        self.procedure.parameters = copy.deepcopy(self.proc_params)
        thread = procedure_thread(self.procedure)
        thread.start()

    def update_globals_handler(self):
        print 'Updated globals'
        self.procedure.parameters = copy.deepcopy(self.proc_params)

    def stop_device_handler(self):
        print 'Stopping sequence'
        self.procedure.activated = False


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
            cb.setStyleSheet(load_stylesheet('digital_cb_light.qss'))
        else:
            cb.setStyleSheet(load_stylesheet('digital_cb_dark.qss'))
        cb.clicked.connect(lambda: gui.update_digital(row, col))
        layout = QHBoxLayout(self)
        layout.addWidget(cb)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(2, 0, 0, 0)


class procedure_thread(Thread):
    def __init__(self, procedure):
        Thread.__init__(self)
        self.procedure = procedure

    def run(self):
        self.procedure.start_sequence()


class gui_thread(QtCore.QThread):
    prog_update = QtCore.pyqtSignal(object)
    text_update = QtCore.pyqtSignal(object)
    file_num_update = QtCore.pyqtSignal(object)

    def __init__(self, procedure):
        QtCore.QThread.__init__(self, parent=None)
        self.procedure = procedure

    def run(self):
        total = self.procedure.parameters.get_total_time()
        init = time.time()
        self.text_update.emit('Cycle {}/{}'.format(self.procedure.current_step, self.procedure.parameters.steps))
        self.file_num_update.emit(self.procedure.cycle_number)
        while (time.time() - init) < total:
            val = math.ceil((time.time() - init) / total * 1000.0)
            self.prog_update.emit(int(val))
            time.sleep(0.01)
        self.prog_update.emit(1000)

# **************************************************************************************
if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    main = Main()
    main.show()
    app1.exec_()
    pb_close()
    sys.exit()