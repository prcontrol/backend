from typing import Self

from tinkerforge.ip_connection import IPConnection  #  type: ignore

from prcontrol.controller.power_box import (
    PowerBox,
    PowerBoxBricklets,
)
from prcontrol.controller.reactor_box import ReactorBox, ReactorBoxBricklets


class Controller:
    reactor_ipcon: IPConnection
    reactor_box: ReactorBox
    power_ipcon: IPConnection
    power_box: PowerBox

    REACTOR_BOX_SENSOR_PERIOD_MS = 200
    POWER_BOX_SENSOR_PERIOD_MS = 200

    def __init__(self) -> None:
        self.reactor_ipcon = IPConnection()
        self.power_ipcon = IPConnection()
        reactor_box_bricklets = ReactorBoxBricklets(self.reactor_ipcon)
        power_box_bricklets = PowerBoxBricklets(self.power_ipcon)

        self.reactor_box = ReactorBox(
            reactor_box_bricklets, self.REACTOR_BOX_SENSOR_PERIOD_MS
        )
        self.power_box = PowerBox(
            power_box_bricklets, self.POWER_BOX_SENSOR_PERIOD_MS
        )

    def initialize(self) -> Self:
        """Initializes controller. Requires established ip connection."""
        self.reactor_box.initialize()
        self.power_box.initialize()
        return self

    def connect(self) -> Self:
        raise NotImplementedError()

    def check_connection(self) -> Self:
        raise NotImplementedError()

    def disconnect(self) -> Self:
        raise NotImplementedError()
