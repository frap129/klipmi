"""
Copyright 2024 Joe Maples <joe@maples.dev>

This file is part of klipmi.

klipmi is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

klipmi is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
klipmi. If not, see <https://www.gnu.org/licenses/>. 
"""

import requests
import io
import logging

from enum import StrEnum
from PIL import Image
from moonraker_api import MoonrakerClient, MoonrakerListener
from moonraker_api.websockets.websocketclient import (
    WEBSOCKET_STATE_CONNECTING,
    WEBSOCKET_STATE_CONNECTED,
    WEBSOCKET_STATE_STOPPING,
    WEBSOCKET_STATE_STOPPED,
    WEBSOCKET_CONNECTION_TIMEOUT,
)
from nextion.client import asyncio
from typing import Callable, Literal
from urllib.request import pathname2url

from config import Config, TABLE_MOONRAKER, KEY_HOST, KEY_PORT, KEY_API
from utils import update


class PrinterState(StrEnum):
    NOT_READY = "not ready"
    READY = "ready"
    STOPPED = "stopped"
    MOONRAKER_ERR = "moonraker error"
    KLIPPER_ERR = "klipper error"


class Notifications(StrEnum):
    KLIPPY_READY = "notify_klippy_ready"
    KLIPPY_SHUTDOWN = "notify_klippy_shutdown"
    KLIPPY_DISCONNECTED = "notify_klippy_shutdown"
    STATUS_UPDATE = "notify_status_update"
    GCODE_RESPONSE = "notify_gcode_response"
    FILES_CHANGED = "notify_filelist_changed"


class Printer(MoonrakerListener):
    _printerObjects: dict = {
        "gcode_move": ["extrude_factor", "speed_factor", "homing_origin"],
        "motion_report": ["live_position", "live_velocity"],
        "fan": ["speed"],
        "heater_bed": ["temperature", "target"],
        "extruder": ["target", "temperature"],
        "heater_generic chamber": ["temperature", "target"],
        "display_status": ["progress"],
        "output_pin caselight": ["value"],
        "output_pin sound": ["value"],
        "print_stats": [
            "state",
            "print_duration",
            "filename",
            "total_duration",
            "info",
        ],
    }

    def __init__(
        self,
        options: Config,
        stateCallback: Callable,
        printerCallback: Callable,
        filesCallback: Callable,
    ):
        self.stateCallback: Callable = stateCallback
        self.printerCallback: Callable = printerCallback
        self.filesCallback: Callable = filesCallback
        self.options: Config = options
        self.running: bool = False
        self.status: dict = {}
        self.client: MoonrakerClient = MoonrakerClient(
            self,
            options[TABLE_MOONRAKER][KEY_HOST],
            options[TABLE_MOONRAKER][KEY_PORT],
            options[TABLE_MOONRAKER][KEY_API],
        )

    async def connect(self) -> bool | None:
        self.running = True
        self.state = PrinterState.NOT_READY
        return await self.client.connect()

    async def disconnect(self) -> None:
        self.running = False
        await self._updateState(PrinterState.STOPPED)
        await self.client.disconnect()

    def runGcode(self, gcode: str):
        asyncio.create_task(
            self.client.call_method("printer.gcode.script", script=gcode)
        )

    def togglePin(self, pin: str):
        self.runGcode(
            "SET_PIN PIN=%s VALUE=%d"
            % (pin, 1 - self.status["output_pin %s" % pin]["value"])
        )

    async def getMetadata(self, filename):
        metadata = await self.client.call_method(
            "server.files.metadata", filename=filename
        )
        return metadata

    async def getThumbnail(self, size: int, filename: str, metadata: dict = {}):
        if metadata == {}:
            metadata = await self.getMetadata(filename)
        best_thumbnail = {}
        for thumbnail in metadata["thumbnails"]:
            if thumbnail["width"] == size:
                best_thumbnail = thumbnail
                break
            if best_thumbnail == {} or thumbnail["width"] > best_thumbnail["width"]:
                best_thumbnail = thumbnail

        path = "/".join(filename.split("/")[:-1])
        if path != "":
            path = path + "/"
        path += best_thumbnail["relative_path"]

        host = self.options[TABLE_MOONRAKER][KEY_HOST]
        if "http" not in host:
            host = "http://%s" % host

        img = requests.get(
            "%s/server/files/gcodes/%s" % (host, pathname2url(path)),
            timeout=5,
        )
        return Image.open(io.BytesIO(img.content))

    async def subscribe(self):
        await self.client.call_method(
            "printer.objects.subscribe", objects=self._printerObjects
        )

    async def _updateKlippyStatus(self):
        status = await self.client.get_klipper_status()
        if status == "ready":
            self.status = await self._getPrinterState()
            await self.stateCallback(PrinterState.READY)
        elif status == "shutdown" or status == "disconnected":
            await self.stateCallback(PrinterState.KLIPPER_ERR)

    async def _getPrinterState(self) -> dict:
        return (
            await self.client.call_method(
                "printer.objects.query", objects=self._printerObjects
            )
        )["status"]

    async def _updateState(self, state: PrinterState):
        self.state = state
        await self.stateCallback(state)

    async def state_changed(self, state: str | Literal[120]):
        printerStatus = PrinterState.NOT_READY
        if state == WEBSOCKET_STATE_CONNECTING:
            pass
        elif state == WEBSOCKET_STATE_CONNECTED:
            await self.subscribe()
            asyncio.create_task(self._updateKlippyStatus())
        elif state == WEBSOCKET_STATE_STOPPING:
            pass
        elif state == WEBSOCKET_STATE_STOPPED:
            printerStatus = PrinterState.STOPPED
        elif state == WEBSOCKET_CONNECTION_TIMEOUT:
            printerStatus = PrinterState.MOONRAKER_ERR

        await self._updateState(printerStatus)

    async def on_notification(self, method: str, data: list):
        if method == Notifications.KLIPPY_READY:
            self.status = await self._getPrinterState()
            await self._updateState(PrinterState.READY)
        elif method == Notifications.KLIPPY_SHUTDOWN:
            await self._updateState(PrinterState.KLIPPER_ERR)
        elif method == Notifications.KLIPPY_DISCONNECTED:
            await self._updateState(PrinterState.KLIPPER_ERR)
        elif method == Notifications.STATUS_UPDATE:
            update(self.status, data[0])
            await self.printerCallback(self.status)
        elif method == Notifications.FILES_CHANGED:
            await self.filesCallback(data)

    async def on_exception(self, exception: type | BaseException) -> None:
        """TODO"""
