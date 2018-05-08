from CycleControl.cycle_plotter import *
from CycleControl.models.instruction import *
from CycleControl.models.hardware import *
from CycleControl.widgets.staging_tables import *
from CycleControl.widgets.variable_editor import *

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'CycleControl', 'cycle_control.ui'))

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, controller):
        super(Main, self).__init__()
        self.setupUi(self)

        self.controller = controller

        self.updating = UpdateLock(False)

        self.dyn_var_model = DynamicVariablesModel(controller)
        self.dyn_var_list.setModel(self.dyn_var_model)

        self.stat_var_model = StaticVariablesModel(controller)
        self.stat_var_table.setModel(self.stat_var_model)

        self.dyn_var_editor = DynamicVariableEditor(self)
        self.dyn_var_editor.model = self.dyn_var_model
        self.verticalLayout_2.addWidget(self.dyn_var_editor)

        self.dyn_var_list.selectionModel().currentChanged.connect(self.dyn_var_editor.selectionChanged)

        self.digital_table = DigitalTable(controller, self)
        self.digital_tab.layout = QVBoxLayout(self.digital_tab)
        self.digital_tab.layout.addWidget(self.digital_table)
        self.digital_tab.setLayout(self.digital_tab.layout)

        self.analog_table = AnalogTable(controller, self)
        self.analog_tab.layout = QVBoxLayout(self.analog_tab)
        self.analog_tab.layout.addWidget(self.analog_table)
        self.analog_tab.setLayout(self.analog_tab.layout)

        self.novatech_table = NovatechTable(controller, self)
        self.novatech_tab.layout = QVBoxLayout(self.novatech_tab)
        self.novatech_tab.layout.addWidget(self.novatech_table)
        self.novatech_tab.setLayout(self.novatech_tab.layout)

        self.current_var_model = CurrentVariablesModel({})
        self.current_vars_table.setModel(self.current_var_model)

        # ------ Process Variables GUI ---------
        self.new_dyn_var.clicked.connect(self.new_dyn_var_handler)
        self.delete_dyn_var.clicked.connect(self.remove_current_dyn_var)

        self.new_stat_var.clicked.connect(self.new_stat_var_handler)
        self.delete_stat_var.clicked.connect(self.remove_current_stat_var)

        # ------ File Management GUI ---------
        self.save_button.clicked.connect(self.save_procedure_handler)
        self.load_button.clicked.connect(self.load_procedure_handler)
        self.new_procedure_button.clicked.connect(self.new_procedure_handler)

        self.load_hardware_button.clicked.connect(self.load_hardware)
        self.save_hardware_button.clicked.connect(self.save_hardware)
        self.new_hardware_button.clicked.connect(self.new_hardware)

        self.digital_model = PulseBlastersModel(controller, self)
        self.digital_tree = QTreeView(self)
        self.digital_tree.setModel(self.digital_model)

        self.analog_model = NIBoardsModel(controller, self)
        self.analog_tree = QTreeView(self)
        self.analog_tree.setItemDelegateForColumn(4, ComboDelegate(self))
        self.analog_tree.setModel(self.analog_model)

        self.novatech_model = NovatechsModel(controller, self)
        self.novatech_tree = QTreeView(self)
        self.novatech_tree.setModel(self.novatech_model)

        self.gridLayout_13.addWidget(self.digital_tree, 0, 0)
        self.gridLayout_13.addWidget(self.analog_tree, 0, 1)
        self.gridLayout_13.addWidget(self.novatech_tree, 0, 2)

        self.new_pulseblaster_button.clicked.connect(self.new_pb_handler)
        self.remove_pulseblaster_button.clicked.connect(self.remove_pb_handler)

        self.new_ni_button.clicked.connect(self.new_ni_handler)
        self.remove_ni_button.clicked.connect(self.remove_ni_handler)

        self.new_novatech_button.clicked.connect(self.new_novatech_handler)
        self.remove_novatech_button.clicked.connect(self.remove_novatech_handler)

        # ------ Header GUI ---------
        self.start_device_button.clicked.connect(self.start_device_handler)
        self.stop_device_button.clicked.connect(self.stop_device_handler)
        self.update_globals_button.clicked.connect(self.update_globals_handler)

        self.worker = gui_thread(self.controller.procedure)
        self.worker.prog_update.connect(self.update_prog)
        self.worker.text_update.connect(self.update_cycle_label)
        self.worker.dyn_var_update.connect(self.update_current_dyn_vars)
        self.worker.file_num_update.connect(self.update_file_num)

        self.steps_num.valueChanged.connect(self.update_steps_num)
        self.persistent_cb.stateChanged.connect(self.update_persistent)
        self.cycle_delay.valueChanged.connect(self.update_cycle_delay)

        self.plotter = CyclePlotter(self)

        self.digital_table.cellChanged.connect(self.highlight_update_globals)
        self.analog_table.cellChanged.connect(self.highlight_update_globals)
        self.novatech_table.cellChanged.connect(self.highlight_update_globals)
        # self.dyn_var_name.textEdited.connect(self.highlight_update_globals)
        # self.dyn_var_start.editingFinished.connect(self.highlight_update_globals)
        # self.dyn_var_end.editingFinished.connect(self.highlight_update_globals)
        # self.dyn_var_default.editingFinished.connect(self.highlight_update_globals)
        # self.dyn_var_log.stateChanged.connect(self.highlight_update_globals)
        # self.dyn_var_send.stateChanged.connect(self.highlight_update_globals)
        self.new_dyn_var.clicked.connect(self.highlight_update_globals)
        self.delete_dyn_var.clicked.connect(self.highlight_update_globals)
        self.new_stat_var.clicked.connect(self.highlight_update_globals)
        self.delete_stat_var.clicked.connect(self.highlight_update_globals)
        self.save_button.clicked.connect(self.highlight_update_globals)
        self.load_button.clicked.connect(self.highlight_update_globals)
        self.new_procedure_button.clicked.connect(self.highlight_update_globals)
        self.steps_num.valueChanged.connect(self.highlight_update_globals)
        self.persistent_cb.stateChanged.connect(self.highlight_update_globals)
        self.cycle_delay.valueChanged.connect(self.highlight_update_globals)

    def copy_inst_handler(self, loc):
        self.controller.clipboard = copy.deepcopy(self.controller.proc_params.instructions[loc])

    def insert_inst_handler(self, loc):
        if self.updating.lock:
            return
        with self.updating:
            inst = Instruction(self.controller.hardware)
            inst.name = 'Instruction ' + str(loc+1)

            self.controller.proc_params.instructions.insert(loc, inst)
            self.insert_inst_row(loc)

    def paste_inst_handler(self, loc):
        if self.updating.lock:
            return
        with self.updating:
            inst = copy.deepcopy(self.controller.clipboard)
            self.controller.proc_params.instructions.insert(loc, inst)
            self.insert_inst_row(loc)

    def remove_inst_handler(self, loc):
        if self.updating.lock or not self.controller.proc_params.instructions:
            return
        with self.updating:
            del self.controller.proc_params.instructions[loc]
            self.remove_inst_row(loc)

    def clip_inst_number(self, num):
        # limits the number between 0 and the number of instructions
        if num < 0 or num >= len(self.controller.proc_params.instructions):
            return len(self.controller.proc_params.instructions)
        return num

    def redraw_all(self):
        self.redraw_all_inst()
        self.dyn_var_model.refresh()
        self.set_proc_param_items()

    def redraw_all_inst(self):
        with self.updating:
            for i in range(self.digital_table.rowCount()):
                self.remove_inst_row(0)
            for i in range(len(self.controller.proc_params.instructions)):
                self.insert_inst_row(i)

    def redraw_inst_row(self, row):
        self.remove_inst_row(row)
        self.insert_inst_row(row)

    def insert_inst_row(self, row):
        self.digital_table.insert_row(row)
        self.analog_table.insert_row(row)
        self.novatech_table.insert_row(row)
        self.set_total_time()
        self.highlight_update_globals()

    def remove_inst_row(self, row):
        self.digital_table.removeRow(row)
        self.analog_table.removeRow(row)
        self.novatech_table.removeRow(row)
        self.set_total_time()

    def new_stat_var_handler(self):
        self.stat_var_model.new_variable()

    def remove_current_stat_var(self):
        row = self.stat_var_table.selectionModel().currentIndex().row()
        if row >= 0:
            self.stat_var_model.remove_variable(row)

    def new_dyn_var_handler(self):
        num = len(self.controller.proc_params.dynamic_variables)
        self.dyn_var_model.insertRow(num)

    def remove_current_dyn_var(self):
        row = self.dyn_var_list.selectionModel().currentIndex().row()
        self.dyn_var_model.remove_variable(row)

    def update_current_dyn_vars(self, dct):
        self.current_var_model.new_vars(dct)

    def update_steps_num(self, val):
        self.controller.proc_params.steps = int(val)
        self.dyn_var_model.refresh()

    def update_persistent(self, state):
        self.controller.proc_params.persistent = state

    def update_cycle_delay(self, val):
        self.controller.proc_params.delay = val

    def set_total_time(self):
        self.cycle_length.setText(str(self.controller.proc_params.get_total_time()))

    def set_proc_param_items(self):
        self.cycle_delay.setValue(self.controller.proc_params.delay)
        self.persistent_cb.setCheckState(bool_to_checkstate(self.controller.proc_params.persistent))
        self.steps_num.setValue(self.controller.proc_params.steps)

    def update_prog(self, val):
        self.cycle_progress.setValue(val)

    def update_cycle_label(self, num, total):
        self.cycle_label.setText('Cycle {}/{}'.format(num, total))
        self.cycle_plot_number.setValue(num)

    def update_file_num(self, val):
        self.file_number.setText(str(val))

    def new_pb_handler(self):
        num = len(self.controller.hardware.pulseblasters)
        self.digital_model.insertRow(num)

    def remove_pb_handler(self):
        self.digital_model.remove_board(self.digital_tree.currentIndex())

    def new_ni_handler(self):
        num = len(self.controller.hardware.ni_boards)
        self.analog_model.insertRow(num)

    def remove_ni_handler(self):
        self.analog_model.remove_board(self.analog_tree.currentIndex())

    def new_novatech_handler(self):
        num = len(self.controller.hardware.novatechs)
        self.novatech_model.insertRow(num)

    def remove_novatech_handler(self):
        self.novatech_model.remove_board(self.novatech_tree.currentIndex())

    def redraw_hardware(self):
        self.digital_model.modelReset.emit()
        self.analog_model.modelReset.emit()
        self.novatech_model.modelReset.emit()
        self.analog_table.redraw_cols()
        self.novatech_table.redraw_cols()
        self.digital_table.redraw_cols()

    def start_device_handler(self):
        if self.controller.procedure.run_lock.running:
            print 'Already running'
            return
        self.controller.procedure.activated = True
        self.controller.procedure.parameters = copy.deepcopy(self.controller.proc_params)
        thread = procedure_thread(self.controller.procedure, self)
        thread.start()

    def update_globals_handler(self):
        print 'Updated globals'
        self.controller.procedure.parameters = copy.deepcopy(self.controller.proc_params)
        self.highlight_update_globals()

    def highlight_update_globals(self):
        if self.controller.procedure.parameters == self.controller.proc_params:
            self.update_globals_button.setStyleSheet(load_stylesheet('update_globals_default.qss'))
        else:
            self.update_globals_button.setStyleSheet(load_stylesheet('update_globals_highlighted.qss'))

    def stop_device_handler(self):
        print 'Stopping sequence'
        self.controller.procedure.activated = False

    def clear_procedure(self):
        self.controller.proc_params = ProcedureParameters()
        self.current_file.setText('Untitled')

    def new_procedure_handler(self):
        confirmation = ConfirmationWindow('New Procedure')
        confirmation.exec_()
        if not confirmation.cancelled:
            self.clear_procedure()

    def new_hardware(self):
        confirmation = ConfirmationWindow('New Hardware Setup', msg = 'All unsaved changes to the current procedure will be lost. Continue?')
        confirmation.exec_()
        if not confirmation.cancelled:
            self.controller.hardware = HardwareSetup()
            self.redraw_hardware()
            self.clear_procedure()

    def save_procedure_handler(self):
        fp = QFileDialog.getSaveFileName(self, 'Save as...', os.path.join(ROOT_PATH, 'presets'), "Text files (*.txt)")[0]
        if fp:
            self.controller.proc_params.save_to_file(fp)
            self.current_file.setText(re.match(r'.*/(.*)$', fp).group(1))

    def load_procedure_handler(self):
        fp = QFileDialog.getOpenFileName(self, 'Open...', os.path.join(ROOT_PATH, 'presets'), "Text files (*.txt)")[0]
        if fp:
            self.controller.proc_params.load_from_file(fp, self.controller)
            self.current_file.setText(re.match(r'.*/(.*)$', fp).group(1))
            self.redraw_all()

    def load_hardware(self):
        fp = QFileDialog.getOpenFileName(self, 'Open...', os.path.join(ROOT_PATH, 'hardware_presets'), "Text files (*.txt)")[0]
        if fp:
            self.controller.hardware.load_hardware_file(fp, self.controller)
            self.controller.default_setup = DefaultSetup(self.controller.hardware)
            self.redraw_hardware()
            self.plotter.update_channels()
            self.controller.programmer.update_task_handles()
            self.clear_procedure()

    def save_hardware(self):
        fp = QFileDialog.getSaveFileName(self, 'Save as...', os.path.join(ROOT_PATH, 'hardware_presets'), "Text files (*.txt)")[0]
        if fp:
            self.controller.hardware.save_hardware_file(fp)


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
    def __init__(self, procedure, gui = None):
        Thread.__init__(self)
        self.procedure = procedure
        self.gui = gui

    def run(self):
        self.procedure.start_sequence(self.gui)


class gui_thread(QtCore.QThread):
    prog_update = QtCore.pyqtSignal(object)
    text_update = QtCore.pyqtSignal(object, object)
    dyn_var_update = QtCore.pyqtSignal(object)
    file_num_update = QtCore.pyqtSignal(object)

    def __init__(self, procedure):
        QtCore.QThread.__init__(self, parent=None)
        self.procedure = procedure

    def run(self):
        total = self.procedure.parameters.get_total_time()
        init = time.time()
        self.text_update.emit(self.procedure.current_step + 1, self.procedure.parameters.steps)
        self.dyn_var_update.emit(self.procedure.current_variables)
        self.file_num_update.emit(self.procedure.cycle_number)
        while (time.time() - init) < total:
            val = math.ceil((time.time() - init) / total * 1000.0)
            self.prog_update.emit(int(val))
            time.sleep(0.01)
        self.prog_update.emit(1000)