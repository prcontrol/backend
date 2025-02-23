# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

import logging
import time
from collections.abc import Iterable
from enum import Enum
from functools import partial
from typing import Self

import attrs
from attr import dataclass, field
from tinkerforge.bricklet_industrial_dual_relay import (
    BrickletIndustrialDualRelay,
)
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge.bricklet_servo_v2 import BrickletServoV2
from tinkerforge.bricklet_temperature_v2 import BrickletTemperatureV2
from tinkerforge.bricklet_voltage_current_v2 import BrickletVoltageCurrentV2

from prcontrol.controller.common import (
    BrickletManager,
    LedLane,
    LedPosition,
    LedSide,
    LedState,
    SensorObserver,
    StatusLeds,
    bricklet,
    callable_field,
    sensor_observer_callback_dispatcher,
)
from prcontrol.controller.measurements import Current, Temperature, Voltage

logger = logging.getLogger(__name__)


class PowerBoxBricklets(BrickletManager):
    # fmt: off
    dual_relay_1f         = bricklet(BrickletIndustrialDualRelay, uid="211B")
    dual_relay_1b         = bricklet(BrickletIndustrialDualRelay, uid="211L")
    dual_relay_2f         = bricklet(BrickletIndustrialDualRelay, uid="211J")
    dual_relay_2b         = bricklet(BrickletIndustrialDualRelay, uid="211A")
    dual_relay_3f         = bricklet(BrickletIndustrialDualRelay, uid="211K")
    dual_relay_3b         = bricklet(BrickletIndustrialDualRelay, uid="211s")
    io                    = bricklet(BrickletIO16V2,              uid="231g")
    temperature           = bricklet(BrickletTemperatureV2,       uid="ZQZ")
    voltage_current_1f    = bricklet(BrickletVoltageCurrentV2,    uid="23j6")
    voltage_current_1b    = bricklet(BrickletVoltageCurrentV2,    uid="23jv")
    voltage_current_2f    = bricklet(BrickletVoltageCurrentV2,    uid="23jJ")
    voltage_current_2b    = bricklet(BrickletVoltageCurrentV2,    uid="23jD")
    voltage_current_3f    = bricklet(BrickletVoltageCurrentV2,    uid="23jw")
    voltage_current_3b    = bricklet(BrickletVoltageCurrentV2,    uid="23jd")
    voltage_current_total = bricklet(BrickletVoltageCurrentV2,    uid="23jb")
    servo                 = bricklet(BrickletServoV2,             uid="SFe")
    # fmt: on


class CaseLidState(Enum):
    OPEN = 0
    CLOSED = 1


@attrs.define(on_setattr=sensor_observer_callback_dispatcher)
class PowerBoxSensorState:
    abmient_temperature: Temperature
    voltage_total: Voltage
    current_total: Current
    voltage_lane_1_front: Voltage
    voltage_lane_1_back: Voltage
    voltage_lane_2_front: Voltage
    voltage_lane_2_back: Voltage
    voltage_lane_3_front: Voltage
    voltage_lane_3_back: Voltage
    current_lane_1_front: Current
    current_lane_1_back: Current
    current_lane_2_front: Current
    current_lane_2_back: Current
    current_lane_3_front: Current
    current_lane_3_back: Current

    powerbox_lid: CaseLidState
    reactorbox_lid: CaseLidState
    led_installed_lane_1_front_and_vial: bool
    led_installed_lane_1_back: bool
    led_installed_lane_2_front_and_vial: bool
    led_installed_lane_2_back: bool
    led_installed_lane_3_front_and_vial: bool
    led_installed_lane_3_back: bool
    water_detected: bool
    cable_control: bool

    callback: SensorObserver[Self] = callable_field()

    @staticmethod
    def empty() -> "PowerBoxSensorState":
        return PowerBoxSensorState(
            abmient_temperature=Temperature.from_celsius(0),
            voltage_total=Voltage.from_milli_volts(0),
            current_total=Current.from_milli_amps(0),
            voltage_lane_1_front=Voltage.from_milli_volts(0),
            voltage_lane_1_back=Voltage.from_milli_volts(0),
            voltage_lane_2_front=Voltage.from_milli_volts(0),
            voltage_lane_2_back=Voltage.from_milli_volts(0),
            voltage_lane_3_front=Voltage.from_milli_volts(0),
            voltage_lane_3_back=Voltage.from_milli_volts(0),
            current_lane_1_front=Current.from_milli_amps(0),
            current_lane_1_back=Current.from_milli_amps(0),
            current_lane_2_front=Current.from_milli_amps(0),
            current_lane_2_back=Current.from_milli_amps(0),
            current_lane_3_front=Current.from_milli_amps(0),
            current_lane_3_back=Current.from_milli_amps(0),
            powerbox_lid=CaseLidState.OPEN,
            reactorbox_lid=CaseLidState.OPEN,
            led_installed_lane_1_front_and_vial=False,
            led_installed_lane_1_back=False,
            led_installed_lane_2_front_and_vial=False,
            led_installed_lane_2_back=False,
            led_installed_lane_3_front_and_vial=False,
            led_installed_lane_3_back=False,
            water_detected=False,
            cable_control=False,
        )

    def copy(self) -> Self:
        return attrs.evolve(self)

    def led_voltage_front(self, lane: LedLane) -> Voltage:
        return lane.demux(
            self.voltage_lane_1_front,
            self.voltage_lane_2_front,
            self.voltage_lane_3_front,
        )

    def led_voltage_back(self, lane: LedLane) -> Voltage:
        return lane.demux(
            self.voltage_lane_1_back,
            self.voltage_lane_2_back,
            self.voltage_lane_3_back,
        )

    def led_current_front(self, lane: LedLane) -> Current:
        return lane.demux(
            self.current_lane_1_front,
            self.current_lane_2_front,
            self.current_lane_3_front,
        )

    def led_current_back(self, lane: LedLane) -> Current:
        return lane.demux(
            self.current_lane_1_back,
            self.current_lane_2_back,
            self.current_lane_3_back,
        )

    def led_installed_lane_front_and_vial(self, lane: LedLane) -> bool:
        return lane.demux(
            self.led_installed_lane_1_front_and_vial,
            self.led_installed_lane_2_front_and_vial,
            self.led_installed_lane_3_front_and_vial,
        )

    def led_installed_lane_back(self, lane: LedLane) -> bool:
        return lane.demux(
            self.led_installed_lane_1_back,
            self.led_installed_lane_2_back,
            self.led_installed_lane_3_back,
        )


class PowerBoxStatusLeds(StatusLeds):
    _CHAN_INPUT_POWERBOX_CLOSED = 0
    _CHAN_INPUT_REACTORBOX_CLOSED = 1
    _CHAN_INPUT_LED_INSTALLED_LANE_1_FRONT_AND_VIAL = 2
    _CHAN_INPUT_LED_INSTALLED_LANE_1_BACK = 3
    _CHAN_INPUT_LED_INSTALLED_LANE_2_FRONT_AND_VIAL = 4
    _CHAN_INPUT_LED_INSTALLED_LANE_2_BACK = 5
    _CHAN_INPUT_LED_INSTALLED_LANE_3_FRONT_AND_VIAL = 6
    _CHAN_INPUT_LED_INSTALLED_LANE_3_BACK = 7
    _CHAN_INPUT_WATER_DETECTED = 9
    _CHAN_INPUT_CABLE_CONTROL = 15

    _CHAN_LED_WARNING_TEMP_AMBIENT = 8
    _CHAN_LED_MAINTENANCE_ACTIVE = 10
    _CHAN_LED_CONNECTED = 11
    _CHAN_LED_WARNING_VOLTAGE = 12
    _CHAN_LED_WARNING_WATER = 13
    _CHAN_LED_BOXES_CLOSED = 14

    led_warning_temp_ambient = StatusLeds.led(_CHAN_LED_WARNING_TEMP_AMBIENT)
    led_maintenance_active = StatusLeds.led(_CHAN_LED_MAINTENANCE_ACTIVE)
    led_connected = StatusLeds.led(_CHAN_LED_CONNECTED)
    led_warning_voltage = StatusLeds.led(_CHAN_LED_WARNING_VOLTAGE)
    led_warning_water = StatusLeds.led(_CHAN_LED_WARNING_WATER)
    led_boxes_closed = StatusLeds.led(_CHAN_LED_BOXES_CLOSED)

    def is_output_channel(self, channel: int) -> bool:
        return channel in {
            self._CHAN_LED_WARNING_TEMP_AMBIENT,
            self._CHAN_LED_MAINTENANCE_ACTIVE,
            self._CHAN_LED_CONNECTED,
            self._CHAN_LED_WARNING_VOLTAGE,
            self._CHAN_LED_WARNING_WATER,
            self._CHAN_LED_BOXES_CLOSED,
        }


@dataclass
class PidController:
    target_current: Current
    last_timepoint_sec: float
    last_error: float
    integral_error: float

    intensity: float

    K_p: float = field(default=-0.2, kw_only=True)
    T_i: float = field(default=100000, kw_only=True)
    T_d: float = field(default=0.5, kw_only=True)

    def _error_fun(self, current: Current) -> float:
        return current.ampere - self.target_current.ampere

    def update_with_new_measurement(self, current: Current) -> float:
        now = time.time()
        delta_seconds = now - self.last_timepoint_sec

        new_error = self._error_fun(current)
        delta_error = new_error - self.last_error
        derivative_error = delta_error / delta_seconds

        self.integral_error += new_error * delta_seconds
        self.last_timepoint_sec = now
        self.last_error = new_error

        self.intensity += self.K_p * (
            new_error
            + self.integral_error / self.T_i
            + self.T_d * derivative_error
        )

        return self.intensity


@dataclass
class PidControllerBootstrapper:
    target_current: Current

    def initialize(self, current: Current) -> tuple[float, PidController]:
        intitial_intensity = self.target_current.ampere * 0.5
        controller = PidController(
            target_current=self.target_current,
            last_timepoint_sec=time.time(),
            last_error=0.0,
            integral_error=0.0,
            intensity=intitial_intensity,
        )
        return intitial_intensity, controller


type LedPid = PidController | PidControllerBootstrapper


class PowerBox:
    bricklets: PowerBoxBricklets

    sensors: PowerBoxSensorState
    io_panel: PowerBoxStatusLeds

    sensor_period_ms: int

    _PWM_PERIOD_US: int = 10000
    _PWM_MAX_DGREE: int = 10000
    _SENSOR_PERIOD_PID_MS: int = 100

    _led_max_current: dict[LedPosition, Current]
    _led_pid: dict[LedPosition, LedPid]

    def __init__(
        self,
        bricklets: PowerBoxBricklets,
        sensor_callback: SensorObserver[PowerBoxSensorState],
        sensor_period_ms: int = 200,
    ) -> None:
        self.bricklets = bricklets
        self.sensors = PowerBoxSensorState.empty()
        self.sensors.callback = sensor_callback
        self.io_panel = PowerBoxStatusLeds(bricklets.io)
        self.sensor_period_ms = sensor_period_ms

        self._led_max_current = dict()
        self._led_pid = dict()

    def initialize(self) -> Self:
        self.io_panel.initialize()
        self.bricklets.io.register_callback(
            BrickletIO16V2.CALLBACK_INPUT_VALUE,
            self._callback_io16_single_input,
        )
        self._callback_io16_all_inputs(  # bootstrap values
            [True] * 16, self.bricklets.io.get_value()
        )
        for channel in range(16):
            # We set value_has_to_change to True because
            # we don't want to log this kind of information
            if self.io_panel.is_input_channel(channel):
                self.bricklets.io.set_input_value_callback_configuration(
                    channel, self.sensor_period_ms, True
                )

        self.bricklets.temperature.register_callback(
            BrickletTemperatureV2.CALLBACK_TEMPERATURE,
            self._callback_temperature,
        )
        self.bricklets.temperature.set_temperature_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )

        vc_bricklets_and_lanes: list[
            tuple[BrickletVoltageCurrentV2, BrickletVoltageCurrentV2, LedLane]
        ] = [
            (
                self.bricklets.voltage_current_1f,
                self.bricklets.voltage_current_1b,
                LedLane.LANE_1,
            ),
            (
                self.bricklets.voltage_current_2f,
                self.bricklets.voltage_current_2b,
                LedLane.LANE_2,
            ),
            (
                self.bricklets.voltage_current_3f,
                self.bricklets.voltage_current_3b,
                LedLane.LANE_3,
            ),
        ]
        for bricklet_front, bricklet_back, lane in vc_bricklets_and_lanes:
            bricklet_front.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_CURRENT,
                partial(
                    self._callback_lane_current,
                    LedPosition(lane, LedSide.FRONT),
                ),
            )
            bricklet_back.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_CURRENT,
                partial(
                    self._callback_lane_current, LedPosition(lane, LedSide.BACK)
                ),
            )
            bricklet_front.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_VOLTAGE,
                partial(
                    self._callback_lane_voltage,
                    LedPosition(lane, LedSide.FRONT),
                ),
            )
            bricklet_back.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_VOLTAGE,
                partial(
                    self._callback_lane_voltage, LedPosition(lane, LedSide.BACK)
                ),
            )

            bricklet_front.set_current_callback_configuration(
                self._SENSOR_PERIOD_PID_MS, False, "x", 0, 0
            )
            bricklet_back.set_current_callback_configuration(
                self._SENSOR_PERIOD_PID_MS, False, "x", 0, 0
            )
            bricklet_front.set_voltage_callback_configuration(
                self.sensor_period_ms, False, "x", 0, 0
            )
            bricklet_back.set_voltage_callback_configuration(
                self.sensor_period_ms, False, "x", 0, 0
            )

        self.bricklets.voltage_current_total.register_callback(
            BrickletVoltageCurrentV2.CALLBACK_CURRENT,
            self._callback_total_current,
        )
        self.bricklets.voltage_current_total.register_callback(
            BrickletVoltageCurrentV2.CALLBACK_VOLTAGE,
            self._callback_total_voltage,
        )
        self.bricklets.voltage_current_total.set_current_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )
        self.bricklets.voltage_current_total.set_voltage_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )

        self.io_panel.led_warning_temp_ambient = LedState.HIGH
        self.io_panel.led_maintenance_active = LedState.HIGH
        self.io_panel.led_connected = LedState.HIGH
        self.io_panel.led_warning_voltage = LedState.HIGH
        self.io_panel.led_warning_water = LedState.HIGH
        self.io_panel.led_boxes_closed = LedState.HIGH

        return self

    def reset_leds(self) -> Self:
        for led in LedPosition.led_iter():
            self._deactivate_led_power(led)
            self._disable_led_pwm_controller(led)
        time.sleep(0.01)
        for chan in self._get_servo_channels():
            self.bricklets.servo.set_degree(chan, 0, self._PWM_MAX_DGREE)
            self.bricklets.servo.set_period(chan, self._PWM_PERIOD_US)
            self.bricklets.servo.set_pulse_width(chan, 0, self._PWM_PERIOD_US)
            self.bricklets.servo.set_position(chan, self._PWM_MAX_DGREE)
            self.bricklets.servo.set_motion_configuration(chan, 0, 0, 0)
            self.bricklets.servo.set_enable(chan, False)
        return self

    def _callback_io16_single_input(
        self,
        chan: int,
        _changed: bool,
        value: bool,
    ) -> None:
        # TODO: maybe some of these are acitve low.
        s = self.sensors
        io = self.io_panel
        if chan == io._CHAN_INPUT_POWERBOX_CLOSED:
            s.powerbox_lid = [CaseLidState.CLOSED, CaseLidState.OPEN][value]
        elif chan == io._CHAN_INPUT_REACTORBOX_CLOSED:
            s.reactorbox_lid = [CaseLidState.CLOSED, CaseLidState.OPEN][value]
        elif chan == io._CHAN_INPUT_LED_INSTALLED_LANE_1_FRONT_AND_VIAL:
            s.led_installed_lane_1_front_and_vial = value
        elif chan == io._CHAN_INPUT_LED_INSTALLED_LANE_1_BACK:
            s.led_installed_lane_1_back = value
        elif chan == io._CHAN_INPUT_LED_INSTALLED_LANE_2_FRONT_AND_VIAL:
            s.led_installed_lane_2_front_and_vial = value
        elif chan == io._CHAN_INPUT_LED_INSTALLED_LANE_2_BACK:
            s.led_installed_lane_2_back = value
        elif chan == io._CHAN_INPUT_LED_INSTALLED_LANE_3_FRONT_AND_VIAL:
            s.led_installed_lane_3_front_and_vial = value
        elif chan == io._CHAN_INPUT_LED_INSTALLED_LANE_3_BACK:
            s.led_installed_lane_3_back = value
        elif chan == io._CHAN_INPUT_WATER_DETECTED:
            s.water_detected = not value
        elif chan == io._CHAN_INPUT_CABLE_CONTROL:
            s.cable_control = value

    def _callback_io16_all_inputs(
        self, changes: list[bool], vals: list[bool]
    ) -> None:
        for chan, (changed, val) in enumerate(zip(changes, vals, strict=True)):
            self._callback_io16_single_input(chan, changed, val)

    def _callback_temperature(self, hundreth_celsius: int) -> None:
        self.sensors.abmient_temperature = Temperature.from_hundreth_celsius(
            hundreth_celsius
        )

    def _callback_lane_voltage(self, led: LedPosition, voltage: int) -> None:
        s = self.sensors
        match led:
            case LedPosition(LedLane.LANE_1, LedSide.FRONT):
                s.voltage_lane_1_front = Voltage.from_milli_volts(voltage)
            case LedPosition(LedLane.LANE_1, LedSide.BACK):
                s.voltage_lane_1_back = Voltage.from_milli_volts(voltage)
            case LedPosition(LedLane.LANE_2, LedSide.FRONT):
                s.voltage_lane_2_front = Voltage.from_milli_volts(voltage)
            case LedPosition(LedLane.LANE_2, LedSide.BACK):
                s.voltage_lane_2_back = Voltage.from_milli_volts(voltage)
            case LedPosition(LedLane.LANE_3, LedSide.FRONT):
                s.voltage_lane_3_front = Voltage.from_milli_volts(voltage)
            case LedPosition(LedLane.LANE_3, LedSide.BACK):
                s.voltage_lane_3_back = Voltage.from_milli_volts(voltage)

    def _callback_lane_current(self, led: LedPosition, current: int) -> None:
        s = self.sensors
        match led:
            case LedPosition(LedLane.LANE_1, LedSide.FRONT):
                s.current_lane_1_front = Current.from_milli_amps(current)
            case LedPosition(LedLane.LANE_1, LedSide.BACK):
                s.current_lane_1_back = Current.from_milli_amps(current)
            case LedPosition(LedLane.LANE_2, LedSide.FRONT):
                s.current_lane_2_front = Current.from_milli_amps(current)
            case LedPosition(LedLane.LANE_2, LedSide.BACK):
                s.current_lane_2_back = Current.from_milli_amps(current)
            case LedPosition(LedLane.LANE_3, LedSide.FRONT):
                s.current_lane_3_front = Current.from_milli_amps(current)
            case LedPosition(LedLane.LANE_3, LedSide.BACK):
                s.current_lane_3_back = Current.from_milli_amps(current)

        if led not in self._led_pid:
            return

        current_ = Current.from_milli_amps(current)
        controller = self._led_pid[led]
        if isinstance(controller, PidControllerBootstrapper):
            intensity, new_controller = controller.initialize(current_)
            self._led_pid[led] = new_controller
        else:
            intensity = controller.update_with_new_measurement(current_)
        intensity = min(max(intensity, 0.0), 1.0)
        self._set_led_pwm_absolute_intensity(led, intensity)

    def _callback_total_voltage(self, voltage: int) -> None:
        self.sensors.voltage_total = Voltage.from_milli_volts(voltage)

    def _callback_total_current(self, current: int) -> None:
        self.sensors.current_total = Current.from_milli_amps(current)

    def _get_led_relay(self, led: LedPosition) -> BrickletIndustrialDualRelay:
        match led:
            case LedPosition(LedLane.LANE_1, LedSide.FRONT):
                return self.bricklets.dual_relay_1f
            case LedPosition(LedLane.LANE_1, LedSide.BACK):
                return self.bricklets.dual_relay_1b
            case LedPosition(LedLane.LANE_2, LedSide.FRONT):
                return self.bricklets.dual_relay_2f
            case LedPosition(LedLane.LANE_2, LedSide.BACK):
                return self.bricklets.dual_relay_2b
            case LedPosition(LedLane.LANE_3, LedSide.FRONT):
                return self.bricklets.dual_relay_3f
            case LedPosition(LedLane.LANE_3, LedSide.BACK):
                return self.bricklets.dual_relay_3b
        raise RuntimeError("Impossible LED!")

    def _get_servo_channel_from_led(self, led: LedPosition) -> int:
        """
        These values are hard coded and non-configurable!
        However I don't think these are gonna change anytime...
        """
        match led:
            case LedPosition(LedLane.LANE_1, LedSide.FRONT):
                return 0
            case LedPosition(LedLane.LANE_1, LedSide.BACK):
                return 7
            case LedPosition(LedLane.LANE_2, LedSide.FRONT):
                return 1
            case LedPosition(LedLane.LANE_2, LedSide.BACK):
                return 8
            case LedPosition(LedLane.LANE_3, LedSide.FRONT):
                return 2
            case LedPosition(LedLane.LANE_3, LedSide.BACK):
                return 9
        raise RuntimeError("Impossible LED!")

    def _get_servo_channels(self) -> Iterable[int]:
        return map(self._get_servo_channel_from_led, LedPosition.led_iter())

    def _activate_led_power(self, led: LedPosition) -> Self:
        bricklet = self._get_led_relay(led)
        bricklet.set_selected_value(1, True)
        time.sleep(0.01)
        bricklet.set_selected_value(0, True)
        return self

    def _deactivate_led_power(self, led: LedPosition) -> Self:
        bricklet = self._get_led_relay(led)
        bricklet.set_selected_value(0, False)
        time.sleep(0.01)
        bricklet.set_selected_value(1, False)
        return self

    def _set_led_pwm_absolute_intensity(
        self, led: LedPosition, intensity: float
    ) -> Self:
        assert 0.0 <= intensity <= 1.0
        assert led in self._led_max_current
        self.bricklets.servo.set_position(
            self._get_servo_channel_from_led(led),
            int(self._PWM_MAX_DGREE * (1 - intensity)),
        )
        return self

    def _enable_led_pwm(self, led: LedPosition) -> Self:
        assert led in self._led_max_current
        self.bricklets.servo.set_enable(
            self._get_servo_channel_from_led(led), True
        )
        return self

    def _disable_led_pwm_controller(self, led: LedPosition) -> Self:
        self.bricklets.servo.set_enable(
            self._get_servo_channel_from_led(led), False
        )
        return self

    def set_led_max_current(self, led: LedPosition, current: Current) -> Self:
        assert 0 <= current.milli_amps <= 1000, "Max current is 1.0A."
        logger.debug(f"Setting led max current {led} to {current!r}")
        self._led_max_current[led] = current
        return self

    def activate_led(self, led: LedPosition, target_intensity: float) -> Self:
        """Activates an led and starts feedback loop to keep its intensity
        Expects a max-current to be set using set_led_max_current.
        """
        assert led in self._led_max_current
        assert 0.0 <= target_intensity <= 1.0

        logger.debug(f"Activating led {led}")

        self._set_led_pwm_absolute_intensity(led, 0.0)
        self._enable_led_pwm(led)
        self._activate_led_power(led)

        self._led_pid[led] = PidControllerBootstrapper(
            target_current=self._led_max_current[led] * target_intensity
        )

        return self

    def deactivate_led(self, led: LedPosition) -> Self:
        """Deactivates an led."""
        logger.debug(f"Deactivating led {led}")
        self._deactivate_led_power(led)
        self._led_pid.pop(led)
        self._disable_led_pwm_controller(led)

        return self

    def is_led_active(self, led: LedPosition) -> bool:
        return led in self._led_pid
