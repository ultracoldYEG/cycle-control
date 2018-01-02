from CycleControl.main import *

import sys

if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    controller = Controller()

    pb = PulseBlasterBoard('0', controller)

    controller.hardware.pulseblasters.append(pb)

    main = Main(controller)
    main.show()
    app1.exec_()
    main.controller.programmer.clear_all_task_handles()
    main.controller.procedure.activated = False
    pb_close()
    sys.exit()