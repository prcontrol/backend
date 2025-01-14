import json
from typing import Any

from attrs import frozen
from flask import Flask, Request, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS
from flask_socketio import SocketIO

from prcontrol.controller.config_manager import ConfigFolder, ConfigManager
from prcontrol.controller.configuration import JSONSeriablizable
from prcontrol.controller.measurements import Current, Temperature
from prcontrol.controller.power_box import PowerBoxSensorStates
from prcontrol.controller.reactor_box import ReactorBoxSensorState

app = Flask(__name__)
CORS(app)

config_manager = ConfigManager()

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/", methods=["GET"])
def index() -> ResponseReturnValue:
    return "<h1> Hello World! </h1>", 200


@app.route("/led", methods=["GET", "POST", "DELETE"])
def led() -> ResponseReturnValue:
    return handle_config_api(config_manager.leds, request)


@app.route("/bricklet", methods=["GET"])
def bricklet() -> ResponseReturnValue:
    return handle_config_api(config_manager.bricklets, request)


@app.route("/exp_tmp", methods=["GET", "POST", "DELETE"])
def exp_tmp() -> ResponseReturnValue:
    return handle_config_api(config_manager.experiment_templates, request)


@app.route("/config", methods=["GET", "POST", "DELETE"])
def config() -> ResponseReturnValue:
    return handle_config_api(config_manager.configs, request)


@app.route("/experiment", methods=["GET", "DELETE"])
def experiment() -> ResponseReturnValue:
    return handle_config_api(config_manager.experiments, request)


@app.route("/list_led", methods=["GET"])
def list_leds() -> ResponseReturnValue:
    return handle_list_api(config_manager.leds, request)


@app.route("/list_bricklet", methods=["GET"])
def list_bricklets() -> ResponseReturnValue:
    return handle_list_api(config_manager.bricklets, request)


@app.route("/list_exp_tmp", methods=["GET"])
def list_exp_tmps() -> ResponseReturnValue:
    return handle_list_api(config_manager.experiment_templates, request)


@app.route("/list_config", methods=["GET"])
def list_configs() -> ResponseReturnValue:
    return handle_list_api(config_manager.configs, request)


@app.route("/list_experiment", methods=["GET"])
def list_experiments() -> ResponseReturnValue:
    return handle_list_api(config_manager.experiments, request)


def handle_config_api(
    folder: ConfigFolder[Any], request: Request
) -> ResponseReturnValue:
    if request.method == "POST":
        try:
            file = request.files["json_file"]
            folder.add_from_json(file.stream.read())
            return "success", 200
        except KeyError:
            return "post expects a json_file", 400

    elif request.method == "GET":
        _uid = request.args.get("uid")
        if not _uid:
            return "get expects argument uid", 400

        try:
            uid = int(_uid)
        except ValueError:
            return "uid must be integer", 400

        try:
            config = folder.load(uid)
            return config.to_json(), 200
        except FileNotFoundError:
            return "file does not exist", 400

    elif request.method == "DELETE":
        _uid = request.args.get("uid")
        if not _uid:
            return "delete expects argument uid", 400

        try:
            uid = int(_uid)
        except ValueError:
            return "uid must be integer", 400

        folder.delete(uid)
        return "success", 200

    raise RuntimeError("We should never get here")


def handle_list_api(
    folder: ConfigFolder[Any], request: Request
) -> ResponseReturnValue:
    assert request.method == "GET"

    list_of_configs = [
        {
            "uid": config_object.get_uid(),
            "description": config_object.get_description(),
        }
        for config_object in folder.load_all()
    ]

    return json.dumps({"results": list_of_configs}), 200


# Websocket part:


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
    photobox_cable_control: bool

    @staticmethod
    def from_state(state: ReactorBoxSensorState) -> "ReactorBoxWsData":
        return ReactorBoxWsData(
            thermocouple_temp=state.thermocouble_temp.celsius,
            ambient_light=state.ambient_light.lux,
            ambient_temperature=state.ambient_temperature.celsius,
            lane_1_ir_temp=state.lane_1_ir_temp.celsius,
            lane_2_ir_temp=state.lane_2_ir_temp.celsius,
            lane_3_ir_temp=state.lane_3_ir_temp.celsius,
            uv_index=state.uv_index.uvi,
            lane_1_sample_taken=state.lane_1_sample_taken,
            lane_2_sample_taken=state.lane_2_sample_taken,
            lane_3_sample_taken=state.lane_3_sample_taken,
            maintenance_mode=state.maintenance_mode,
            photobox_cable_control=state.photobox_cable_control,
        )


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

    powerbox_closed: bool
    reactorbox_closed: bool
    led_installed_lane_1_front_and_vial: bool
    led_installed_lane_1_back: bool
    led_installed_lane_2_front_and_vial: bool
    led_installed_lane_2_back: bool
    led_installed_lane_3_front_and_vial: bool
    led_installed_lane_3_back: bool
    water_detected: bool

    @staticmethod
    def from_state(state: PowerBoxSensorStates) -> "PowerBoxWsData":
        return PowerBoxWsData(
            abmient_temperature=state.abmient_temperature.celsius,
            voltage_total=state.voltage_total.volts,
            current_total=state.current_total.ampere,
            voltage_lane_1_front=state.voltage_lane_1_front.volts,
            voltage_lane_1_back=state.voltage_lane_1_back.volts,
            voltage_lane_2_front=state.voltage_lane_2_front.volts,
            voltage_lane_2_back=state.voltage_lane_2_back.volts,
            voltage_lane_3_front=state.voltage_lane_3_front.volts,
            voltage_lane_3_back=state.voltage_lane_3_back.volts,
            current_lane_1_front=state.current_lane_1_front.ampere,
            current_lane_1_back=state.current_lane_1_back.ampere,
            current_lane_2_front=state.current_lane_2_front.ampere,
            current_lane_2_back=state.current_lane_2_back.ampere,
            current_lane_3_front=state.current_lane_3_front.ampere,
            current_lane_3_back=state.current_lane_3_back.ampere,
            powerbox_closed=state.powerbox_closed,
            reactorbox_closed=state.reactorbox_closed,
            led_installed_lane_1_front_and_vial=state.led_installed_lane_1_front_and_vial,
            led_installed_lane_1_back=state.led_installed_lane_1_back,
            led_installed_lane_2_front_and_vial=state.led_installed_lane_2_front_and_vial,
            led_installed_lane_2_back=state.led_installed_lane_2_back,
            led_installed_lane_3_front_and_vial=state.led_installed_lane_3_front_and_vial,
            led_installed_lane_3_back=state.led_installed_lane_3_back,
            water_detected=state.water_detected,
        )


@frozen
class StateWsData(JSONSeriablizable):
    reactor_box: ReactorBoxWsData
    power_box: PowerBoxWsData

    @staticmethod
    def from_sensor_states(
        state_reactor: ReactorBoxSensorState, state_power: PowerBoxSensorStates
    ) -> "StateWsData":
        return StateWsData(
            reactor_box=ReactorBoxWsData.from_state(state_reactor),
            power_box=PowerBoxWsData.from_state(state_power),
        )


@socketio.on("connect")
def handle_connect() -> None:
    socketio.start_background_task(target=send_data)
    print("WebSocket-Client verbunden!")


@socketio.on("disconnect")
def handle_disconnect() -> None:
    print("WebSocket-Client getrennt!")


def send_data() -> None:
    while True:
        data_r = ReactorBoxSensorState.empty()
        data_p = PowerBoxSensorStates.empty()

        # set example values for testing
        data_r.ambient_temperature = Temperature.from_celsius(20)
        data_p.current_total = Current.from_milli_amps(2222)

        socketio.emit(
            "pcrdata",
            {"data": StateWsData.from_sensor_states(data_r, data_p).to_json()},
        )
        socketio.sleep(1)
