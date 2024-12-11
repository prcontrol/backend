import io
import json

import pytest
from flask import request

from prcontrol.controller.config_manager import ConfigFolder
from prcontrol.webapi import app
from prcontrol.webapi.api import handle_config_api, handle_list_api
from tests.test_config_folder import MyConfigTestObject, clean, init_test_folder


def get_dir() -> ConfigFolder:
    return ConfigFolder("./test/", MyConfigTestObject)


@app.route("/test_config_api", methods=["GET", "POST", "DELETE"])
def route_for_testing_handle_config():
    return handle_config_api(get_dir(), request)


@app.route("/test_list_api", methods=["GET"])
def route_for_testing_list_configs():
    return handle_list_api(get_dir(), request)


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def dir_path():
    test_dir = get_dir()
    clean(test_dir.workspace)
    yield test_dir.workspace
    clean(test_dir.workspace)


def test_availability(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<h1> Hello World! </h1>" in response.data


def test_list_api(client, dir_path):
    dir = init_test_folder(2, dir_path)
    response = client.get("/test_list_api")
    assert response.status_code == 200
    return_obj = json.loads(response.data)
    assert len(return_obj["results"]) == 2
    assert return_obj["results"][0]["uid"] == 0
    assert (
        return_obj["results"][0]["description"] == dir.load(0).get_description()
    )  # noqa: E501
    assert return_obj["results"][1]["uid"] == 1
    assert (
        return_obj["results"][1]["description"] == dir.load(1).get_description()
    )  # noqa: E501


def test_config_api_GET_normal(client, dir_path):
    dir = init_test_folder(1, dir_path)
    response = client.get("/test_config_api", query_string=dict(uid=0))
    assert response.status_code == 200
    rec_obj = MyConfigTestObject.from_json(response.data)
    assert rec_obj == dir.load(0)


def test_config_api_GET_no_uid(client):
    response = client.get("/test_config_api")
    assert response.status_code == 400
    assert response.data == b"get expects argument uid"


def test_config_api_GET_uid_as_str(client):
    response = client.get("/test_config_api", query_string=dict(uid="test"))
    assert response.status_code == 400
    assert response.data == b"uid must be integer"


def test_config_api_GET_no_file(client, dir_path):
    _ = init_test_folder(3, dir_path)
    response = client.get("/test_config_api", query_string=dict(uid=40))
    assert response.status_code == 400
    assert response.data == b"file does not exist"


def test_config_api_POST_new_file(client, dir_path):
    dir = init_test_folder(0, dir_path)
    obj = MyConfigTestObject(0, "test")
    data = {"json_file": (io.BytesIO(obj.to_json().encode()), "test.json")}
    response = client.post("/test_config_api", data=data)
    assert response.status_code == 200
    dir._update()  # ToDo: fix that
    assert obj == dir.load(0)


def test_config_api_POST_no_file(client):
    obj = MyConfigTestObject(0, "test")
    data = {"file": (io.BytesIO(obj.to_json().encode()), "test.json")}
    response = client.post("/test_config_api", data=data)
    assert response.status_code == 400
    assert response.data == b"post expects a json_file"
