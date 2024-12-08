# mypy: disable-error-code=import-untyped
# We dont have typing information for tinkerforge unfurtunately :(

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from typing import Any

import attrs
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge.ip_connection import Device, IPConnection

logger = logging.getLogger(__name__)


class LedState(Enum):
    UNDEFINED = -1
    LOW = 0
    HIGH = 1
    BLINK_SLOW = 500
    BLINK_FAST = 200


@attrs.frozen
class _BrickletRepr[T: Device]:
    """Represents a future bricklet."""

    kind: type[T]
    uid: str


def bricklet[T: Device](bricklet_type: type[T], *, uid: str) -> T:
    """Defines a bricklet in a `BrickletManager` subclass."""
    # We do some type trickery here.
    # mypy thinks that the fields of PhotoBox objects have the same type
    # as the fields of the PhotBox class.
    # We have to lie while defining the class fields
    # in order to have the right types on the object.
    # Objects with the correct types are swapped in, when initializing
    # in BrickletManager.__init__
    return _BrickletRepr[T](bricklet_type, uid)  #  type: ignore


class BrickletManager:
    """A system containing several TinkerForge bricklets.

    Convenience class for defining TinkerForge bricklets declaratively.
    All components must be reachable through a single IPConnection!

    Should probably be used in compination with TinkerForgeClient

    Example:
        class MyTinkerForgeBuild(BrickletManager):
            io_bricklet = bricklet(BrickletIO16V2, uid="XYZ")
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


class StatusLeds(ABC):
    """Convenience class for the I/O-16 bricklet

    This class is for namespacing and easy control of LEDs using properties.
    """

    _bricklet: BrickletIO16V2
    _blinking_io16_channels: dict[int, int]

    def __init__(self, bricklet: BrickletIO16V2):
        super().__init__()
        self._bricklet = bricklet
        self._blinking_io16_channels = dict()

    def initialize(self) -> None:
        """Registers the necessary callbacks for blinking LEDs on IO bricklets
        Sets channels to input/output accorting to `is_output_channel`.
        """

        for channel in range(16):
            direction = "i" if self.is_input_channel(channel) else "o"
            self._bricklet.set_configuration(channel, direction, True)

        self._bricklet.register_callback(
            BrickletIO16V2.CALLBACK_MONOFLOP_DONE,
            self._callback_io_16_led_blink,
        )

    @staticmethod
    def led(channel: int) -> LedState:
        """Creates a property for an Led.

        The field will automatically set the TinkerForge IO16-Led to the
        supplied value.
        """
        value_box: list[LedState] = [LedState.UNDEFINED]  # use a list as a box

        def _set_led(self: "StatusLeds", new_value: LedState) -> None:
            if new_value == value_box[0]:
                return
            value_box[0] = new_value
            if (
                new_value == LedState.BLINK_SLOW
                or new_value == LedState.BLINK_FAST
            ):
                self._blink_led(channel, new_value.value)
            elif new_value == LedState.HIGH:
                self._blink_stop_led(channel)
                self._set_led(channel, True)
            elif new_value == LedState.LOW:
                self._blink_stop_led(channel)
                self._set_led(channel, False)

        def _get_led(_self: "StatusLeds") -> LedState:
            return value_box[0]

        # type trickery: we lie about the return value
        # because property attaches the necessary getters and setters
        return property(_get_led, _set_led)  # type: ignore

    def is_input_channel(self, channel: int) -> bool:
        return not self.is_output_channel(channel)

    @abstractmethod
    def is_output_channel(self, channel: int) -> bool:
        raise NotImplementedError("Abstractmethod must be overwritten")

    def _callback_io_16_led_blink(self, channel: int, val: bool) -> None:
        """A monoflop callback for io16 that oscilates `channel_to_blink`"""
        duration_ms = self._blinking_io16_channels.get(channel)
        if duration_ms is None:
            return
        self._bricklet.set_monoflop(channel, val, duration_ms)

    def _set_led(self, channel: int, value: bool) -> None:
        assert self.is_output_channel(channel)
        self._bricklet.set_selected_value(channel, value)

    def _blink_led(self, channel: int, period_ms: int) -> None:
        assert self.is_output_channel(channel)
        self._blinking_io16_channels[channel] = period_ms
        # Bootstrap blinking
        self._callback_io_16_led_blink(channel, True)

    def _blink_stop_led(self, channel: int) -> None:
        if channel in self._blinking_io16_channels:
            self._blinking_io16_channels.pop(channel)
