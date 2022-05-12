#!/bin/bash

cd "$(dirname "$0")"/../bot || exit
python3 -u main.py >> ../../BattleBot-Data/logging/discord_bot.out 2>&1
