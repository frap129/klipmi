#!/usr/bin/env bash

KLIPMI_DIR=$(dirname $(realpath $0))
SYSTEMD_DIR="/etc/systemd/system"

root_check() {
    if [[ "$EUID" -eq 0 ]]; then
        echo "Do not run this script as root."
        echo "You will be prompted for your password when root access is needed."
        exit 1
    fi
}

install_klipmi_service() {
    sudo cp ${KLIPMI_DIR}/klipmi.service ${SYSTEMD_DIR}/klipmi.service
    sudo sed -i "s|%USER%|${USER}|g; s|%KLIPMI_DIR%|${KLIPMI_DIR}|;" ${SYSTEMD_DIR}/klipmi.service
    sudo systemctl enable --now klipmi.service
}

create_klipmi_venv() {
    python3 -m venv ${KLIPMI_DIR}/.venv
    ${KLIPMI_DIR}/.venv/bin/pip install -r ${KLIPMI_DIR}/requirements.txt
}

root_check
create_klipmi_venv
install_klipmi_service
