import json
from abc import ABC, abstractmethod

import attrs
from cattr import structure, unstructure


class JSONSeriablizable(ABC):
    @classmethod
    @abstractmethod
    def from_json[T](cls: type[T], json_string: str | bytes | bytearray) -> T:
        return structure(json.loads(json_string), cls)

    @abstractmethod
    def to_json(self) -> str:
        return json.dumps(unstructure(self))


@attrs.frozen(slots=True)
class EmmissionPair(JSONSeriablizable):
    wavelength: int
    intensity: float


@attrs.frozen(slots=True)
class LED(JSONSeriablizable):
    uid: int
    fwhm: int
    max_of_emission: int
    min_wavelength: int
    max_wavelength: int
    color: str
    max_current: int
    manufacturer_id: int
    order_id: int
    date_soldering: str
    soldered_by: str
    operating_time: float
    defect: bool
    emission_spectrum: tuple[EmmissionPair, EmmissionPair]
    emission_spectrum_recorded_on: str
