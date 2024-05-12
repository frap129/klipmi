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
from typing import List

from klipmi.model.config import (
    Config,
    getConfigPath,
    TABLE_DISPLAY,
    KEY_DEVICE,
    KEY_BAUD,
)
from klipmi.model.printer import Printer, PrinterState
from klipmi.model.state import KlipmiState
from klipmi.model.ui import BasePage
from klipmi.ui.openq1 import registerPages


class Klipmi:
    def __init__(self):
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
            handlers=[logging.StreamHandler()],
        )
        self.pages = registerPages()
        self.state: KlipmiState = KlipmiState()
        self.state.options = Config(getConfigPath())
        self.state.display = TJC(
            self.state.options[TABLE_DISPLAY][KEY_DEVICE],
            self.state.options[TABLE_DISPLAY][KEY_BAUD],
            self.onDisplayEvent,
        )
        self.state.display.encoding = "utf-8"
        self.state.printer = Printer(
            self.state.options,
            self.onConnectionEvent,
            self.onPrinterStatusUpdate,
            self.onFileListUpdate,
        )
        self.backstack: List[BasePage] = []

    def currentPage(self) -> BasePage:
        return self.backstack[-1]

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.RECONNECTED:
            # Force update status on reconnect
            await self.onConnectionEvent(self.state.status)
        else:
            logging.info("Passing event to page %s", self.currentPage().name)
            asyncio.create_task(self.currentPage().onDisplayEvent(type, data))

    async def onConnectionEvent(self, status: PrinterState):
        logging.info("Conenction status: %s", status)
        self.state.status = status
        if status == PrinterState.NOT_READY:
            await self.changePage("boot")
            pass
        elif status == PrinterState.READY:
            await self.changePage("main")
            pass
        elif status == PrinterState.STOPPED:
            pass
        elif status == PrinterState.MOONRAKER_ERR:
            pass
        elif status == PrinterState.KLIPPER_ERR:
            pass

    async def onPrinterStatusUpdate(self, data: dict):
        asyncio.create_task(self.currentPage().onPrinterStatusUpdate(data))

    async def onFileListUpdate(self, data: dict):
        self.state.fileList = data
        asyncio.create_task(self.currentPage().onFileListUpdate(data))

    async def changePage(self, page: str):
        if len(self.backstack) >= 2 and self.backstack[-2].name == page:
            self.backstack.pop()
        else:
            self.backstack.append(self.pages[page](self.state, self.changePage))

        await self.state.display.wakeup()
        await self.state.display.command(
            "page %d" % self.currentPage().id, self.state.options.timeout
        )
        await self.currentPage().init()

    async def init(self):
        await self.state.display.connect()
        await self.state.display.wakeup()
        await self.changePage("boot")
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
