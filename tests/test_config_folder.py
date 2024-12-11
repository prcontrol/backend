import os
import shutil

import attrs
import pytest

from prcontrol.controller.config_manager import ConfigFolder
from prcontrol.controller.configuration import ConfigObject


@attrs.frozen(slots=True)
class MyConfigTestObject(ConfigObject):
    uid: int
    name: str

    def get_uid(self):
        return self.uid

    def get_description(self):
        return self.name


def clean(dir: str):
    if os.path.isdir("./test/"):
        shutil.rmtree("./test/")


def init_test_folder(
    num_elements: int, workspace: str
) -> ConfigFolder[MyConfigTestObject]:
    dir = ConfigFolder(workspace, MyConfigTestObject)

    for i in range(num_elements):
        obj = MyConfigTestObject(uid=i, name=f"default_obj_{i}")
        dir.add(obj)

    return dir


@pytest.fixture
def dir_path():
    dir_path = "./test/"
    clean(dir_path)
    yield dir_path
    clean(dir_path)


def test_creation_of_new_folder(dir_path):
    dir = init_test_folder(0, dir_path)
    assert len(dir._configs) == 0
    assert len(os.listdir(dir.workspace)) == 0


def test_opening_existing_folder(dir_path):
    wrk_spc = init_test_folder(4, dir_path).workspace
    new_dir = ConfigFolder(wrk_spc, MyConfigTestObject)
    assert len(new_dir._configs) == 4


def test_adding_json(dir_path):
    dir = init_test_folder(0, dir_path)
    obj = MyConfigTestObject(0, "new object")
    dir.add(obj)
    assert len(dir._configs) == 1
    assert len(os.listdir(dir.workspace)) == 1


def test_loading_json(dir_path):
    dir = init_test_folder(0, dir_path)
    obj = MyConfigTestObject(0, "new object")
    dir.add(obj)
    loaded_obj = dir.load(0)
    assert loaded_obj == MyConfigTestObject(uid=0, name="new object")


def test_overwriting_json(dir_path):
    dir = init_test_folder(1, dir_path)
    obj = MyConfigTestObject(0, "new name")
    dir.add(obj)
    assert len(dir._configs) == 1
    assert len(os.listdir(dir.workspace)) == 1
    loaded_obj = dir.load(0)
    assert loaded_obj.name == "new name"


def test_load_not_existing_json(dir_path):
    dir = init_test_folder(2, dir_path)
    try:
        _ = dir.load(5)
        raise AssertionError()
    except FileNotFoundError:
        assert True


def test_deleting_json(dir_path):
    dir = init_test_folder(1, dir_path)
    dir.delete(0)
    assert len(dir._configs) == 0
    assert len(os.listdir(dir.workspace)) == 0


def test_deleting_not_existing_json(dir_path):
    dir = init_test_folder(5, dir_path)
    dir.delete(40)
    assert len(dir._configs) == 5
    assert len(os.listdir(dir.workspace)) == 5


def test_list_all_json(dir_path):
    dir = init_test_folder(5, dir_path)
    assert len(list(dir.load_all())) == 5
