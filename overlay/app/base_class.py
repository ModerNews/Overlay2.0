
import os
import configparser
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

        self.timer = TimerState()
        self.info_bar = []
        self.emblem_visible = self._configparser.getboolean('DEFAULT', 'emblem_visible')
        self.comment_mode = self._configparser.getboolean('DEFAULT', 'comment_mode')
        self.infobar_visible = self._configparser.getboolean('DEFAULT', 'infobar_visible')
        self.map_state = {"visible": False,
                     "team1": "Vape Clan",
                     "team2": "D0mmyM0mmies"}
        self.overlay_mode = self._configparser.get("DEFAULT", "overlay_mode")

        self.teams = ["Nieznany", "Nieznany"]

        with open("/home/wybory/strings.txt") as file:
            self.predefs = [item.strip() for item in file.read().split("\n")]

        with open("/home/wybory/candidates.txt") as file:
            self.candidates = [item.strip() for item in file.read().split("\n")]

        super().__init__()
        self.mount("/static", StaticFiles(directory="/home/wybory/static"), name="static")
        self.templating = Jinja2Templates(directory="/home/wybory/templates")

    def dump_to_config(self):
        self._configparser.set('DEFAULT', 'emblem_visible', str(self.emblem_visible))
        self._configparser.set('DEFAULT', 'comment_mode', str(self.comment_mode))
        self._configparser.set('DEFAULT', 'infobar_visible', str(self.infobar_visible))
        self._configparser.set("DEFAULT", "overlay_mode", str(self.overlay_mode))
        with open(self._config_file, 'w') as file:
            self._configparser.write(file)

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