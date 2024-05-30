#!/usr/bin/env bash

KLIPMI_DIR=$(dirname $(realpath $0))
SYSTEMD_DIR="/etc/systemd/system"

install_klipmi_service() {
    sudo cp ${KLIPMI_DIR}/klipmi.service ${SYSTEMD_DIR}/klipmi.service
    sudo sed -i "s|%USER%|${USER}|g; s|%KLIPMI_DIR%|${KLIPMI_DIR}|;" ${SYSTEMD_DIR}/klipmi.service
    sudo systemctl enable --now klipmi.service
}

create_klipmi_venv() {
    python3 -m venv ${KLIPMI_DIR}/.venv
    ${KLIPMI_DIR}/.venv/bin/pip install -r ${KLIPMI_DIR}/requirements.txt
}

create_klipmi_venv
install_klipmi_service
