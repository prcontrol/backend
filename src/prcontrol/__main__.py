import contextlib
import logging
import os

from tinkerforge.ip_connection import Error as TfIpError  # type: ignore

from prcontrol.controller.controller import TfEndpoint
from prcontrol.webapi.api import create_app

logging.root.setLevel(logging.DEBUG)

log_stdout = logging.StreamHandler()
log_stdout.setFormatter(
    logging.Formatter(
        "[%(asctime)s] %(levelname)s "
        "[%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
    )
)
log_stdout.setLevel(logging.DEBUG)
logging.basicConfig(handlers=[log_stdout])


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


logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logger.info("Starting...")
    app, socketio, _, controller = create_app(
        reactor_box_endpoint=get_reactor_box_endpoint(),
        power_box_endpoint=get_power_box_endpoint(),
        mock=True,
    )

    try:
        socketio.run(
            app, debug=True, host="0.0.0.0", allow_unsafe_werkzeug=True
        )
    finally:
        print("Shutting down")
        with contextlib.suppress(TfIpError):
            controller._power_box.reset_leds()
