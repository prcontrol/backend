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


def init_test_folder(
    num_elements: int, workspace: str
) -> ConfigFolder[MyConfigTestObject]:
    dir = ConfigFolder(workspace, MyConfigTestObject)

    for i in range(num_elements):
        obj = MyConfigTestObject(uid=i, name=f"default_obj_{i}")
        dir.add_from_json(obj.to_json())

    return dir


def test_creation_of_new_folder():
    if os.path.isdir("./test1/"):
        shutil.rmtree("./test1/")
    dir = init_test_folder(0, "./test1/")
    assert len(dir._configs) == 0
    shutil.rmtree("./test1/")


def test_opening_existing_folder():
    if os.path.isdir("./test2/"):
        shutil.rmtree("./test2/")
    dir = init_test_folder(4, "./test2/")
    assert len(dir._configs) == 4
    shutil.rmtree("./test2/")


def test_adding_json():
    if os.path.isdir("./test3/"):
        shutil.rmtree("./test3/")

    dir = init_test_folder(0, "./test3/")

    obj = MyConfigTestObject(0, "new object")
    dir.add(obj)
    assert len(dir._configs) == 1
    assert len(os.listdir(dir.workspace)) == 1
    shutil.rmtree("./test3/")


def test_loading_json():
    if os.path.isdir("./test4/"):
        shutil.rmtree("./test4/")

    dir = init_test_folder(0, "./test4/")

    obj = MyConfigTestObject(0, "new object")
    dir.add(obj)
    loaded_obj = dir.load(0)

    assert loaded_obj == MyConfigTestObject(uid=0, name="new object")
    shutil.rmtree("./test4/")


def test_overwriting_json():
    if os.path.isdir("./test5/"):
        shutil.rmtree("./test5/")
    dir = init_test_folder(1, "./test5/")
    obj = MyConfigTestObject(0, "new name")
    dir.add(obj)

    assert len(list(dir.load_all())) == 1
    assert len(os.listdir(dir.workspace)) == 1

    loaded_obj = dir.load(0)
    assert loaded_obj.name == "new name"
    shutil.rmtree("./test5/")


def test_load_not_existing_json():
    if os.path.isdir("./test6/"):
        shutil.rmtree("./test6/")
    dir = init_test_folder(2, "./test6/")

    try:
        _ = dir.load(5)
        raise AssertionError()
    except FileNotFoundError:
        assert True
        shutil.rmtree("./test6/")


def test_deleting_json():
    if os.path.isdir("./test7/"):
        shutil.rmtree("./test7/")
    dir = init_test_folder(1, "./test7/")
    dir.delete(0)
    assert len(dir._configs) == 0
    assert len(os.listdir(dir.workspace)) == 0
    shutil.rmtree("./test7/")


def test_deleting_not_existing_json():
    if os.path.isdir("./test8/"):
        shutil.rmtree("./test8/")
    dir = init_test_folder(5, "./test8/")
    dir.delete(40)
    assert len(dir._configs) == 5
    assert len(os.listdir(dir.workspace)) == 5
    shutil.rmtree("./test8/")
