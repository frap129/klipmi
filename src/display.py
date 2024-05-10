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
from .config import *
from .printer import Printer


class State:
    def __init__(self):
        self.options: Config
        self.display: TJC
        self.printer: Printer
        self.backstack = []


class OpenQ1Display:
    def __init__(self):
        setproctitle("OpenQ1Display")
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
            handlers=[logging.StreamHandler()],
        )
        self.state: State = State()
        self.state.options = Config(getConfigPath())
        self.state.display = TJC(
            self.state.options[TABLE_DISPLAY][KEY_DEVICE],
            self.state.options[TABLE_DISPLAY][KEY_BAUD],
            self.onDisplayEvent,
        )
        self.state.printer = Printer(
            self.state.options, self.onMoonrakerEvent, self.onPrinterEvent
        )

    async def onDisplayEvent(self, type: EventType, data):
        logging.info("Event %s data: %s", type, str(data))

    async def onMoonrakerEvent(self, state: str):
        logging.info("Moonraker status: %s", state)

    async def onPrinterEvent(self, method: str, data):
        """TODO"""

    async def init(self):
        await self.state.display.connect()
        await self.state.printer.connect()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    app = OpenQ1Display()
    asyncio.ensure_future(app.init())
    loop.run_forever()
