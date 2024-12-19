from prcontrol.webapi import app
from prcontrol.webapi.api import socketio

if __name__ == "__main__":

    socketio.run(app, debug=True)
