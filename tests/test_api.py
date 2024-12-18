import io
import json

import pytest

from prcontrol.controller.config_manager import ConfigFolder
from prcontrol.controller.configuration import (
    LED,
    EmmissionPair,
)
from prcontrol.webapi import app, config_manager
from tests.test_config_folder import clean


def get_default_LED(id: int, desc: str) -> LED:
    return LED(
        uid=id,
        name=desc,
        fwhm=1,
        max_of_emission=2,
        min_wavelength=3,
        max_wavelength=4,
        color="blue",
        max_current=5,
        manufacturer_id=6,
        order_id=7,
        date_soldering="2024-01-01",
        soldered_by="Tim",
        operating_time=8.0,
        defect=False,
        emission_spectrum=(
            EmmissionPair(wavelength=9, intensity=10.0),
            EmmissionPair(wavelength=11, intensity=12.0),
        ),
        emission_spectrum_recorded_on="2023-01-01",
    )


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def dir():
    test_dir = config_manager.leds
    clean(test_dir.workspace)
    yield test_dir
    clean(test_dir.workspace)


def init_dir_with(num_elements: int, dir: ConfigFolder):
    for i in range(num_elements):
        obj = get_default_LED(i, f"default_obj_{i}")
        dir.add(obj)


def test_availability(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<h1> Hello World! </h1>" in response.data


def test_list_api(client, dir):
    init_dir_with(2, dir)
    response = client.get("/list_led")
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


def test_config_api_GET_normal(client, dir):
    init_dir_with(1, dir)
    response = client.get("/led", query_string=dict(uid=0))
    assert response.status_code == 200
    rec_obj = LED.from_json(response.data)
    assert rec_obj == dir.load(0)


def test_config_api_GET_no_uid(client):
    response = client.get("/led")
    assert response.status_code == 400
    assert response.data == b"get expects argument uid"


def test_config_api_GET_uid_as_str(client):
    response = client.get("/led", query_string=dict(uid="test"))
    assert response.status_code == 400
    assert response.data == b"uid must be integer"


def test_config_api_GET_no_file(client, dir):
    init_dir_with(3, dir)
    response = client.get("/led", query_string=dict(uid=40))
    assert response.status_code == 400
    assert response.data == b"file does not exist"


def test_config_api_POST_new_file(client, dir):
    obj = get_default_LED(0, "test")
    data = {"json_file": (io.BytesIO(obj.to_json().encode()), "test.json")}
    response = client.post("/led", data=data)
    assert response.status_code == 200
    assert obj == dir.load(0)


def test_config_api_POST_no_file(client):
    obj = get_default_LED(0, "test")
    data = {"file": (io.BytesIO(obj.to_json().encode()), "test.json")}
    response = client.post("/led", data=data)
    assert response.status_code == 400
    assert response.data == b"post expects a json_file"


def test_config_api_DELETE_normal(client, dir):
    init_dir_with(10, dir)
    response = client.delete("/led", query_string=dict(uid=5))
    assert response.status_code == 200
    assert len(dir._configs) == 9


def test_config_api_DELETE_no_file(client, dir):
    init_dir_with(10, dir)
    response = client.delete("/led", query_string=dict(uid=42))
    assert response.status_code == 200
    assert len(dir._configs) == 10


def test_config_api_DELETE_no_uid(client):
    response = client.delete("/led")
    assert response.status_code == 400
    assert response.data == b"delete expects argument uid"


def test_config_api_DELETE_uid_as_str(client):
    response = client.delete("/led", query_string=dict(uid="test"))
    assert response.status_code == 400
    assert response.data == b"uid must be integer"
