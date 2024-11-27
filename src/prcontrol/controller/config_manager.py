#This file contains the tools for managing and loading stored configuration files

import attrs
import os
import configuration

@define
class ConfigManager:

    leds: list[int] = field(init=False, default = []) #ToDo: read only for public
    bricklets: list[int] = field(init=False, default = [])
    configs: list[int] = field(init=False, default = [])
    exp_temps: list[int] = field(init=False, default = [])
    exps: list[int] = field(init=False, default = [])

    def update(self):
        self.leds = map(lambda name: int(name[name.find('_') : name.find('.')]), os.listdir(LED.get_working_dir()))
        self.bricklets = map(lambda name: int(name[name.find('_') : name.find('.')]), os.listdir(TinkerforgeBricklet.get_working_dir()))
        self.configs = map(lambda name: int(name[name.find('_') : name.find('.')]), os.listdir(ConfigFile.get_working_dir()))
        self.exp_temps = map(lambda name: int(name[name.find('_') : name.find('.')]), os.listdir(ExperimentTemplate.get_working_dir()))
        self.exps = map(lambda name: int(name[name.find('_') : name.find('.')]), os.listdir(Experiment.get_working_dir()))

    def load_led(self, id: int) -> LED:

        if(id in self.leds):
            file = open(LED.get_working_dir() + "object_" + str(id) + ".json", "r")
            json = file.read()
            led = structure(json.loads(json), LED)
            return led
        else:
            return None

    def load_bricklet(self, id: int) -> TinkerforgeBricklet:

        if(id in self.bricklets):
            file = open(TinkerforgeBricklet.get_working_dir() + "object_" + str(id) + ".json", "r")
            json = file.read()
            bricklet = structure(json.loads(json), TinkerforgeBricklet)
            return bricklet
        else:
            return None

    def load_config(self, id: int) -> ConfigFile:

        if(id in self.configs):
            file = open(ConfigFile.get_working_dir() + "object_" + str(id) + ".json", "r")
            json = file.read()
            config = structure(json.loads(json), ConfigFile)
            return config
        else:
            return None

    def load_experiment_temp(self, id: int) -> ExperimentTemplate:

        if(id in self.exp_temps):
            file = open(ExperimentTemplate.get_working_dir() + "object_" + str(id) + ".json", "r")
            json = file.read()
            template = structure(json.loads(json), ExperimentTemplate)
            return template
        else:
            return None

    def load_experiment(self, id: int) -> Experiment:

        if(id in self.exps):
            file = open(Experiment.get_working_dir() + "object_" + str(id) + ".json", "r")
            json = file.read()
            exp = structure(json.loads(json), Experiment)
            return exp
        else:
            return None

    def add_led(self, json: str):
        uid = json.loads(json)['uid']
        file = open(LED.get_working_dir() + "object_" + str(uid) + ".json", 'w')
        file.write(json)
        
        if(not (uid in self.leds)):
            self.leds.append(uid)

    def add_bricklet(self, json: str):
        uid = json.loads(json)['uid']
        file = open(TinkerforgeBricklet.get_working_dir() + "object_" + str(uid) + ".json", 'w')
        file.write(json)
        
        if(not (uid in self.bricklets)):
            self.bricklets.append(uid)

    def add_config(self, json: str):
        uid = json.loads(json)['uid']
        file = open(ConfigFile.get_working_dir() + "object_" + str(uid) + ".json", 'w')
        file.write(json)
        
        if(not (uid in self.configs)):
            self.configs.append(uid)

    def add_experiment_template(self, json: str):
        uid = json.loads(json)['uid']
        file = open(ExperimentTemplate.get_working_dir() + "object_" + str(uid) + ".json", 'w')
        file.write(json)
        
        if(not (uid in self.exp_temps)):
            self.exp_temps.append(uid)

    def add_experiment(self, json: str):
        uid = json.loads(json)['uid']
        file = open(Experiment.get_working_dir() + "object_" + str(uid) + ".json", 'w')
        file.write(json)
        
        if(not (uid in self.exps)):
            self.exps.append(uid)

    def delete_led(self, id: int):
        os.remove(LED.get_working_dir() + "object_" + str(id) + ".json")
        self.leds.remove(id)

    def delete_bricklet(self, id: int):
        os.remove(TinkerforgeBricklet.get_working_dir() + "object_" + str(id) + ".json")
        self.bricklets.remove(id)

    def delete_config(self, id: int):
        os.remove(ConfigFile.get_working_dir() + "object_" + str(id) + ".json")
        self.configs.remove(id)

    def delete_experiment_template(self, id: int):
        os.remove(ExperimentTemplate.get_working_dir() + "object_" + str(id) + ".json")
        self.exp_temps.remove(id)
    
    def delete_experiment(self, id: int):
        os.remove(Experiment.get_working_dir() + "object_" + str(id) + ".json")
        self.exps.remove(id)
        


