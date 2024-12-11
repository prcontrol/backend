import pytest
from flask import request

from prcontrol.webapi import app
from prcontrol.webapi.api import handle_config_api
from tests.test_config_folder import clean, init_test_folder

dir_test = init_test_folder(0, "./tests/")


@app.route("/test_handle_config", methods=["GET", "POST", "DELETE"])
def route_for_testing_handle_config():
    handle_config_api(dir_test, request)


@pytest.fixture
def client():
    clean(dir_test.workspace)
    with app.test_client() as client:
        yield client
    clean(dir_test.workspace)


def test_availability(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<h1> Hello World! </h1>" in response.data
