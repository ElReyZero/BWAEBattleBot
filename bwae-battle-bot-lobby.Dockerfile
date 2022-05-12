# Download base image ubuntu 20.04
FROM ubuntu:20.04

# LABEL about the custom image
LABEL maintainer= #Maintainer email
LABEL version="1.0"
LABEL description="This is custom Docker Image BWAE Discord Services."

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN apt update && apt dist-upgrade -y && apt install -y python python3 python3-pip git nano vim

RUN pip3 install beautifulsoup4 elasticsearch==7.16.3 numpy requests websocket-client pytz aiohttp \
pymongo gspread python-dateutil schedule Pillow pynacl sphinx sphinx-rtd-theme

RUN pip3 install git+https://github.com/Rapptz/discord.py@45d498c1b76deaf3b394d17ccf56112fa691d160

RUN mkdir "/home/bwae-services"
ADD bot /home/bwae-services/bot
ADD commands /home/bwae-services/commands
ADD fonts /home/bwae-services/fonts
ADD logos /home/bwae-services/logos
ADD media /home/bwae-services/media
ADD TS3-bot /home/bwae-services/TS3-bot
ADD TS3-Bot-Linux /home/bwae-services/TS3-Bot-Linux
ADD CHANGELOG.md /home/bwae-services/CHANGELOG.md
ADD LICENSE.md /home/bwae-services/LICENSE.md
ADD README.md /home/bwae-services/README.md

ENTRYPOINT cd /home/bwae-services/bot/ && python3 scripts.py && python3 main.py

#ENTRYPOINT ["tail", "-f", "/dev/null"]
