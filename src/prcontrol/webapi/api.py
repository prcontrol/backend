import json
import logging
from time import sleep
from typing import Any

from flask import Flask, Request, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS
from flask_socketio import SocketIO

from prcontrol.controller.common import LedLane
from prcontrol.controller.config_manager import ConfigFolder, ConfigManager
from prcontrol.controller.controller import (
    Controller,
    ControllerConfig,
    TfEndpoint,
)
from prcontrol.controller.state_snapshots import ControllerStateWsData

config_manager: ConfigManager
controller: Controller

logger = logging.getLogger(__name__)


def create_app(
    reactor_box_endpoint: TfEndpoint | tuple[str, int],
    power_box_endpoint: TfEndpoint | tuple[str, int],
    mock: bool = False,
) -> tuple[Flask, SocketIO, ConfigManager, Controller]:
    global config_manager, controller
    app = Flask(__name__)
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")

    config_manager = ConfigManager()

    controller = Controller(
        reactor_box=reactor_box_endpoint,
        power_box=power_box_endpoint,
        config_manager=config_manager,
        config=ControllerConfig.default_values(),
    )

    if not mock:
        logger.info("Connecting to controller.")
        controller.connect()
        logger.debug("Connected.")
        sleep(1.0)
        controller.reactor_box.initialize()
        logger.debug("Initialized reactor box")
        sleep(0.1)
        controller.power_box.initialize()
        sleep(0.1)
        controller.power_box.reset_leds()
        logger.debug("Initialized power box")

        sleep(0.5)
        controller.initialize()

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

    # Routes for Experiments

    @app.route("/start_experiment", methods=["GET"])
    def start_experiment() -> ResponseReturnValue:
        # Read and parse parameters
        _lane_nr = request.args.get("lane")
        if not _lane_nr:
            return "start_experiment expects a lane", 400
        try:
            lane_nr = int(_lane_nr)
        except ValueError:
            return "lane must be an integer", 400

        _template_id = request.args.get("template")
        if not _template_id:
            return "start_experiment expects a template id", 400
        try:
            template_id = int(_template_id)
            template = config_manager.experiment_templates.load(template_id)
        except ValueError:
            return "template must be an integer", 400
        except FileNotFoundError:
            return "no template with provided uid found", 400

        _lab_notebook_entry = request.args.get("lab_notebook_entry")
        if not _lab_notebook_entry:
            return "start_experiment expects a notebook entry", 400
        try:
            lab_notebook_entry = str(_lab_notebook_entry)
        except ValueError:
            return "notebook entry must be a string", 400

        # Start task
        if lane_nr == 0:
            lane = LedLane.LANE_1
        elif lane_nr == 1:
            lane = LedLane.LANE_2
        elif lane_nr == 2:
            lane = LedLane.LANE_3
        else:
            return "invalid lane nr", 400

        uid = config_manager.experiments.next_uid()

        controller.experiment_supervisor.start_experiment_on(
            lane, template, uid, lab_notebook_entry
        )
        return "experiment was started", 200

    @app.route("/pause_experiment", methods=["GET"])
    def pause_experiment() -> ResponseReturnValue:
        _lane_nr = request.args.get("lane")
        if not _lane_nr:
            return "start_experiment expects a lane", 400
        try:
            lane_nr = int(_lane_nr)
        except ValueError:
            return "lane must be an integer", 400
        if lane_nr == 0:
            lane = LedLane.LANE_1
        elif lane_nr == 1:
            lane = LedLane.LANE_2
        elif lane_nr == 2:
            lane = LedLane.LANE_3
        else:
            return "invalid lane nr", 400

        controller.experiment_supervisor.pause_experiment_on(lane)
        return "experiment was paused"

    @app.route("/resume_experiment", methods=["GET"])
    def resume_experiment() -> ResponseReturnValue:
        _lane_nr = request.args.get("lane")
        if not _lane_nr:
            return "start_experiment expects a lane", 400
        try:
            lane_nr = int(_lane_nr)
        except ValueError:
            return "lane must be an integer", 400
        if lane_nr == 0:
            lane = LedLane.LANE_1
        elif lane_nr == 1:
            lane = LedLane.LANE_2
        elif lane_nr == 2:
            lane = LedLane.LANE_3
        else:
            return "invalid lane nr", 400

        controller.experiment_supervisor.resume_experiment_on(lane)
        return "experiment was resumed", 200

    @app.route("/cancel_experiment", methods=["GET"])
    def cancel_experiment() -> ResponseReturnValue:
        _lane_nr = request.args.get("lane")
        if not _lane_nr:
            return "start_experiment expects a lane", 400
        try:
            lane_nr = int(_lane_nr)
        except ValueError:
            return "lane must be an integer", 400
        if lane_nr == 0:
            lane = LedLane.LANE_1
        elif lane_nr == 1:
            lane = LedLane.LANE_2
        elif lane_nr == 2:
            lane = LedLane.LANE_3
        else:
            return "invalid lane nr", 400

        controller.experiment_supervisor.cancel_experiment_on(lane)
        return "canceled experiment", 200

    # Websocket part:
    @socketio.on("connect")
    def handle_connect() -> None:
        socketio.start_background_task(target=send_data)
        logger.debug("WebSocker client connected.")

    @socketio.on("disconnect")
    def handle_disconnect() -> None:
        socketio.start_background_task(target=send_data)
        logger.debug("WebSocket client disconnected.")

    def send_data() -> None:
        while True:
            snapshot = ControllerStateWsData.from_state(controller.state)
            socketio.emit(
                "pcrdata",
                {"data": snapshot.to_json()},
            )
            socketio.sleep(1)

    return app, socketio, config_manager, controller
