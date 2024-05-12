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

from logging import exception
from optparse import OptionParser
import os
import tomllib

CONFIG_PATH = "printer_data/config/klipmi.toml"

TABLE_DISPLAY = "klipmi"
TABLE_MOONRAKER = "moonraker"
KEY_DEVICE = "device"
KEY_BAUD = "baudrate"
KEY_HOST = "host"
KEY_PORT = "port"
KEY_API = "api-key"


def getCommaSeparatedArgs(option, _, value, parser):
    setattr(parser.values, option.dest, value.split(","))


def getConfigPath() -> str:
    parser = OptionParser()
    parser.add_option(
        "-c",
        "--config",
        dest="configPath",
        type="string",
        action="callback",
        callback=getCommaSeparatedArgs,
        metavar=CONFIG_PATH,
        help="Path to user config file.",
    )

    try:
        path = parser.parse_args()[0].configPath[0]
    except:
        path = os.path.expanduser("~") + "/" + CONFIG_PATH

    return path


class Config:
    timeout: int = 5

    def __init__(self, configPath):
        self.reloadConfig(configPath)

    def parse(self) -> dict:
        with open(self.configPath, "rb") as f:
            try:
                return tomllib.load(f)
            except Exception as e:
                exception(e)
                return {}

    def reloadConfig(self, configPath):
        self.configPath = configPath or CONFIG_PATH
        self.configDict = self.parse()

    def __getitem__(self, key) -> dict:
        return self.configDict[key]
