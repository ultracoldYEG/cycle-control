from CycleControl import *
import sys

if __name__ == '__main__':
    app1 = cycle_control.QApplication(sys.argv)
    main = cycle_control.Main()
    main.show()
    app1.exec_()
    main.programmer.clear_all_task_handles()
    main.procedure.activated = False
    cycle_control.pb_close()
    sys.exit()