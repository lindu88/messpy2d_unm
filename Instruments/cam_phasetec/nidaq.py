import nidaqmx
from nidaqmx import constants as c
from nidaqmx import system
import nidaqmx
from nidaqmx import constants as c
from nidaqmx import system

with nidaqmx.Task() as task, nidaqmx.Task() as di_task:

    task.ai_channels.add_ai_voltage_chan("Dev1/ai1")
    di_task.di_channels.add_di_chan('Dev1/port0/line0:1')
    task.triggers.sync_type.MASTER = True
    task.timing.cfg_samp_clk_timing(1100, "PFI0", c.Edge.RISING,
                                    c.AcquisitionType.FINITE, 1000)
    task.export_signals.export_signal(c.Signal.START_TRIGGER, "RTSI0")
    di_task.timing.cfg_samp_clk_timing(1100, "PFI0", c.Edge.RISING,
                                    c.AcquisitionType.FINITE, 1000)
    di_task.triggers.sync_type.SLAVE = True
    #start_trig.dig_edge_src = "Dev1/PFI0"
    task.start()


    print(task.read())
