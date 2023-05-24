from typing import Optional
import os

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..dependencies.timer import *

websocket_router = APIRouter(prefix='/websocket')


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def send_text(self, message: str, *, websocket: Optional[WebSocket] = None):
        if websocket is None:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    manager.disconnect(connection)
            return {"code": 200, "message": message, "times_send": len(self.active_connections)}
        await websocket.send_text(message)
        return {"code": 200, "message": message, "times_send": 1}

    async def send_json(self, message: dict, *, websocket: Optional[WebSocket] = None):
        if websocket is None:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except:
                    manager.disconnect(connection)
            return {"code": 200, "message": message, "times_send": len(self.active_connections)}
        await websocket.send_json(message)
        return {"code": 200, "message": message, "times_send": 1}


manager = ConnectionManager()

@websocket_router.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"event": "infobar", "content": websocket.app.info_bar})
    await websocket.send_json({"event": "show_emblem", "value": websocket.app.emblem_visible})
    await websocket.send_json({"event": "show_bottom", "value": websocket.app.infobar_visible})
    await websocket.send_json({"event": "show_lobby", "value": websocket.app.comment_mode})
    await websocket.send_json({"event": "predefs", "content": websocket.app.predefs})
    await websocket.send_json({"event": "candidates", "content": websocket.app.candidates})
    await websocket.send_json({"event": "timer_state", "state": websocket.app.timer.__dict__()})
    await websocket.send_json({"event": "maps_state", "state": websocket.app.map_state})
    await websocket.send_json({"event": "setup_system", "mode": websocket.app.overlay_mode})
    await websocket.send_json({"event": "teams", "team1": websocket.app.teams[0], "team2": websocket.app.teams[1]})
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received:\n{data}")
            if data["event"] == "timer":
                if data["type"] == "start" and not websocket.app.timer.running:
                    websocket.app.timer.running = True
                    websocket.app.timer.started_at = datetime.datetime.now()
                    data = {"event": "timer_state", "state": websocket.app.timer.__dict__()}
                elif data["type"] == "stop":
                    websocket.app.timer = update_timer(websocket.app.timer)
                    websocket.app.timer.running = False
                    data = {"event": "timer_state", "state": websocket.app.timer.__dict__()}
                elif data["type"] == "set":
                    websocket.app.timer.running = False
                    websocket.app.timer.time = int(data["time"])
                    data = {"event": "timer_state", "state": websocket.app.timer.__dict__()}

            elif data['event'] == 'setup_system':
                websocket.app.overlay_mode = data['mode']
                os.system("explorer http://localhost:80/controller")
                data = {"event": "setup_system", "mode": websocket.app.overlay_mode}

            elif data['event'] == "show_emblem":
                websocket.app.emblem_visible = data['value']
                data = {"event": "show_emblem", "value": websocket.app.emblem_visible}

            elif data['event'] == "show_bottom":
                websocket.app.infobar_visible = data['value']
                data = {"event": "show_bottom", "value": websocket.app.infobar_visible}

            elif data['event'] == "show_lobby":
                websocket.app.comment_mode = data['value']
                data = {"event": "show_lobby", "value": websocket.app.comment_mode}

            elif data['event'] == "infobar":
                websocket.app.info_bar = data['content']
                data = {"event": "infobar", "content": websocket.app.info_bar}

            elif data['event'] == "predefs":
                websocket.app.predefs = data['content']
                data = {"event": "predefs", "content": websocket.app.predefs}

            elif data['event'] == 'candidates':
                websocket.app.candidates = data['content']
                data = {"event": "candidates", "content": websocket.app.candidates}

            elif data['event'] == 'maps_state':
                websocket.app.map_state = data['state']
                data = {"event": "maps_state", "state": websocket.app.map_state}

            elif data['event'] == 'teams':
                websocket.app.teams[0] = data['team1']
                websocket.app.teams[1] = data['team2']
                print(websocket.app.teams)
                data = {"event": "teams", "team1": data['team1'], "team2": data["team2"]}

            elif data['event'] == 'config_dump':
                websocket.app.dump_to_config()
                continue

            print(f"Sent:\n{data}")
            await manager.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
