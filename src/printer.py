"""
Copyright 2024 Joe Maples <joe@maples.dev>

This file is part of OpenQ1Display.

OpenQ1Display is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

OpenQ1Display is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
OpenQ1Display. If not, see <https://www.gnu.org/licenses/>. 
"""

import json
import logging

from enum import StrEnum
from moonraker_api import MoonrakerClient, MoonrakerListener
from moonraker_api.websockets.websocketclient import (
    WEBSOCKET_STATE_CONNECTING,
    WEBSOCKET_STATE_CONNECTED,
    WEBSOCKET_STATE_STOPPING,
    WEBSOCKET_STATE_STOPPED,
    WEBSOCKET_CONNECTION_TIMEOUT,
)
from typing import Any, Awaitable, Callable, Literal
from config import *


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
        "extruder": ["temperature", "target"],
        "heater_generic heater_bed_outer": ["temperature", "target"],
        "display_status": ["progress"],
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

    async def subscribe(self):
        return await self.client.call_method(
            "printer.objects.subscribe", objects=self._printerObjects
        )

    async def queryKlippyStatus(self):
        status = await self.client.get_klipper_status()
        if status == "ready":
            self.status = json.load(await self._queryPrinterState())
            await self.stateCallback(PrinterState.READY)
        elif status == "shutdown" or status == "disconnected":
            await self.stateCallback(PrinterState.KLIPPER_ERR)

    async def _queryPrinterState(self):
        return await self.client.call_method(
            "printer.objects.query", objects=self._printerObjects
        )

    async def _updateState(self, state: PrinterState) -> Awaitable:
        self.state = state
        return self.stateCallback()

    async def state_changed(self, state: str | Literal[120]):
        printerStatus = PrinterState.NOT_READY
        if state == WEBSOCKET_STATE_CONNECTING:
            pass
        elif state == WEBSOCKET_STATE_CONNECTED:
            await self.queryKlippyStatus()
            logging.info("status %s" % str(await self.subscribe()))
        elif state == WEBSOCKET_STATE_STOPPING:
            pass
        elif state == WEBSOCKET_STATE_STOPPED:
            printerStatus = PrinterState.STOPPED
        elif state == WEBSOCKET_CONNECTION_TIMEOUT:
            printerStatus = PrinterState.MOONRAKER_ERR

        await self._updateState(printerStatus)

    async def on_notification(self, method: str, data: Any):
        if method == Notifications.KLIPPY_READY:
            self.status = json.load(await self._queryPrinterState())
            await self._updateState(PrinterState.READY)
        elif method == Notifications.KLIPPY_SHUTDOWN:
            await self._updateState(PrinterState.KLIPPER_ERR)
        elif method == Notifications.KLIPPY_DISCONNECTED:
            await self._updateState(PrinterState.KLIPPER_ERR)
        elif method == Notifications.STATUS_UPDATE:
            self.status = json.load(data)["status"]
            logging.info("Status update")
            await self.printerCallback(self.status)
        elif method == Notifications.FILES_CHANGED:
            await self.filesCallback(json.load(data))

    async def on_exception(self, exception: type | BaseException) -> None:
        """TODO"""
