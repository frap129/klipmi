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

import logging
import os
import tomllib

from optparse import OptionParser

CONFIG_PATH = "printer_data/config/klipmi.toml"
TABLE_KLIPMI = "klipmi"
TABLE_MOONRAKER = "moonraker"
KEY_DEVICE = "device"
KEY_BAUD = "baudrate"
KEY_UI = "ui"
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


class KlipmiConfig:
    device: str = ""
    baud: int = 115200
    ui: str = ""

    def __init__(self, config: dict):
        try:
            self.device = config[KEY_DEVICE]
        except Exception as e:
            logging.exception(e)

        try:
            self.baud = config[KEY_BAUD]
        except Exception as e:
            logging.warning("baud not set in config, defaulting to %d" % self.baud)

        try:
            self.ui = config[KEY_UI]
        except Exception as e:
            logging.exception(e)


class MoonrakerConfig:
    host: str = "0.0.0.0"
    port: int = 7125
    api_key: str = ""

    def __init__(self, config: dict):
        try:
            self.host = config[KEY_HOST]
        except Exception as e:
            logging.warning("host not set in config, defaulting to %s" % self.host)

        try:
            self.port = config[KEY_PORT]
        except Exception as e:
            logging.warning("port not set in config, defaulting to %d" % self.port)

        try:
            self.api_key = config[KEY_API]
        except Exception as e:
            logging.exception(e)


class Config:
    timeout: int = 5

    def __init__(self):
        self.path: str = getConfigPath() or CONFIG_PATH
        self._raw: dict = self.parse()
        self.klipmi: KlipmiConfig = KlipmiConfig(self._raw[TABLE_KLIPMI])
        self.moonraker: MoonrakerConfig = MoonrakerConfig(self._raw[TABLE_MOONRAKER])

    def parse(self) -> dict:
        with open(self.path, "rb") as f:
            try:
                return tomllib.load(f)
            except Exception as e:
                logging.exception(e)
                return {}
