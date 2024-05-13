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

from nextion import EventType

from klipmi.model.ui import BasePage
from klipmi.utils import classproperty


class MainPage(BasePage):
    @classproperty
    def name(cls) -> str:
        return "main"

    @classproperty
    def id(cls) -> int:
        return 3

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

    async def init(self):
        await self.state.display.set("b6.picc", 31)

    async def onDisplayEvent(self, type: EventType, data):
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

        filename = data["print_stats"]["filename"]
        await self.state.display.set("t0.txt", filename)
        if filename == "":
            await self.state.display.command("vis cp0,0")
        else:
            if filename != self.filename:
                self.filename = filename
                if self.metadata == {}:
                    self.metadata = await self.state.printer.getMetadata(self.filename)
                await self.uploadThumbnail(
                    "cp0", 160, "4d4d4d", self.filename, self.metadata
                )
                await self.state.display.command("vis cp0,1")
