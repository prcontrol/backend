import json
from typing import Any

from flask import Flask, Request, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS

from prcontrol.controller.config_manager import ConfigFolder, ConfigManager

app = Flask(__name__)
CORS(app)

config_manager = ConfigManager()


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
        except Exception:
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
