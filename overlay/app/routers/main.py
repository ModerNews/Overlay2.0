import asyncio
import datetime
import json
import hashlib
import logging
import os
import configparser

from logging.config import dictConfig
from typing import Optional

import uvicorn

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..dependencies.timer import *

router = APIRouter()


@router.get("/overlay")
async def index_loader(request: Request):
    print(request.app.teams[0], request.app.teams[1])
    return request.app.templating.TemplateResponse("index.html", {"request": request, "team1": request.app.teams[0], "team2": request.app.teams[1]})
    # with open('../templates/index.html', encoding='utf8') as file:
    #     data = file.read()
    # return HTMLResponse(data)


@router.get("/")
async def start_overlay(request: Request):
    return request.app.templating.TemplateResponse("start_page.html", {"request": request})



@router.get("/controller")
async def main_controller(request: Request):
    return request.app.templating.TemplateResponse("controller.html", {"request": request})
    # with open('../templates/controller.html', encoding='utf8') as file:
    #     data = file.read()
    # return HTMLResponse(data)

@router.get("/tournament")
async def tournament_view(request: Request):
    return request.app.templating.TemplateResponse('tournament-table.html', {"request": request})
    # with open('../templates/tournament-table.html', encoding='utf8') as file:
    #     data = file.read()
    # return HTMLResponse(data)

@router.get("/ladder")
async def tournament_view(request: Request):
    return request.app.templating.TemplateResponse('tournament-ladder.html', {"request": request})


@router.get('/results')
async def results_view(request: Request):
    return request.app.templating.TemplateResponse('results.html', {"request": request})