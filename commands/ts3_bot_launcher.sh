#!/bin/bash

cd "$(dirname "$0")"/../../TS3-bot/ || exit
dotnet TS3AudioBot.dll >> ../BattleBot-Data/logging/ts3_bot.out 2>&1
