# This file contains the tools for managing and
# loading stored configuration files

import logging
import os
import pathlib
import re
from collections.abc import Iterable

from attrs import define, field

from prcontrol.controller.configuration import (
    LED,
    ConfigObject,
    Experiment,
    ExperimentTemplate,
    HardwareConfig,
    TinkerforgeBricklet,
)

logger = logging.getLogger(__name__)


@define
class ConfigFolder[T: ConfigObject]:
    workspace: pathlib.Path = field(converter=pathlib.Path)
    kind: type[T]

    _configs: set[int] = field(init=False, factory=set)
    _FILENAME_PATTERN = re.compile(r"obj_([0-9]+)\.json")

    def __attrs_post_init__(self) -> None:
        logger.debug(f"Initializing config folder at {self.workspace!r}")
        if not os.path.isdir(self.workspace):
            os.makedirs(self.workspace)
        self._update()

    def _update(self) -> None:
        """Helper Method: Update configuration files from disk.
        Runs only after Initilization!"""
        logger.debug(f"Reading config files in {self.workspace!r}")
        for file_path in os.listdir(self.workspace):
            _match = self._FILENAME_PATTERN.fullmatch(file_path)
            if _match is None:
                continue

            id = int(_match.groups()[0])
            self._configs.add(id)

    def _path_of_uid(self, uid: int) -> pathlib.Path:
        return self.workspace / f"obj_{uid}.json"

    def load(self, uid: int) -> T:
        """Get configuration with given `uid`.

        Throws `FileNotFoundError` if there is no configuration with the given
        `uid`.
        """
        if uid not in self._configs:
            raise FileNotFoundError(
                "Config for {self.name} with uid {uid} not found."
            )
        logger.debug(f"Loading uid {uid} from {self.workspace!r}")
        with open(self._path_of_uid(uid)) as config:
            return self.kind.from_json(config.read())

    def add(self, config_object: T) -> None:
        """Store configuration under the uid `uid`.
        May overwrite the given `uid`.
        """
        path = self._path_of_uid(config_object.get_uid())
        logger.debug(
            f"Adding object {config_object.get_description()}"
            f" to {self.workspace!r}"
        )
        with open(path, "w") as file:
            file.write(config_object.to_json())

            self._configs.add(config_object.get_uid())

    def add_from_json(self, config_json: str | bytes | bytearray) -> None:
        """Store configuration under the uid `uid`.
        May overwrite the given `uid`.
        Validates the json string's structure.
        """
        logger.debug(f"Adding object from json to {self.workspace!r}")
        self.add(self.kind.from_json(config_json))

    def delete(self, uid: int) -> None:
        """Delete configuration `id` if exists"""
        logger.debug(f"Deleting object with uid {uid} to {self.workspace!r}")
        if uid in self._configs:
            os.remove(self._path_of_uid(uid))
            self._configs.remove(uid)

    def load_all(self) -> Iterable[ConfigObject]:
        logger.debug(f"Loading all objects from {self.workspace!r}")
        for uid in self._configs:
            yield self.load(uid)


class ConfigManager:
    leds: ConfigFolder[LED]
    bricklets: ConfigFolder[TinkerforgeBricklet]
    experiment_templates: ConfigFolder[ExperimentTemplate]
    experiments: ConfigFolder[Experiment]
    configs: ConfigFolder[HardwareConfig]

    def __init__(self, base_path: str | pathlib.Path | None = None) -> None:
        logger.info(f"ConfigManager at {base_path!r}.")
        if base_path is None:
            base_path = "./workspace"
        base_path = pathlib.Path(base_path)

        self.leds = ConfigFolder(base_path / "leds", LED)
        self.bricklets = ConfigFolder(
            base_path / "bricklets", TinkerforgeBricklet
        )
        self.experiment_templates = ConfigFolder(
            base_path / "exp_tmps", ExperimentTemplate
        )
        self.experiments = ConfigFolder(base_path / "experiments", Experiment)
        self.configs = ConfigFolder(base_path / "configs", HardwareConfig)
