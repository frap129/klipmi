#!/usr/bin/env python3
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

import asyncio
import logging

from nextion import TJC, EventType
from setproctitle import setproctitle
from typing import List

from state import State
from config import *
from printer import Printer, PrinterStatus
from pages import registerPages, BasePage


class OpenQ1Display:
    def __init__(self):
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
            handlers=[logging.StreamHandler()],
        )
        self.pages = registerPages()
        self.state: State = State()
        self.state.options = Config(getConfigPath())
        self.state.display = TJC(
            self.state.options[TABLE_DISPLAY][KEY_DEVICE],
            self.state.options[TABLE_DISPLAY][KEY_BAUD],
            self.onDisplayEvent,
        )
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
        logging.debug("Display: Event %s data: %s", type, str(data))
        logging.debug("Passing event to page %s", self.currentPage().name)
        asyncio.create_task(self.currentPage().onDisplayEvent(type, data))

    async def onConnectionEvent(self, status: PrinterStatus):
        logging.info("Conenction status: %s", status)
        if status == PrinterStatus.NOT_READY:
            asyncio.create_task(self.changePage("boot"))
            pass
        elif status == PrinterStatus.READY:
            asyncio.create_task(self.changePage("main"))
            pass
        elif status == PrinterStatus.STOPPED:
            pass
        elif status == PrinterStatus.MOONRAKER_ERR:
            pass
        elif status == PrinterStatus.KLIPPER_ERR:
            pass

    async def onPrinterStatusUpdate(self, data: dict):
        self.state.printerData = data
        asyncio.create_task(self.currentPage().onPrinterStatusUpdate(data))

    async def onFileListUpdate(self, data: dict):
        self.state.fileList = data
        asyncio.create_task(self.currentPage().onFileListUpdate(data))

    async def changePage(self, page: str):
        if len(self.backstack) >= 2 and self.backstack[-2].name == page:
            self.backstack.pop()
        else:
            self.backstack.append(self.pages[page](self.state, self.changePage))

        await self.state.display.command("page %d" % self.currentPage().id)

    async def init(self):
        await self.state.display.connect()
        await self.state.display.wakeup()
        asyncio.create_task(self.changePage("boot"))
        await self.state.printer.connect()


if __name__ == "__main__":
    setproctitle("OpenQ1Display")
    loop = asyncio.get_event_loop()
    app = OpenQ1Display()
    asyncio.ensure_future(app.init())
    loop.run_forever()
