import io
import json

import pytest

from prcontrol.controller import config_manager
from prcontrol.controller.config_manager import ConfigFolder, ConfigManager
from prcontrol.controller.configuration import (
    LED,
    EmmissionPair,
)
from prcontrol.webapi.api import create_app
from tests.test_config_folder import clean_directory


def create_mock_led(id: int, desc: str) -> LED:
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


config_manager: ConfigManager


@pytest.fixture
def client():
    global config_manager
    app, _, config_manager = create_app(mock=True)
    with app.test_client() as client:
        yield client


@pytest.fixture
def clean_environment():
    test_dir = config_manager.leds
    clean_directory(test_dir.workspace)
    yield test_dir
    clean_directory(test_dir.workspace)


def init_dir_with_n_leds(num_elements: int, dir: ConfigFolder):
    for i in range(num_elements):
        obj = create_mock_led(i, f"default_obj_{i}")
        dir.add(obj)


def test_availability(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<h1> Hello World! </h1>" in response.data


def test_list_api(client, clean_environment):
    init_dir_with_n_leds(2, clean_environment)
    response = client.get("/list_led")
    assert response.status_code == 200
    return_obj = json.loads(response.data)
    assert len(return_obj["results"]) == 2
    assert return_obj["results"][0]["uid"] == 0
    assert (
        return_obj["results"][0]["description"]
        == clean_environment.load(0).get_description()
    )
    assert return_obj["results"][1]["uid"] == 1
    assert (
        return_obj["results"][1]["description"]
        == clean_environment.load(1).get_description()
    )


def test_config_api_GET_normal(client, clean_environment):
    init_dir_with_n_leds(1, clean_environment)
    response = client.get("/led", query_string=dict(uid=0))
    assert response.status_code == 200
    rec_obj = LED.from_json(response.data)
    assert rec_obj == clean_environment.load(0)


def test_config_api_GET_no_uid(client):
    response = client.get("/led")
    assert response.status_code == 400
    assert response.data == b"get expects argument uid"


def test_config_api_GET_uid_as_str(client):
    response = client.get("/led", query_string=dict(uid="test"))
    assert response.status_code == 400
    assert response.data == b"uid must be integer"


def test_config_api_GET_no_file(client, clean_environment):
    init_dir_with_n_leds(3, clean_environment)
    response = client.get("/led", query_string=dict(uid=40))
    assert response.status_code == 400
    assert response.data == b"file does not exist"


def test_config_api_POST_new_file(client, clean_environment):
    obj = create_mock_led(0, "test")
    data = {"json_file": (io.BytesIO(obj.to_json().encode()), "test.json")}
    response = client.post("/led", data=data)
    assert response.status_code == 200
    assert obj == clean_environment.load(0)


def test_config_api_POST_no_file(client):
    obj = create_mock_led(0, "test")
    data = {"file": (io.BytesIO(obj.to_json().encode()), "test.json")}
    response = client.post("/led", data=data)
    assert response.status_code == 400
    assert response.data == b"post expects a json_file"


def test_config_api_DELETE_normal(client, clean_environment):
    init_dir_with_n_leds(10, clean_environment)
    response = client.delete("/led", query_string=dict(uid=5))
    assert response.status_code == 200
    assert len(clean_environment._configs) == 9


def test_config_api_DELETE_no_file(client, clean_environment):
    init_dir_with_n_leds(10, clean_environment)
    response = client.delete("/led", query_string=dict(uid=42))
    assert response.status_code == 200
    assert len(clean_environment._configs) == 10


def test_config_api_DELETE_no_uid(client):
    response = client.delete("/led")
    assert response.status_code == 400
    assert response.data == b"delete expects argument uid"


def test_config_api_DELETE_uid_as_str(client):
    response = client.delete("/led", query_string=dict(uid="test"))
    assert response.status_code == 400
    assert response.data == b"uid must be integer"
