import logging

from prcontrol.webapi.api import create_app

stderr_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s "
    "[%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
stderr_handler.setFormatter(formatter)
stderr_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(stderr_handler)


logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logger.info("Starting...")
    app, socketio = create_app()
    socketio.run(app, debug=True, host="0.0.0.0", allow_unsafe_werkzeug=True)
