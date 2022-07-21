# BWAE Battle Bot

This repository contains the BWAE Battle bot, a discord bot used by the [BWAE] Bushido Way planetside outfit to provide a community-driven matchmaking system for TDM infantry scrims, 1v1 matches and trainings in Planetside2.

The bot was originally created by [YakMM](https://github.com/yakMM) but modified my me.

Link to the original POG bot: [Link](https://github.com/yakMM/POG-bot)

This version of the bot adds a lot of new features, including:
- 1v1 matches
- Join ongoing 1v1 matches (try =join1v1 on an ongoing match)
- TDM matches, wanna do a 6v6? Go for it. 2v2? 3v2? Or even 100v100? You can do it! (you can adjust the lobby size using =lbsize)
- Custom round time. Use =rndtime to change the next match's duration
- Match results just as if you were in a tournament!
- A training mode where you can set a custom amount of rounds
- QOL admin commands (restart bot, set db match, get current global variables, etc)
And more...

### Requirements:
- This project relies on several [python dependencies](#python-dependencies).
- A [discord bot application and channels](#discord-bot-component) have to be created.
- A [MongoDB database](#preparing-mongodb-component) is used for persistent data storage.
- An [Elasticsearch] component is used for account handling (The MongoDB database can be used for this as well)
- By default, the mongo database will be used for accounts usage. If you want to use the elasticsearch component, you need to delete `bot/modules/accounts_handler.py` and rename `accounts_handler_es.py` to `accounts_handler.py`. 
- Jaeger accounts are pulled from a [Google Sheet](#preparing-google-component). 
- To retrieve Planetside2 information a [Daybreak Census ID](#assigning-census-id) has to be provided.
- To use the TeamSpeak 3 Integration, set up an instance of [TS3AudioBot](#teamspeak-integration).
- Finally, to initialize the application, [scripts functions](#populating-the-collections) are provided.

### Python dependencies:
- Python 3.8 or above is required to run the project.
- We recommend using [pipenv](https://pypi.org/project/pipenv/) to set up the project environment. Pipenv will install automatically install the required dependencies from the `Pipfile` provided with the project.
- Alternatively, the dependencies are also listed in the `requirements.txt` file (compatible with [venv](https://docs.python.org/3/library/venv.html))

### Notes for the developer:
- Master branch is a release branch, it will stay clean and is synced with the official POG hosting server.
- So developments should be done on feature or development branches and will be then merged in.
- Keep fork repos up to date from upstream as much as possible.
- `google_api_secret.json` and `config.cfg` are not available for confidentiality reasons, templates are given instead.
- The code of the application itself can be found in the `bot` folder. It contains:
  - The `cogs` folder: it holds cogs modules as described in discord.py. Each of them regroups a set of commands and their associated checks. These modules are not to be imported in any way (they are only launched through the discord.py client)
  - The `display` folder: it is a python package handling all the display from the application to discord. All discords embed and strings used are stored there.
  - The `modules` folder: it is a python package containing general interfaces and tools that can be used in the rest of the application.
  - The `classes` folder: it contains the main classes of the application: `Player`, `Team`, `Weapon`, `Base`, `Account`, etc...
  - The `lib` folder: it contains third-party modules that were modified for the purpose of the application.
  - The `match` folder: it contains all the code handling the match processes and commands.
  
### Discord Bot Component
Create a bot application following the [discord.py documentation](https://discordpy.readthedocs.io/en/latest/discord.html).
The client-secret retrieved at this manual has to put into the configuration file:
```buildoutcfg
[General]
token = RetrievedDiscordApiBotToken
```

#### Create channels and roles
To retrieve discord channel, message and role-ids you have to enable Discord Developer Mode which can be toggled at appearance.
`Copy ID` will then appear at the right click menu for channels, messages and roles.
At that point you can populate the `[channels]` and `[roles]`sections of the configuration file.

### Preparing MongoDB Component
Pymongo is used for interaction with the mongodb. The database should contain several collections:
- One for the user data.
- One for the bases.
- One for the weapons.
- One for the matches.
- One for the player stats
- One for persistent restart data
- One for jaeger account usage
Check `script.py` to populate the databases.
The naming of these collections can be configured at the `[Collections]` part of the configuration file.

There are two common ways to get MongoDB running: [Atlas](#Atlas) and [Manual Deployment](#manual-deployment).

#### Atlas
Atlas can be run using a free instance at [MongoDB Cloud Atlas](https://www.mongodb.com/cloud/atlas)
When using MongoDB Atlas the following URI format is expected:
```buildoutcfg
[Database]
url = mongodb+srv://username:password@clusteruri/databasename
cluster = ClusterName
```

#### Manual Deployment
When using a single manually deployed MongoDB instance, omit `+srv` and remove the database name from the `url` and put it at `cluster` instead:
```buildoutcfg
[Database]
url = mongodb://username:password@host:port/
cluster = DatabaseName
```

### Preparing the Elasticsearch Component
Elasticsearch is used for account handling. It should be configured in bot/modules/config.py.

After setting up the host, you need to add all of your practice account information in bot/db_account_info.py and run the script to populate the elasticsearch database.

Setting up the account information:
```
userdata = {
    'Account1Username': {'password': 'password',
                        'character_names': ['BWAExPractice1NC', 'BWAExPractice1VS', 'BWAExPractice1TR',
                                            'BWAExPractice1NS'],
                        'basename': "Practice",
                        'base_account_number': '1'},
    'Account2Username': {'password': 'password',
                        ...
}
```

### Preparing Google Component
The Gspread module is used for interaction with google API. [Follow these steps to create your google_api_secret.json](https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account)

#### Prepare Google Sheet
An example sheet has been provided called `accounts_sheet_template.xlsx`. 
By creating a new Google Sheet in your Drive and importing the excel file through the menu you can avoid format and naming convention errors.

The `accounts` field from the `[Database]` section of the configuration file has to contain the ID of the Google Sheet.
This ID can be easily retrieved from the URI of the document: `https://docs.google.com/spreadsheets/d/GOOGLE_SHEET_ID/edit#gid=0`.

Finally, add the service account email to the shared users with editor permissions to the google sheet. 
This email is also listed as `client_email` in the `google_api_secret.json` file.

### Assigning Census ID
Communication with the Daybreak Census API is required to retrieve game information, therefore you have to supply a Service ID.
You can apply for one at the [Daybreak Census](http://census.daybreakgames.com/#service-id) website.
Once you obtained an ID, add it the configuration as `api_key`:
```buildoutcfg
[General]
api_key = Daybreak_Registered_Service_ID
```

### Teamspeak integration
The bot used for Teamspeak audio integration is Splamy's [TS3AudioBot](https://github.com/Splamy/TS3AudioBot).
This bot works on the dotnet runtime and can be built and installed following the readme available in TS3AudioBot github's repo.

#### TS3-bot folder structure
The structure of the TS3AudioBot folder is the following:
```
TS3-bot
+-- TS3AudioBot.dll
+-- rights.toml
+-- ts3audiobot.toml
+-- ...
+-- audio
|   +-- audio_file_1.mp3
|   +-- audio_file_1.mp3
|   +-- ...
+-- bots
|   +-- 1
|   | +-- bot.toml
|   +-- 2
|   | +-- bot.toml
|   +-- 3
|   | +-- bot.toml
|   +-- ...
```
The audio files should be put in the `audio` repository. Each sub-repository of `bots` represent TS3 bot (one bot per match channel is needed).

#### Main configuration file
The first file to modify is `ts3audiobot.toml`. The relevant parameters for are listed below. You may want to change the parameters depending on your project file structure.
```buildoutcfg
[configs]
# Path for the bots
bots_path = "bots"

[factories]
# Path for audio files
media = { path = "audio" }

[bot.audio]
# Activate subscription-based whispers
send_mode = "!whisper subscription"


[bot.connect]
# TS3 default connect information
address = Your_TS3_Url
channel = Your_TS3_Bot_Channel_Id (example: /10)
```

Additionally, add access to all commands for localhost in the `rights.toml` file:
```buildoutcfg
# Admin rule
[[rule]]
        # Treat requests from localhost as admin
        ip = [ "::ffff:127.0.0.1" ]
        "+" = "*"
```

#### Configuring individual bots
Each individual bot can also be configured, in each `bot.toml` files. This allows for example to change the name of each individual bot.
```buildoutcfg
[connect]
# Client nickname when connecting.
name = "POG_3"

```

#### Setting up TS3 channels IDs
The `Teamspeak` section of the configuration file can now be completed 
```buildoutcfg
[Teamspeak]
url = # Teamspeak bot webapi url
lobby_id = # Lobby channel id
matches = # Matches channel ids (example: 1/2/3,4/5/6) (matches separated by commas, channels by slashes, no spaces)
```



### Populating the collections
You need to run the following scripts before running the bot for the first time!
The file `scripts.py` contains two functions called `push_accounts()` and `get_all_maps_from_api()`.
The file `weapons_script.py` contains the function `push_all_weapons()`.
Running all of these functions will populate the MongoDB users, bases and weapons collections, allowing you to run `main.py`.
