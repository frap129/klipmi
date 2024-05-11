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

from config import Config
from nextion import TJC
from printer import Printer, PrinterStatus


class State:
    def __init__(self):
        self.options: Config
        self.display: TJC
        self.printer: Printer
        self.printerData: dict = {}
        self.fileList: dict = {}
        self.status: PrinterStatus = PrinterStatus.NOT_READY
