#!/bin/bash

chromeInstaller="google-chrome-stable_current_amd64.deb"
chromeLinux="https://dl.google.com/linux/direct/${chromeInstaller}"

DEBIAN_FRONTEND=noninteractive sudo apt-get update && \
sudo apt-get install python3-pip \
python3-venv -y && \

wget -O "${chromeInstaller}" "${chromeLinux}" && sudo dpkg -i "${chromeInstaller}"
