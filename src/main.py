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

import asyncio
import logging

from nextion import TJC, EventType
from setproctitle import setproctitle

from klipmi import ui
from klipmi.model.config import Config
from klipmi.model.printer import Printer, PrinterState
from klipmi.model.state import KlipmiState
from klipmi.model.ui import BaseUi


class Klipmi:
    def __init__(self):
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
            handlers=[logging.StreamHandler()],
        )

        self.state: KlipmiState = KlipmiState()
        self.state.options = Config()
        self.state.display = TJC(
            self.state.options.klipmi.device,
            self.state.options.klipmi.baud,
            self.onDisplayEvent,
        )
        self.state.display.encoding = "utf-8"
        self.state.printer = Printer(
            self.state.options.moonraker,
            self.onConnectionEvent,
            self.onPrinterStatusUpdate,
            self.onFileListUpdate,
        )
        self.ui: BaseUi = ui.implementations[self.state.options.klipmi.ui](self.state)

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.RECONNECTED:
            # Force update status on reconnect
            await self.onConnectionEvent(self.state.status)
        else:
            asyncio.create_task(self.ui.onDisplayEvent(type, data))

    async def onConnectionEvent(self, status: PrinterState):
        logging.info("Conenction status: %s", status)
        self.state.status = status
        if status == PrinterState.NOT_READY:
            self.ui.onNotReady()
        elif status == PrinterState.READY:
            self.ui.onReady()
        elif status == PrinterState.STOPPED:
            self.ui.onMoonrakerError()
        elif status == PrinterState.KLIPPER_ERR:
            self.ui.onKlipperError()

    async def onPrinterStatusUpdate(self, data: dict):
        asyncio.create_task(self.ui.onPrinterStatusUpdate(data))

    async def onFileListUpdate(self, data: dict):
        self.state.fileList = data
        asyncio.create_task(self.ui.onFileListUpdate(data))

    async def init(self):
        await self.state.display.connect()
        await self.state.display.wakeup()
        self.ui.onNotReady()
        await self.state.printer.connect()

    def start(self):
        self.state.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.init(), loop=self.state.loop)
        self.state.loop.run_forever()


def main():
    setproctitle("klipmi")
    Klipmi().start()


if __name__ == "__main__":
    main()
