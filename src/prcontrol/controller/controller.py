# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

import logging
from collections.abc import Callable
from enum import Enum
from functools import partial
from typing import Any, Self

import attrs
from attrs import define, field, frozen, setters
from tinkerforge.ip_connection import IPConnection

from prcontrol.controller.common import LedLane, LedPosition, LedSide, LedState
from prcontrol.controller.configuration import Experiment
from prcontrol.controller.experiment import ExperimentSupervisor
from prcontrol.controller.measurements import Temperature, UvIndex, Voltage
from prcontrol.controller.power_box import (
    CaseLidState,
    PowerBox,
    PowerBoxBricklets,
    PowerBoxSensorState,
)
from prcontrol.controller.reactor_box import (
    ReactorBox,
    ReactorBoxBricklets,
    ReactorBoxSensorState,
)

logger = logging.getLogger(__name__)


class ThresholdStatus(Enum):
    OK = 0
    EXCEEDED = 1
    OK_AGAIN = 2
    ABORT = 3


@define
class ControllerState:
    reactor_box_connected: bool
    power_box_connected: bool

    sample_lane_1: bool
    sample_lane_2: bool
    sample_lane_3: bool

    exp_running_lane_1: bool
    exp_running_lane_2: bool
    exp_running_lane_3: bool

    uv_installed: bool

    ambient_temp_status: ThresholdStatus
    IR_temp_1_threshold_status: ThresholdStatus
    IR_temp_2_threshold_status: ThresholdStatus
    IR_temp_3_threshold_status: ThresholdStatus
    thermocouple_theshold_status: ThresholdStatus

    reactor_box_state: ReactorBoxSensorState = field(on_setattr=setters.NO_OP)
    power_box_state: PowerBoxSensorState = field(on_setattr=setters.NO_OP)

    @staticmethod
    def default(
        reactor_state: ReactorBoxSensorState, power_state: PowerBoxSensorState
    ) -> "ControllerState":
        return ControllerState(
            reactor_box_connected=True,
            power_box_connected=True,
            sample_lane_1=True,
            sample_lane_2=True,
            sample_lane_3=True,
            exp_running_lane_1=True,
            exp_running_lane_2=True,
            exp_running_lane_3=True,
            uv_installed=True,
            ambient_temp_status=ThresholdStatus.OK,
            IR_temp_1_threshold_status=ThresholdStatus.OK,
            IR_temp_2_threshold_status=ThresholdStatus.OK,
            IR_temp_3_threshold_status=ThresholdStatus.OK,
            thermocouple_theshold_status=ThresholdStatus.OK,
            reactor_box_state=reactor_state,
            power_box_state=power_state,
        )


@frozen
class TfEndpoint:
    host: str
    port: int


@frozen
class ControllerConfig:
    threshold_warn_ambient_temp: Temperature
    threshold_abort_ambient_temp: Temperature

    threshold_warn_IR_temp: tuple[Temperature, Temperature, Temperature]
    threshold_abort_IR_temp: tuple[Temperature, Temperature, Temperature]

    threshold_thermocouple_temp: Temperature
    threshold_thermocouple_affected_lanes: frozenset[LedLane]

    threshold_uv: UvIndex

    @staticmethod
    def default_values() -> "ControllerConfig":
        # TODO get sensible values
        return ControllerConfig(
            threshold_warn_ambient_temp=Temperature.from_celsius(0),
            threshold_abort_ambient_temp=Temperature.from_celsius(0),
            threshold_warn_IR_temp=(
                Temperature.from_celsius(0),
                Temperature.from_celsius(0),
                Temperature.from_celsius(0),
            ),
            threshold_abort_IR_temp=(
                Temperature.from_celsius(0),
                Temperature.from_celsius(0),
                Temperature.from_celsius(0),
            ),
            threshold_thermocouple_temp=Temperature.from_celsius(0),
            threshold_thermocouple_affected_lanes=frozenset(
                (LedLane.LANE_1, LedLane.LANE_2, LedLane.LANE_3)
            ),
            threshold_uv=UvIndex.from_tenth_uvi(29),
        )


type SensorObserver[T] = Callable[
    [T, T, attrs.Attribute[Any], Any],
    None,
]


class Controller:
    # TODO:
    #  - depending the config, set UV installed (software)
    #      Ist laut Software eine UV-LED installiert (Emissionsmaxima < 400 nm),
    #      dann soll diese LED zur Warnung leuchten (mittels A6 PhotoBox).
    #  - implement missing observers
    #

    state: ControllerState

    _reactor_box_ipcon: IPConnection
    _reactor_box_endpoint: TfEndpoint
    reactor_box: ReactorBox

    _power_box_ipcon: IPConnection
    _power_box_endpoint: TfEndpoint
    power_box: PowerBox

    _config: ControllerConfig

    experiment_supervisor: ExperimentSupervisor

    # These are used to specify the callback handlers for changes in
    # both ReactorBoxSensorState and PowerBoxSensorState.
    # The observers receive
    #  - the old state
    #  - the new, modifyed state
    #  - the modified attribute
    #  - the new value
    _callback_handlers_reactor_box: dict[
        "attrs.Attribute[Any]",
        SensorObserver[ReactorBoxSensorState],
    ]
    _callback_handlers_power_box: dict[
        "attrs.Attribute[Any]",
        SensorObserver[PowerBoxSensorState],
    ]

    _voltage_errors: set[LedPosition]

    def __init__(
        self,
        reactor_box: TfEndpoint | tuple[str, int],
        power_box: TfEndpoint | tuple[str, int],
        config: None | ControllerConfig = None,
        reactor_box_sensor_period_ms: int = 200,
        power_box_sensor_period_ms: int = 200,
    ) -> None:
        logger.info("Initializing Controller")

        if not isinstance(reactor_box, TfEndpoint):
            reactor_box = TfEndpoint(*reactor_box)
        if not isinstance(power_box, TfEndpoint):
            power_box = TfEndpoint(*power_box)

        if config is None:
            config = ControllerConfig.default_values()
        self.config = config

        self._voltage_errors = set()

        self._reactor_box_ipcon = IPConnection()
        self._reactor_box_endpoint = reactor_box
        self.reactor_box = ReactorBox(
            ReactorBoxBricklets(self._reactor_box_ipcon),
            self._dispatch_onchange_reactor_box,
            reactor_box_sensor_period_ms,
        )

        self._power_box_ipcon = IPConnection()
        self._power_box_endpoint = power_box
        self.power_box = PowerBox(
            PowerBoxBricklets(self._power_box_ipcon),
            self._dispatch_onchange_power_box,
            power_box_sensor_period_ms,
        )

        self.state = ControllerState.default(
            self.reactor_box.sensors, self.power_box.sensors
        )

        self._power_box_ipcon.register_callback(
            IPConnection.CALLBACK_CONNECTED,
            self._callback_power_box_connected,
        )
        self._power_box_ipcon.register_callback(
            IPConnection.CALLBACK_DISCONNECTED,
            self._callback_power_box_disconnected,
        )
        self._reactor_box_ipcon.register_callback(
            IPConnection.CALLBACK_CONNECTED,
            self._callback_reactor_box_connected,
        )
        self._reactor_box_ipcon.register_callback(
            IPConnection.CALLBACK_DISCONNECTED,
            self._callback_reactor_box_disconnected,
        )

        def noop[T](
            _old: T, _new: T, _attribute: "attrs.Attribute[Any]", _value: Any
        ) -> None: ...

        # The callback handlers for both reactorbox and powerbox
        # will dispatch the callbacks according to these functions.
        # You should use noop to explicitly mark a sensor as unhandled.
        reactor_sensors = attrs.fields(ReactorBoxSensorState)
        self._callback_handlers_reactor_box = {
            reactor_sensors.thermocouble_temp: self._observer_thermocouple,
            reactor_sensors.ambient_light: noop,
            reactor_sensors.ambient_temperature: self._observer_ambient_temp,
            reactor_sensors.lane_1_ir_temp: partial(
                self._observer_ir_temp_lane, lane=LedLane.LANE_1
            ),
            reactor_sensors.lane_2_ir_temp: partial(
                self._observer_ir_temp_lane, lane=LedLane.LANE_2
            ),
            reactor_sensors.lane_3_ir_temp: partial(
                self._observer_ir_temp_lane, lane=LedLane.LANE_3
            ),
            reactor_sensors.uv_index: self._observer_uv_sensor,
            reactor_sensors.lane_1_sample_taken: partial(
                self._observer_sample_taken, lane=LedLane.LANE_1
            ),
            reactor_sensors.lane_2_sample_taken: partial(
                self._observer_sample_taken, lane=LedLane.LANE_2
            ),
            reactor_sensors.lane_3_sample_taken: partial(
                self._observer_sample_taken, lane=LedLane.LANE_3
            ),
            reactor_sensors.maintenance_mode: self._observer_maintenance,
            reactor_sensors.cable_control: self._observer_reactor_box_cable,
        }
        # fmt: off
        assert frozenset(self._callback_handlers_reactor_box) \
            == frozenset(reactor_sensors) - {reactor_sensors.callback}, \
            "There are fields in ReactorBoxSensorStates that dont have a " \
            "callback handler in Controller! Pls fix!"
        # fmt: on

        power_sensors = attrs.fields(PowerBoxSensorState)
        self._callback_handlers_power_box = {
            power_sensors.abmient_temperature: noop,
            power_sensors.voltage_total: noop,
            power_sensors.current_total: noop,
            power_sensors.voltage_lane_1_front: partial(
                self._observer_voltage_error,
                led=LedPosition(LedLane.LANE_1, LedSide.FRONT),
            ),
            power_sensors.voltage_lane_1_back: partial(
                self._observer_voltage_error,
                led=LedPosition(LedLane.LANE_1, LedSide.BACK),
            ),
            power_sensors.voltage_lane_2_front: partial(
                self._observer_voltage_error,
                led=LedPosition(LedLane.LANE_2, LedSide.FRONT),
            ),
            power_sensors.voltage_lane_2_back: partial(
                self._observer_voltage_error,
                led=LedPosition(LedLane.LANE_2, LedSide.BACK),
            ),
            power_sensors.voltage_lane_3_front: partial(
                self._observer_voltage_error,
                led=LedPosition(LedLane.LANE_3, LedSide.FRONT),
            ),
            power_sensors.voltage_lane_3_back: partial(
                self._observer_voltage_error,
                led=LedPosition(LedLane.LANE_3, LedSide.BACK),
            ),
            power_sensors.current_lane_1_front: noop,
            power_sensors.current_lane_1_back: noop,
            power_sensors.current_lane_2_front: noop,
            power_sensors.current_lane_2_back: noop,
            power_sensors.current_lane_3_front: noop,
            power_sensors.current_lane_3_back: noop,
            power_sensors.powerbox_lid: self._observer_boxes_closed,
            power_sensors.reactorbox_lid: self._observer_boxes_closed,
            power_sensors.led_installed_lane_1_front_and_vial: noop,
            power_sensors.led_installed_lane_1_back: noop,
            power_sensors.led_installed_lane_2_front_and_vial: noop,
            power_sensors.led_installed_lane_2_back: noop,
            power_sensors.led_installed_lane_3_front_and_vial: noop,
            power_sensors.led_installed_lane_3_back: noop,
            power_sensors.water_detected: self._observer_water_sensor,
            power_sensors.cable_control: self._observer_power_box_cable,
        }
        # fmt: off
        assert frozenset(self._callback_handlers_power_box) \
            == frozenset(power_sensors) - {power_sensors.callback}, \
            "There are fields in PowerBoxSensorStates that dont have a " \
            "callback handler in Controller! Pls fix!"
        # fmt: on

        self.experiment_supervisor = ExperimentSupervisor(self)
        logger.debug("Initializing Controller done.")

    def connect(self) -> Self:
        logger.info("Connecting to reactorbox and powerbox.")
        self._reactor_box_ipcon.connect(
            self._reactor_box_endpoint.host, self._reactor_box_endpoint.port
        )
        logger.debug(f"Connected to reactorbox ({self._reactor_box_endpoint})")
        self._power_box_ipcon.connect(
            self._power_box_endpoint.host, self._power_box_endpoint.port
        )
        logger.debug(f"Connected to powerbox ({self._power_box_endpoint})")
        self._reactor_box_ipcon.set_auto_reconnect(True)
        self._power_box_ipcon.set_auto_reconnect(True)
        return self

    def disconnect(self) -> Self:
        logger.info("Disconnecting.")
        self._reactor_box_ipcon.disconnect()
        self._power_box_ipcon.disconnect()
        return self

    def _add_event_on_all_lanes(self, event_str: str) -> None:
        self.experiment_supervisor.add_event_on(LedLane.LANE_1, event_str)
        self.experiment_supervisor.add_event_on(LedLane.LANE_2, event_str)
        self.experiment_supervisor.add_event_on(LedLane.LANE_3, event_str)

    def _cancel_all_experiments(self, msg: str | None = None) -> None:
        logger.warning(f"Canceling all experiments! Reason: {msg}")
        self.experiment_supervisor.register_error_on(LedLane.LANE_1)
        self.experiment_supervisor.register_error_on(LedLane.LANE_2)
        self.experiment_supervisor.register_error_on(LedLane.LANE_3)
        self.experiment_supervisor.cancel_experiment_on(LedLane.LANE_1)
        self.experiment_supervisor.cancel_experiment_on(LedLane.LANE_2)
        self.experiment_supervisor.cancel_experiment_on(LedLane.LANE_3)

    def _dispatch_onchange_reactor_box(
        self,
        old_sensors: ReactorBoxSensorState,
        new_sensors: ReactorBoxSensorState,
        attribute: "attrs.Attribute[Any]",
        value: Any,
    ) -> None:
        if attribute not in self._callback_handlers_reactor_box:
            raise RuntimeError(f"Unhandled callback attribute {attribute}.")
        self._callback_handlers_reactor_box[attribute](
            old_sensors, new_sensors, attribute, value
        )

    def _dispatch_onchange_power_box(
        self,
        old_sensors: PowerBoxSensorState,
        new_sensors: PowerBoxSensorState,
        attribute: "attrs.Attribute[Any]",
        value: Any,
    ) -> None:
        if attribute not in self._callback_handlers_power_box:
            raise RuntimeError(f"Unhandled callback attribute {attribute}.")
        self._callback_handlers_power_box[attribute](
            old_sensors, new_sensors, attribute, value
        )

    def _callback_reactor_box_connected(self, *_: Any) -> None:
        self.state.reactor_box_connected = True
        logger.debug("Connection callback received from reactor box")
        self.reactor_box.initialize()
        self._set_connected_led()

    def _callback_reactor_box_disconnected(self, *_: Any) -> None:
        logger.info("Disconnected from reactor box!")
        self.state.reactor_box_connected = False
        self._set_connected_led()

    def _callback_power_box_connected(self, *_: Any) -> None:
        self.state.power_box_connected = True
        # TODO can initilize can be called twice without creating a bug?
        #   see above....
        logger.debug("Connection callback received from power box")
        self.power_box.initialize()
        self._set_connected_led()

    def _callback_power_box_disconnected(self, *_: Any) -> None:
        logger.info("Disconnected from power box!")
        self.state.power_box_connected = False
        self._set_connected_led()

    def _set_connected_led(self) -> None:
        """
        Wenn erfolgreich zu beiden Boxen eine IP-Verbindung aufgebaut werden
        konnte & die Initialisierung abgeschlossen ist, soll diese LED
        leuchten. Wenn die Verbindung aufgebaut ist, aber die Initialisierung
        der Software bzw. der Bricklets noch erfolgt, soll diese LED blinken
        (500 ms an / 500 ms aus).
        """
        # We gonna switch that up. The LED blinks, while the boxes are connected
        # Otherwise, how should we change the LED color on disconnect?
        # We wouldn't have a connection to communicate with the led...
        # The blinking stops automatically after the last monoflop has passed.
        if self.state.reactor_box_connected and self.state.power_box_connected:
            self.power_box.io_panel.led_connected = LedState.BLINK_FAST

    # ===============================
    # =           EVENTS            =
    # ===============================

    def alert_take_sample(self, lane: LedLane) -> Self:
        """
        Wurde im Experiment hinterlegt, dass nach einem Zeitraum X eine
        Probe genommen werden soll, dann soll nach diesem Zeitraum diese
        LED leuchten LED (A3/4/5 PhotoBox) , zudem soll die LED Running
        blinken (→ siehe dort für weitere Informationen). Sollte ein
        Spannungsfehler für diese Lane detektiert geworden sein, soll die
        entsprechende Take Sample LED blinken (500 ms an / 500 ms aus),
        wurden zwei Spannungsfehler für eine Lane detektiert, soll die
        LED schnell blinken (250 ms an / 250 ms aus).
        """
        if lane == LedLane.LANE_1:
            self.state.sample_lane_1 = True
            self.reactor_box.io_panel.led_state_lane_1 = LedState.HIGH
        elif lane == LedLane.LANE_2:
            self.state.sample_lane_2 = True
            self.reactor_box.io_panel.led_state_lane_2 = LedState.HIGH
        elif lane == LedLane.LANE_3:
            self.state.sample_lane_3 = True
            self.reactor_box.io_panel.led_state_lane_3 = LedState.HIGH

        return self

    def end_experiment(self, lane: LedLane, data: Experiment) -> None:
        print("Experiment done, here is the data:")
        print(data.to_json())
        print("This was only for Debug, Programm will crash now....")
        raise NotImplementedError()  # Call Frontend and config_manager

    def reset_ambient_temp_warning(self) -> Self:
        self.state.ambient_temp_status = ThresholdStatus.OK
        return self

    def reset_lane_ir_warnings(self) -> Self:
        self.state.IR_temp_1_threshold_status = ThresholdStatus.OK
        self.state.IR_temp_2_threshold_status = ThresholdStatus.OK
        self.state.IR_temp_3_threshold_status = ThresholdStatus.OK
        return self

    # ===============================
    # =      SENSOR OBSERVERS       =
    # ===============================

    def _observer_boxes_closed(
        self,
        _old_state: PowerBoxSensorState,
        new_state: PowerBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        state: CaseLidState,
    ) -> None:
        # Both the power- and the reactor-boxes lid state is measured
        # by the powerbox. Because we need to check both boxes anyway,
        # we ignore most of the inputs.
        """
        Wenn erkannt wird, dass beiden Boxen zu sind (A0 StromBox erkennt
        Öffnungszustand StromBox; A1 StromBox erkennt Öffnungszustand
        PhotoBox), soll diese LED leuchten.
        """
        if (
            new_state.powerbox_lid
            == new_state.reactorbox_lid
            == CaseLidState.CLOSED
        ):
            self.power_box.io_panel.led_boxes_closed = LedState.HIGH
        else:
            self.power_box.io_panel.led_boxes_closed = LedState.LOW

    def _observer_power_box_cable(
        self,
        _old_state: PowerBoxSensorState,
        _new_state: PowerBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        correct: bool,
    ) -> None:
        # Not sure what to do here tbh...
        return  # TODO implement this.

    def _observer_maintenance(
        self,
        _old_state: ReactorBoxSensorState,
        new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        maintenance_mode_active: bool,
    ) -> None:
        if maintenance_mode_active:
            self.power_box.io_panel.led_maintenance_active = LedState.HIGH
        else:
            self.power_box.io_panel.led_maintenance_active = LedState.LOW

    def _observer_water_sensor(
        self,
        _old_state: PowerBoxSensorState,
        _new_state: PowerBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        detected: bool,
    ) -> None:
        """
        Wurde ein Wasser Error detektiert (mittels B1 StromBox) soll diese LED
        schnell blinken (B5 StromBox; 250 ms an / 250 ms aus) & alle Experimente
        abgebrochen werden.
        """
        if not detected:
            self.power_box.io_panel.led_warning_water = LedState.LOW
            return
        logger.warning(f"WATER DETECTED!!!!! Current state: {_new_state}")
        self._add_event_on_all_lanes("Water leakage detected")
        self._cancel_all_experiments()
        self.power_box.io_panel.led_warning_water = LedState.BLINK_FAST

    def _observer_voltage_error(
        self,
        _old_state: PowerBoxSensorState,
        _new_state: PowerBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        voltage: Voltage,
        /,
        led: LedPosition,
    ) -> None:
        """
        Wenn laut Software eine LED an einer Position sein soll, für diese
        Position beim Einschalten der LED aber keine Spannung / Strom mit dem
        entsprechenden Voltage/Current Bricklet gemessen werden kann soll
        diese LED blinken (B4 StromBox; 500 ms an / 500 ms aus), sollten
        mehrere Fehler erkannt worden sein, soll die LED schnell blinken
        (250 ms an / 250 ms aus).
        """
        if voltage.milli_volts == 0 and self.power_box.is_led_active(led):
            self._voltage_errors.add(led)
            self.experiment_supervisor.add_event_on(led.lane, "Voltage Error")
            self.experiment_supervisor.register_error_on(led.lane)
            self.experiment_supervisor.cancel_experiment_on(led.lane)
        elif led in self._voltage_errors:
            self._voltage_errors.remove(led)

        num_errors = len(self._voltage_errors)
        if num_errors == 1:
            self.power_box.io_panel.led_warning_voltage = LedState.BLINK_SLOW
        elif num_errors:
            self.power_box.io_panel.led_warning_voltage = LedState.BLINK_FAST
        else:
            self.power_box.io_panel.led_warning_voltage = LedState.LOW

    def _observer_ir_temp_lane(
        self,
        _old_state: ReactorBoxSensorState,
        _new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        temp: Temperature,
        /,
        lane: LedLane,
    ) -> None:
        """
        Standartmäßig leuchtet die grüne LED (B1/2/3 PhotoBox = high)
        es soll eine (anpassbarer) Temperatur (für jede Lane / jedes
        Experiment) hinterlegt sein, wird diese Temperatur überschritten,
        soll auf die rote LED umgeschaltet werden (B1/2/3 PhotoBox →
        low), sollte die Temperatur danach wieder unter die hinterlegte
        Temperatur fallen soll alle 500 ms zwischen rot und grün gewechselt
        werden. Sollte der Wert über eine zweite (höhere) hinterlegte
        Temperatur steigen soll das Experiment in dieser Lane abgebrochen
        werden und nur die rote LED leuchten → dementsprechend soll
        Running dann auch ausgeschaltet werden (wenn dies da einzige oder
        letzte Experiment war).
        """
        threshold_abort = lane.demux(*self.config.threshold_abort_IR_temp)
        threshold_warn = lane.demux(*self.config.threshold_warn_IR_temp)

        old_status = lane.demux(
            self.state.IR_temp_1_threshold_status,
            self.state.IR_temp_2_threshold_status,
            self.state.IR_temp_3_threshold_status,
        )

        if temp > threshold_abort or old_status == ThresholdStatus.ABORT:
            warning = (
                f"IR temp threshold reached for lane {lane}!: "
                f"Threshold: {threshold_abort}, "
                f"Temperature: {temp}"
            )
            self.experiment_supervisor.add_event_on(
                lane, "IR Temperature exceeded critical threshold"
            )
            self.experiment_supervisor.register_error_on(lane)
            self.experiment_supervisor.cancel_experiment_on(lane)
            logger.warning(warning)
            new_status = ThresholdStatus.ABORT

        elif temp > threshold_warn:
            logger.warning(
                f"IR temp in lane {lane} exceeded threshold. "
                f"Threshold: {threshold_warn}, temp: {temp}"
            )
            self.experiment_supervisor.add_event_on(
                lane, "IR Temperature exceeded first threshold"
            )
            new_status = ThresholdStatus.EXCEEDED

        elif old_status == ThresholdStatus.EXCEEDED:
            self.experiment_supervisor.add_event_on(
                lane, "IR Temperature back to normal"
            )
            new_status = ThresholdStatus.OK_AGAIN

        else:
            new_status = old_status

        if new_status == ThresholdStatus.ABORT:
            new_led = LedState.LOW
        elif new_status == ThresholdStatus.EXCEEDED:
            new_led = LedState.BLINK_FAST
        elif new_status == ThresholdStatus.OK_AGAIN:
            new_led = LedState.BLINK_SLOW
        else:
            new_led = LedState.HIGH

        if lane == LedLane.LANE_1:
            self.state.IR_temp_1_threshold_status = new_status
            self.reactor_box.io_panel.led_warning_temp_lane_1 = new_led
        elif lane == LedLane.LANE_2:
            self.state.IR_temp_2_threshold_status = new_status
            self.reactor_box.io_panel.led_warning_temp_lane_2 = new_led
        elif lane == LedLane.LANE_3:
            self.state.IR_temp_3_threshold_status = new_status
            self.reactor_box.io_panel.led_warning_temp_lane_3 = new_led

    def _observer_reactor_box_cable(
        self,
        _old_state: ReactorBoxSensorState,
        _new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        correct: bool,
    ) -> None:
        # Not sure what to do here tbh...
        return

    def _observer_sample_taken(
        self,
        _old_state: ReactorBoxSensorState,
        _new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        taken: bool,
        /,
        lane: LedLane,
    ) -> None:
        """
        Wurde im Experiment hinterlegt, dass nach einem Zeitraum X eine
        Probe genommen werden soll, dann soll nach diesem Zeitraum diese
        LED leuchten LED (A3/4/5 PhotoBox) , zudem soll die LED Running
        blinken (→ siehe dort für weitere Informationen). Sollte ein
        Spannungsfehler für diese Lane detektiert geworden sein, soll die
        entsprechende Take Sample LED blinken (500 ms an / 500 ms aus),
        wurden zwei Spannungsfehler für eine Lane detektiert, soll die
        LED schnell blinken (250 ms an / 250 ms aus).
        """
        if not taken:
            return

        self.experiment_supervisor.sample_was_taken_on(lane)
        if lane == LedLane.LANE_1:
            self.state.sample_lane_1 = False
            self.reactor_box.io_panel.led_state_lane_1 = LedState.LOW
        elif lane == LedLane.LANE_2:
            self.state.sample_lane_2 = False
            self.reactor_box.io_panel.led_state_lane_2 = LedState.LOW
        elif lane == LedLane.LANE_3:
            self.state.sample_lane_3 = False
            self.reactor_box.io_panel.led_state_lane_3 = LedState.LOW

    def _observer_uv_sensor(
        self,
        _old_state: ReactorBoxSensorState,
        _new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        uv_index: UvIndex,
    ) -> None:
        """
        Standartmäßig leuchtet die grüne LED (A7 PhotoBox = high)
        es soll eine (anpassbarer) UV-Index hinterlegt sein, wird diese
        UV-Index überschritten, soll auf die rote LED umgeschaltet werden
        (A7 PhotoBox → low), sollte der Wert danach wieder unter den
        hinterlegten Wert fallen soll wieder auf grün geschaltet werden.
        """
        if uv_index > self.config.threshold_uv:
            self.reactor_box.io_panel.led_uv_warning = LedState.LOW
        else:
            self.reactor_box.io_panel.led_uv_warning = LedState.HIGH

        self.reactor_box.io_panel.led_uv_installed = (
            LedState.HIGH if self.state.uv_installed else LedState.LOW
        )

    def _observer_ambient_temp(
        self,
        _old_state: ReactorBoxSensorState,
        _new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        temp: Temperature,
    ) -> None:
        """
        Standartmäßig leuchtet die grüne LED (B0 StromBox = high) es
        soll eine (anpassbarer) Temperatur hinterlegt sein, wird diese
        Temperatur überschritten, soll auf die rote LED umgeschaltet
        werden (B0 StromBox → low), diese Temperatur soll aber nicht
        berücksichtigt werden, um Experimente abzubrechen, sollte die
        Temperatur danach wieder unter die hinterlegte Temperatur fallen
        soll alle 500 ms zwischen rot und grün gewechselt werden
        """
        if (
            temp > self.config.threshold_abort_ambient_temp
            or self.state.ambient_temp_status == ThresholdStatus.ABORT
        ):
            warning = (
                f"Ambient threshold reached!: "
                f"Threshold: {self.config.threshold_abort_ambient_temp}, "
                f"Temperature: {temp}"
            )
            self._add_event_on_all_lanes(
                "Ambient Temperature exceeded critical threshold"
            )
            self._cancel_all_experiments()
            logger.warning(warning)
            self.state.ambient_temp_status = ThresholdStatus.ABORT
        elif temp > self.config.threshold_warn_ambient_temp:
            self.state.ambient_temp_status = ThresholdStatus.EXCEEDED
            self._add_event_on_all_lanes(
                "Ambient Temperature exceeded first threshold"
            )
            logger.warning("High temperature ({temp})")
        elif self.state.ambient_temp_status == ThresholdStatus.EXCEEDED:
            self.state.ambient_temp_status = ThresholdStatus.OK_AGAIN
            self._add_event_on_all_lanes("Ambient Temperature back to normal")
        # Otherwise we hold the state...

        # And set the LED accordingly
        status = self.state.ambient_temp_status
        if status == ThresholdStatus.OK:
            led = LedState.HIGH
        elif status in (ThresholdStatus.EXCEEDED, ThresholdStatus.ABORT):
            led = LedState.LOW
        elif status == ThresholdStatus.OK_AGAIN:
            led = LedState.BLINK_SLOW
        else:
            raise RuntimeError(f"Unhandled status {status}")
        self.power_box.io_panel.led_warning_temp_ambient = led

    def _observer_thermocouple(
        self,
        _old_state: ReactorBoxSensorState,
        _new_state: ReactorBoxSensorState,
        _attribute: "attrs.Attribute[Any]",
        temp: Temperature,
    ) -> None:
        """
        Standartmäßig leuchtet die grüne LED (B5 StromBox = high)
        es soll eine (anpassbarer) Temperatur hinterlegt sein, wird diese
        Temperatur überschritten, soll auf die rote LED umgeschaltet werden
        (B5 StromBox → low), sollte die Temperatur danach wieder unter
        die hinterlegte Temperatur fallen soll alle 500 ms zwischen rot und
        grün gewechselt werden. Zudem soll es möglich sein die Position
        an der der sich das Thermocouple befindet (z.B. Metallkörper in
        Lane 1 oder in der Reaktion in Lane 3) hinterlegbar sein. Zudem
        soll hinterlegbar sein, ob ein (bestimmtes) Experiment abgebrochen
        werden soll, sollte der Temperatur-Wert überschritten werden.
        """
        st = self.state
        if temp > self.config.threshold_thermocouple_temp:
            st.thermocouple_theshold_status = ThresholdStatus.EXCEEDED
            for lane in self.config.threshold_thermocouple_affected_lanes:
                self.experiment_supervisor.add_event_on(
                    lane, "Thermocouple exceeded critical threshold"
                )
                self.experiment_supervisor.register_error_on(lane)
                self.experiment_supervisor.cancel_experiment_on(lane)
        elif st.thermocouple_theshold_status == ThresholdStatus.EXCEEDED:
            st.thermocouple_theshold_status = ThresholdStatus.OK_AGAIN

        if st.thermocouple_theshold_status == ThresholdStatus.OK:
            self.reactor_box.io_panel.led_warning_thermocouple = LedState.HIGH
        elif st.thermocouple_theshold_status == ThresholdStatus.OK_AGAIN:
            self.reactor_box.io_panel.led_warning_thermocouple = (
                LedState.BLINK_SLOW
            )
        else:
            self.reactor_box.io_panel.led_warning_thermocouple = LedState.HIGH
