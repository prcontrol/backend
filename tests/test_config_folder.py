import os
import shutil

import attrs

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
        dir.add_from_json(obj.to_json())

    return dir


def test_creation_of_new_folder():
    clean("./test/")
    dir = init_test_folder(0, "./test/")
    assert len(dir._configs) == 0
    assert len(os.listdir(dir.workspace)) == 0
    clean("./test/")


def test_opening_existing_folder():
    clean("./test/")
    wrk_spc = init_test_folder(4, "./test/").workspace
    new_dir = ConfigFolder(wrk_spc, MyConfigTestObject)
    assert len(new_dir._configs) == 4
    clean("./test/")


def test_adding_json():
    clean("./test/")
    dir = init_test_folder(0, "./test/")
    obj = MyConfigTestObject(0, "new object")
    dir.add(obj)
    assert len(dir._configs) == 1
    assert len(os.listdir(dir.workspace)) == 1
    clean("./test/")


def test_loading_json():
    clean("./test/")
    dir = init_test_folder(0, "./test/")
    obj = MyConfigTestObject(0, "new object")
    dir.add(obj)
    loaded_obj = dir.load(0)
    assert loaded_obj == MyConfigTestObject(uid=0, name="new object")
    clean("./test/")


def test_overwriting_json():
    clean("./test/")
    dir = init_test_folder(1, "./test/")
    obj = MyConfigTestObject(0, "new name")
    dir.add(obj)
    assert len(dir._configs) == 1
    assert len(os.listdir(dir.workspace)) == 1
    loaded_obj = dir.load(0)
    assert loaded_obj.name == "new name"
    clean("./test/")


def test_load_not_existing_json():
    clean("./test/")
    dir = init_test_folder(2, "./test/")
    try:
        _ = dir.load(5)
        clean("./test/")
        raise AssertionError()
    except FileNotFoundError:
        assert True
        clean("./test/")


def test_deleting_json():
    clean("./test/")
    dir = init_test_folder(1, "./test/")
    dir.delete(0)
    assert len(dir._configs) == 0
    assert len(os.listdir(dir.workspace)) == 0
    clean("./test/")


def test_deleting_not_existing_json():
    clean("./test/")
    dir = init_test_folder(5, "./test/")
    dir.delete(40)
    assert len(dir._configs) == 5
    assert len(os.listdir(dir.workspace)) == 5
    clean("./test/")


def test_list_all_json():
    clean("./test/")
    dir = init_test_folder(5, "./test/")
    assert len(list(dir.load_all())) == 5
    clean("/test/")
