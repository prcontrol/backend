# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

from collections.abc import Iterator
from contextlib import contextmanager

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


@attrs.frozen
class _BrickletRepr[T: Device]:
    kind: type[T]
    uid: str


def bricklet[T](bricklet_type: type[T], *, uid: str) -> T:
    """Defines a bricklet in a `TinkerForgeComponents` subclass."""
    # We do some type trickery here.
    # mypy thinks that the fields of PhotoBox objects have the same type
    # as the fields of the PhotBox class.
    # We have to lie while defining the class fields
    # in order to have the right types on the object.
    # Objects with the correct types are swapped in, when initializing
    # in TinkerForgeComponents.__init__
    return _BrickletRepr[T](bricklet_type, uid)  #  type: ignore


class TinkerForgeComponents:
    """A system containing several TinkerForge components.

    Convenience Class for defining TinkerForge declaratively.
    All components must be reachable through a single IPConnection!

    Should probably be used in compination with TinkerForgeClient

    Example:
        class MyTinkerForgeBuild(TinkerForgeComponents):
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

    def __init__(self, ip_connection: IPConnection) -> None:
        for var, value in vars().items():
            if isinstance(value, _BrickletRepr):
                setattr(self, var, value.kind(value.uid, ip_connection))


@attrs.frozen
class TinkerForgeClient:
    """Thin wrapper around the TinkerForge IPConnection API.

    Example:
        class MyTinkerForgeBuild(TinkerForgeComponents):
            io_bricklet           = bricklet(BrickletIO16V2, uid="XYZ")
            termperature_bricklet = bricklet(BrickletTemperatureV2, uid="ABC")

        my_client = TinkerForgeClient("127.0.0.1", 1234)

        components = my_client.attach(MyTinkerForgeBuild)

        with my_client.connect():
            components.io_bricklet.set_port_configuration(
                "a", 1 << 0, "o", False
            )
    """

    host: str
    port: int

    channel: IPConnection = attrs.field(init=False, factory=IPConnection)

    def attach[T: TinkerForgeComponents](self, components: type[T]) -> T:
        return components(self.channel)

    @contextmanager
    def connect(self) -> Iterator[None]:
        try:
            self.channel.connect(self.host, self.port)
            yield
        finally:
            self.channel.disconnect()


# fmt: off
class PhotoBoxBricklets(TinkerForgeComponents):
    thermocouple   = bricklet(BrickletThermocoupleV2,  uid="232m")
    io             = bricklet(BrickletIO16V2,          uid="231w")
    ambient_light  = bricklet(BrickletAmbientLightV3,  uid="25sN")
    temperature    = bricklet(BrickletTemperatureV2,   uid="ZQH")
    lane_1_temp_ir = bricklet(BrickletTemperatureIRV2, uid="Tzv")
    lane_2_temp_ir = bricklet(BrickletTemperatureIRV2, uid="TzV")
    lane_3_temp_ir = bricklet(BrickletTemperatureIRV2, uid="TDe")
    uv_light       = bricklet(BrickletUVLightV2,       uid="MxN")

class StromBoxBricklets(TinkerForgeComponents):
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
