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

from PIL.Image import init
from nextion import EventType

from klipmi.model.ui import BasePage
from klipmi.utils import classproperty


class OpenQ1Page(BasePage):
    def handleNavBarButtons(self, component_id: int):
        if component_id == 30:
            self.changePage(MainPage)
        elif component_id == 31:
            self.changePage(MovePage)
        elif component_id == 32:
            self.changePage(FilelistPage)
        elif component_id == 33:
            self.changePage(SettingsPage)


class BootPage(BasePage):
    @classproperty
    def name(cls) -> str:
        return "logo"

    @classproperty
    def id(cls) -> int:
        return 0

    async def init(self):
        await self.state.display.set("version.val", 18, self.state.options.timeout)


class MainPage(OpenQ1Page):
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
                self.state.printer.emergencyStop()
            else:
                self.handleNavBarButtons(data.component_id)

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
                await self.uploadThumbnail("cp0", 160, "4d4d4d", self.filename)
                await self.state.display.command("vis cp0,1")


class MovePage(OpenQ1Page):
    @classproperty
    def name(cls) -> str:
        return "move"

    @classproperty
    def id(cls) -> int:
        return 18

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.TOUCH:
            if data.component_id == 22:
                self.changePage(FilamentPage)
            else:
                self.handleNavBarButtons(data.component_id)

    async def onPrinterStatusUpdate(self, data: dict):
        await self.state.display.set(
            "t0.txt", f'{data["motion_report"]["live_position"][0]:.1f}'
        )
        await self.state.display.set(
            "t1.txt", f'{data["motion_report"]["live_position"][1]:.1f}'
        )
        await self.state.display.set(
            "t2.txt", f'{data["motion_report"]["live_position"][2]:.1f}'
        )


class FilelistPage(OpenQ1Page):
    @classproperty
    def name(cls) -> str:
        return "filelist"

    @classproperty
    def id(cls) -> int:
        return 4

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.TOUCH:
            self.handleNavBarButtons(data.component_id)


class SettingsPage(OpenQ1Page):
    @classproperty
    def name(cls) -> str:
        return "common_set"

    @classproperty
    def id(cls) -> int:
        return 45

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.TOUCH:
            if data.component_id == 0:
                self.changePage(LanguagePage)
            if data.component_id == 22:
                self.changePage(CalibrationPage)
            else:
                self.handleNavBarButtons(data.component_id)


class LanguagePage(OpenQ1Page):
    @classproperty
    def name(cls) -> str:
        return "language"

    @classproperty
    def id(cls) -> int:
        return 46

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.TOUCH:
            if data.component_id == 0:
                self.changePage(SettingsPage)
            else:
                self.handleNavBarButtons(data.component_id)


class FilamentPage(OpenQ1Page):
    @classproperty
    def name(cls) -> str:
        return "filament"

    @classproperty
    def id(cls) -> int:
        return 62

    # Element image id's
    _regular = 176
    _highlight = 177

    def isHeating(self, heaterData: dict) -> bool:
        return heaterData["target"] > heaterData["temperature"]

    async def setHighlight(self, element: str, highlight: bool):
        await self.state.display.set(
            "%s.picc" % element, self._highlight if highlight else self._regular
        )

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.TOUCH:
            if data.component_id == 23:
                self.changePage(MovePage)
            else:
                self.handleNavBarButtons(data.component_id)

    async def onPrinterStatusUpdate(self, data: dict):
        await self.state.display.set(
            "t0.txt", str(int(data["extruder"]["temperature"]))
        )
        await self.state.display.set("n0.val", int(data["extruder"]["target"]))
        await self.setHighlight("b2", self.isHeating(data["extruder"]))
        await self.setHighlight("b0", self.isHeating(data["extruder"]))

        await self.state.display.set(
            "t1.txt", str(int(data["heater_bed"]["temperature"]))
        )
        await self.state.display.set("n1.val", int(data["heater_bed"]["target"]))
        await self.setHighlight("b3", self.isHeating(data["heater_bed"]))
        await self.setHighlight("b1", self.isHeating(data["heater_bed"]))

        await self.state.display.set(
            "t2.txt", str(int(data["heater_generic chamber"]["temperature"]))
        )
        await self.state.display.set(
            "n2.val", int(data["heater_generic chamber"]["target"])
        )
        await self.setHighlight("b12", self.isHeating(data["heater_generic chamber"]))
        await self.setHighlight("b13", self.isHeating(data["heater_generic chamber"]))


class CalibrationPage(OpenQ1Page):
    @classproperty
    def name(cls) -> str:
        return "level_mode"

    @classproperty
    def id(cls) -> int:
        return 27

    async def onDisplayEvent(self, type: EventType, data):
        if type == EventType.TOUCH:
            if data.component_id == 23:
                self.changePage(SettingsPage)
            else:
                self.handleNavBarButtons(data.component_id)


class ResetPage(BasePage):
    @classproperty
    def name(cls) -> str:
        return "reset"

    @classproperty
    def id(cls) -> int:
        return 48
