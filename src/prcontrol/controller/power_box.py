# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

from collections.abc import Iterable
from enum import Enum
from functools import partial
from typing import Self

import attrs
from tinkerforge.bricklet_industrial_dual_relay import (
    BrickletIndustrialDualRelay,
)
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge.bricklet_servo_v2 import BrickletServoV2
from tinkerforge.bricklet_temperature_v2 import BrickletTemperatureV2
from tinkerforge.bricklet_voltage_current_v2 import BrickletVoltageCurrentV2

from prcontrol.controller.device import (
    BrickletManager,
    StatusLeds,
    bricklet,
)
from prcontrol.controller.measurements import Current, Temperature, Voltage


class LedSide(Enum):
    FRONT = 0
    BACK = 1


class LedLane(Enum):
    LANE_1 = 0
    LANE_2 = 1
    LANE_3 = 2


@attrs.frozen
class Led:
    lane: LedLane
    side: LedSide

    @staticmethod
    def possible_leds() -> Iterable["Led"]:
        for lane in LedLane.LANE_1, LedLane.LANE_2, LedLane.LANE_3:
            for side in LedSide.FRONT, LedSide.BACK:
                yield Led(lane, side)


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


@attrs.define
class PowerBoxSensorStates:
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

    powerbox_closed: bool
    reactorbox_closed: bool
    led_installed_lane_1_front_and_vial: bool
    led_installed_lane_1_back: bool
    led_installed_lane_2_front_and_vial: bool
    led_installed_lane_2_back: bool
    led_installed_lane_3_front_and_vial: bool
    led_installed_lane_3_back: bool
    water_detected: bool

    @staticmethod
    def empty() -> "PowerBoxSensorStates":
        return PowerBoxSensorStates(
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
            powerbox_closed=False,
            reactorbox_closed=False,
            led_installed_lane_1_front_and_vial=False,
            led_installed_lane_1_back=False,
            led_installed_lane_2_front_and_vial=False,
            led_installed_lane_2_back=False,
            led_installed_lane_3_front_and_vial=False,
            led_installed_lane_3_back=False,
            water_detected=False,
        )

    def copy(self) -> Self:
        return attrs.evolve(self)


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

    _CHAN_LED_WARNING_TEMP_AMIBENT = 8
    _CHAN_LED_MAINTENANCE_ACTIVE = 10
    _CHAN_LED_CONNECTED = 11
    _CHAN_LED_WARNING_VOLTAGE = 12
    _CHAN_LED_WARNING_WATER = 13
    _CHAN_LED_BOXES_CLOSED = 14
    _CHAN_LED_CABLE_CONTROL = 15

    led_warning_temp_amibent = StatusLeds.led(_CHAN_LED_WARNING_TEMP_AMIBENT)
    led_maintenance_active = StatusLeds.led(_CHAN_LED_MAINTENANCE_ACTIVE)
    led_connected = StatusLeds.led(_CHAN_LED_CONNECTED)
    led_warning_voltage = StatusLeds.led(_CHAN_LED_WARNING_VOLTAGE)
    led_warning_water = StatusLeds.led(_CHAN_LED_WARNING_WATER)
    led_boxes_closed = StatusLeds.led(_CHAN_LED_BOXES_CLOSED)
    led_cable_control = StatusLeds.led(_CHAN_LED_CABLE_CONTROL)

    def is_output_channel(self, channel: int) -> bool:
        return channel in {
            self._CHAN_LED_WARNING_TEMP_AMIBENT,
            self._CHAN_LED_MAINTENANCE_ACTIVE,
            self._CHAN_LED_CONNECTED,
            self._CHAN_LED_WARNING_VOLTAGE,
            self._CHAN_LED_WARNING_WATER,
            self._CHAN_LED_BOXES_CLOSED,
            self._CHAN_LED_CABLE_CONTROL,
        }


class PowerBox:
    bricklets: PowerBoxBricklets

    sensors: PowerBoxSensorStates
    io_panel: PowerBoxStatusLeds

    sensor_period_ms: int

    _PWM_PERIOD_US = 10000
    _PWM_MAX_DGREE = 10000

    led_max_current: dict[Led, Current]
    led_target_intensity: dict[Led, float]

    def __init__(
        self, bricklets: PowerBoxBricklets, sensor_period_ms: int = 200
    ) -> None:
        self.bricklets = bricklets
        self.sensors = PowerBoxSensorStates.empty()
        self.io_panel = PowerBoxStatusLeds(bricklets.io)
        self.sensor_period_ms = sensor_period_ms

        self.led_max_current = dict()
        self.led_target_intensity = dict()

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
                partial(self._callback_lane_current, Led(lane, LedSide.FRONT)),
            )
            bricklet_back.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_CURRENT,
                partial(self._callback_lane_current, Led(lane, LedSide.BACK)),
            )
            bricklet_front.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_VOLTAGE,
                partial(self._callback_lane_voltage, Led(lane, LedSide.FRONT)),
            )
            bricklet_back.register_callback(
                BrickletVoltageCurrentV2.CALLBACK_VOLTAGE,
                partial(self._callback_lane_voltage, Led(lane, LedSide.BACK)),
            )

            bricklet_front.set_current_callback_configuration(
                self.sensor_period_ms, False, "x", 0, 0
            )
            bricklet_back.set_current_callback_configuration(
                self.sensor_period_ms, False, "x", 0, 0
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

        for chan in self._get_servo_channels():
            self.bricklets.servo.set_degree(chan, 0, self._PWM_MAX_DGREE)
            self.bricklets.servo.set_period(chan, self._PWM_PERIOD_US)
            self.bricklets.servo.set_pulse_width(  # Something safe
                chan, self._PWM_MAX_DGREE - 1, self._PWM_MAX_DGREE
            )
            self.bricklets.servo.set_motion_configuration(chan, 0, 0, 0)
            self.bricklets.servo.set_enable(chan, False)

        self.bricklets.dual_relay_1f.set_response_expected_all(False)
        self.bricklets.dual_relay_1b.set_response_expected_all(False)
        self.bricklets.dual_relay_2f.set_response_expected_all(False)
        self.bricklets.dual_relay_2b.set_response_expected_all(False)
        self.bricklets.dual_relay_3f.set_response_expected_all(False)
        self.bricklets.dual_relay_3b.set_response_expected_all(False)

        for led in Led.possible_leds():
            self._deactivate_led_power(led)
            self._disable_led_pwm_controller(led)

        return self

    def _callback_io16_single_input(
        self,
        channel: int,
        changed: bool,
        value: bool,
    ) -> None:
        # TODO: maybe some of these are acitve low.
        # fmt: off
        if channel == self.io_panel._CHAN_INPUT_POWERBOX_CLOSED:
            self.sensors.powerbox_closed = value
        elif channel == self.io_panel._CHAN_INPUT_REACTORBOX_CLOSED:
            self.sensors.reactorbox_closed = value
        elif channel \
            == self.io_panel._CHAN_INPUT_LED_INSTALLED_LANE_1_FRONT_AND_VIAL:
            self.sensors.led_installed_lane_1_front_and_vial = value
        elif channel == self.io_panel._CHAN_INPUT_LED_INSTALLED_LANE_1_BACK:
            self.sensors.led_installed_lane_1_back = value
        elif channel \
            == self.io_panel._CHAN_INPUT_LED_INSTALLED_LANE_2_FRONT_AND_VIAL:
            self.sensors.led_installed_lane_2_front_and_vial = value
        elif channel == self.io_panel._CHAN_INPUT_LED_INSTALLED_LANE_2_BACK:
            self.sensors.led_installed_lane_2_back = value
        elif channel \
            == self.io_panel._CHAN_INPUT_LED_INSTALLED_LANE_3_FRONT_AND_VIAL:
            self.sensors.led_installed_lane_3_front_and_vial = value
        elif channel == self.io_panel._CHAN_INPUT_LED_INSTALLED_LANE_3_BACK:
            self.sensors.led_installed_lane_3_back = value
        elif channel == self.io_panel._CHAN_INPUT_WATER_DETECTED:
            self.sensors.water_detected = value
        # fmt: on

    def _callback_io16_all_inputs(
        self, changes: list[bool], vals: list[bool]
    ) -> None:
        for chan, (changed, val) in enumerate(zip(changes, vals, strict=True)):
            self._callback_io16_single_input(chan, changed, val)

    def _callback_temperature(self, hundreth_celsius: int) -> None:
        self.sensors.abmient_temperature = Temperature.from_hundreth_celsius(
            hundreth_celsius
        )

    def _callback_lane_voltage(self, led: Led, voltage: int) -> None:
        s = self.sensors
        match led:
            case Led(LedLane.LANE_1, LedSide.FRONT):
                s.voltage_lane_1_front = Voltage.from_milli_volts(voltage)
            case Led(LedLane.LANE_1, LedSide.BACK):
                s.voltage_lane_1_back = Voltage.from_milli_volts(voltage)
            case Led(LedLane.LANE_2, LedSide.FRONT):
                s.voltage_lane_2_front = Voltage.from_milli_volts(voltage)
            case Led(LedLane.LANE_2, LedSide.BACK):
                s.voltage_lane_2_back = Voltage.from_milli_volts(voltage)
            case Led(LedLane.LANE_3, LedSide.FRONT):
                s.voltage_lane_3_front = Voltage.from_milli_volts(voltage)
            case Led(LedLane.LANE_3, LedSide.BACK):
                s.voltage_lane_3_back = Voltage.from_milli_volts(voltage)

    def _callback_lane_current(self, led: Led, current: int) -> None:
        s = self.sensors
        match led:
            case Led(LedLane.LANE_1, LedSide.FRONT):
                s.current_lane_1_front = Current.from_milli_amps(current)
            case Led(LedLane.LANE_1, LedSide.BACK):
                s.current_lane_1_back = Current.from_milli_amps(current)
            case Led(LedLane.LANE_2, LedSide.FRONT):
                s.current_lane_2_front = Current.from_milli_amps(current)
            case Led(LedLane.LANE_2, LedSide.BACK):
                s.current_lane_2_back = Current.from_milli_amps(current)
            case Led(LedLane.LANE_3, LedSide.FRONT):
                s.current_lane_3_front = Current.from_milli_amps(current)
            case Led(LedLane.LANE_3, LedSide.BACK):
                s.current_lane_3_back = Current.from_milli_amps(current)

    def _callback_total_voltage(self, voltage: int) -> None:
        self.sensors.voltage_total = Voltage.from_milli_volts(voltage)

    def _callback_total_current(self, current: int) -> None:
        self.sensors.current_total = Current.from_milli_amps(current)

    def _get_led_relay(self, led: Led) -> BrickletIndustrialDualRelay:
        match led:
            case Led(LedLane.LANE_1, LedSide.FRONT):
                return self.bricklets.dual_relay_1f
            case Led(LedLane.LANE_1, LedSide.BACK):
                return self.bricklets.dual_relay_1b
            case Led(LedLane.LANE_2, LedSide.FRONT):
                return self.bricklets.dual_relay_2f
            case Led(LedLane.LANE_2, LedSide.BACK):
                return self.bricklets.dual_relay_2b
            case Led(LedLane.LANE_3, LedSide.FRONT):
                return self.bricklets.dual_relay_3f
            case Led(LedLane.LANE_3, LedSide.BACK):
                return self.bricklets.dual_relay_3b
        raise RuntimeError("Impossible LED!")

    def _get_servo_channel_from_led(self, led: Led) -> int:
        match led:
            case Led(LedLane.LANE_1, LedSide.FRONT):
                return 0
            case Led(LedLane.LANE_1, LedSide.BACK):
                return 7
            case Led(LedLane.LANE_2, LedSide.FRONT):
                return 1
            case Led(LedLane.LANE_2, LedSide.BACK):
                return 8
            case Led(LedLane.LANE_3, LedSide.FRONT):
                return 2
            case Led(LedLane.LANE_3, LedSide.BACK):
                return 9
        raise RuntimeError("Impossible LED!")

    def _get_servo_channels(self) -> Iterable[int]:
        return map(self._get_servo_channel_from_led, Led.possible_leds())

    def _activate_led_power(self, led: Led) -> Self:
        bricklet = self._get_led_relay(led)
        bricklet.set_selected_value(0, True)
        bricklet.set_selected_value(1, True)
        return self

    def _deactivate_led_power(self, led: Led) -> Self:
        bricklet = self._get_led_relay(led)
        bricklet.set_selected_value(1, False)
        bricklet.set_selected_value(0, False)
        return self

    def _set_led_pwm_from_intensity(self, led: Led, intensity: float) -> Self:
        assert 0.0 <= intensity <= 1.0
        assert led in self.led_max_current
        self.bricklets.servo.set_position(
            self._get_servo_channel_from_led(led),
            int(self._PWM_MAX_DGREE * (1 - intensity)),
        )
        return self

    def _enable_led_pwm(self, led: Led) -> Self:
        assert led in self.led_max_current
        self.bricklets.servo.set_enable(
            self._get_servo_channel_from_led(led), True
        )
        return self

    def _disable_led_pwm_controller(self, led: Led) -> Self:
        self.bricklets.servo.set_enable(
            self._get_servo_channel_from_led(led), False
        )
        return self

    def set_led_max_current(self, led: Led, current: Current) -> Self:
        assert 0.0 <= current.ampere <= 1.0, "Max current is 1.0A."
        self.led_max_current[led] = current

        self.bricklets.servo.set_pulse_width(
            self._get_servo_channel_from_led(led),
            int(self._PWM_PERIOD_US * current.ampere),
            self._PWM_PERIOD_US,
        )
        return self

    def activate_led(self, led: Led, target_intensity: float) -> Self:
        """Activates an led and starts feedback loop to keep its intensity
        Expects a max-current to be set using set_led_max_current.
        """
        assert led in self.led_max_current
        assert 0.0 <= target_intensity <= 1.0
        self.led_target_intensity[led] = target_intensity

        start_position_for_feedback_loop = target_intensity * 0.9
        self._set_led_pwm_from_intensity(led, start_position_for_feedback_loop)
        self._enable_led_pwm(led)
        self._activate_led_power(led)

        return self

    def deactivate_led(self, led: Led) -> Self:
        """Deactivates an led."""
        self.led_target_intensity.pop(led)
        self._deactivate_led_power(led)
        self._disable_led_pwm_controller(led)

        return self

    # TODO: Feedback loop
