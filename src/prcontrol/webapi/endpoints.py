import os

from prcontrol.controller.controller import TfEndpoint


def _error() -> None:
    print(
        "Error. IP-Addresses of reactor- and power-box must be "
        "specified in the environment variables REACTOR_BOX and POWER_BOX"
    )
    exit(-1)


def get_reactor_box_endpoint() -> TfEndpoint:
    host = os.environ.get("REACTOR_BOX")
    if host is None:
        _error()
        raise RuntimeError("Show mypy that this is unreachable...")

    return TfEndpoint(
        host=host,
        port=int(os.environ.get("REACTOR_BOX_PORT", 4223)),
    )


def get_power_box_endpoint() -> TfEndpoint:
    host = os.environ.get("POWER_BOX")
    if host is None:
        _error()
        raise RuntimeError("Show mypy that this is unreachable...")

    return TfEndpoint(
        host=host,
        port=int(os.environ.get("POWER_BOX_PORT", 4223)),
    )
