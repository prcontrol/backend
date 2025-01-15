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


@define
class ControllerState:
    reactor_connected: bool
    power_connected: bool

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

    callback_aboart_expt: Callable[[int], None]  # Aboarts experiment on lane i

    def __init__(
        self, power_host, reactor_host, power_port, reactor_port
    ) -> None:  # noqa: E501
        self.power_ipcon = IPConnection()
        self.power_host = power_host
        self.power_port = power_port

        self.reactor_ipcon = IPConnection()
        self.reactor_ipcon.register_callback()  # ToDo
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

    def register_callback_aboart_expt(
        self, callback: Callable[[int], None]
    ) -> None:  # noqa: E501
        self.callback_aboart_expt = callback

    # Semantic Wrappers for Events (both)

    def _boxes_closed(self) -> None:
        self.power_box.io_panel.led_boxes_closed = LedState.HIGH

    def _box_opened(self) -> None:
        self.power_box.io_panel.led_boxes_closed = LedState.LOW

    def _maintenance(self) -> None:
        self.power_box.io_panel.led_maintenance_active = LedState.HIGH

    def _running(self) -> None:
        self.reactor_box.io_panel.led_experiment_running = LedState.HIGH

    def _take_single_sample(self) -> None:  # Needs Callback
        self.reactor_box.io_panel.led_experiment_running = LedState.BLINK_SLOW

    def _take_multiple_samples(self) -> None:  # Needs Callback
        self.reactor_box.io_panel.led_experiment_running = LedState.BLINK_FAST

    def single_voltage_error(self) -> None:
        self.power_box.io_panel.led_warning_voltage = LedState.BLINK_SLOW

    def _multiple_voltage_error(self) -> None:
        self.power_box.io_panel.led_warning_voltage = LedState.BLINK_FAST

    def _water_error(self) -> None:  # Needs callback
        self.power_box.io_panel.led_warning_water = LedState.BLINK_FAST

    def _ambient_temp_high(self) -> None:
        self.power_box.io_panel.led_warning_temp_ambient = LedState.LOW

    def _ambient_temp_ok(self) -> None:
        self.power_box.io_panel.led_warning_temp_ambient = LedState.HIGH

    def _ambient_temp_again_ok(self) -> None:
        self.power_box.io_panel.led_warning_temp_ambient = LedState.BLINK_SLOW

    # Semantic Wrappers for Events (Power Box)

    def _connected(self) -> None:
        self.power_box.io_panel.led_connected = LedState.BLINK_SLOW

    def _connected_and_init(self) -> None:
        self.power_box.io_panel.led_connected = LedState.HIGH

    # Semantic Wrappers for Events (Reactor Box)

    def _IR_temp_ok(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.HIGH
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.HIGH
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.HIGH

    def _IR_temp_high(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.LOW
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.LOW
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.LOW

    def _IR_temp_again_ok(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = (
                LedState.BLINK_SLOW
            )  # noqa: E501
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = (
                LedState.BLINK_SLOW
            )  # noqa: E501
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = (
                LedState.BLINK_SLOW
            )  # noqa: E501

    def _IR_temp_too_high(self, lane: int) -> None:  # Needs Callback
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.LOW
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.LOW
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.LOW

    def _uv_installed(self) -> None:
        self.reactor_box.io_panel.led_uv_installed = LedState.HIGH

    def _take_sample_on(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = LedState.HIGH
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = LedState.HIGH
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = LedState.HIGH

    def _single_voltage_error_on(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = (
                LedState.BLINK_SLOW
            )  # noqa: E501
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = (
                LedState.BLINK_SLOW
            )  # noqa: E501
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = (
                LedState.BLINK_SLOW
            )  # noqa: E501

    def _double_voltage_error_on(self, lane: int) -> None:
        if lane == 1:
            self.reactor_box.io_panel.led_warning_temp_lane_1 = (
                LedState.BLINK_FAST
            )  # noqa: E501
        elif lane == 2:
            self.reactor_box.io_panel.led_warning_temp_lane_2 = (
                LedState.BLINK_FAST
            )  # noqa: E501
        elif lane == 3:
            self.reactor_box.io_panel.led_warning_temp_lane_3 = (
                LedState.BLINK_FAST
            )  # noqa: E501

    def _uv_detected(self) -> None:
        self.reactor_box.io_panel.led_uv_warning = LedState.LOW

    def _no_uv_detected(self) -> None:
        self.reactor_box.io_panel.led_uv_warning = LedState.HIGH

    def _ambient_temp_too_high(self) -> None:  # Needs callback
        self.power_box.io_panel.led_warning_temp_ambient = LedState.LOW

    def _thermocouple_ok(self) -> None:
        self.reactor_box.io_panel.led_warning_thermocouple = LedState.HIGH

    def _thermocouple_high(self, aboard_exp: bool) -> None:  # Needs callback
        pass

    def _thermocouple_again_high(self) -> None:
        pass

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
