
# klipmi

[Klip]per for H[MI] displays like TJC and Nextion

## Overview

`klipmi` is a framework for integrate Klipper with HMI displays such as TJC and Nextion. This repository contains the necessary code and configuration files to build klipper support for any UI running on a TJC or Nextion diplay

Note: Currently designed for TJC displays, though little work is needed to support Nextion. Open an issue if you need this.

## Features

- Handles TJC/Nextion diplay communication
- Handles interacting with moonraker
- Provides a simplified framework for interacting with both

# Supported HMIs
Currently klipmi supports:
- OpenQ1 for TJC4827X243_011

## Installation

To install `klipmi`, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/frap129/klipmi.git
    cd klipmi
    ```

2. Run the installation script:
    ```bash
    ./install.sh
    ```

3. Configure `klipmi` by editing the example configuration file:
    ```bash
    cp klipmi.toml.example ~/printer_data/config/klpmi.toml
    ```
4. Get moonraker API key
    ```bash
    http://IP OF PRINTER/access/api_key
    ```
## Instal Touch Screen firmware

1. Stop `klipmi`
    ```bash
    systemctl stop klipmi
    ```
2. Install TFT Firmware
    ```bash
    .venv/bin/nextion-fw-upload -b 115200 -ub 921600 /dev/ttyS1 ~/klipmi/hmi/openq1/Q1_UI.tft
    ```
    
## Usage

To start the service, use the following command:
```bash
sudo systemctl start klipmi.service
```

To enable the service to start on boot:
```bash
sudo systemctl enable klipmi.service
```

If it not working check log

```bash
sudo journalctl -xeu klipmi
```
## Errors
If you see this error No such file or directory: '/root/printer_data/config/klipmi.toml' change the service user to mks

```bash
sudo nano /etc/systemd/system/klipmi.service
```

Then restart

```bash
sudo systemctl restart klipmi
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## License

This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.

