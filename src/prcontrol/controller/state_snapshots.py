from attrs import frozen

from prcontrol.controller.configuration import JSONSeriablizable
from prcontrol.controller.controller import ControllerState
from prcontrol.controller.power_box import PowerBoxSensorState
from prcontrol.controller.reactor_box import ReactorBoxSensorState


@frozen
class ReactorBoxWsData(JSONSeriablizable):
    thermocouple_temp: float
    ambient_light: float
    ambient_temperature: float
    lane_1_ir_temp: float
    lane_2_ir_temp: float
    lane_3_ir_temp: float
    uv_index: float
    lane_1_sample_taken: bool
    lane_2_sample_taken: bool
    lane_3_sample_taken: bool
    maintenance_mode: bool
    cable_control: bool

    # fmt: off
    @staticmethod
    def from_state(s: ReactorBoxSensorState) -> "ReactorBoxWsData":
        return ReactorBoxWsData(
            thermocouple_temp   =s.thermocouble_temp.celsius,
            ambient_light       =s.ambient_light.lux,
            ambient_temperature =s.ambient_temperature.celsius,
            lane_1_ir_temp      =s.lane_1_ir_temp.celsius,
            lane_2_ir_temp      =s.lane_2_ir_temp.celsius,
            lane_3_ir_temp      =s.lane_3_ir_temp.celsius,
            uv_index            =s.uv_index.uvi,
            lane_1_sample_taken =s.lane_1_sample_taken,
            lane_2_sample_taken =s.lane_2_sample_taken,
            lane_3_sample_taken =s.lane_3_sample_taken,
            maintenance_mode    =s.maintenance_mode,
            cable_control       =s.cable_control,
        )
    # fmt: on


@frozen
class PowerBoxWsData(JSONSeriablizable):
    abmient_temperature: float
    voltage_total: float
    current_total: float
    voltage_lane_1_front: float
    voltage_lane_1_back: float
    voltage_lane_2_front: float
    voltage_lane_2_back: float
    voltage_lane_3_front: float
    voltage_lane_3_back: float
    current_lane_1_front: float
    current_lane_1_back: float
    current_lane_2_front: float
    current_lane_2_back: float
    current_lane_3_front: float
    current_lane_3_back: float

    powerbox_lid: str
    reactorbox_lid: str
    led_in_lane_1_front_and_vial: bool
    led_in_lane_1_back: bool
    led_in_lane_2_front_and_vial: bool
    led_in_lane_2_back: bool
    led_in_lane_3_front_and_vial: bool
    led_in_lane_3_back: bool
    water_detected: bool
    cable_control: bool

    # fmt: off
    @staticmethod
    def from_state(s: PowerBoxSensorState) -> "PowerBoxWsData":
        return PowerBoxWsData(
            abmient_temperature          =s.abmient_temperature.celsius,
            voltage_total                =s.voltage_total.volts,
            current_total                =s.current_total.ampere,
            voltage_lane_1_front         =s.voltage_lane_1_front.volts,
            voltage_lane_1_back          =s.voltage_lane_1_back.volts,
            voltage_lane_2_front         =s.voltage_lane_2_front.volts,
            voltage_lane_2_back          =s.voltage_lane_2_back.volts,
            voltage_lane_3_front         =s.voltage_lane_3_front.volts,
            voltage_lane_3_back          =s.voltage_lane_3_back.volts,
            current_lane_1_front         =s.current_lane_1_front.ampere,
            current_lane_1_back          =s.current_lane_1_back.ampere,
            current_lane_2_front         =s.current_lane_2_front.ampere,
            current_lane_2_back          =s.current_lane_2_back.ampere,
            current_lane_3_front         =s.current_lane_3_front.ampere,
            current_lane_3_back          =s.current_lane_3_back.ampere,
            powerbox_lid                 =s.powerbox_lid.name,
            reactorbox_lid               =s.reactorbox_lid.name,
            led_in_lane_1_front_and_vial =s.led_installed_lane_1_front_and_vial,
            led_in_lane_1_back           =s.led_installed_lane_1_back,
            led_in_lane_2_front_and_vial =s.led_installed_lane_2_front_and_vial,
            led_in_lane_2_back           =s.led_installed_lane_2_back,
            led_in_lane_3_front_and_vial =s.led_installed_lane_3_front_and_vial,
            led_in_lane_3_back           =s.led_installed_lane_3_back,
            water_detected               =s.water_detected,
            cable_control                =s.cable_control,
        )
    # fmt: on


@frozen
class ControllerStateWsData(JSONSeriablizable):
    reactor_box_connected: bool
    power_box_connected: bool

    sample_lane_1: bool
    sample_lane_2: bool
    sample_lane_3: bool

    exp_running_lane_1: bool
    exp_running_lane_2: bool
    exp_running_lane_3: bool

    uv_installed: bool

    ambient_temp_status: str
    IR_temp_1_threshold_status: str
    IR_temp_2_threshold_status: str
    IR_temp_3_threshold_status: str
    thermocouple_theshold_status: str

    reactor_box_state: ReactorBoxWsData
    power_box_state: PowerBoxWsData

    @staticmethod
    def from_state(s: ControllerState) -> "ControllerStateWsData":
        return ControllerStateWsData(
            reactor_box_connected=s.reactor_box_connected,
            power_box_connected=s.power_box_connected,
            sample_lane_1=s.sample_lane_1,
            sample_lane_2=s.sample_lane_2,
            sample_lane_3=s.sample_lane_3,
            exp_running_lane_1=s.exp_running_lane_1,
            exp_running_lane_2=s.exp_running_lane_2,
            exp_running_lane_3=s.exp_running_lane_3,
            uv_installed=s.uv_installed,
            ambient_temp_status=s.ambient_temp_status.name,
            IR_temp_1_threshold_status=s.IR_temp_1_threshold_status.name,
            IR_temp_2_threshold_status=s.IR_temp_2_threshold_status.name,
            IR_temp_3_threshold_status=s.IR_temp_3_threshold_status.name,
            thermocouple_theshold_status=s.thermocouple_theshold_status.name,
            reactor_box_state=ReactorBoxWsData.from_state(s.reactor_box_state),
            power_box_state=PowerBoxWsData.from_state(s.power_box_state),
        )
