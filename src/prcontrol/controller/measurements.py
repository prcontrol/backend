from attrs import field, frozen


@frozen
class Temperature:
    hundredth_celsius: int = field(kw_only=True)

    @staticmethod
    def from_celsius(temperature: float | int) -> "Temperature":
        return Temperature(hundredth_celsius=round(temperature * 100.0))

    @staticmethod
    def from_tenth_celsius(temperature: float | int) -> "Temperature":
        return Temperature(hundredth_celsius=round(temperature * 10.0))

    @staticmethod
    def from_hundreth_celsius(temperature: float | int) -> "Temperature":
        return Temperature(hundredth_celsius=round(temperature * 1.0))

    @property
    def celsius(self) -> float:
        return self.hundredth_celsius / 100.0


@frozen
class Illuminance:
    hudreth_lux: int = field(kw_only=True)

    @staticmethod
    def from_lux(illuminance: float | int) -> "Illuminance":
        return Illuminance(hudreth_lux=round(illuminance * 100.0))

    @staticmethod
    def from_hundreth_lux(illuminance: float | int) -> "Illuminance":
        return Illuminance(hudreth_lux=round(illuminance))

    @property
    def lux(self) -> float:
        return self.hudreth_lux / 100.0


@frozen
class UvIndex:
    tenth_uvi: int = field(kw_only=True)

    @staticmethod
    def from_tenth_uvi(uvi: float | int) -> "UvIndex":
        return UvIndex(tenth_uvi=round(uvi))

    @property
    def uvi(self) -> float:
        return self.tenth_uvi / 10.0


@frozen
class Voltage: ...  # TODO


@frozen
class Current: ...  # TODO
