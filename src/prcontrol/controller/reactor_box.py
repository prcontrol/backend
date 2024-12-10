# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(


from functools import partial
from typing import Self

import attrs
from tinkerforge.bricklet_ambient_light_v3 import BrickletAmbientLightV3
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge.bricklet_temperature_ir_v2 import BrickletTemperatureIRV2
from tinkerforge.bricklet_temperature_v2 import BrickletTemperatureV2
from tinkerforge.bricklet_thermocouple_v2 import BrickletThermocoupleV2
from tinkerforge.bricklet_uv_light_v2 import BrickletUVLightV2

from prcontrol.controller.device import (
    BrickletManager,
    LedState,
    StatusLeds,
    bricklet,
)
from prcontrol.controller.measurements import Illuminance, Temperature, UvIndex


class ReactorBoxBricklets(BrickletManager):
    # fmt: off
    thermocouple   = bricklet(BrickletThermocoupleV2,  uid="232m")
    io             = bricklet(BrickletIO16V2,          uid="231w")
    ambient_light  = bricklet(BrickletAmbientLightV3,  uid="25sN")
    temperature    = bricklet(BrickletTemperatureV2,   uid="ZQH")
    lane_1_temp_ir = bricklet(BrickletTemperatureIRV2, uid="Tzv")
    lane_2_temp_ir = bricklet(BrickletTemperatureIRV2, uid="TzV")
    lane_3_temp_ir = bricklet(BrickletTemperatureIRV2, uid="TDe")
    uv_light       = bricklet(BrickletUVLightV2,       uid="MxN")
    # fmt: on


@attrs.define
class ReactorBoxSensorState:
    thermocouble_temp: Temperature | None
    ambient_light: Illuminance | None
    ambient_temperature: Temperature | None
    lane_ir_temp: list[Temperature | None]
    uv_index: UvIndex | None

    lane_sample_taken: list[bool | None]
    maintenance_mode: bool | None
    photobox_cable_control: bool | None

    @staticmethod
    def empty() -> "ReactorBoxSensorState":
        return ReactorBoxSensorState(
            thermocouble_temp=None,
            ambient_light=None,
            ambient_temperature=None,
            lane_ir_temp=[None, None, None],
            uv_index=None,
            lane_sample_taken=[None, None, None],
            maintenance_mode=None,
            photobox_cable_control=None,
        )

    def copy(self) -> Self:
        return attrs.evolve(self)


class ReactorBoxStatusLeds(StatusLeds):
    _CHAN_LED_STATE_LANE_1 = 3
    _CHAN_LED_STATE_LANE_2 = 4
    _CHAN_LED_STATE_LANE_3 = 5
    _CHAN_LED_UV_INSTALLED = 6
    _CHAN_LED_UV_WARNING = 7
    _CHAN_LED_EXPERIMENT_RUNNING = 8
    _CHAN_LED_WARNING_TEMP_LANE_1 = 9
    _CHAN_LED_WARNING_TEMP_LANE_2 = 10
    _CHAN_LED_WARNING_TEMP_LANE_3 = 11
    _CHAN_LED_WARNING_TEMP_AMBIENT = 12
    _CHAN_LED_WARNING_THERMOCOUPLE = 13

    _CHAN_INPUT_SAMPLE_LANE_1 = 0
    _CHAN_INPUT_SAMPLE_LANE_2 = 1
    _CHAN_INPUT_SAMPLE_LANE_3 = 2
    _CHAN_INPUT_MAINTENANCE_MODE = 14
    _CHAN_INPUT_PHOTOBOX_CABLE_CONTROL = 15

    def is_output_channel(self, channel: int) -> bool:
        return channel in {
            self._CHAN_LED_STATE_LANE_1,
            self._CHAN_LED_STATE_LANE_2,
            self._CHAN_LED_STATE_LANE_3,
            self._CHAN_LED_UV_INSTALLED,
            self._CHAN_LED_UV_WARNING,
            self._CHAN_LED_EXPERIMENT_RUNNING,
            self._CHAN_LED_WARNING_TEMP_LANE_1,
            self._CHAN_LED_WARNING_TEMP_LANE_2,
            self._CHAN_LED_WARNING_TEMP_LANE_3,
            self._CHAN_LED_WARNING_TEMP_AMBIENT,
            self._CHAN_LED_WARNING_THERMOCOUPLE,
        }

    led_state_lane_1 = StatusLeds.led(_CHAN_LED_STATE_LANE_1)
    led_state_lane_2 = StatusLeds.led(_CHAN_LED_STATE_LANE_2)
    led_state_lane_3 = StatusLeds.led(_CHAN_LED_STATE_LANE_3)
    led_uv_installed = StatusLeds.led(_CHAN_LED_UV_INSTALLED)
    led_uv_warning = StatusLeds.led(_CHAN_LED_UV_WARNING)
    led_experiment_running = StatusLeds.led(_CHAN_LED_EXPERIMENT_RUNNING)
    led_warning_temp_lane_1 = StatusLeds.led(_CHAN_LED_WARNING_TEMP_LANE_1)
    led_warning_temp_lane_2 = StatusLeds.led(_CHAN_LED_WARNING_TEMP_LANE_2)
    led_warning_temp_lane_3 = StatusLeds.led(_CHAN_LED_WARNING_TEMP_LANE_3)
    led_warning_temp_ambient = StatusLeds.led(_CHAN_LED_WARNING_TEMP_AMBIENT)
    led_warning_thermocouple = StatusLeds.led(_CHAN_LED_WARNING_THERMOCOUPLE)


class ReactorBox:
    bricklets: ReactorBoxBricklets
    sensor_period_ms: int

    sensors: ReactorBoxSensorState
    io_panel: ReactorBoxStatusLeds

    def __init__(
        self, bricklets: ReactorBoxBricklets, sensor_period_ms: int = 200
    ):
        self.bricklets = bricklets
        self.sensor_period_ms = sensor_period_ms

        self.sensors = ReactorBoxSensorState.empty()
        self.io_panel = ReactorBoxStatusLeds(bricklets.io)

    def initialize(self) -> Self:
        """Register the callbacks and set i/o direction."""

        # register callbacks for all sensors and the io bricklet
        self.bricklets.thermocouple.register_callback(
            BrickletThermocoupleV2.CALLBACK_TEMPERATURE,
            self._callback_thermocouple,
        )
        self.bricklets.thermocouple.set_temperature_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )

        self.io_panel.initialize()
        self.bricklets.io.register_callback(
            BrickletIO16V2.CALLBACK_INPUT_VALUE,
            self._callback_io16_single_input,
        )
        for channel in range(16):
            # We set value_has_to_change to True because
            # we don'- want to log this kind of information
            if self.io_panel.is_input_channel(channel):
                self.bricklets.io.set_input_value_callback_configuration(
                    channel, self.sensor_period_ms, True
                )

        self.bricklets.ambient_light.register_callback(
            BrickletAmbientLightV3.CALLBACK_ILLUMINANCE,
            self._callback_ambient_light,
        )
        self.bricklets.ambient_light.set_illuminance_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )

        self.bricklets.temperature.register_callback(
            BrickletTemperatureV2.CALLBACK_TEMPERATURE,
            self._callback_temperature,
        )
        self.bricklets.temperature.set_temperature_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )

        for sensor, lane in (
            (self.bricklets.lane_1_temp_ir, 0),
            (self.bricklets.lane_2_temp_ir, 1),
            (self.bricklets.lane_3_temp_ir, 2),
        ):
            sensor.register_callback(
                BrickletTemperatureIRV2.CALLBACK_OBJECT_TEMPERATURE,
                partial(self._callback_temperature_ir, lane),
            )
            sensor.set_object_temperature_callback_configuration(
                self.sensor_period_ms, False, "x", 0, 0
            )

        self.bricklets.uv_light.register_callback(
            BrickletUVLightV2.CALLBACK_UVI, self._callback_uv_light
        )
        self.bricklets.uv_light.set_uvi_callback_configuration(
            self.sensor_period_ms, False, "x", 0, 0
        )

        # set all status leds to their default value
        self.io_panel.led_state_lane_1 = LedState.LOW
        self.io_panel.led_state_lane_2 = LedState.LOW
        self.io_panel.led_state_lane_3 = LedState.LOW
        self.io_panel.led_uv_installed = LedState.LOW
        self.io_panel.led_uv_warning = LedState.LOW
        self.io_panel.led_experiment_running = LedState.LOW
        self.io_panel.led_warning_temp_lane_1 = LedState.HIGH
        self.io_panel.led_warning_temp_lane_2 = LedState.HIGH
        self.io_panel.led_warning_temp_lane_3 = LedState.HIGH
        self.io_panel.led_warning_temp_ambient = LedState.HIGH
        self.io_panel.led_warning_thermocouple = LedState.HIGH
        return self

    def _callback_thermocouple(self, hundreth_celsius: int) -> None:
        self.sensors.thermocouble_temp = Temperature.from_hundreth_celsius(
            hundreth_celsius
        )

    def _callback_io16_single_input(
        self,
        channel: int,
        changed: bool,
        value: bool,
    ) -> None:
        if channel == self.io_panel._CHAN_INPUT_SAMPLE_LANE_1:
            self.sensors.lane_sample_taken[0] = value
        elif channel == self.io_panel._CHAN_INPUT_SAMPLE_LANE_2:
            self.sensors.lane_sample_taken[1] = value
        elif channel == self.io_panel._CHAN_INPUT_SAMPLE_LANE_3:
            self.sensors.lane_sample_taken[2] = value
        elif channel == self.io_panel._CHAN_INPUT_MAINTENANCE_MODE:
            self.sensors.maintenance_mode = value
        elif channel == self.io_panel._CHAN_INPUT_PHOTOBOX_CABLE_CONTROL:
            self.sensors.photobox_cable_control = value

    def _callback_io16_all_inputs(
        self, changes: list[bool], vals: list[bool]
    ) -> None:
        for chan, (changed, val) in enumerate(zip(changes, vals, strict=True)):
            self._callback_io16_single_input(chan, changed, val)

    def _callback_ambient_light(self, hundreth_lux: int) -> None:
        self.sensors.ambient_light = Illuminance.from_hundreth_lux(hundreth_lux)

    def _callback_temperature(self, hundreth_celsius: int) -> None:
        self.sensors.ambient_temperature = Temperature.from_hundreth_celsius(
            hundreth_celsius
        )

    def _callback_temperature_ir(self, lane: int, tenth_celsius: int) -> None:
        self.sensors.lane_ir_temp[lane] = Temperature.from_tenth_celsius(
            tenth_celsius
        )

    def _callback_uv_light(self, tenth_uv_index: int) -> None:
        self.sensors.uv_index = UvIndex(tenth_uvi=tenth_uv_index)
