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

router = APIRouter()  # Base router containing all http routes to be imported
__all__ = ['router']

@router.get("/overlay")
async def index_loader(request: Request):
    """
    Endpoint for main page - displaying overlay, which can be rendered on video
    """
    print(request.app.teams[0], request.app.teams[1])
    return request.app.templating.TemplateResponse("index.html", {"request": request, "team1": request.app.teams[0], "team2": request.app.teams[1]})


@router.get("/")
async def start_overlay(request: Request):
    """
    Page with basic configuration and information on upcoming stream

    Possible states are:
    * "GP" - for general purpose
    * "Wybory" - for voting system - generates vote count page using data from candidates
    * "Turniej" - Takes additional data - names of two teams, and prepares additional toggleable headers
    """
    # TODO debug mode enabling all possible controls
    return request.app.templating.TemplateResponse("start_page.html", {"request": request})



@router.get("/controller")
async def main_controller(request: Request):
    """
    Main page for control team - contains all configuration options enabled in current mode
    Additional toggleable configurations are stored in their own divs for easier management
    """
    return request.app.templating.TemplateResponse("controller.html", {"request": request})


@router.get("/tournament")
async def tournament_view(request: Request):
    """
    DEBUG ONLY
    """
    return request.app.templating.TemplateResponse('tournament-table.html', {"request": request})

@router.get("/ladder")
async def tournament_view(request: Request):
    """
    DEBUG ONLY
    """
    return request.app.templating.TemplateResponse('tournament-ladder.html', {"request": request})


@router.get('/results')
async def results_view(request: Request):
    """
    Renders page with vote count displayed on animated bar graph
    Each bar's animation can be started using their respective buttons in `/controller`
    .. warn:
        Insert all values before starting animations - all values will be summed to calculate percentages and bar heights
    """
    return request.app.templating.TemplateResponse('results.html', {"request": request})