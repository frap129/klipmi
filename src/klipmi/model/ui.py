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
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Dict, List, Type

from nextion import EventType

from klipmi.model.state import KlipmiState
from klipmi.utils import classproperty
from klipmi.utils.libcolpic import parseThumbnail


class BasePage(ABC):
    @classproperty
    @abstractmethod
    def name(cls) -> str:
        pass

    @classproperty
    @abstractmethod
    def id(cls) -> int:
        pass

    def __init__(self, state: KlipmiState, changePageCallback: Callable):
        self.state = state
        self.changePageCallback = changePageCallback

    async def init(self):
        pass

    async def onDisplayEvent(self, type: EventType, data):
        pass

    async def onPrinterStatusUpdate(self, data: dict):
        pass

    async def onFileListUpdate(self, data: dict):
        pass

    def changePage(self, page):
        self.changePageCallback(page)

    async def uploadThumbnail(
        self, element: str, size: int, bgColor: str, filename: str, metadata: dict = {}
    ):
        thumbnail = parseThumbnail(
            await self.state.printer.getThumbnail(size, filename, metadata),
            size,
            size,
            bgColor,
        )
        await self.state.display.command("p[%d].%s.close()" % (self.id, element))

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
                'p[%d].%s.write("%s")' % (self.id, element, str(part))
            )


class BaseUi(ABC):
    currentPage: BasePage | None = None

    @classproperty
    @abstractmethod
    def printerObjects(cls) -> Dict[str, List[str]]:
        pass

    def __init__(self, state: KlipmiState):
        self.state = state

    @abstractmethod
    def onNotReady(self):
        pass

    @abstractmethod
    def onReady(self):
        pass

    @abstractmethod
    def onStopped(self):
        pass

    @abstractmethod
    def onMoonrakerError(self):
        pass

    @abstractmethod
    def onKlipperError(self):
        pass

    async def onDisplayEvent(self, type: EventType, data):
        if self.currentPage is not None:
            await self.currentPage.onDisplayEvent(type, data)

    async def onPrinterStatusUpdate(self, data: dict):
        if self.currentPage is not None:
            await self.currentPage.onPrinterStatusUpdate(data)

    async def onFileListUpdate(self, data: dict):
        if self.currentPage is not None:
            await self.currentPage.onFileListUpdate(data)

    async def __executePageChange(self):
        if self.currentPage is not None:
            await self.state.display.wakeup()
            await self.state.display.command(
                "page %d" % self.currentPage.id, self.state.options.timeout
            )
            await self.currentPage.init()

    def changePage(self, page: Type[BasePage]):
        self.currentPage = page(self.state, self.changePage)
        asyncio.create_task(self.__executePageChange())
