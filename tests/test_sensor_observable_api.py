from typing import Self

import attrs

from prcontrol.controller.device import (
    SensorObserver,
    sensor_observer_callback_dispatcher,
)
from prcontrol.controller.measurements import Temperature


@attrs.define(on_setattr=sensor_observer_callback_dispatcher)
class SensorState:
    button_pressed: bool
    temp: Temperature

    callback: SensorObserver[Self] = attrs.field(
        default=None,
        on_setattr=attrs.setters.NO_OP,
        eq=False,
    )


def test_simple_callback_dispatcher():
    received_callbacks = []

    def cb(old, *rest):
        old = attrs.evolve(old)  # we need to take a snapshot
        received_callbacks.append((old, *rest))

    s = SensorState(False, Temperature.from_celsius(0), callback=cb)

    s.button_pressed = True
    s.temp = Temperature.from_celsius(1)

    fields = attrs.fields(SensorState)

    assert received_callbacks == [
        (
            SensorState(False, Temperature.from_celsius(0)),
            SensorState(True, Temperature.from_celsius(0)),
            fields.button_pressed,
            True,
        ),
        (
            SensorState(True, Temperature.from_celsius(0)),
            SensorState(True, Temperature.from_celsius(1)),
            fields.temp,
            Temperature.from_celsius(1),
        ),
    ]


def test_no_callback_specified():
    s = SensorState(False, Temperature.from_celsius(0))

    s.button_pressed = True
    s.temp = Temperature.from_celsius(1)

    assert s == SensorState(True, Temperature.from_celsius(1))


def test_callback_lst():
    def cb2(*args): ...
    def cb1(*args): ...

    s = SensorState(False, Temperature.from_celsius(0), callback=[cb1, cb2])

    s.button_pressed = True
    s.temp = Temperature.from_celsius(1)

    assert s == SensorState(True, Temperature.from_celsius(1))
