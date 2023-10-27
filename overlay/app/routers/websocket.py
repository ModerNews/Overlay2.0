from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

from .. import base_class
from ..dependencies.timer import *

websocket_router = APIRouter(prefix='/websocket')  # Additional router to handle all websocket connections
__all__ = ["manager", "websocket_router"]


class ConnectionManager:
    """
    Simple manager for websocket connections handles passing messages from one client to others
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []  # list of currently connected websocket clients

    async def connect(self, websocket: WebSocket) -> None:
        """
        Append new client to manager

        :param websocket: class representing newly appended client
        """
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect client from manager

        :param websocket: websocket to be removed
        """
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass  # websocket was already disconnected

    async def send_text(self, message: str, *, receivers: Optional[list[WebSocket]] = None) -> dict:
        """
        Sends text object to specified clients (if available in network)

        :param message: text message to be sent
        :param receivers: Optional, contains objects of clients which will receive message, all clients will be picked if none are specified
        :return: Dictionary containing information on functions execution
        """
        if not receivers:
            receivers = self.active_connections
        response_object = {"code": 207, "clients": {},
                           "message": message}  # prep response object, 207 indicates multiple clients will be contained in response
        for connection in receivers:
            try:
                await connection.send_text(message)
                response_object["clients"][receivers.index(connection)] = {"code": 200}
            except (WebSocketDisconnect, ConnectionClosed):
                manager.disconnect(connection)
                response_object["clients"][receivers.index(connection)] = {
                    "code": 410}  # 410 Gone - indicates endpoint (websocket) no longer exists
        return response_object

    async def send_json(self, message: str, *, receivers: Optional[list[WebSocket]] = None) -> dict:
        """
        Sends JSON-like object to specified clients (if available in network)

        :param message: JSON-like message to be sent in pythonic dictionary format
        :param receivers: Optional, contains objects of clients which will receive message, all clients will be picked if none are specified
        :return: Dictionary containing information on functions execution
        """
        if not receivers:
            receivers = self.active_connections
        response_object = {"code": 207, "clients": {},
                           "message": message}  # prep response object, 207 indicates multiple clients will be contained in response
        for connection in receivers:
            try:
                await connection.send_json(message)
                response_object["clients"][receivers.index(connection)] = {"code": 200}
            except (WebSocketDisconnect, ConnectionClosed):
                manager.disconnect(connection)
                response_object["clients"][receivers.index(connection)] = {
                    "code": 410}  # 410 Gone - indicates endpoint (websocket) no longer exists
        return response_object


manager = ConnectionManager()


async def update_websocket(websocket: WebSocket):
    app: base_class.StreamOverlay = websocket.app
    await websocket.send_json({"event": "infobar", "content": app.infobar})
    await websocket.send_json({"event": "show_emblem", "value": app.emblem_visible})
    await websocket.send_json({"event": "show_bottom", "value": app.infobar_visible})
    await websocket.send_json({"event": "show_lobby", "value": app.comment_mode})
    await websocket.send_json({"event": "predefs", "content": app.predefs})
    await websocket.send_json({"event": "candidates", "content": app.candidates})
    await websocket.send_json({"event": "timer_state", "state": app.timer.to_dict()})
    await websocket.send_json({"event": "maps_state", "state": app.map_state})
    await websocket.send_json({"event": "overlay_mode", "mode": app.overlay_mode})
    await websocket.send_json({"event": "teams", "team1": app.teams[0], "team2": app.teams[1]})
    await websocket.send_json({"event": "darkmode", "value": app.darkmode})


@websocket_router.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    app: base_class.StreamOverlay = websocket.app
    await websocket.accept()
    await update_websocket(websocket)
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received:\n{data}")
            if data["event"] == "timer":
                # WARNING: None of those events shows the timer, timer may run in background
                if data["type"] == "start" and not websocket.app.timer.running:  # Starts countdown timer on page
                    websocket.app.timer.running = True
                    websocket.app.timer.started_at = datetime.datetime.now()
                    data = {"event": "timer_state", "state": websocket.app.timer.to_dict()}
                elif data["type"] == "stop":  # Stops countdown timer, stopping the timer does not reset the value
                    websocket.app.update_timer()
                    websocket.app.timer.running = False
                    data = {"event": "timer_state", "state": websocket.app.timer.to_dict()}
                elif data["type"] == "set":  # Updates timer with new values from controller
                    websocket.app.timer.running = False
                    websocket.app.timer.time = int(data["time"])
                    data = {"event": "timer_state", "state": websocket.app.timer.to_dict()}
                elif data["type"] == "sound":
                    websocket.app.timer.sound = data["value"]
                    data = {"event": "timer_state", "state": websocket.app.timer.to_dict()}

            elif data['event'] == 'setup_system':
                # Ideally sent only once, when start page is exited
                app.overlay_mode = data['mode']
                app.teams = data['teams'] if list(data['teams']) != ['', ''] else app.teams

            elif data['event'] == "show_emblem":
                # Controls header visibility
                app.emblem_visible = data['value']
                data = {"event": "show_emblem", "value": app.emblem_visible}

            elif data['event'] == "show_bottom":
                # Controls infobar visibility
                app.infobar_visible = data['value']
                data = {"event": "show_bottom", "value": app.infobar_visible}

            elif data['event'] == "show_lobby":
                # Controls middle header visibility
                app.comment_mode = data['value']
                data = {"event": "show_lobby", "value": app.comment_mode}

            elif data['event'] == "infobar":
                # Changes current infobar contents, multiple messages will be split with logo
                app.infobar = data['content']
                data = {"event": "infobar", "content": app.infobar}

            elif data['event'] == "predefs":
                # Sends predefined lines for pop-up bar from strings.txt
                app.predefs = data['content']
                data = {"event": "predefs", "content": app.predefs}

            elif data['event'] == 'candidates':
                # For results graph only, sends list of candidates to which points can be assigned in controller
                app.candidates = data['content']
                data = {"event": "candidates", "content": app.candidates}

            elif data['event'] == 'maps_state':
                # This is responsible for small boxes under header with additional information
                # State contains two strings, with keys: team1, team2
                # As well as additional field "visible", which determines if boxes should be visible in overlay
                app.map_state = data['state']
                data = {"event": "maps_state", "state": app.map_state}

            elif data['event'] == 'update_teams':
                # This can be used to change team names, visible in header, on the fly
                app.teams = [data['team1'], data['team2']]
                data = {"event": "update_teams", "team1": app.teams[0], "team2": app.teams[1]}

            elif data['event'] == 'config_dump':
                # Listener only, dumps current config into cfg file.
                websocket.app.dump_to_config()
                continue

            elif data['event'] == 'darkmode':
                app.darkmode = data['value']
                data = {"event": "darkmode", "value": app.darkmode}

            print(f"Sent:\n{data}")
            await manager.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
