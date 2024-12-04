import json
import os
import shutil

import attrs
from cattr import structure

from prcontrol.controller.config_manager import ConfigFolder
from prcontrol.controller.configuration import JSONSeriablizable


@attrs.frozen(slots=True)
class TestObj(JSONSeriablizable):
    uid: int
    name: str


def init_test_folder(num_elements: int, workspace: str) -> str:
    dir = ConfigFolder(workspace)

    for i in range(0, num_elements):
        obj = TestObj(uid=i, name="default_obj_" + str(i))
        dir.add(obj.to_json())

    return dir.workspace


def test_creation_of_new_folder():
    if os.path.isdir("./test1/"):
        shutil.rmtree("./test1/")
    dir = ConfigFolder(init_test_folder(0, "./test1/"))
    assert len(dir.configs) == 0
    shutil.rmtree("./test1/")


def test_opening_existing_folder():
    if os.path.isdir("./test2/"):
        shutil.rmtree("./test2/")
    dir = ConfigFolder(init_test_folder(4, "./test2/"))
    assert len(dir.configs) == 4
    shutil.rmtree("./test2/")


def test_adding_json():
    if os.path.isdir("./test3/"):
        shutil.rmtree("./test3/")
    dir = ConfigFolder(init_test_folder(0, "./test3/"))
    obj = TestObj(0, "new object")
    dir.add(obj.to_json())
    assert len(dir.configs) == 1
    assert len(os.listdir(dir.workspace)) == 1
    shutil.rmtree("./test3/")


def test_loading_json():
    if os.path.isdir("./test4/"):
        shutil.rmtree("./test4/")
    dir = ConfigFolder(init_test_folder(0, "./test4/"))
    obj = TestObj(0, "new object")
    dir.add(obj.to_json())
    loaded_obj = structure(json.loads(dir.load(0)), TestObj)
    assert loaded_obj.uid == 0
    assert loaded_obj.name == "new object"
    shutil.rmtree("./test4/")


def test_overwriting_json():
    if os.path.isdir("./test5/"):
        shutil.rmtree("./test5/")
    dir = ConfigFolder(init_test_folder(1, "./test5/"))
    obj = TestObj(0, "new name")
    dir.add(obj.to_json())
    assert len(dir.configs) == 1
    assert len(os.listdir(dir.workspace)) == 1
    loaded_obj = structure(json.loads(dir.load(0)), TestObj)
    assert loaded_obj.name == "new name"
    shutil.rmtree("./test5/")


def test_load_not_existing_json():
    if os.path.isdir("./test6/"):
        shutil.rmtree("./test6/")
    dir = ConfigFolder(init_test_folder(2, "./test6/"))

    try:
        _ = dir.load(5)
        raise AssertionError()
    except FileNotFoundError:
        assert True
        shutil.rmtree("./test6/")


def test_deleting_json():
    if os.path.isdir("./test7/"):
        shutil.rmtree("./test7/")
    dir = ConfigFolder(init_test_folder(1, "./test7/"))
    dir.delete(0)
    assert len(dir.configs) == 0
    assert len(os.listdir(dir.workspace)) == 0
    shutil.rmtree("./test7/")


def test_deleting_not_existing_json():
    if os.path.isdir("./test8/"):
        shutil.rmtree("./test8/")
    dir = ConfigFolder(init_test_folder(5, "./test8/"))
    dir.delete(40)
    assert len(dir.configs) == 5
    assert len(os.listdir(dir.workspace)) == 5
    shutil.rmtree("./test8/")
