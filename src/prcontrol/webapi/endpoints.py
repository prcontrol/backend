import os

from prcontrol.controller.controller import TfEndpoint

REACTOR_BOX_ENDPOINT = TfEndpoint(
    host=os.environ["REACTOR_BOX"],
    port=int(os.environ.get("REACTOR_BOX_PORT", 4223)),
)


POWER_BOX_ENDPOINT = TfEndpoint(
    host=os.environ["POWER_BOX"],
    port=int(os.environ.get("POWER_BOX_PORT", 4223)),
)
