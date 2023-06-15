import os
import configparser

import redis

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .dependencies.timer import *


class StreamOverlay(FastAPI):
    def __init__(self, config_file="config.ini"):
        # Populate config file with default values if config is non-existent
        self._config_file = config_file
        if not os.path.exists(self._config_file):
            self.populate_deafult_config(self._config_file)

        self._configparser = configparser.ConfigParser()
        self._configparser.read(config_file)

        with open("/home/wybory/strings.txt") as file:
            self.predefs = [item.strip() for item in file.read().split("\n")]

        with open("/home/wybory/candidates.txt") as file:
            self.candidates = [item.strip() for item in file.read().split("\n")]

        super().__init__()
        self.mount("/static", StaticFiles(directory="/home/wybory/static"), name="static")
        self.templating = Jinja2Templates(directory="/home/wybory/templates")

        self.redis: redis.Redis
        self._setup_redis()
        self._update_values()

    @property
    def emblem_visible(self):
        return self.redis.get("emblem_visible")

    @emblem_visible.setter
    def emblem_visible(self, value):
        self.redis.set("emblem_visible", value)

    @property
    def comment_mode(self):
        return self.redis.get("comment_mode")

    @comment_mode.setter
    def comment_mode(self, value):
        self.redis.set("comment_mode", value)

    @property
    def infobar_visible(self):
        return self.redis.get("infobar_visible")

    @infobar_visible.setter
    def infobar_visible(self, value):
        self.redis.set("infobar_visible", value)

    @property
    def map_state(self):
        return self.redis.hgetall("map_state")

    @map_state.setter
    def map_state(self, value):
        self.redis.hset("map_state", value)

    @property
    def overlay_mode(self):
        return self.redis.get("overlay_mode")

    @overlay_mode.setter
    def overlay_mode(self, value):
        self.redis.set("overlay_mode", value)

    @property
    def teams(self):
        return self.redis.lrange("teams", 0, -1)

    @teams.setter
    def teams(self, value):
        self.redis.delete("teams")
        self.redis.lpush("teams", *value)

    @property
    def infobar(self):
        return self.redis.lrange("info_bar", 0, -1)

    @infobar.setter
    def infobar(self, value):
        self.redis.delete("info_bar")
        self.redis.lpush("info_bar", *value)

    def _setup_redis(self):
        self.redis = redis.Redis(host=os.getenv("BROKER_BACKEND_URL"), db=0)

    def _update_values(self):
        """
        Ensures that all values on redis are set
        :return:
        """
        self.timer = TimerState()

        self.infobar = ["Transmisja wkrótce się rozpocznie"]

        self.emblem_visible = False

        self.comment_mode = False
            
        self.infobar_visible = True

        # TODO duplicate values
        self.map_state = {"visible": False,
                          "team1": "Vape Clan",
                          "team2": "D0mmyM0mmies"}
        self.teams = ["NA", "NA"]

        self.overlay_mode = "GP"


    def dump_to_config(self):
        with open(self._config_file, 'w+') as file:
            self._configparser.write(file)

    def redis_to_cfg(self):
        self._configparser.set("DEFAULT", "emblem_visible", str(self.redis.get("emblem_visible")))
        self._configparser.set("DEFAULT", "comment_mode", str(self.redis.get("comment_mode")))
        self._configparser.set("DEFAULT", "infobar_visible", str(self.redis.get("infobar_visible")))
        self._configparser.set("DEFAULT", "overlay_mode", str(self.redis.get("overlay_mode")))
        self.dump_to_config()

    @staticmethod
    def populate_deafult_config(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        config.set('DEFAULT', 'emblem_visible', "False")
        config.set('DEFAULT', 'comment_mode', "False")
        config.set('DEFAULT', 'infobar_visible', "True")
        config.set("DEFAULT", "overlay_mode", "GP")
        with open(config_file, 'w+') as file:
            config.write(file)