# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from time import sleep
from typing import Any, Self

import attrs
from tinkerforge.bricklet_ambient_light_v3 import BrickletAmbientLightV3
from tinkerforge.bricklet_industrial_dual_relay import (
    BrickletIndustrialDualRelay,
)
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge.bricklet_servo_v2 import BrickletServoV2
from tinkerforge.bricklet_temperature_ir_v2 import BrickletTemperatureIRV2
from tinkerforge.bricklet_temperature_v2 import BrickletTemperatureV2
from tinkerforge.bricklet_thermocouple_v2 import BrickletThermocoupleV2
from tinkerforge.bricklet_uv_light_v2 import BrickletUVLightV2
from tinkerforge.bricklet_voltage_current_v2 import BrickletVoltageCurrentV2
from tinkerforge.ip_connection import Device, IPConnection

from prcontrol.controller.measurements import Illuminance, Temperature, UvIndex

logger = logging.getLogger(__name__)


@attrs.frozen
class _BrickletRepr[T: Device]:
    """Represents a future bricklet."""

    kind: type[T]
    uid: str


def bricklet[T: Device](bricklet_type: type[T], *, uid: str) -> T:
    """Defines a bricklet in a `TinkerForgeComponents` subclass."""
    # We do some type trickery here.
    # mypy thinks that the fields of PhotoBox objects have the same type
    # as the fields of the PhotBox class.
    # We have to lie while defining the class fields
    # in order to have the right types on the object.
    # Objects with the correct types are swapped in, when initializing
    # in TinkerForgeComponents.__init__
    return _BrickletRepr[T](bricklet_type, uid)  #  type: ignore


class BrickletManager:
    """A system containing several TinkerForge bricklets.

    Convenience class for defining TinkerForge bricklets declaratively.
    All components must be reachable through a single IPConnection!

    Should probably be used in compination with TinkerForgeClient

    Example:
        class MyTinkerForgeBuild(BrickletManager):
            io_bricklet           = bricklet(BrickletIO16V2, uid="XYZ")
            termperature_bricklet = bricklet(BrickletTemperatureV2, uid="ABC")

        ipcon = IPConnection()
        my_bricklets = MyTinkerForgeBuild(ipcon)

        ipcon.connect("127.0.0.1", 4223)

        my_bricklets.io_bricklet.set_port_configuration(
            "a", 1 << 0, "o", False
        )

        ipcon.disconnect()

    """

    ipcon: IPConnection
    bricklet_from_repr: dict[_BrickletRepr[Any], Device]

    def __init__(self, ip_connection: IPConnection) -> None:
        self.ipcon = ip_connection
        self.bricklet_from_repr = dict()

        # replace all fields declared using bricklet(...) with
        # their initialized bricklets
        for field_name, value in vars(self.__class__).items():
            if not isinstance(value, _BrickletRepr):
                continue

            bricklet = value.kind(value.uid, ip_connection)
            self.bricklet_from_repr[value] = bricklet
            setattr(self, field_name, bricklet)


@contextmanager
def establish_connection(
    ipcon: IPConnection, host: str, port: int
) -> Iterator[None]:
    """Contextmanager to connect to a TinkerForge IPConnection

    Example:
        HOST, PORT = "localhost", 4223

        ipcon = IPConnection()
        io = BrickletIO16V2(UID, ipcon)

        with establish_connection(ipcon, HOST, PORT):
            print(io.get_value())
    """
    try:
        logger.info(f"Connecting to {host}:{port}.")
        ipcon.connect(host, port)
        logger.info("Connected.")
        yield
    finally:
        logger.info("Disconnecting from {self.host}:{self.port}.")
        ipcon.disconnect()


# fmt: off
class ReactorBoxBricklets(BrickletManager):
    thermocouple   = bricklet(BrickletThermocoupleV2,  uid="232m")
    io             = bricklet(BrickletIO16V2,          uid="231w")
    ambient_light  = bricklet(BrickletAmbientLightV3,  uid="25sN")
    temperature    = bricklet(BrickletTemperatureV2,   uid="ZQH")
    lane_1_temp_ir = bricklet(BrickletTemperatureIRV2, uid="Tzv")
    lane_2_temp_ir = bricklet(BrickletTemperatureIRV2, uid="TzV")
    lane_3_temp_ir = bricklet(BrickletTemperatureIRV2, uid="TDe")
    uv_light       = bricklet(BrickletUVLightV2,       uid="MxN")

class StromBoxBricklets(BrickletManager):
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
class ReactorBoxSensors:
    thermocouble_temp: Temperature | None
    ambient_light: Illuminance | None
    ambient_temperature: Temperature | None
    lane_ir_temp: list[Temperature | None]
    uv_index: UvIndex | None

    sample_lane_1: bool | None
    sample_lane_2: bool | None
    sample_lane_3: bool | None
    maintenance_mode: bool | None
    photobox_cable_control: bool | None

    @staticmethod
    def empty() -> "ReactorBoxSensors":
        return ReactorBoxSensors(
            thermocouble_temp=None,
            ambient_light=None,
            ambient_temperature=None,
            lane_ir_temp=[None, None, None],
            uv_index=None,
            sample_lane_1=None,
            sample_lane_2=None,
            sample_lane_3=None,
            maintenance_mode=None,
            photobox_cable_control=None,
        )


@attrs.define
class ReactorBoxClient:
    bricklets: ReactorBoxBricklets
    state: ReactorBoxSensors = attrs.field(factory=ReactorBoxSensors.empty)
    period_ms: int = 100

    _LED_STATE_LANE_1 = 3
    _LED_STATE_LANE_2 = 4
    _LED_STATE_LANE_3 = 5
    _LED_UV_INSTALLED = 6
    _LED_WARNING_UV = 7
    _LED_EXPERIMENT_RUNNING = 8
    _LED_WARNING_TEMP_LANE_1 = 9
    _LED_WARNING_TEMP_LANE_2 = 10
    _LED_WARNING_TEMP_LANE_3 = 11
    _LED_WARNING_TEMP_AMBIENT = 12
    _LED_WARNING_THERMOCOUPLE = 13

    _INPUT_SAMPLE_LANE_1 = 0
    _INPUT_SAMPLE_LANE_2 = 1
    _INPUT_SAMPLE_LANE_3 = 2
    _INPUT_MAINTENANCE_MODE = 14
    _INPUT_PHOTOBOX_CABLE_CONTROL = 15

    IO16_CONF = (  # channel, direction, initial # TODO use constants
        (0, "i", False),  # Sample Lane 1
        (1, "i", False),  # Sample Lane 2
        (2, "i", False),  # Sample Lane 3
        (3, "o", False),  # State Lane 1
        (4, "o", False),  # State Lane 1
        (5, "o", False),  # State Lane 1
        (6, "o", False),  # uv led installed
        (7, "o", False),  # uv measured
        (8, "o", False),  # experiment ongoing
        (9, "o", True),  # logic ir temp error lane 1
        (10, "o", True),  # logic ir temp error lane 2
        (11, "o", True),  # logic ir temp error lane 3
        (12, "o", True),  # logic ambient temp error (PhotoBox)
        (13, "o", True),  # logic thermocouple temp error
        (14, "i", False),  # maintenence mode
        (15, "i", False),  # cable control
    )

    def initialize(self) -> Self:
        """Register the callbacks and set i/o direction."""
        self.bricklets.thermocouple.register_callback(
            BrickletThermocoupleV2.CALLBACK_TEMPERATURE,
            self._callback_thermocouple,
        )
        self.bricklets.thermocouple.set_temperature_callback_configuration(
            self.period_ms, False, "x", 0, 0
        )

        self.bricklets.io.register_callback(
            BrickletIO16V2.CALLBACK_INPUT_VALUE,
            self._callback_single_input_io,
        )
        for chan, dir, val in self.IO16_CONF:
            self.bricklets.io.set_configuration(chan, dir, val)
            if dir == "i":
                # We set value_has_to_change to True because
                # we don't want to log this kind of information
                self.bricklets.io.set_input_value_callback_configuration(
                    chan, self.period_ms, True
                )

        self.bricklets.ambient_light.register_callback(
            BrickletAmbientLightV3.CALLBACK_ILLUMINANCE,
            self._callback_ambient_light,
        )
        self.bricklets.ambient_light.set_illuminance_callback_configuration(
            self.period_ms, False, "x", 0, 0
        )

        self.bricklets.temperature.register_callback(
            BrickletTemperatureV2.CALLBACK_TEMPERATURE,
            self._callback_temperature,
        )
        self.bricklets.temperature.set_temperature_callback_configuration(
            self.period_ms, False, "x", 0, 0
        )

        for sensor, lane in (
            (self.bricklets.lane_1_temp_ir, 0),
            (self.bricklets.lane_2_temp_ir, 1),
            (self.bricklets.lane_3_temp_ir, 2),
        ):
            sensor.register_callback(
                BrickletTemperatureIRV2.CALLBACK_OBJECT_TEMPERATURE,
                partial(self._callback_temp_object_ir, lane),
            )
            sensor.set_object_temperature_callback_configuration(
                self.period_ms, False, "x", 0, 0
            )

        self.bricklets.uv_light.register_callback(
            BrickletUVLightV2.CALLBACK_UVI,
            self._callback_uv_index,
        )
        self.bricklets.uv_light.set_uvi_callback_configuration(
            self.period_ms, False, "x", 0, 0
        )

        return self

    def uninitialize(self) -> Self:
        # TODO: maybe remove callbacks
        return self

    def _callback_thermocouple(self, hundreth_cel: int) -> None:
        self.state.thermocouble_temp = Temperature.from_hundreth_celsius(
            hundreth_cel
        )

    def _callback_single_input_io(
        self,
        channel: int,
        changed: bool,
        value: bool,
    ) -> None:
        if channel == self._INPUT_SAMPLE_LANE_1:
            ...  # TODO: Handle _INPUT_SAMPLE_LANE_1
        elif channel == self._INPUT_SAMPLE_LANE_2:
            ...  # TODO: Handle _INPUT_SAMPLE_LANE_2
        elif channel == self._INPUT_SAMPLE_LANE_3:
            ...  # TODO: Handle _INPUT_SAMPLE_LANE_3
        elif channel == self._INPUT_MAINTENANCE_MODE:
            ...  # TODO: Handle _INPUT_MAINTENANCE_MODE
        elif channel == self._INPUT_PHOTOBOX_CABLE_CONTROL:
            ...  # TODO: Handle _INPUT_PHOTOBOX_CABLE_CONTROL
        else:
            # This might be an output channel
            ...  # TODO: Handle Unknown channel

    def _callback_all_input_io(
        self, changes: list[bool], vals: list[bool]
    ) -> None:
        for chan, (changed, val) in enumerate(zip(changes, vals, strict=True)):
            self._callback_single_input_io(chan, changed, val)

    def _callback_ambient_light(self, hundreth_lux: int) -> None:
        self.state.ambient_light = Illuminance.from_hundreth_lux(hundreth_lux)

    def _callback_temperature(self, hundreth_cel: int) -> None:
        self.state.ambient_temperature = Temperature.from_hundreth_celsius(
            hundreth_cel
        )

    def _callback_temp_object_ir(self, lane: int, tenth_cel: int) -> None:
        self.state.lane_ir_temp[lane] = Temperature.from_tenth_celsius(
            tenth_cel
        )

    def _callback_uv_index(self, tenth_uvi: int) -> None:
        self.state.uv_index = UvIndex(tenth_uvi=tenth_uvi)


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 4223

    ipcon = IPConnection()
    bricklets = ReactorBoxBricklets(ipcon)
    client = ReactorBoxClient(bricklets)

    with establish_connection(ipcon, HOST, PORT):
        client.initialize()
        while 1:
            print(client.state)
            sleep(1)
