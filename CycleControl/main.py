
import sys
from PyQt5.uic import loadUiType
from helpers import *

from CycleControl.objects.cycle_controller import *
from CycleControl.cycle_plotter import *

from CycleControl.models.instruction import *

from CycleControl.views.staging_tables import *

from widgets import *

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'CycleControl', 'cycle_control.ui'))

DynVarBase, DynVarForm = loadUiType(os.path.join(ROOT_PATH, 'CycleControl', 'dynamic_var_widget.ui'))

class DynamicVariableEditor(DynVarForm, DynVarBase):
    def __init__(self, parent = None):
        super(DynamicVariableEditor, self).__init__()
        self.setupUi(self)
        self._model = None
        self._data_mapper = QDataWidgetMapper(self)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self._data_mapper.setModel(model)

        self._data_mapper.addMapping(self.dyn_var_name, 0)
        self._data_mapper.addMapping(self.dyn_var_default, 1)
        self._data_mapper.addMapping(self.dyn_var_start, 2)
        self._data_mapper.addMapping(self.dyn_var_end, 3)
        self._data_mapper.addMapping(self.dyn_var_log, 4)
        self._data_mapper.addMapping(self.dyn_var_send, 5)

    def selectionChanged(self, current_index, old_index):
        self._data_mapper.setCurrentIndex(current_index.row())


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, controller):
        super(Main, self).__init__()
        self.setupUi(self)

        self.controller = controller

        self.dyn_var_model = DynamicVariablesModel(controller)
        self.dyn_var_list.setModel(self.dyn_var_model)

        self.stat_var_model = StaticVariablesModel(controller)
        self.stat_var_table.setModel(self.stat_var_model)

        self.dyn_var_editor = DynamicVariableEditor(self)
        self.dyn_var_editor.model = self.dyn_var_model
        self.verticalLayout_2.addWidget(self.dyn_var_editor)

        self.dyn_var_list.selectionModel().currentChanged.connect(self.dyn_var_editor.selectionChanged)

        self.digital_table = DigitalTableView(controller, self)
        self.digital_tab.layout = QVBoxLayout(self.digital_tab)
        self.digital_tab.layout.addWidget(self.digital_table)
        self.digital_tab.setLayout(self.digital_tab.layout)

        self.analog_table = StagingTableView(controller, self)
        self.analog_tab.layout = QVBoxLayout(self.analog_tab)
        self.analog_tab.layout.addWidget(self.analog_table)
        self.analog_tab.setLayout(self.analog_tab.layout)

        self.novatech_table = StagingTableView(controller, self)
        self.novatech_tab.layout = QVBoxLayout(self.novatech_tab)
        self.novatech_tab.layout.addWidget(self.novatech_table)
        self.novatech_tab.setLayout(self.novatech_tab.layout)

        self.instructions_model = InstructionsModel(controller)

        self.digital_proxy = DigitalProxyModel()
        self.digital_proxy.setSourceModel(self.instructions_model)

        self.analog_proxy = AnalogProxyModel()
        self.analog_proxy.setSourceModel(self.instructions_model)

        self.novatech_proxy = NovatechProxyModel()
        self.novatech_proxy.setSourceModel(self.instructions_model)

        self.digital_table.setModel(self.digital_proxy)

        self.analog_table.setModel(self.analog_proxy)

        self.novatech_table.setModel(self.novatech_proxy)

        # ------ Process Variables GUI ---------
        self.new_dyn_var.clicked.connect(self.new_dyn_var_handler)
        self.delete_dyn_var.clicked.connect(self.remove_current_dyn_var)

        self.new_stat_var.clicked.connect(self.new_stat_var_handler)
        self.delete_stat_var.clicked.connect(self.remove_current_stat_var)

        # ------ File Management GUI ---------
        self.save_button.clicked.connect(self.save_procedure_handler)
        self.load_button.clicked.connect(self.load_procedure_handler)
        self.new_procedure_button.clicked.connect(self.new_procedure_handler)
        #
        # self.load_hardware_button.clicked.connect(self.load_hardware)
        # self.save_hardware_button.clicked.connect(self.save_hardware)
        # self.new_hardware_button.clicked.connect(self.new_hardware)
        #
        # self.digital_tree = hardware_trees.DigitalTree(self)
        # self.analog_tree = hardware_trees.AnalogTree(self)
        # self.novatech_tree = hardware_trees.NovatechTree(self)
        #
        # self.gridLayout_13.addWidget(self.digital_tree, 0, 0)
        # self.gridLayout_13.addWidget(self.analog_tree, 0, 1)
        # self.gridLayout_13.addWidget(self.novatech_tree, 0, 2)
        #
        # self.new_pulseblaster_button.clicked.connect(self.new_pb_handler)
        # self.remove_pulseblaster_button.clicked.connect(self.remove_pb_handler)
        #
        # self.new_ni_button.clicked.connect(self.new_ni_handler)
        # self.remove_ni_button.clicked.connect(self.remove_ni_handler)
        #
        # self.new_novatech_button.clicked.connect(self.new_novatech_handler)
        # self.remove_novatech_button.clicked.connect(self.remove_novatech_handler)
        #
        # # ------ Header GUI ---------
        # self.start_device_button.clicked.connect(self.start_device_handler)
        # self.stop_device_button.clicked.connect(self.stop_device_handler)
        # self.update_globals_button.clicked.connect(self.update_globals_handler)
        #
        # self.worker = gui_thread(self.procedure)
        # self.worker.prog_update.connect(self.update_prog)
        # self.worker.text_update.connect(self.update_cycle_label)
        # self.worker.dyn_var_update.connect(self.update_current_dyn_vars)
        # self.worker.file_num_update.connect(self.update_file_num)
        #
        # self.steps_num.valueChanged.connect(self.update_steps_num)
        # self.persistent_cb.stateChanged.connect(self.update_persistent)
        # self.cycle_delay.valueChanged.connect(self.update_cycle_delay)
        #
        # self.plotter = CyclePlotter(self)
        #
        # self.digital_table.cellChanged.connect(self.highlight_update_globals)
        # self.analog_table.cellChanged.connect(self.highlight_update_globals)
        # self.novatech_table.cellChanged.connect(self.highlight_update_globals)
        # self.dyn_var_name.textEdited.connect(self.highlight_update_globals)
        # self.dyn_var_start.editingFinished.connect(self.highlight_update_globals)
        # self.dyn_var_end.editingFinished.connect(self.highlight_update_globals)
        # self.dyn_var_default.editingFinished.connect(self.highlight_update_globals)
        # self.dyn_var_log.stateChanged.connect(self.highlight_update_globals)
        # self.dyn_var_send.stateChanged.connect(self.highlight_update_globals)
        # self.new_dyn_var.clicked.connect(self.highlight_update_globals)
        # self.delete_dyn_var.clicked.connect(self.highlight_update_globals)
        # self.new_stat_var.clicked.connect(self.highlight_update_globals)
        # self.delete_stat_var.clicked.connect(self.highlight_update_globals)
        # self.save_button.clicked.connect(self.highlight_update_globals)
        # self.load_button.clicked.connect(self.highlight_update_globals)
        # self.new_procedure_button.clicked.connect(self.highlight_update_globals)
        # self.steps_num.valueChanged.connect(self.highlight_update_globals)
        # self.persistent_cb.stateChanged.connect(self.highlight_update_globals)
        # self.cycle_delay.valueChanged.connect(self.highlight_update_globals)

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
        for i in range(self.current_vars_table.rowCount()):
            self.current_vars_table.removeRow(0)
        row = 0
        for name, value in dct.iteritems():
            self.current_vars_table.insertRow(row)
            self.current_vars_table.setItem(row, 0, QTableWidgetItem(name))
            self.current_vars_table.setItem(row, 1, QTableWidgetItem(str(value)))
            row += 1

    # def update_steps_num(self, val):
    #     self.proc_params.steps = int(val)
    #     self.set_stepsize_text()
    #
    # def update_persistent(self, state):
    #     self.proc_params.persistent = state
    #
    # def update_cycle_delay(self, val):
    #     self.proc_params.delay = val
    #
    # def set_stepsize_text(self):
    #     try:
    #         stepsize = self.current_dyn_var.get_stepsize(self.proc_params.steps)
    #         self.dyn_var_stepsize.setText(str(stepsize))
    #     except (ValueError, ZeroDivisionError, AttributeError):
    #         self.dyn_var_stepsize.setText('NaN')
    #
    # def set_total_time(self):
    #     self.cycle_length.setText(str(self.proc_params.get_total_time()))
    #
    # def set_proc_param_items(self):
    #     self.cycle_delay.setValue(self.proc_params.delay)
    #     self.persistent_cb.setCheckState(bool_to_checkstate(self.proc_params.persistent))
    #     self.steps_num.setValue(self.proc_params.steps)
    #
    # def update_prog(self, val):
    #     self.cycle_progress.setValue(val)
    #
    # def update_cycle_label(self, num, total):
    #     self.cycle_label.setText('Cycle {}/{}'.format(num, total))
    #     self.cycle_plot_number.setValue(num)
    #
    # def update_file_num(self, val):
    #     self.file_number.setText(str(val))
    #
    # def new_pb_handler(self):
    #     pb = PulseBlasterBoard(str(len(self.hardware.pulseblasters)))
    #     self.hardware.pulseblasters.append(pb)
    #     self.digital_tree.redraw()
    #
    # def remove_pb_handler(self):
    #     item = self.digital_tree.currentItem()
    #     if item and not item.parent():
    #         index = self.digital_tree.currentIndex().row()
    #         del self.hardware.pulseblasters[index]
    #         self.digital_tree.redraw()
    #
    # def new_ni_handler(self):
    #     ni = NIBoard('Dev' + str(len(self.hardware.ni_boards)))
    #     self.hardware.ni_boards.append(ni)
    #     self.analog_tree.redraw()
    #
    # def remove_ni_handler(self):
    #     item = self.analog_tree.currentItem()
    #     if item and not item.parent():
    #         index = self.analog_tree.currentIndex().row()
    #         del self.hardware.ni_boards[index]
    #         self.analog_tree.redraw()
    #
    # def new_novatech_handler(self):
    #     nova = NovatechBoard('COM' + str(len(self.hardware.novatechs)))
    #     self.hardware.novatechs.append(nova)
    #     self.novatech_tree.redraw()
    #
    # def remove_novatech_handler(self):
    #     item = self.novatech_tree.currentItem()
    #     if item and not item.parent():
    #         index = self.novatech_tree.currentIndex().row()
    #         del self.hardware.novatechs[index]
    #         self.novatech_tree.redraw()
    #
    # def redraw_hardware(self):
    #     self.digital_tree.redraw()
    #     self.analog_tree.redraw()
    #     self.novatech_tree.redraw()
    #     self.analog_table.redraw_cols()
    #     self.novatech_table.redraw_cols()
    #     self.digital_table.redraw_cols()
    #
    # def start_device_handler(self):
    #     if self.procedure.run_lock.running:
    #         print 'Already running'
    #         return
    #     self.procedure.activated = True
    #     self.procedure.parameters = copy.deepcopy(self.proc_params)
    #     thread = procedure_thread(self.procedure)
    #     thread.start()
    #
    # def update_globals_handler(self):
    #     print 'Updated globals'
    #     self.procedure.parameters = copy.deepcopy(self.proc_params)
    #     self.highlight_update_globals()
    #
    # def highlight_update_globals(self):
    #     if self.procedure.parameters == self.proc_params:
    #         self.update_globals_button.setStyleSheet(load_stylesheet('update_globals_default.qss'))
    #     else:
    #         self.update_globals_button.setStyleSheet(load_stylesheet('update_globals_highlighted.qss'))
    #
    # def stop_device_handler(self):
    #     print 'Stopping sequence'
    #     self.procedure.activated = False
    #
    def clear_procedure(self):
        self.controller.proc_params = ProcedureParameters()
        self.current_file.setText('Untitled')
    #
    def new_procedure_handler(self):
        confirmation = ConfirmationWindow('New Procedure')
        confirmation.exec_()
        if not confirmation.cancelled:
            self.clear_procedure()
    #
    # def new_hardware(self):
    #     confirmation = ConfirmationWindow('New Hardware Setup', msg = 'All unsaved changes to the current procedure will be lost. Continue?')
    #     confirmation.exec_()
    #     if not confirmation.cancelled:
    #         self.hardware = HardwareSetup()
    #         self.redraw_hardware()
    #         self.clear_procedure()

    def save_procedure_handler(self):
        fp = QFileDialog.getSaveFileName(self, 'Save as...', os.path.join(ROOT_PATH, 'presets'), "Text files (*.txt)")[0]
        if fp:
            self.controller.proc_params.save_to_file(fp, self)
            self.current_file.setText(re.match(r'.*/(.*)$', fp).group(1))

    def load_procedure_handler(self):
        fp = QFileDialog.getOpenFileName(self, 'Open...', os.path.join(ROOT_PATH, 'presets'), "Text files (*.txt)")[0]
        if fp:
            self.controller.proc_params.load_from_file(fp, self)
            self.current_file.setText(re.match(r'.*/(.*)$', fp).group(1))

    # def load_hardware(self):
    #     fp = QFileDialog.getOpenFileName(self, 'Open...', os.path.join(ROOT_PATH, 'hardware_presets'), "Text files (*.txt)")[0]
    #     if fp:
    #         self.hardware.load_hardware_file(fp)
    #         self.default_setup = DefaultSetup(self.hardware)
    #         self.redraw_hardware()
    #         self.plotter.update_channels()
    #         self.programmer.update_task_handles()
    #         self.clear_procedure()
    #
    # def save_hardware(self):
    #     fp = QFileDialog.getSaveFileName(self, 'Save as...', os.path.join(ROOT_PATH, 'hardware_presets'), "Text files (*.txt)")[0]
    #     if fp:
    #         self.hardware.save_hardware_file(fp)


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


if __name__ == '__main__':
    app1 = QApplication(sys.argv)

    controller = Controller()

    editor = DynamicVariableEditor()
    editor.show()

    main = Main(controller)
    main.show()
    app1.exec_()
    pb_close()
    sys.exit()