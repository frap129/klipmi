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

import logging

from collections.abc import Callable
from nextion import EventType

from libcolpic import parse_thumbnail
from state import State
from utils import SimpleDict


def registerPages() -> SimpleDict:
    pages = SimpleDict()

    # pages[BasePage.name] = BasePage
    pages[BootPage.name] = BootPage
    pages[MainPage.name] = MainPage

    return pages


class BasePage:
    name = ""
    id = -1

    def __init__(self, state: State, changePageCallback: Callable):
        self.state = state
        self.changePageCallback = changePageCallback

    async def init(self):
        """Implimented on a page-by-page basis"""

    async def onDisplayEvent(self, type: EventType, data):
        logging.info("Event %s data: %s", type, str(data))

    async def onPrinterStatusUpdate(self, data: dict):
        """Implimented on a page-by-page basis"""

    async def onFileListUpdate(self, data: dict):
        """NO-OP for non-files pages"""

    def changePage(self, page: str):
        self.changePageCallback(page)


class BootPage(BasePage):
    name = "boot"
    id = 0

    async def init(self):
        await self.state.display.set("version.val", 18, self.state.options.timeout)


class MainPage(BasePage):
    name = "main"
    id = 15

    # Element image id's
    _regular = 32
    _highlight = 33

    # Thumbnail
    filename = ""
    metadata = {}

    def isHeating(self, heaterData: dict) -> bool:
        return heaterData["target"] > heaterData["temperature"]

    async def setHighlight(self, element: str, highlight: bool):
        await self.state.display.set(
            "%s.picc" % element, self._highlight if highlight else self._regular
        )

    async def onDisplayEvent(self, type: EventType, data):
        await super().onDisplayEvent(type, data)
        if type == EventType.TOUCH:
            if data.component_id == 0:
                self.state.printer.togglePin("caselight")
            elif data.component_id == 1:
                self.state.printer.togglePin("sound")
                self.state.printer.togglePin("beep")
            elif data.component_id == 2:
                self.state.printer.runGcode("M112")

    async def onPrinterStatusUpdate(self, data: dict):
        await self.state.display.set("n0.val", int(data["extruder"]["temperature"]))
        await self.setHighlight("b3", self.isHeating(data["extruder"]))

        await self.state.display.set("n1.val", int(data["heater_bed"]["temperature"]))
        await self.setHighlight("b4", self.isHeating(data["heater_bed"]))

        await self.state.display.set(
            "n2.val", int(data["heater_generic chamber"]["temperature"])
        )
        await self.setHighlight("b5", self.isHeating(data["heater_generic chamber"]))

        await self.setHighlight("b0", data["output_pin caselight"]["value"] > 0)
        await self.setHighlight("b1", data["output_pin sound"]["value"] > 0)

        self.filename = data["print_stats"]["filename"]
        await self.state.display.set("t0.txt", self.filename)
        if self.filename == "":
            await self.state.display.set("b6.picc", 31)
            await self.state.display.command("vis cp0,0")
        else:
            if self.metadata == {}:
                self.metadata = await self.state.printer.getMetadata(self.filename)

                thumbnail = parse_thumbnail(
                    await self.state.printer.getThumbnail(
                        160, self.filename, self.metadata
                    ),
                    160,
                    160,
                    "4d4d4d",
                )
                await self.state.display.command("p[" + str(self.id) + "].cp0.close()")

                parts = []
                start = 0
                end = 1024
                while start + 1024 < len(thumbnail):
                    parts.append(thumbnail[start:end])
                    start = start + 1024
                    end = end + 1024

                parts.append(thumbnail[start : len(thumbnail)])
                for part in parts:
                    await self.state.display.command(
                        "p[" + str(self.id) + '].cp0.write("' + str(part) + '")'
                    )
            await self.state.display.command("vis cp0,1")
