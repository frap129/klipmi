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
from typing import Callable, Coroutine, Dict, List, Literal
from urllib.request import pathname2url

from klipmi.model.config import MoonrakerConfig
from klipmi.utils import updateNestedDict


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
    def __init__(
        self,
        options: MoonrakerConfig,
        stateCallback: Callable,
        printerCallback: Callable,
        filesCallback: Callable,
        objects: Dict[str, List[str]],
    ):
        self.stateCallback: Callable = stateCallback
        self.printerCallback: Callable = printerCallback
        self.filesCallback: Callable = filesCallback
        self.options: MoonrakerConfig = options
        self.objects = objects
        self.running: bool = False
        self.status: dict = {}
        self.files: dict = {}
        self.client: MoonrakerClient = MoonrakerClient(
            self, options.host, options.port, options.api_key
        )

    async def connect(self) -> bool | None:
        self.running = True
        self.state = PrinterState.NOT_READY
        return await self.client.connect()

    async def disconnect(self) -> None:
        self.running = False
        await self.__updateState(PrinterState.STOPPED)
        await self.client.disconnect()

    async def state_changed(self, state: str | Literal[120]):
        tasks: List[Coroutine] = []
        printerStatus = PrinterState.NOT_READY
        if state == WEBSOCKET_STATE_CONNECTING:
            pass
        elif state == WEBSOCKET_STATE_CONNECTED:
            tasks.append(self.__subscribe())
            tasks.append(self.__updateKlippyStatus())
        elif state == WEBSOCKET_STATE_STOPPING:
            pass
        elif state == WEBSOCKET_STATE_STOPPED:
            printerStatus = PrinterState.STOPPED
        elif state == WEBSOCKET_CONNECTION_TIMEOUT:
            printerStatus = PrinterState.MOONRAKER_ERR

        tasks.append(self.__updateState(printerStatus))
        asyncio.gather(*tasks)

    async def on_notification(self, method: str, data: list):
        tasks: List[Coroutine] = []
        if method == Notifications.KLIPPY_READY:
            tasks.append(self.__updatePrinterStatus())
            tasks.append(self.__subscribe())
            tasks.append(self.__updateKlippyStatus())
            tasks.append(self.__updateState(PrinterState.READY))
        elif method == Notifications.KLIPPY_SHUTDOWN:
            tasks.append(self.__updateState(PrinterState.KLIPPER_ERR))
        elif method == Notifications.KLIPPY_DISCONNECTED:
            tasks.append(self.__updateState(PrinterState.KLIPPER_ERR))
        elif method == Notifications.STATUS_UPDATE:
            updateNestedDict(self.status, data[0])
            tasks.append(self.printerCallback(self.status))
        elif method == Notifications.FILES_CHANGED:
            self.files = data[0]
            tasks.append(self.filesCallback(self.files))
        asyncio.gather(*tasks)

    async def on_exception(self, exception: type | BaseException) -> None:
        """TODO"""

    async def __subscribe(self):
        await self.client.call_method("printer.objects.subscribe", objects=self.objects)

    async def __updateKlippyStatus(self):
        status = await self.client.get_klipper_status()
        if status == "ready":
            await self.__updatePrinterStatus()
            await self.stateCallback(PrinterState.READY)
        elif status == "shutdown" or status == "disconnected":
            await self.stateCallback(PrinterState.KLIPPER_ERR)

    async def __updatePrinterStatus(self):
        self.status = (
            await self.client.call_method("printer.objects.query", objects=self.objects)
        )["status"]

    async def __updateState(self, state: PrinterState):
        self.state = state
        await self.stateCallback(state)

    async def getMetadata(self, filename):
        metadata = await self.client.call_method(
            "server.files.metadata", filename=filename
        )
        return metadata

    async def getThumbnail(self, size: int, filename: str):
        thumbnailsList = await self.client.call_method(
            "server.files.thumbnails", filename=filename
        )

        thumbnail = {}
        for item in thumbnailsList:
            if item["width"] == size:
                thumbnail = item
                break
            if thumbnail == {} or item["width"] > item["width"]:
                thumbnail = item

        path = thumbnail["thumbnail_path"]
        host = self.options.host
        if "http" not in host:
            host = "http://%s" % host

        img = requests.get(
            "%s/server/files/gcodes/%s" % (host, pathname2url(path)),
            timeout=5,
        )
        return Image.open(io.BytesIO(img.content))

    def runGcode(self, gcode: str):
        asyncio.create_task(
            self.client.call_method("printer.gcode.script", script=gcode)
        )

    def emergencyStop(self):
        asyncio.create_task(self.client.call_method("printer.emergency_stop"))

    def restart(self):
        asyncio.create_task(self.client.call_method("printer.restart"))

    def firmwareRestart(self):
        asyncio.create_task(self.client.call_method("printer.firmware_restart"))

    def startPrint(self, filename: str):
        asyncio.create_task(
            self.client.call_method("printer.print.start", filename=filename)
        )

    def pausePrint(self):
        asyncio.create_task(self.client.call_method("printer.print.pause"))

    def resumePrint(self):
        asyncio.create_task(self.client.call_method("printer.print.resume"))

    def cancelPrint(self):
        asyncio.create_task(self.client.call_method("printer.print.cancel"))

    def togglePin(self, pin: str):
        self.runGcode(
            "SET_PIN PIN=%s VALUE=%d"
            % (pin, 1 - self.status["output_pin %s" % pin]["value"])
        )
