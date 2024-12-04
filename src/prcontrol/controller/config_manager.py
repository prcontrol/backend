# This file contains the tools for managing and
# loading stored configuration files

import json
import os

from attrs import define, field


@define
class ConfigFolder:
    configs: list[int] = field(init=False, factory=list)
    workspace: str

    def __attrs_post_init__(self) -> None:
        if not os.path.isdir(self.workspace):
            os.makedirs(self.workspace)
        self.update()

    def update(self) -> None:
        self.configs = list(
            map(
                lambda name: int(name[(name.find("_") + 1) : name.find(".")]),
                os.listdir(self.workspace),
            )
        )

    def load(self, uid: int) -> str:
        with open(self.workspace + "obj_" + str(uid) + ".json") as config:
            json_str = config.read()
            return json_str
        raise FileNotFoundError

    def add(self, json_str) -> None:
        uid = json.loads(json_str)["uid"]
        with open(self.workspace + "obj_" + str(uid) + ".json", "w") as file:
            file.write(json_str)
            if uid not in self.configs:
                self.configs.append(uid)

    def delete(self, uid: int) -> None:
        if uid in self.configs:
            os.remove(self.workspace + "obj_" + str(uid) + ".json")
            self.configs.remove(uid)

    def get_name_of(self, uid: int) -> str:
        json_str = self.load(uid)
        return json.loads(json_str)["name"]


class ConfigManager:
    leds: ConfigFolder = ConfigFolder("./workspace/leds/")
    bricklets: ConfigFolder = ConfigFolder("./workspace/bricklets/")
    exp_templates: ConfigFolder = ConfigFolder("./workspace/exp_tmps/")
    experiments: ConfigFolder = ConfigFolder("./workspace/experiments/")
    configs: ConfigFolder = ConfigFolder("./workspace/configs/")
