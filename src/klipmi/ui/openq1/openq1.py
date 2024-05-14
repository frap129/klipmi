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

from typing import Dict, List
from klipmi.model.ui import BaseUi
from klipmi.utils.utils import classproperty
from .pages import *


class OpenQ1UI(BaseUi):
    @classproperty
    def printerObjects(cls) -> Dict[str, List[str]]:
        return {
            "gcode_move": ["extrude_factor", "speed_factor", "homing_origin"],
            "motion_report": ["live_position", "live_velocity"],
            "fan": ["speed"],
            "heater_bed": ["temperature", "target"],
            "extruder": ["target", "temperature"],
            "heater_generic chamber": ["temperature", "target"],
            "display_status": ["progress"],
            "output_pin caselight": ["value"],
            "output_pin sound": ["value"],
            "print_stats": [
                "state",
                "print_duration",
                "filename",
                "total_duration",
                "info",
            ],
        }

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
