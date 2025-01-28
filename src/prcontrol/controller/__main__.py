from prcontrol.controller.common import LedLane
from prcontrol.controller.controller import Controller, ControllerConfig
from prcontrol.controller.measurements import Temperature

controller = Controller(
    reactor_box=("127.0.0.1", 4224),
    power_box=("127.0.0.1", 4223),
    config=ControllerConfig(
        threshold_warn_ambient_temp=Temperature.from_celsius(100),
        threshold_abort_ambient_temp=Temperature.from_celsius(100),
        threshold_warn_IR_temp=(
            Temperature.from_celsius(25),
            Temperature.from_celsius(25),
            Temperature.from_celsius(25),
        ),
        threshold_abort_IR_temp=(
            Temperature.from_celsius(100),
            Temperature.from_celsius(100),
            Temperature.from_celsius(100),
        ),
        threshold_thermocouple_temp=Temperature.from_celsius(1),
        threshold_thermocouple_affected_lanes=frozenset(
            (LedLane.LANE_1, LedLane.LANE_2, LedLane.LANE_3)
        ),
    ),
)

controller.connect()
