import json
from typing import Any, Self

from attrs import frozen
from flask import Flask, Request, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS
from flask_socketio import SocketIO

from prcontrol.controller.config_manager import ConfigFolder, ConfigManager
from prcontrol.controller.configuration import JSONSeriablizable
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
        print(request)
        file = request.files["file"]
        if not file:
            return "post expects a file", 400
        folder.add_from_json(file.stream.read())
        return "success", 200

    elif request.method == "GET":
        _uid = request.args.get("uid")
        if not _uid:
            return "get expects argument uid", 400

        try:
            uid = int(_uid)
        except ValueError:
            return "uid must be integral", 400

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
            return "uid must be integral", 400

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
    lane_ir_temp1: float
    lane_ir_temp2: float
    lane_ir_temp3: float
    uv_index: float

    lane_sample_taken1: bool
    lane_sample_taken2: bool
    lane_sample_taken3: bool

    maintenance_mode: bool
    photobox_cable_control: bool


    @staticmethod
    def from_state(state: ReactorBoxSensorState) -> "ReactorBoxWsData":
        return ReactorBoxWsData(
            thermocouple_temp=state.thermocouple_temp.celsius,
            ambient_light=state.ambient_light.lux,
            ambient_temperature=state.ambient_temperature.celsius,
            lane_ir_temp1=state.lane_ir_temp[0].celsius,
            lane_ir_temp2=state.lane_ir_temp[1].celsius,
            lane_ir_temp3=state.lane_ir_temp[2].celsius,
            uv_index=state.uv_index.uvi,
            lane_sample_taken1=state.lane_sample_taken[0],
            lane_sample_taken2=state.lane_sample_taken[1],
            lane_sample_taken3=state.lane_sample_taken[2],
            maintenance_mode=state.maintenance_mode,
            photobox_cable_control=state.photobox_cable_control,

        )
@frozen
class PowerBoxWsData(JSONSeriablizable):

    abmient_temperature: float
    voltage_total: float
    current_total: float
    voltage_lane1: float
    voltage_lane2: float
    voltage_lane3: float
    current_lane1: float
    current_lane2: float
    current_lane3: float

    @staticmethod
    def from_state(state: PowerBoxSensorStates) -> "PowerBoxWsData":
        return PowerBoxWsData(
            abmient_temperature=state.abmient_temperature.celsius,
            voltage_total=state.voltage_total.volts,
            current_total=state.current_total.ampere,
            voltage_lane1=state.voltage_lane[0].volts,
            voltage_lane2=state.voltage_lane[1].volts,
            voltage_lane3=state.voltage_lane[2].volts,
            current_lane1=state.current_lane[0].ampere,
            current_lane2=state.current_lane[1].ampere,
            current_lane3=state.current_lane[3].ampere,
        )

@frozen
class StateWsData:
    reactor_box: ReactorBoxWsData
    power_box: PowerBoxWsData

    @staticmethod
    def from_sensor_states(state_reactor: ReactorBoxSensorState,
     state_power: PowerBoxSensorStates) -> "StateWsData":
        return StateWsData(
            reactor_box=ReactorBoxWsData.from_state(state_reactor),
            power_box=PowerBoxWsData.from_state(state_power)
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
        #data = reactor_box.sensors.to_json()
        data_r= ReactorBoxSensorState.empty()
        data_p= PowerBoxSensorStates.empty()

        socketio.emit("pcr_data",
                    {"event": "update", "data":
                        StateWsData.from_sensor_states(data_r, data_p)})

        socketio.sleep(1)

"""Flask-SocketIO socketio.start_background_task() und socketio.sleep()
   blockieren den Event-Loop nicht """





