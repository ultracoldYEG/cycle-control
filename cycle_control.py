
import sys

from hardware_types import *
from helpers import *
from instruction import *
from programmer import *
from staging_tables import *
from cycle_plotter import *

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'cycle_control.ui'))


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)

        self.updating = UpdateLock(False)

        self.hardware = HardwareSetup()

        self.programmer = Programmer()

        self.procedure = Procedure(self.programmer, self)

        self.proc_params = ProcedureParameters(self)

        # ------ Instruction GUI ---------
        self.digital_table = DigitalTable(self)
        self.digital_tab.layout = QVBoxLayout(self.digital_tab)
        self.digital_tab.layout.addWidget(self.digital_table)
        self.digital_tab.setLayout(self.digital_tab.layout)

        self.analog_table = AnalogTable(self)
        self.analog_tab.layout = QVBoxLayout(self.analog_tab)
        self.analog_tab.layout.addWidget(self.analog_table)
        self.analog_tab.setLayout(self.analog_tab.layout)

        self.novatech_table = NovatechTable(self)
        self.novatech_tab.layout = QVBoxLayout(self.novatech_tab)
        self.novatech_tab.layout.addWidget(self.novatech_table)
        self.novatech_tab.setLayout(self.novatech_tab.layout)

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
        self.save_button.clicked.connect(self.save_procedure_handler)
        self.load_button.clicked.connect(self.load_procedure_handler)
        self.new_procedure_button.clicked.connect(self.new_procedure_handler)

        self.load_hardware_button.clicked.connect(self.load_hardware)
        self.save_hardware_button.clicked.connect(self.save_hardware)
        self.new_hardware_button.clicked.connect(self.new_hardware)

        self.new_pulseblaster_button.clicked.connect(self.new_pb_handler)
        self.remove_pulseblaster_button.clicked.connect(self.remove_pb_handler)

        self.new_ni_button.clicked.connect(self.new_ni_handler)
        self.remove_ni_button.clicked.connect(self.remove_ni_handler)

        self.new_novatech_button.clicked.connect(self.new_novatech_handler)
        self.remove_novatech_button.clicked.connect(self.remove_novatech_handler)

        self.digital_hardware_tree.itemChanged.connect(self.digital_tree_change)
        self.analog_hardware_tree.itemChanged.connect(self.analog_tree_change)
        self.novatech_hardware_tree.itemChanged.connect(self.novatech_tree_change)

        self.analog_hardware_tree.itemDoubleClicked.connect(self.checkEdit)
        self.analog_hardware_tree.setEditTriggers(self.analog_hardware_tree.NoEditTriggers)

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

        self.plotter = CyclePlotter(self)

    def insert_inst_handler(self, loc):
        if self.updating.lock:
            return
        with self.updating:
            inst = Instruction(self.hardware)
            inst.set_name('Instruction ' + str(loc+1))

            self.proc_params.instructions.insert(loc, inst)
            self.insert_inst_row(loc)

    def remove_inst_handler(self, loc):
        if self.updating.lock or not self.proc_params.instructions:
            return
        with self.updating:
            del self.proc_params.instructions[loc]
            self.remove_inst_row(loc)

    def clip_inst_number(self, num):
        # limits the number between 0 and the number of instructions
        if num < 0 or num >= len(self.proc_params.instructions):
            return len(self.proc_params.instructions)
        return num

    def redraw_all(self):
        self.redraw_all_inst()
        self.redraw_all_dyn_var()
        self.redraw_all_stat_var()
        self.set_stepsize_text()
        self.set_proc_param_items()

    def redraw_all_inst(self):
        with self.updating:
            for i in range(self.digital_table.rowCount()):
                self.remove_inst_row(0)
            for i in range(len(self.proc_params.instructions)):
                self.insert_inst_row(i)

    def redraw_inst_row(self, row):
        self.remove_inst_row(row)
        self.insert_inst_row(row)

    def insert_inst_row(self, row):
        self.digital_table.insert_row(row)
        self.analog_table.insert_row(row)
        self.novatech_table.insert_row(row)
        self.set_total_time()

    def remove_inst_row(self, row):
        self.digital_table.removeRow(row)
        self.analog_table.removeRow(row)
        self.novatech_table.removeRow(row)
        self.set_total_time()

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

    def update_current_dyn_vars(self, dct):
        for i in range(self.current_vars_table.rowCount()):
            self.current_vars_table.removeRow(0)
        row = 0
        for name, value in dct.iteritems():
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

    def new_pb_handler(self):
        pb = PulseBlasterBoard(str(len(self.hardware.pulseblasters)))
        self.hardware.pulseblasters.append(pb)
        self.redraw_digital_hardware()

    def remove_pb_handler(self):
        if not self.digital_hardware_tree.currentItem().parent():
            index = self.digital_hardware_tree.currentIndex().row()
            del self.hardware.pulseblasters[index]
            self.redraw_digital_hardware()

    def new_ni_handler(self):
        ni = NIBoard('Dev' + str(len(self.hardware.ni_boards)))
        self.hardware.ni_boards.append(ni)
        self.redraw_analog_hardware()

    def remove_ni_handler(self):
        if not self.analog_hardware_tree.currentItem().parent():
            index = self.analog_hardware_tree.currentIndex().row()
            del self.hardware.ni_boards[index]
            self.redraw_analog_hardware()

    def new_novatech_handler(self):
        nova = NovatechBoard('COM' + str(len(self.hardware.novatechs)))
        self.hardware.novatechs.append(nova)
        self.redraw_novatech_hardware()

    def remove_novatech_handler(self):
        if not self.novatech_hardware_tree.currentItem().parent():
            index = self.novatech_hardware_tree.currentIndex().row()
            del self.hardware.novatechs[index]
            self.redraw_novatech_hardware()

    def redraw_hardware(self):
        self.redraw_analog_hardware()
        self.redraw_digital_hardware()
        self.redraw_novatech_hardware()
        self.analog_table.redraw_cols()
        self.novatech_table.redraw_cols()
        self.digital_table.redraw_cols()

    def redraw_analog_hardware(self):
        with self.updating:
            root = self.analog_hardware_tree
            for i in range(root.topLevelItemCount()):
                root.takeTopLevelItem(0)
            for board in self.hardware.ni_boards:
                board_root = QTreeWidgetItem(root, [board.board_identifier])
                board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
                for i, channel in enumerate(board.channels):
                    item = QTreeWidgetItem(board_root, [str(i)])
                    item.setData(1, QtCore.Qt.DisplayRole, channel.label)
                    item.setData(2, QtCore.Qt.DisplayRole, channel.min)
                    item.setData(3, QtCore.Qt.DisplayRole, channel.max)
                    item.setData(4, QtCore.Qt.DisplayRole, channel.scaling)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                    item.setCheckState(0, bool_to_checkstate(channel.enabled))

    def redraw_digital_hardware(self):
        with self.updating:
            root = self.digital_hardware_tree
            for i in range(root.topLevelItemCount()):
                root.takeTopLevelItem(0)
            for board in self.hardware.pulseblasters:
                board_root = QTreeWidgetItem(root, [board.board_identifier])
                board_root.setData(1, QtCore.Qt.DisplayRole, board.analog_pin)
                board_root.setData(2, QtCore.Qt.DisplayRole, board.novatech_pin)
                board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
                for i, channel in enumerate(board.channels):
                    item = QTreeWidgetItem(board_root, [str(i)])
                    item.setCheckState(0, bool_to_checkstate(channel.enabled))

    def redraw_novatech_hardware(self):
        with self.updating:
            root = self.novatech_hardware_tree
            for i in range(root.topLevelItemCount()):
                root.takeTopLevelItem(0)
            for board in self.hardware.novatechs:
                board_root = QTreeWidgetItem(root, [board.board_identifier])
                board_root.setFlags(board_root.flags() | QtCore.Qt.ItemIsEditable)
                for i, channel in enumerate(board.channels):
                    item = QTreeWidgetItem(board_root, [str(i)])
                    item.setCheckState(0, bool_to_checkstate(channel.enabled))

    def digital_tree_change(self, item, col):
        if self.updating.lock:
            return
        with self.updating:
            if item.parent():
                board_index = self.digital_hardware_tree.indexOfTopLevelItem(item.parent())
                channel = self.hardware.pulseblasters[board_index].channels[int(item.text(0))]
                if col == 0:
                    channel.enabled = bool(item.checkState(col))

    def analog_tree_change(self, item, col):
        if self.updating.lock:
            return
        with self.updating:
            if item.parent():
                board_index = self.analog_hardware_tree.indexOfTopLevelItem(item.parent())
                channel = self.hardware.ni_boards[board_index].channels[int(item.text(0))]
                if col == 0:
                    channel.enabled = bool(item.checkState(col))
                elif col == 1:
                    channel.label = item.text(col)
                elif col == 2:
                    channel.min = float(item.text(col))
                elif col == 3:
                    channel.max = float(item.text(col))
                elif col == 4:
                    channel.scaling = item.text(col)

    def novatech_tree_change(self, item, col):
        if self.updating.lock:
            return
        with self.updating:
            if item.parent():
                board_index = self.novatech_hardware_tree.indexOfTopLevelItem(item.parent())
                channel = self.hardware.novatechs[board_index].channels[int(item.text(0))]
                if col == 0:
                    channel.enabled = bool(item.checkState(col))

    def checkEdit(self, item, col):
        if item.parent() and col > 0:
            self.analog_hardware_tree.editItem(item, col)
        elif not item.parent() and col == 0:
            self.analog_hardware_tree.editItem(item, col)

    def start_device_handler(self):
        if self.procedure.run_lock.running:
            print 'Already running'
            return
        self.procedure.activated = True
        self.procedure.parameters = copy.copy(self.proc_params)
        thread = procedure_thread(self.procedure)
        thread.start()

    def update_globals_handler(self):
        print 'Updated globals'
        self.procedure.parameters = copy.copy(self.proc_params)

    def stop_device_handler(self):
        print 'Stopping sequence'
        self.procedure.activated = False

    def clear_procedure(self):
        self.proc_params = ProcedureParameters(self)
        self.current_file.setText('Untitled')
        self.redraw_all()

    def new_procedure_handler(self):
        confirmation = ConfirmationWindow('New Procedure')
        confirmation.exec_()
        if not confirmation.cancelled:
            self.clear_procedure()

    def new_hardware(self):
        confirmation = ConfirmationWindow('New Hardware Setup', msg = 'All unsaved changes to the current procedure will be lost. Continue?')
        confirmation.exec_()
        if not confirmation.cancelled:
            self.hardware = HardwareSetup()
            self.redraw_hardware()
            self.clear_procedure()

    def save_procedure_handler(self):
        fp = QFileDialog.getSaveFileName(self, 'Save as...', os.path.join(ROOT_PATH, 'presets'), "Text files (*.txt)")[0]
        if fp:
            self.proc_params.save_to_file(fp)
            self.current_file.setText(re.match(r'.*/(.*)$', fp).group(1))

    def load_procedure_handler(self):
        fp = QFileDialog.getOpenFileName(self, 'Open...', os.path.join(ROOT_PATH, 'presets'), "Text files (*.txt)")[0]
        if fp:
            self.proc_params.load_from_file(fp)
            self.current_file.setText(re.match(r'.*/(.*)$', fp).group(1))
            self.redraw_all()

    def load_hardware(self):
        fp = QFileDialog.getOpenFileName(self, 'Open...', os.path.join(ROOT_PATH, 'hardware_presets'), "Text files (*.txt)")[0]
        if fp:
            self.hardware.load_hardware_file(fp)
            self.redraw_hardware()
            self.plotter.update_channels()
            self.clear_procedure()

    def save_hardware(self):
        fp = QFileDialog.getSaveFileName(self, 'Save as...', os.path.join(ROOT_PATH, 'hardware_presets'), "Text files (*.txt)")[0]
        if fp:
            self.hardware.save_hardware_file(fp)


class ConfirmationWindow(QDialog):
    def __init__(self, title,  msg = 'Are you sure?'):
        super(ConfirmationWindow, self).__init__()
        self.cancelled = True
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.setWindowTitle(title)

        message = QLabel(msg)
        yes_btn = QPushButton('Yes')
        no_btn = QPushButton('Cancel')

        yes_btn.clicked.connect(self.confirm)
        no_btn.clicked.connect(self.cancel)

        self.layout.addWidget(message)
        self.layout.addWidget(yes_btn)
        self.layout.addWidget(no_btn)

    def confirm(self):
        self.cancelled = False
        self.done(0)

    def cancel(self):
        self.done(0)


class UpdateLock(object):
    def __init__(self, lock):
        self.lock = lock

    def __enter__(self):
        self.lock = True

    def __exit__(self, *args):
        self.lock = False


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


if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    main = Main()
    main.show()
    app1.exec_()
    pb_close()
    sys.exit()