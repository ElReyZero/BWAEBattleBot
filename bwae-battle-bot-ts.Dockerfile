# Download base image ubuntu 20.04
FROM ubuntu:20.04

# LABEL about the custom image
LABEL maintainer= #Maintainer email
LABEL version="1.0"
LABEL description="This is custom Docker Image BWAE Discord Services."

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN apt update && apt dist-upgrade -y && apt install -y python python3 python3-pip git nano vim wget libopus-dev ffmpeg

RUN pip3 install beautifulsoup4 elasticsearch numpy requests websocket-client pytz aiohttp \
pymongo gspread python-dateutil schedule Pillow pynacl sphinx sphinx-rtd-theme

RUN pip3 install git+https://github.com/Rapptz/discord.py

# Install Dotnet Dependencies for TS3AudioBot
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt update \
    && apt install -y apt-transport-https  \
    && apt update  \
    && apt install -y dotnet-sdk-6.0 

# build bot
RUN mkdir "/home/bwae-services"\
    && cd /home/bwae-services \
    && git clone --recurse-submodules https://github.com/Splamy/TS3AudioBot.git \
    && cd TS3AudioBot \
    && dotnet build --version-suffix 0.12.2 --os linux --no-incremental --framework netcoreapp3.1 --configuration Release TS3AudioBot \
    && pwd \
    && cd TS3AudioBot \
    && cd bin \
    && cd Release \
    && cd netcoreapp3.1 \
    && cd linux-x64 \
    && pwd \
    && ls 



ADD bot /home/bwae-services/bot
ADD commands /home/bwae-services/commands
ADD fonts /home/bwae-services/fonts
ADD logos /home/bwae-services/logos
ADD media /home/bwae-services/media
ADD TS3-bot /home/bwae-services/TS3-bot
ADD TS3-Bot-Linux /home/bwae-services/TS3-Bot-Linux
ADD TS3-Bot-Linux/TS3AudioBot/bin/Release/netcoreapp3.1/rights.toml /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64/rights.toml
ADD TS3-Bot-Linux/TS3AudioBot/bin/Release/netcoreapp3.1/ts3audiobot.toml /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64/ts3audiobot.toml
ADD TS3-Bot-Linux/TS3AudioBot/bin/Release/netcoreapp3.1/bots /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64/bots
ADD TS3-Bot-Linux/TS3AudioBot/bin/Release/netcoreapp3.1/audio /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64/audio
ADD CHANGELOG.md /home/bwae-services/CHANGELOG.md
ADD LICENSE.md /home/bwae-services/LICENSE.md
ADD README.md /home/bwae-services/README.md


RUN chmod -R 777 /home/bwae-services \
    && cd /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64 \
    && pwd \
    && ls 

ENTRYPOINT cd /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64/ \
    && pwd \
    && ls \
    && dotnet TS3AudioBot.dll --non-interactive # --config /home/bwae-services/TS3AudioBot/TS3AudioBot/bin/Release/netcoreapp3.1/linux-x64/ts3audiobot.toml



