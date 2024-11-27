from flask import Flask, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS

from prcontrol.controller import configuration, config_manager


app = Flask(__name__)
config_manager = ConfigManager()
CORS(app)


@app.route("/", methods=["GET"])
def index() -> ResponseReturnValue:
    return "<h1> Hello World! </h1>", 200

@app.route("/get_led", methods=["GET"])
def get_led() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "get_led expects argument uid", 400

    json = config_manager.load_led(uid).to_json()

    return json, 200

@app.route("/get_available_led_uids", methods=["GET"])
def get_available_led_uids() -> ResponseReturnValue:
    
    led_uids = json.dumps(config_manager.leds)
    return led_uids, 200

@app.route("/get_bricklet", methods=["GET"])
def get_bricklet() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "get_bricklet expects argument uid", 400

    json = config_manager.load_bricklet(uid).to_json()

    return json, 200

@app.route("/get_available_bricklet_uids", methods=["GET"])
def get_available_bricklet_uids() -> ResponseReturnValue:
    
    bricklet_uids = json.dumps(config_manager.bricklets)
    return bricklet_uids, 200

@app.route("/get_config", methods=["GET"])
def get_config() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "get_config expects argument uid", 400

    json = config_manager.load_config(uid).to_json()

    return json, 200

@app.route("/get_available_config_uids", methods=["GET"])
def get_available_config_uids() -> ResponseReturnValue:
    
    config_uids = json.dumps(config_manager.configs)
    return config_uids, 200

@app.route("/get_experiment_template", methods=["GET"])
def get_experiment_template() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "get_experiment_template expects argument uid", 400

    json = config_manager.load_experiment_template(uid).to_json()

    return json, 200

@app.route("/get_available_experiment_template_uids", methods=["GET"])
def get_available_experiment_template_uids() -> ResponseReturnValue:
    
    experiment_template_uids = json.dumps(config_manager.exp_temps)
    return experiment_template_uids, 200

@app.route("/get_experiment", methods=["GET"])
def get_experiment() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "get_experiment expects argument uid", 400

    json = config_manager.load_experiment(uid).to_json()

    return json, 200

@app.route("/get_available_experiments_uids", methods=["GET"])
def get_available_experiment_uids() -> ResponseReturnValue:
    
    experiment_uids = json.dumps(config_manager.exps)
    return experiment_uids, 200

@app.route("/delete_led", methods=["GET"])
def delete_led() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "delete_led expects argument uid", 400

    config_manager.delete_led(uid)

    return "LED deleted", 200

@app.route("/delete_bricklet", methods=["GET"])
def delete_bricklet() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "delete_bricklet expects argument uid", 400

    config_manager.delete_bricklet(uid)

    return "Bricklet deleted", 200

@app.route("/delete_config", methods=["GET"])
def delete_config() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "delete_config expects argument uid", 400

    config_manager.delete_config(uid)

    return "Config deleted", 200

@app.route("/delete_experiment_template", methods=["GET"])
def delete_experiment_template() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "delete_experiment_template expects argument uid", 400

    config_manager.delete_experiment_template(uid)

    return "Template deleted", 200

@app.route("/delete_experiment", methods=["GET"])
def delete_experiment() -> ResponseReturnValue:

    uid = request.args.get('uid');
    if (uid == None)
        return "delete_experiment expects argument uid", 400

    config_manager.delete_experiment(uid)

    return "Experiment deleted", 200

@app.route("/upload_led", methods=["POST"])
def upload_led() -> ResponseReturnValue:

    file = request.files["file"]
    if not file:
        return "upload_led expects a file", 400

    config_manager.add_led(file.stream.read())
    return "Received LED", 200
    
@app.route("/upload_config", methods=["POST"])
def upload_config() -> ResponseReturnValue:

    file = request.files["file"]
    if not file:
        return "upload_config expects a file", 400

    config_manager.add_config(file.stream.read())
    return "Received Config", 200

@app.route("/upload_bricklet", methods=["POST"])
def upload_bricklet() -> ResponseReturnValue:

    file = request.files["file"]
    if not file:
        return "upload_bricklet expects a file", 400

    config_manager.add_bricklet(file.stream.read())
    return "Received Bricklet", 200

@app.route("/upload_experiment_template", methods=["POST"])
def upload_experiment_template() -> ResponseReturnValue:

    file = request.files["file"]
    if not file:
        return "upload_experiment_template expects a file", 400

    config_manager.add_experiment_template(file.stream.read())
    return "Received Template", 200


#@app.route("/upload_file", methods=["POST"])
#def uploade_config() -> ResponseReturnValue:
#    print(f"Received request: {request}")
#    file = request.files["file"]
#    if not file:
#        return "upload_files expects a file", 400
#
#    print(f"Received LED: {configuration.LED.from_json(file.stream.read())}")
#    return "TOP!", 200
