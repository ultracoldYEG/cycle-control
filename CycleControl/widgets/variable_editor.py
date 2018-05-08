from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QDataWidgetMapper
import os

ROOT_PATH = os.getcwd()
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
        self._data_mapper.addMapping(self.dyn_var_stepsize, 6, 'text')

        self.dyn_var_log.clicked.connect(self.dyn_var_log.clearFocus)
        self.dyn_var_send.clicked.connect(self.dyn_var_send.clearFocus)


    def selectionChanged(self, current_index, old_index):
        self._data_mapper.setCurrentIndex(current_index.row())