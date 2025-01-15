from enum import Enum
from typing import Callable, Self  # noqa: UP035

from attrs import define, field, setters
from tinkerforge.ip_connection import IPConnection  #  type: ignore

from prcontrol.controller.device import LedState
from prcontrol.controller.power_box import (
    PowerBox,
    PowerBoxBricklets,
    PowerBoxSensorStates,
)
from prcontrol.controller.reactor_box import (
    ReactorBox,
    ReactorBoxBricklets,
    ReactorBoxSensorState,
)


class ThresholdStatus(Enum):
    OK = 0
    EXCEEDED = 1
    OK_AGAIN = 2
    ABORT = 3


@define
class ControllerState:
    reactor_connected: bool
    power_connected: bool

    sample_lane_1: bool
    sample_lane_2: bool
    sample_lane_3: bool

    exp_running_lane_1: bool
    exp_running_lane_2: bool
    exp_running_lane_3: bool

    uv_installed: bool

    ambient_temp_threshold_status: ThresholdStatus
    IR_temp_1_threshold_status: ThresholdStatus
    IR_temp_2_threshold_status: ThresholdStatus
    IR_temp_3_threshold_status: ThresholdStatus
    thermocouple_theshold_status: ThresholdStatus

    reactor_state = field(type=ReactorBoxSensorState, on_setattr=setters.NO_OP)
    power_state = field(type=PowerBoxSensorStates, on_setattr=setters.NO_OP)


class Controller:
    state: ControllerState

    reactor_ipcon: IPConnection
    reactor_box_host: str
    reactor_box_port: int
    reactor_box: ReactorBox
    REACTOR_BOX_SENSOR_PERIOD_MS = 200

    power_ipcon: IPConnection
    power_box_host: str
    power_box_port: int
    power_box: PowerBox
    POWER_BOX_SENSOR_PERIOD_MS = 200

    threshold_warn_ambient_temp: float
    threshold_abort_ambient_temp: float

    threshold_warn_IR_temp_1: float
    threshold_abort_IR_temp_1: float
    threshold_warn_IR_temp_2: float
    threshold_abort_IR_temp_2: float
    threshold_warn_IR_temp_3: float
    threshold_abort_IR_temp_3: float

    threshold_thermocouple: float
    thermocouple_abort_on_theshold: list[int]

    callback_abort_expt: Callable[[int], None]  # aborts experiment on lane i

    def __init__(
        self, power_host, reactor_host, power_port, reactor_port
    ) -> None:
        self.power_ipcon = IPConnection()
        self.power_host = power_host
        self.power_port = power_port

        self.reactor_ipcon = IPConnection()
        self.reactor_host = reactor_host
        self.reactor_port = reactor_port

        reactor_box_bricklets = ReactorBoxBricklets(self.reactor_ipcon)
        power_box_bricklets = PowerBoxBricklets(self.power_ipcon)

        self.reactor_box = ReactorBox(
            reactor_box_bricklets, self.REACTOR_BOX_SENSOR_PERIOD_MS
        )
        self.power_box = PowerBox(
            power_box_bricklets, self.POWER_BOX_SENSOR_PERIOD_MS
        )

        self.state = ControllerState(
            reactor_connected=False,
            power_connected=False,
            reactor_state=self.reactor_box.sensors,
            power_state=self.power_box.sensors,
        )

        # Register Callbacks

        self.power_ipcon.register_callback(
            IPConnection.CALLBACK_CONNECTED, self._callback_power_box_connected
        )
        self.power_ipcon.register_callback(
            IPConnection.CALLBACK_DISCONNECTED,
            self._callback_power_box_disconnected,
        )
        self.reactor_ipcon.register_callback(
            IPConnection.CALLBACK_CONNECTED,
            self._callback_reactor_box_connected,
        )
        self.reactor_ipcon.register_callback(
            IPConnection.CALLBACK_DISCONNECTED,
            self._callback_reactor_box_disconnected,
        )

    # Replaced by callbacks
    # def initialize(self) -> Self:
    #    """Initializes controller. Requires established ip connection."""
    #    self.reactor_box.initialize()
    #    self.power_box.initialize()
    #    return self

    # Methods for outside use

    def connect(self) -> Self:  # ToDo: Catch Exceptions
        self.reactor_ipcon.connect(self.reactor_host, self.reactor_box_port)
        self.power_ipcon.connect(self.power_host, self.power_port)
        self.reactor_ipcon.set_auto_reconnect(True)
        self.power_ipcon.set_auto_reconnect(True)
        return self

    def disconnect(self) -> Self:
        self.reactor_ipcon.disconnect()
        self.power_ipcon.disconnect()
        return self

    # ToDo implement these methods
    def take_sample_on_lane(self, i: int) -> None:
        pass

    def start_exp(self, lane: int) -> None:
        pass

    def end_exp(self, lane: int) -> None:
        pass

    def set_uv_installed(self, b: bool) -> None:
        pass

    def set_threshold_ambient_temp(self, t: float) -> None:
        pass

    def set_threshold_ambient_temp_abort(self, t: float) -> None:
        pass

    def set_threshold_IR_temp(self, lane: int, t: float) -> None:
        pass

    def set_threshold_IR_temp_abort(self, lane: int, t: float) -> None:
        pass

    def set_threshold_thermocouple(self, t: float) -> None:
        pass

    def set_thermocouple_abort_on_threshold(self, b: bool) -> None:
        pass

    def register_callback_abort_expt(
        self, callback: Callable[[int], None]
    ) -> None:
        self.callback_abort_expt = callback

    # Wrappers for Events
    # ToDo: There are needed some additional Events like sample_taken, ...

    def _boxes_closed(self) -> None:
        self.power_box.io_panel.led_boxes_closed = LedState.HIGH

    def _box_opened(self) -> None:
        self.power_box.io_panel.led_boxes_closed = LedState.LOW

    def _maintenance(self) -> None:
        self.power_box.io_panel.led_maintenance_active = LedState.HIGH

    def _running(self) -> None:
        self.reactor_box.io_panel.led_experiment_running = LedState.HIGH

    def _take_single_sample(
        self,
    ) -> None:  # ToDo: replace this by _take_sample_on
        self.reactor_box.io_panel.led_experiment_running = LedState.BLINK_SLOW

    def _take_multiple_samples(
        self,
    ) -> None:  # ToDo: replace this by _take_sample_on
        self.reactor_box.io_panel.led_experiment_running = LedState.BLINK_FAST

    def single_voltage_error(
        self,
    ) -> None:  # ToDo: replace this by _take_sample_on
        self.power_box.io_panel.led_warning_voltage = LedState.BLINK_SLOW

    def _multiple_voltage_error(
        self,
    ) -> None:  # ToDo: replace this by _take_sample_on
        self.power_box.io_panel.led_warning_voltage = LedState.BLINK_FAST

    def _water_error(self) -> None:
        self.power_box.io_panel.led_warning_water = LedState.BLINK_FAST
        self.callback_abort_expt(1)
        self.callback_abort_expt(2)
        self.callback_abort_expt(3)

    def _ambient_temp_high(self) -> None:  # ToDo: set ControlerState
        self.power_box.io_panel.led_warning_temp_ambient = LedState.LOW

    def _ambient_temp_ok(self) -> None:  # ToDo: set ControlerState
        self.power_box.io_panel.led_warning_temp_ambient = LedState.HIGH

    def _ambient_temp_again_ok(self) -> None:  # ToDo: set ControlerState
        self.power_box.io_panel.led_warning_temp_ambient = LedState.BLINK_SLOW

    def _connected(self) -> None:
        self.power_box.io_panel.led_connected = LedState.BLINK_SLOW

    def _connected_and_init(self) -> None:
        self.power_box.io_panel.led_connected = LedState.HIGH

    def _IR_temp_ok(self, lane: int) -> None:  # ToDo: set ControlerState
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.HIGH
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.HIGH
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.HIGH

    def _IR_temp_high(self, lane: int) -> None:  # ToDo: set ControlerState
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.LOW
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.LOW
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.LOW

    def _IR_temp_again_ok(self, lane: int) -> None:  # ToDo: set ControlerState
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = (
                LedState.BLINK_SLOW
            )
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = (
                LedState.BLINK_SLOW
            )
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = (
                LedState.BLINK_SLOW
            )

    def _IR_temp_too_high(self, lane: int) -> None:  # ToDo: set ControlerState
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.LOW
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.LOW
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.LOW
        self.callback_abort_expt(lane)

    def _uv_installed(self) -> None:  # ToDo: set ControlerState
        self.reactor_box.io_panel.led_uv_installed = LedState.HIGH

    def _take_sample_on(self, lane: int) -> None:  # ToDo: set ControlerState
        if lane == 1:
            self.reactor_box.io_panel.led_state_lane_1 = LedState.HIGH
        elif lane == 2:
            self.reactor_box.io_panel.led_state_lane_2 = LedState.HIGH
        elif lane == 3:
            self.reactor_box.io_panel.led_state_lane_3 = LedState.HIGH

    def _single_voltage_error_on(
        self, lane: int
    ) -> None:  # ToDo: set ControlerState
        if lane == 1:
            self.reactor_box.io_panel.led_state_lane_1 = LedState.BLINK_SLOW  # noqa: E501
        elif lane == 2:
            self.reactor_box.io_panel.led_state_lane_2 = LedState.BLINK_SLOW  # noqa: E501
        elif lane == 3:
            self.reactor_box.io_panel.led_state_lane_3 = LedState.BLINK_SLOW  # noqa: E501

    def _double_voltage_error_on(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_state_lane_1 = LedState.BLINK_FAST  # noqa: E501
        elif lane == 2:
            self.reactor_box.io_panel.led_state_lane_2 = LedState.BLINK_FAST  # noqa: E501
        elif lane == 3:
            self.reactor_box.io_panel.led_state_lane_3 = LedState.BLINK_FAST  # noqa: E501

    def _uv_detected(self) -> None:  # ToDo: set ControlerState
        self.reactor_box.io_panel.led_uv_warning = LedState.LOW

    def _no_uv_detected(self) -> None:  # ToDo: set ControlerState
        self.reactor_box.io_panel.led_uv_warning = LedState.HIGH

    def _ambient_temp_too_high(self) -> None:  # ToDo: set ControlerState
        self.power_box.io_panel.led_warning_temp_ambient = LedState.LOW
        self.callback_abort_expt(1)
        self.callback_abort_expt(2)
        self.callback_abort_expt(3)

    def _thermocouple_ok(self) -> None:  # ToDo: set ControlerState
        self.reactor_box.io_panel.led_warning_thermocouple = LedState.HIGH

    def _thermocouple_high(
        self, abort_lanes: list[int]
    ) -> None:  # ToDo: set ControlerState
        self.reactor_box.io_panel.led_warning_thermocouple = LedState.LOW

        for i in abort_lanes:
            self.callback_abort_expt(i)

    def _thermocouple_again_ok(self) -> None:  # ToDo: set ControlerState
        self.reactor_box.io_panel.led_warning_thermocouple = LedState.BLINK_SLOW

    # Callbacks
    def _callback_reactor_box_connected(self) -> None:
        self.state.reactor_connected = True
        self.reactor_box.initialize()
        # Assumption: initilize can be called twice without creating a bug

    def _callback_reactor_box_disconnected(self) -> None:
        self.state.reactor_connected = False

    def _callback_power_box_connected(self) -> None:
        self.state.power_connected = True
        self.power_box.initialize()
        # Assumption: initilize can be called twice without creating a bug

    def _callback_power_box_disconnected(self) -> None:
        self.state.power_connected = False
