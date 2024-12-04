import json

from flask import Flask, Request, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS

from prcontrol.controller.config_manager import ConfigFolder, ConfigManager

app = Flask(__name__)
CORS(app)


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
    return handle_config_api(config_manager.exp_templates, request)


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
    return handle_list_api(config_manager.exp_templates, request)


@app.route("/list_config", methods=["GET"])
def list_configs() -> ResponseReturnValue:
    return handle_list_api(config_manager.configs, request)


@app.route("/list_experiment", methods=["GET"])
def list_experiments() -> ResponseReturnValue:
    return handle_list_api(config_manager.experiments, request)


# Generic helping methods start here

config_manager = ConfigManager()


def handle_config_api(dir: ConfigFolder, req: Request) -> ResponseReturnValue:
    if req.method == "POST":
        file = req.files["file"]
        if not file:
            return "post expects a file", 400
        dir.add(file.stream.read())
        return "success", 200

    elif req.method == "GET":
        uid = req.args.get("uid")
        if not uid:
            return "get expects argument uid", 400

        try:
            json = dir.load(uid)
            return json, 200
        except FileNotFoundError:
            return "file does not exist", 400

    elif req.method == "DELETE":
        uid = req.args.get("uid")
        if not uid:
            return "delete expects argument uid", 400
        dir.delete(uid)
        return "success", 200


def handle_list_api(folder: ConfigFolder) -> ResponseReturnValue:
    json_obj = {
        "results": list(
            map(
                lambda uid: {"uid": uid, "name": folder.get_name_of(uid)},
                folder.configs,
            )
        )
    }

    return json.dumps(json_obj), 200
