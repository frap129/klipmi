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

from types import FunctionType
from moonraker_api import MoonrakerClient, MoonrakerListener
from typing import Any, Callable
from .config import *


class Printer(MoonrakerListener):
    def __init__(
        self, options: Config, stateCallback: Callable, notifCallback: Callable
    ):
        self.stateCallback: Callable = stateCallback
        self.notifCallback: Callable = notifCallback
        self.options: Config = options
        self.running: bool = False
        self.client: MoonrakerClient = MoonrakerClient(
            self,
            options[TABLE_MOONRAKER][KEY_HOST],
            options[TABLE_MOONRAKER][KEY_PORT],
            options[TABLE_MOONRAKER][KEY_API],
        )

    async def connect(self) -> bool | None:
        self.running = True
        return await self.client.connect()

    async def disconnect(self) -> None:
        self.running = False
        await self.client.disconnect()

    async def state_changed(self, state: str) -> None:
        self.stateCallback(state)

    async def on_notification(self, method: str, data: Any) -> None:
        self.notifCallback(method, data)

    async def on_exception(self, exception: type | BaseException) -> None:
        """TODO"""
