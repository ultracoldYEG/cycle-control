from CycleControl.main import *

import sys

if __name__ == '__main__':
    app1 = QApplication(sys.argv)
    controller = Controller()

    pb_board = PulseBlasterBoard(0)
    for channel in pb_board:
        channel.enabled = True

    ni_board = NIBoard('Dev1')
    for channel in ni_board:
        channel.enabled = True

    nova_board = NovatechBoard('COM0')
    for channel in nova_board:
        channel.enabled = True

    controller.hardware.pulseblasters.append(pb_board)
    controller.hardware.ni_boards.append(ni_board)
    controller.hardware.novatechs.append(nova_board)

    static_var = StaticProcessVariable(
        name='TEST',
        default = '30.2'
    )

    dynamic_var = DynamicProcessVariable(
        name='dyn_var1',
        start='500',
        send=True,
    )

    inst = Instruction(
        hardware = controller.hardware,
        name='INST1',
        duration='1.2',
    )
    inst.digital_pins.get(0)[3] = True

    controller.proc_params.static_variables.append(static_var)
    controller.proc_params.dynamic_variables.append(dynamic_var)
    controller.proc_params.instructions.append(inst)

    main = Main(controller)
    main.show()
    app1.exec_()
    main.controller.programmer.clear_all_task_handles()
    main.controller.procedure.activated = False
    pb_close()
    sys.exit()