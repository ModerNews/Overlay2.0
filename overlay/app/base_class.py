import os
import configparser
from typing import Literal

import redis

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .dependencies.timer import *


class StreamOverlay(FastAPI):
    """
    Base class for overlay server

    .. note:
        Overlay's functionalities are described in `README.md`, please refer to this file first.

    This class handles Fast API server, connection to Redis service, and config file
    .. warn:
        Config files are still experimental feature, because of that most functionalities are still missing

    All values connected directly to overlay functionalities are stored in redis,
    because of that they're defined as properties rather than attributes.
    Most setters are only redis pushes, so if no additional serialization is done documentation will be omitted
    """
    def __init__(self, config_file="config.ini"):
        # TODO: Config as good God intended
        # It really is unholy
        # Populate config file with default values if config is non-existent
        self._config_file = config_file
        if not os.path.exists(self._config_file):
            self.populate_deafult_config(self._config_file)

        self._configparser = configparser.ConfigParser()
        self._configparser.read(config_file)

        # read predefined pop-up bar contents
        with open("/home/wybory/strings.txt") as file:
            self.predefs = [item.strip() for item in file.read().split("\n")]

        # read list of candidates for "Wybory" mode
        with open("/home/wybory/candidates.txt") as file:
            self.candidates = [item.strip() for item in file.read().split("\n")]

        # Instantiate Fast API base and mount static files and templating engine
        super().__init__()
        self.mount("/static", StaticFiles(directory="/home/wybory/static"), name="static")
        self.templating = Jinja2Templates(directory="/home/wybory/templates")

        # Instantiate redis and set default values
        self.redis: redis.Redis
        self._setup_redis()
        self._update_values()

    @property
    def emblem_visible(self) -> bool:
        """
        Defines general visibility of header
        """
        return bool(int(self.redis.get("emblem_visible").decode()))

    @emblem_visible.setter
    def emblem_visible(self, value: bool) -> None:
        self.redis.set("emblem_visible", str(int(value)))

    @property
    def darkmode(self):
        """
        Defines darkmode state (on/off)
        """
        return bool(int(self.redis.get("darkmode").decode()))

    @darkmode.setter
    def darkmode(self, value: bool):
        self.redis.set("darkmode", str(int(value)))

    @property
    def comment_mode(self) -> bool:
        """
        Defines visibility of the middle part of the header
        """
        return bool(int(self.redis.get("comment_mode").decode()))

    @comment_mode.setter
    def comment_mode(self, value: bool) -> None:
        self.redis.set("comment_mode", str(int(value)))

    @property
    def infobar_visible(self) -> bool:
        """
        Defines visibility of the bottom infobar
        """
        return bool(int(self.redis.get("infobar_visible").decode()))

    @infobar_visible.setter
    def infobar_visible(self, value) -> None:
        self.redis.set("infobar_visible", str(int(value)))

    @property
    def map_state(self) -> dict:
        """
        Stores information about contents of the small boxes underneath header.
        "visible" key describes current visibility of the boxes, which can be toggled.

        Read is done in such manner because, data is stored on redis as binary representation and must be decoded before use
        :return: dictionary with 3 keys: visible, team1, team2
        """
        tmp = self.redis.hgetall("map_state")
        return {"visible": bool(int(tmp[b"visible"].decode())), "team1": tmp[b"team1"].decode(), "team2": tmp[b"team2"].decode()}

    @map_state.setter
    def map_state(self, value: dict) -> None:
        """
        Sets values from dictionary to redis. This must be done with sub-keys one by one, as object breaks otherwise

        :param value: New map_state dictionary to be appended to redis with 3 sub-keys: visible, team1, team2
        """
        self.redis.hset("map_state", "visible", str(int(value["visible"])))
        self.redis.hset("map_state", "team1", value["team1"])
        self.redis.hset("map_state", "team2", value["team2"])

    @property
    def overlay_mode(self) -> Literal["GP", "Wybory", "Turniej"]:
        """
        Stores current overlay mode, defining its functionalities
        """
        return self.redis.get("overlay_mode").decode()

    @overlay_mode.setter
    def overlay_mode(self, value: Literal["GP", "Wybory", "Turniej"]) -> None:
        """
        Sets overlay_mode key on redis

        :param value: Must be one of GP, Wybory, Turniej
        """
        self.redis.set("overlay_mode", value)

    @property
    def teams(self) -> list:
        """
        Stores current team names as list
        :return: Two item list of team names
        """
        return [item.decode() for item in self.redis.lrange("teams", 0, -1)]

    @teams.setter
    def teams(self, value) -> None:
        """
        Sets new team names on redis. For clarity previous values are removed from redis, before setting new ones.
        :param value: Two item list containing new team names
        """
        self.redis.delete("teams")
        self.redis.rpush("teams", *value)

    @property
    def infobar(self) -> list:
        """
        Stores current infobar messages
        :return: array of messages
        """
        return [item.decode() for item in self.redis.lrange("info_bar", 0, -1)]

    @infobar.setter
    def infobar(self, value: list) -> None:
        """
        Sets new array of messages on redis.
        .. warn:
            This does not append new values to arrays, it creates new array

        :param value: new array to be sent to redis
        """
        self.redis.delete("info_bar")
        self.redis.rpush("info_bar", *value)

    def _setup_redis(self) -> None:
        """
        Simple helper function to setup redis.
        All parameters should be handled using Environmental Variables in docker
        """
        self.redis = redis.Redis(host=os.getenv("BROKER_BACKEND_URL"), db=0)

    def _update_values(self) -> None:
        """
        Ensures that all values on redis are set
        """
        # TODO: Those should check if the value is not already present on redis
        # This will enable overlay to be quickly restarted without loosing session
        self.timer = TimerState()

        self.infobar = ["Transmisja wkrótce się rozpocznie"]

        self.emblem_visible = False

        # TODO those do not respond

        self.comment_mode = False
            
        self.infobar_visible = True

        # Those are actually contents of the table describing map points, not teams as field names suggest
        self.map_state = {"visible": False,
                          "team1": "",
                          "team2": ""}
        self.teams = ["NA", "NA"]

        self.overlay_mode = "GP"

        self.darkmode = True

    def dump_to_config(self) -> None:
        """
        Simple helper function to write configuration into config file
        """
        if not os.path.exists(self._config_file):
            self.populate_deafult_config(self._config_file)

        with open(self._config_file, 'w+') as file:
            self._configparser.write(file)

    @staticmethod
    def populate_deafult_config(config_file) -> None:
        """
        Write default overlay configuration to config file
        :param config_file: config file filename/directory
        """
        config = configparser.ConfigParser()
        config.read(config_file)
        config.set('DEFAULT', 'emblem_visible', "False")
        config.set('DEFAULT', 'comment_mode', "False")
        config.set('DEFAULT', 'infobar_visible', "True")
        config.set("DEFAULT", "overlay_mode", "GP")
        with open(config_file, 'w+') as file:
            config.write(file)