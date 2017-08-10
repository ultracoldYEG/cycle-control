from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QColor

class TestTable(QTableWidget):
    def __init__(self, hardware):
        super(TestTable, self).__init__()
        self.hardware = hardware
        self.redraw_cols(hardware)
        self.insertColumn(0)
        self.insertColumn(1)
        self.insertColumn(2)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('Duration'))
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Stepsize'))


    def redraw_cols(self, hardware):
        self.hardware = hardware
        for i in range(self.columnCount()-3):
            self.removeColumn(3)
        for i in range(self.rowCount()):
            self.removeRow(0)
        n = 3
        colors = [QColor(200,200,255), QColor(255,200,200)]
        self.colors = [QColor(255,255,255), QColor(255,255,255), QColor(255,255,255)]
        for i, board in enumerate(self.hardware.ni_boards):
            color = colors[i % 2]
            for channel in board.channels:
                if channel.enabled:
                    self.insertColumn(n)
                    self.setHorizontalHeaderItem(n, QTableWidgetItem(channel.label))
                    self.colors.append(color)
                    n += 1

    def insert_inst(self, row, inst):
        self.insertRow(row)
        for col in range((self.columnCount())):
            if col == 0:
                new_string = inst.name
            elif col == 1:
                new_string = inst.duration
            elif col == 2:
                new_string = inst.stepsize
            else:
                new_string = inst.analog_functions[col - 3]

            item = QTableWidgetItem(new_string)
            item.setBackground(self.colors[col])
            self.setItem(row, col, item)
            self.setRowHeight(row, 25)
