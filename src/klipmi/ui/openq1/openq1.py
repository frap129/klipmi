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

from klipmi.model.ui import BaseUi
from . import BootPage
from . import MainPage


class OpenQ1UI(BaseUi):
    def onNotReady(self):
        self.changePage(BootPage)

    def onReady(self):
        self.changePage(MainPage)
        pass

    def onStopped(self):
        pass

    def onMoonrakerError(self):
        pass

    def onKlipperError(self):
        pass
