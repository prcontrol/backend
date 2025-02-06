# This file contains all the attrs classes, which represent all the diffrent
# JSON Files for hardware configuration of the reactor

import json
from abc import ABC, abstractmethod

import attrs
from cattr import structure, unstructure


class JSONSeriablizable:
    @classmethod
    def from_json[T](cls: type[T], json_string: str | bytes | bytearray) -> T:
        return structure(json.loads(json_string), cls)

    def to_json(self) -> str:
        return json.dumps(unstructure(self))


class ConfigObject(ABC, JSONSeriablizable):
    @abstractmethod
    def get_description(self) -> str:
        raise NotImplementedError("get_description must be overwritten!")

    @abstractmethod
    def get_uid(self) -> int:
        raise NotImplementedError("get_uid must be overwritten!")


@attrs.frozen(slots=True)
class EmmissionPair(JSONSeriablizable):
    wavelength: int
    intensity: float


@attrs.frozen(slots=True)
class EventPair(JSONSeriablizable):
    timepoint: float
    event: str


@attrs.frozen(slots=True)
class MeasuredDataAtTimePoint(JSONSeriablizable):
    timepoint: float
    temperature_thermocouple: float
    ambient_temp_strombox: float
    ambient_temp_photobox: float
    voltage_lane1: float
    current_lane1: float
    ir_temp_lane1: float
    voltage_lane2: float
    current_lane2: float
    ir_temp_lane2: float
    voltage_lane3: float
    current_lane3: float
    ir_temp_lane3: float
    uv_index: float
    ambient_light: float


@attrs.frozen(slots=True)
class LED(ConfigObject):
    uid: int
    name: str
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
    emission_spectrum: tuple[EmmissionPair, ...]
    emission_spectrum_recorded_on: str

    def get_description(self) -> str:
        if self.name:
            return self.name
        return f"max wavelength: {self.max_wavelength}"

    def get_uid(self) -> int:
        return self.uid

    def is_uv(self) -> bool:
        return self.min_wavelength <= 400


@attrs.frozen(slots=True)
class TinkerforgeBricklet(ConfigObject):
    uid: int  # TODO: we have a problem here. TinkerForge uids may be literal.
    name: str
    version: str
    defective: bool
    date_bought: str

    def get_description(self) -> str:
        return f"self.name({self.uid})"

    def get_uid(self) -> int:
        return self.uid


@attrs.frozen(slots=True)
class HardwareConfig(ConfigObject):
    uid: int
    name: str
    tinkerforge_bricklets: tuple[TinkerforgeBricklet, ...]
    software_version: str
    date: str
    default_distance_led_vial: float
    default_position_thermocouple: str
    default_pwm_channels: tuple[float, ...]
    default_temperature_threshold: float
    default_uv_threshold: float
    default_sensor_query_interval: float
    default_reaction_vessel_volume: float

    def get_description(self) -> str:
        return self.name

    def get_uid(self) -> int:
        return self.uid


@attrs.frozen(slots=True)
class ExperimentTemplate(ConfigObject):
    uid: int
    name: str
    date: str
    config_file: HardwareConfig
    active_lane: int
    led_front: LED
    led_front_intensity: int
    led_front_distance_to_vial: float
    led_front_exposure_time: float
    led_back: LED
    led_back_intensity: int
    led_back_distance_to_vial: float
    led_back_exposure_time: float
    time_points_sample_taking: tuple[int, ...]
    position_thermocouple: str

    def get_description(self) -> str:
        return self.name

    def get_uid(self) -> int:
        return self.uid


@attrs.frozen(slots=True)
class Experiment(ConfigObject):
    uid: int
    name: str
    lab_notebook_entry: str
    date: str
    config_file: HardwareConfig
    active_lane: int
    led_front: LED
    led_front_intensity: int
    led_front_distance_to_vial: float
    led_front_exposure_time: float
    led_back: LED
    led_back_intensity: int
    led_back_distance_to_vial: float
    led_back_exposure_time: float
    time_points_sample_taking: tuple[int, ...]
    size_sample: float
    parallel_experiments: tuple[int, ...]
    position_thermocouple: str
    error_occured: bool
    experiment_cancelled: bool
    event_log: tuple[EventPair, ...]
    measured_data: tuple[MeasuredDataAtTimePoint, ...]

    def get_description(self) -> str:
        return self.name

    def get_uid(self) -> int:
        return self.uid
