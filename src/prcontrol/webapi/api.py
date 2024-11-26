from flask import Flask, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS

from prcontrol.controller import configuration

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def index() -> ResponseReturnValue:
    return "<h1> Hello World! </h1>", 200


@app.route("/upload_file", methods=["POST"])
def uploade_config() -> ResponseReturnValue:
    print(f"Received request: {request}")
    file = request.files["file"]
    if not file:
        return "upload_files expects a file", 400

    print(f"Received LED: {configuration.LED.from_json(file.stream.read())}")
    return "TOP!", 200
