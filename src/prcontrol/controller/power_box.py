# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

from typing import Self

import attrs
from tinkerforge.bricklet_industrial_dual_relay import (
    BrickletIndustrialDualRelay,
)
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge.bricklet_servo_v2 import BrickletServoV2
from tinkerforge.bricklet_temperature_v2 import BrickletTemperatureV2
from tinkerforge.bricklet_voltage_current_v2 import BrickletVoltageCurrentV2

from prcontrol.controller.device import BrickletManager, StatusLeds, bricklet
from prcontrol.controller.measurements import Current, Temperature, Voltage


class PowerBoxBricklets(BrickletManager):
    # fmt: off
    dual_relay_1      = bricklet(BrickletIndustrialDualRelay, uid="221B")
    dual_relay_2      = bricklet(BrickletIndustrialDualRelay, uid="221s")
    dual_relay_3      = bricklet(BrickletIndustrialDualRelay, uid="221J")
    dual_relay_4      = bricklet(BrickletIndustrialDualRelay, uid="221K")
    dual_relay_5      = bricklet(BrickletIndustrialDualRelay, uid="221L")
    dual_relay_6      = bricklet(BrickletIndustrialDualRelay, uid="221A")
    io                = bricklet(BrickletIO16V2,              uid="231g")
    temperature       = bricklet(BrickletTemperatureV2,       uid="ZQZ")
    voltage_current_1 = bricklet(BrickletVoltageCurrentV2,    uid="23j6")
    voltage_current_2 = bricklet(BrickletVoltageCurrentV2,    uid="23jJ")
    voltage_current_3 = bricklet(BrickletVoltageCurrentV2,    uid="23jd")
    voltage_current_4 = bricklet(BrickletVoltageCurrentV2,    uid="23jD")
    voltage_current_5 = bricklet(BrickletVoltageCurrentV2,    uid="23jw")
    voltage_current_6 = bricklet(BrickletVoltageCurrentV2,    uid="23jv")
    servo             = bricklet(BrickletServoV2,             uid="SFe")
    # fmt: on


@attrs.define
class PowerBoxSensorStates:
    abmient_temperature: Temperature | None
    voltage_total: Voltage | None
    current_total: Current | None
    voltage_lane: list[Voltage | None]
    current_lane: list[Current | None]

    @staticmethod
    def empty() -> "PowerBoxSensorStates":
        return PowerBoxSensorStates(
            abmient_temperature=None,
            voltage_total=None,
            current_total=None,
            voltage_lane=[None, None, None],
            current_lane=[None, None, None],
        )

    def copy(self) -> Self:
        return attrs.evolve(self)


class PowerBoxStatusLeds(StatusLeds):
    _CHAN_INPUT_POWERBOX_CLOSED = 0
    _CHAN_INPUT_REACTORBOX_CLOSED = 1
    _CHAN_INPUT_LED_INSTALLED_LANE_1_FRON_AND_VIAL = 2
    _CHAN_INPUT_LED_INSTALLED_LANE_1_BACK = 3
    _CHAN_INPUT_LED_INSTALLED_LANE_2_FRON_AND_VIAL = 4
    _CHAN_INPUT_LED_INSTALLED_LANE_2_BACK = 5
    _CHAN_INPUT_LED_INSTALLED_LANE_3_FRON_AND_VIAL = 6
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

    def __init__(self, bricklets: PowerBoxBricklets) -> None:
        self.bricklets = bricklets
        self.io_panel = PowerBoxStatusLeds(bricklets.io)

    def initialize(self) -> Self:
        self.io_panel.initialize()
        self.bricklets.io.register_callback(
            BrickletIO16V2.CALLBACK_INPUT_VALUE,
            self._callback_io16_single_input,
        )
        for channel in range(16):
            # We set value_has_to_change to True because
            # we don't want to log this kind of information
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

        # TODO: voltage/current callbacks

        return self

    def _callback_io16_single_input(
        self,
        channel: int,
        changed: bool,
        value: bool,
    ) -> None:
        # Todo: asdf
        ...

    def _callback_io16_all_inputs(
        self, changes: list[bool], vals: list[bool]
    ) -> None:
        for chan, (changed, val) in enumerate(zip(changes, vals, strict=True)):
            self._callback_io16_single_input(chan, changed, val)

    def _callback_temperature(self, hundreth_celsius: int) -> None:
        self.sensors.abmient_temperature = Temperature.from_hundreth_celsius(
            hundreth_celsius
        )

    def _callback_total_voltage(self, _: int) -> None: ...  # TODO

    def _callback_total_current(self, _: int) -> None: ...  # TODO

    def _callback_lane_voltage(self, _: int) -> None: ...  # TODO

    def _callback_lane_current(self, _: int) -> None: ...  # TODO
