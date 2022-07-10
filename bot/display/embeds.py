from discord import Embed, Color
import modules.config as cfg
from datetime import datetime as dt
from datetime import timezone as tz

from modules.roles import is_admin
import modules.tools as tools
from match import MatchStatus


def global_variables_display(ctx):
    """Display the current status of the bot's global variables"""
    embed = Embed(
        colour=Color.blurple(),
        title='Global variables',
        description=f'`=gv` - Display the current status of the bot\'s global variables\n'
    )
    embed.add_field(name="Lobby Size",
                    value=f'{cfg.general["lobby_size"]} players',
                    inline=False)
    embed.add_field(name="Training Lobby Size",
                    value=f'{cfg.general["training_lobby_size"]} players',
                    inline=False)
    embed.add_field(name="TDM Round Length",
                    value=f'{cfg.general["round_length"]} minutes',
                    inline=False)
    embed.add_field(name="Training Rounds Configured",
                    value=f'{cfg.general["training_rounds"]} rounds',
                    inline=False)
    embed.add_field(name="Practice Accounts Role Check",
                    value=f'Role check enabled.\nValue: {cfg.general["no_account_role"]}' if cfg.general["no_account_role"] else f'Role check disabled.\nValue: {cfg.general["no_account_role"]}',
                    inline=False)
    embed.add_field(name="Show player scores check",
                    value=f'Player scores are enabled\nValue: {cfg.general["show_player_scores"]}' if cfg.general["show_player_scores"] else f'Player scores are hidden.\nValue: {cfg.general["show_player_scores"]}',
                    inline=False)
    return embed
    
def register_help(ctx):
    """ Returns register help embed
    """
    embed = Embed(
        colour=Color.blurple(),
        title='How to register?',
        description=f'You have to accept the rules in <#{cfg.channels["rules"]}> to register'
    )
    embed.add_field(name='If you don\'t have a Jaeger account',
                    value='`=r no account`\n',
                    inline=False)
    embed.add_field(name='If you have a Jaeger account',
                    value='`=r charName` - If your character names have faction suffixes '
                          '(charNameVS, charNameTR, charNameNC)\n'
                          '`=r charName1 charName2 charName3` - If your character names don\'t have faction suffixes',
                    inline=False)
    embed.add_field(name='Notify feature',
                    value='`=notify` - To join or leave the Notify feature\n'
                          f'When subscribed to Notify, you can be mentioned with <@&{cfg.roles["notify"]}> '
                          'when the queue is almost full',
                    inline=False)
    embed.add_field(name='DM command',
                    value='`=dm` - To receive a direct message when a match is starting',
                    inline=False)
    embed.add_field(name='Quit command',
                    value='`=quit` - To temporarily leave the channels\n'
                          f'You will be removed from the active BWAE Internals channels. Accept the rules in <#{cfg.channels["rules"]}> to come back.',
                    inline=False)
    try:
        if is_admin(ctx.author):
            embed.add_field(name="Staff commands",
                            value='`=rename @player New Name` - Change the player name within the system\n'
                                '`=unregister @player` - Permanently remove player profile from the system\n'
                                '`=channel freeze`/`unfreeze` - Prevent / Allow players to send messages',
                            inline=False)
    except AttributeError:
        pass
    return embed


def lobby_help(ctx):
    """ Returns lobby help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Lobby commands',
                    value='`=join` (`=j`) - Join the lobby\n'
                          '`=1v1` (`=1v1`) - Join the 1v1 queue\n'
                          '`=leave` (`=l`)  - Leave the lobby\n'
                          '`=queue` (`=q`)  - See the current lobby\n'
                          '`=reset` (`=rst`)  - Reset your queue timeout\n'
                          '`=info` (`=i`)  - Display the global information prompt\n'
                          '`=join1v1` (`=join1v1`) - Join a current 1v1 match (Can only be used in the match channels)\n'
                          '`=lobbysize` (`=lbsize`) - Change the lobby size\n'
                          '`=rndtime` - Change the amount of time in a match round\n'
                          '`=training` - Configure the next training match\n'
                          '`=tr` - Join the training queue',
                    inline=False)
    try:
        if is_admin(ctx.author):
            embed.add_field(name="Staff commands",
                            value='`=clear` - Clear the lobby\n'
                                '`=remove @player` - Remove player from lobby\n'
                                '`=channel freeze`/`unfreeze` - Prevent / Allow players to send messages\n'
                                '`=lobby save`/`get`/`restore` - Will save, get or restore the lobby from player IDs\n'
                                '`=forcestart` (`=fstart`) - Force start a match with current people in lobby\n'
                                '`=trainingstart` (`=tstart`) - Force start a training match with current people in lobby'
                                ,
                            inline=False)
    except AttributeError:
        pass
    return embed


def admin_help(ctx):
    """ Returns admin help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Debug commands',
                    value='`=channel (un)freeze` - Prevent users from typing in a channel\n'
                          '`=version` - Display current version and lock status\n'
                          '`=(un)lock` - Prevent users from interacting with the bot (but admins still can)\n'
                          '`=reload accounts`/`bases`/`weapons`/`config` - Reload specified element from the database\n'
                          '`=spam clear` - Clear the spam filter\n'
                          '`=variables` - Display the current status of the bot\'s global variables\n'
                          '`=restart` - Restart the bot\n'
                          '`=logs` - Send the latest bot logs',
                    inline=False)
    embed.add_field(name='Lobby commands',
                    value='`=remove @player` - Remove the player from queue\n'
                          '`=clear` - Clear queue\n'
                          '`=lobby save`/`get`/`restore` - Will save, get or restore the lobby from player IDs',
                    inline=False)
    embed.add_field(name='Player Management commands',
                    value='`=rename @player New Name` - Rename a player within the system\n'
                          '`=timeout @player duration` - Mute the player from POF for a given time\n'
                          '`=unregister @player` - Forcibly unregisters and removes a user from the system\n'
                          '`=check roles` - Enable or disable the role check for people with no Jaeger Accounts',
                    inline=False)
    embed.add_field(name='Match commands',
                    value='`=sub @player1 @player2` - Sub player1 by player2\n'
                          '`=clear` - Clear the match\n'
                          '`=check account/online` - Disable account or online check',
                    inline=False)
    return embed


def default_help(ctx):
    """ Returns fallback help embed
    """
    embed = Embed(colour=Color.red())
    embed.add_field(name='No available command',
                    value='You are not supposed to use the bot on this channel',
                    inline=False)
    return embed

def exceptions_help(ctx):
    """Returns exceptions help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name="Exception help",
                    value="This channel is used for debugging. Exceptions not catched by the bot are sent here.",
                    inline=False)
    return embed

def base_help(ctx):
    """ Returns base help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Base selection commands',
                    value=f'`=base nanite realm` - Display all the bases containing *nanite realm* in their name\n'
                          f'`=base 3` - Choose the base number 3 from the selection\n'
                          f'`=base` (`=b`)  - Display the current selection or show the help\n'
                          f'`=base list` (`=b l`) - Force the display of all available bases\n'
                          f'`=base accept` (`=b a`) - Accept the base selection\n'
                          f'`=base decline` (`=b d`) - Decline the base selection\n'
                          f'`=base cancel` (`=b c`) - Cancel the base selection',
                    inline=False)
    return embed


def captain_help(ctx):
    """ Returns base help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Captain selection commands',
                    value=f'`=captain volunteer` (`=c v`) - Volunteer as a captain for the match\n'
                          f'`=captain accept` (`=c a`) - Accept the captain proposal\n'
                          f'`=captain decline` (`=c d`) - Decline the captain proposal\n'
                          f'`=captain` (`=c`) - Display the current status\n'
                          f'`=captain help` (`=c h`) - Display the help prompt',
                    inline=False)
    return embed


def usage_help(ctx):
    """ Returns base help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='BWAE Battle Bot usage commands',
                    value=f'`=usage x` - Get last usages of Practice account x\n'
                          f'`=usage @user` - Get last usages of the mentioned user\n'
                          f'`=psb @user (date)` - Get user activity formatted for PSB purposes\n'
                          f'`=stats @user (duration)` - Get player stats for the duration provided',
                    inline=False)
    embed.add_field(name='Extra Commands', 
                    value='`=variables` - Display the current status of the bot\'s global variables\n'
                          '`=restart` - Restart the bot\n'
                          '`=logs` - Send the latest bot logs',
                          inline=False)
    return embed


def timeout_help(ctx):
    """ Returns timeout help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Timeout command',
                    value='`=timeout @player 10 days` - Mute @player from BWAE Internals for 10 days\n'
                          '`=timeout @player 10 hours` - Mute @player from BWAE Internals for 10 hours\n'
                          '`=timeout @player 10 minutes` - Mute @player from BWAE Internals for 10 minutes\n'
                          '`=timeout @player remove` - Unmute @player from BWAE Internals\n'
                          '`=timeout @player` - Get info on current timeout for @player',
                    inline=False)
    return embed


def dm_help(ctx):
    """ Returns timeout help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Direct Message commands',
                    value='`help` - Display this prompt\n'
                          '`stats` - Display your tracked stats\n'
                          '`modmail` (`dm`) - Send a message to the Battle Bot staff\n',
                    inline=False)
    return embed


def muted_help(ctx):
    """ Returns help for muted players embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='You are currently muted!',
                    value='`=escape` See how long you are muted for, give back permissions if no longer muted',
                    inline=False)
    return embed


def match_help(ctx):
    """ Returns match help embed
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Match commands',
                    value='`=info` (`=i`) - Display the match status and team composition\n'
                          "`=squittal` - Display player data for integration in Chirtle's script",
                    inline=False)
    embed.add_field(name='Team Captain commands',
                    value='`=p @player` - Pick a player in your team\n'
                          '`=p VS`/`NC`/`TR` - Pick a faction\n'
                          '`=base` (`=b`) - Command for the base selection, use `=b help` to know more\n'
                          '`=ready` (`=rdy`) - To toggle the ready status of your team\n'
                          '`=sub @player` - Pick someone in queue to replace the player mentioned\n'
                          '`=swap @player1 @player2` - Swap the two players from one team to the other\n'
                          '`=bench`/`=unbench @player` - Bench or un-bench player from the match',
                    inline=False)
    try:
        if is_admin(ctx.author):
            embed.add_field(name="Staff commands",
                            value='`=clear` - Clear the match\n'
                                '`=captain @player` - Make @player a team captain\n'
                                '`=sub @player1 @player2` - Replace player1 by player2\n'
                                '`=check account/online` - Disable account or online check\n'
                                '`=channel freeze`/`unfreeze` - Prevent / Allow players to send messages',
                            inline=False)
    except AttributeError:
        pass
    return embed


def match_help_1v1(ctx):
    """ Returns match help embed for 1v1s
    """
    embed = Embed(colour=Color.blurple())
    embed.add_field(name='Match commands',
                    value='`=info` (`=i`) - Display the match status and team composition\n'
                          '`=end1v1` (`=end1v1`) - End the 1v1 match',
                    inline=False)
    embed.add_field(name='Team commands',
                    value='`=p VS`/`NC`/`TR` - Pick a faction\n'
                          '`=base` (`=b`) - Command for the base selection, use `=b help` to know more\n'
                          '`=ready` (`=rdy`) - To toggle the ready status of your team\n'
                          '`=swap @player1 @player2` - Swap the two players from one team to the other\n'
                          '`=bench`/`=unbench @player` - Bench or un-bench player from the match\n',
                    inline=False)
    if is_admin(ctx.author):
        embed.add_field(name="Staff commands",
                        value='`=clear` - Clear the match\n'
                              '`=captain @player` - Make @player a team captain\n'
                              '`=sub @player1 @player2` - Replace player1 by player2\n'
                              '`=check account/online` - Disable account or online check\n'
                              '`=channel freeze`/`unfreeze` - Prevent / Allow players to send messages',
                        inline=False)
    return embed


def register_status(ctx, player):
    embed = Embed(colour=Color.blue(), title="Player status",
                  description=f"Handle: {player.mention}\nName: {player.name}\nID: `{player.id}`\n")
    if player.is_notify:
        value = "You are subscribed to the notify feature!"
    else:
        value = "You are **not** subscribed to the notify feature!"
    embed.add_field(name="Notify", value=value, inline=False)
    if player.has_own_account:
        value = "You are registered with the following Jaeger characters:\n`{}`, `{}`, `{}`".format(*player.ig_names)
    else:
        value = "You are registered without a Jaeger account!\nIf you have your own " \
                "account, please re-register with your Jaeger characters."
    embed.add_field(name="Account", value=value, inline=False)
    embed.add_field(name="Help",
                    value="Use `=notify` to join or leave the notify feature\n"
                          "Use `=register` (`=r`) to update your account information",
                    inline=False)
    return embed

def steps_to_join_match(ctx):
    embed = Embed(colour=Color.green(), title="How to Join a Match?")
    embed.add_field(name="Steps:",value="Steps to join a match:\n"
                                    "1) Accept the rules by clicking the button in rules.\n"
                                    "2) Register with or without a Jaeger account using =register (or =r) command in the register channel.\n"
                                    "3) You may join use =notify to be pinged when a match is about to start (the mention will trigger only if you are online or idle on discord).\n"
                                    "4) Join the lobby in lobby using =join (or =j).\n" 
                                    "5) Once the lobby is full, a match will start. Join the appropriate match channel and Teamspeak for voice communication (address: ts.bushidoway.net).\n", inline=False)
    return embed

def account(ctx, account):
    """ Returns account message embed
    """
    desc = ""
    color = None
    if account.is_destroyed:
        desc = "This account token is no longer valid"
        color = Color.dark_grey()
    elif account.is_validated:
        desc = f'Id: `{account.str_id}`\n' + f'Username: `{account.username}`\n' + f'Password: `{account.password}`\n' \
                                                                                   'Note: This account is given to you only for the time of **ONE** match'
        color = Color.green()
    else:
        desc = "Accept the rules by reacting with a checkmark to get your account details."
        color = Color.red()
    embed = Embed(
        colour=color,
        title='Jaeger Account',
        description=f'**MUST READ: [Account usage](https://planetsideguide.com/other/jaeger/)**'
    )
    embed.add_field(name="Logging details", value=desc, inline=False)
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/icons/546928840497299456/f916fc156bbbf89e80fe8c5a1cfa54c6.png")
    embed.set_footer(
        text='Failure to follow account usage rules can result in your suspension from ALL Jaeger events.')
    return embed

def auto_help(ctx, is_dm=False):
    """ Return help embed depending on current channel """
    if is_dm:
        return dm_help(ctx)
    if ctx.channel_id == cfg.channels['register']:
        return register_help(ctx)
    if ctx.channel_id == cfg.channels['lobby']:
        return lobby_help(ctx)
    if ctx.channel_id in cfg.channels['matches']:
        return match_help(ctx)
    if ctx.channel_id in cfg.channels['matches1v1']:
        return match_help_1v1(ctx)
    if ctx.channel_id == cfg.channels['muted']:
        if ctx.author and is_admin(ctx.author):
            return timeout_help(ctx)
        else:
            return muted_help(ctx)
    if ctx.channel_id == cfg.channels['staff']:
        return admin_help(ctx)
    if ctx.channel_id == cfg.channels['usage']:
        return usage_help(ctx)
    if ctx.channel_id == cfg.channels['exceptions']:
        return exceptions_help(ctx)
    return default_help(ctx)

def lobby_list_info(ctx, names_in_lobby, names_in_1v1_lobby):
    """ Returns the lobby info both nvn and 1v1"""
    embed = Embed(colour=Color.blue())
    list_of_names = "\n".join(names_in_lobby)
    list_of_names_1v1 = "\n".join(names_in_1v1_lobby)
    if list_of_names == "":
        list_of_names = "Queue is empty"
    embed.add_field(name=f'Lobby: {len(names_in_lobby)} / {cfg.general["lobby_size"]}', value=list_of_names,
                    inline=False)
    if list_of_names_1v1 == "":
        list_of_names_1v1 = "1v1 Queue is empty"
    embed.add_field(name=f'1v1 Lobby: {len(names_in_1v1_lobby)} / 2', value=list_of_names_1v1,
                    inline=False)
    return embed


def lobby_list(ctx, names_in_lobby):
    """ Returns the lobby list """
    embed = Embed(colour=Color.blue())
    list_of_names = "\n".join(names_in_lobby)
    if list_of_names == "":
        list_of_names = "Queue is empty"
    embed.add_field(name=f'Lobby: {len(names_in_lobby)} / {cfg.general["lobby_size"]}', value=list_of_names,
                    inline=False)
    return embed

def lobby_list_training(ctx, names_in_lobby):
    embed = Embed(colour=Color.blue())
    list_of_names = "\n".join(names_in_lobby)
    if list_of_names == "":
        list_of_names = "Queue is empty"
    embed.add_field(name=f'Training Lobby: {len(names_in_lobby)} / {cfg.general["training_lobby_size"]}', value=list_of_names,
                    inline=False)
    return embed

def lobby_list_1v1(ctx, names_in_lobby):
    """ Returns the lobby list """
    embed = Embed(colour=Color.blue())
    list_of_names = "\n".join(names_in_lobby)
    if list_of_names == "":
        list_of_names = "Queue is empty"
    embed.add_field(name=f'1v1 Lobby: {len(names_in_lobby)} / {2}', value=list_of_names,
                    inline=False)
    return embed

def offline_list(ctx, p_list):
    embed = Embed(
        colour=Color.red(),
        title='Offline Players',
        description=f'If your character info is incorrect, re-register using `=r` in <#{cfg.channels["register"]}>!'
    )
    embed.add_field(name=f"The following {'players are' if len(p_list) > 1 else 'player is'} not online ingame:",
                    value="\n".join(f"{p.ig_name} ({p.mention})" for p in p_list),
                    inline=False)

    return embed


def global_info(ctx, lobby, lobby1v1, match_list):
    embed = Embed(
        colour=Color.greyple(),
        title='Global Info',
        description=f'BWAE Battle Bot version `{cfg.VERSION}`'
    )
    lb_embed = lobby_list(ctx, names_in_lobby=lobby).fields[0]
    lb_1v1_embed = lobby_list_1v1(ctx, names_in_lobby=lobby1v1).fields[0]
    embed.add_field(name=lb_embed.name, value=lb_embed.value, inline=lb_embed.inline)
    embed.add_field(name=lb_1v1_embed.name, value=lb_1v1_embed.value, inline=lb_1v1_embed.inline)
    for m in match_list:
        desc = ""
        if m.status is MatchStatus.IS_FREE:
            continue
        else:
            if m.round_no != 0:
                desc += f"Match {m.id} - Round {m.round_no}"
            else:
                desc += f"Match {m.id}"
            desc += "\n"
        desc += f"Status: *{m.status_str}*"
        if m.status is MatchStatus.IS_PLAYING:
            desc += f"\nTime Remaining: **{m.get_formatted_time_to_round_end()}**"
        if m.base:
            desc += f"\nBase: [{m.base.name}]({cfg.base_images[m.base.id]})"
        for tm in m.teams:
            if tm and tm.faction != 0:
                desc += f"\n{tm.name}: {cfg.emojis[cfg.factions[tm.faction]]} {cfg.factions[tm.faction]}"

        embed.add_field(name=m.channel.name, value=desc, inline=False)
    return embed


def flip_accounts(ctx, account_names):
    embed = Embed(colour=Color.red())
    embed.add_field(name="Characters affected:",
                    value="\n".join(i_name for i_name in account_names),
                    inline=False)

    return embed


def team_update(ctx, match):
    """ Returns the current teams
    """
    # title = ""
    if match.round_no != 0:
        title = f"Match {int(match.id)} - Round {match.round_no}"
    else:
        title = f"Match {int(match.id)}"
    desc = match.status_str
    if match.status is MatchStatus.IS_PLAYING:
        desc += f"\nTime Remaining: **{match.get_formatted_time_to_round_end()}**"
    embed = Embed(colour=Color.blue(), title=title, description=desc)
    if match.base is not None:
        embed.add_field(name="Base", value=match.base.name, inline=False)
        if match.base.id in cfg.base_images:
            embed.set_thumbnail(url=cfg.base_images[match.base.id])
    for tm in match.teams:
        if tm.captain:
            value = ""
            name = ""
            cap_mention = f"{tm.captain.mention} ({tm.captain.name})"
            if match.next_status in (MatchStatus.IS_WAITING, MatchStatus.IS_STARTING, MatchStatus.IS_PLAYING):
                cap_mention += f" [{tm.captain.ig_name}]"
            if match.next_status in (MatchStatus.IS_FACTION, MatchStatus.IS_PICKING) and tm.captain.is_turn:
                value = f"Captain **[pick]**: {cap_mention}\n"
            else:
                value = f"Captain: {cap_mention}\n"
            if tm.player_pings:
                value += "Players:\n" + '\n'.join(tm.player_pings)
            faction = ""
            if tm.faction != 0:
                faction = f"{cfg.emojis[cfg.factions[tm.faction]]} {cfg.factions[tm.faction]}"
            if match.next_status is MatchStatus.IS_WAITING:
                if tm.captain.is_turn:
                    name = f"{tm.name} - {faction} - not ready"
                else:
                    name = f"{tm.name} - {faction} - ready"
            elif faction:
                name = f"{tm.name} - {faction}"
            else:
                name = f"{tm.name}"
            embed.add_field(name=name,
                            value=value,
                            inline=False)
    name = ""
    if match.next_status is MatchStatus.IS_PICKING:
        name = "Remaining"
    if match.next_status is MatchStatus.IS_CAPTAIN:
        name = "Players"
    if name:
        players_string = "\n".join([f"- {p.mention} ({p.name})" for p in match.get_left_players()])
        embed.add_field(name=name, value=players_string, inline=False)
    return embed


def jaeger_calendar(arg):
    """ Returns an embedded link to the formatted Jaeger Calendar
    """
    embed = Embed(colour=Color.blue(), title="Jaeger Calendar",
                  url="https://docs.google.com/spreadsheets/d/1eA4ybkAiz-nv_mPxu_laL504nwTDmc-9GnsojnTiSRE",
                  description="Pick a base currently available in the calendar!")
    date = dt.now(tz.utc)
    embed.add_field(name="Current UTC time",
                    value=date.strftime("%Y-%m-%d %H:%M UTC"),
                    inline=False)
    return embed


def base_display(ctx, base, is_booked):
    description = f"[Full Base Pool]" \
                  f"(https://docs.google.com/presentation/d/1xOtNU4THuHe7PTj8RcVpLOLmfQk9zL9QmN9JYR29c5U)"
    if is_booked:
        embed = Embed(colour=Color.red(), title=base.name,
                      description=f"{description}\nWARNING! This base seems to be unavailable!")
    else:
        embed = Embed(colour=Color.blue(), title=base.name, description=description)
    if base.id in cfg.base_images:
        embed.set_image(url=cfg.base_images[base.id])
    else:
        embed.add_field(name=f"Image",
                        value="Not available for this base",
                        inline=False)
    return embed


def join_ts(ctx):
    embed = Embed(colour=Color.blue(), title="Teamspeak server",
                  description="Join the Teamspeak server for the duration of the match! "
                              "The address is `ts.bushidoway.net` (no password)")
    if cfg.ts["config_help"]:
        embed.set_image(url=cfg.ts["config_help"])
    return embed


def direct_message(ctx, player, msg):
    description = f"Received a DM"
    if player:
        description += f"\nHandle: {player.mention}\nName: {player.name}\nID: `{player.id}`\n"
    else:
        description += f" from unregistered user {msg.author.mention} (id: {msg.author.id})\n"
    embed = Embed(colour=Color.dark_grey(), title="Direct Message",
                  description=description)
    embed.add_field(name=f"Message:",
                    value=msg.content,
                    inline=False)
    return embed


def usage(ctx, data):
    is_account = data["_id"] < 1000
    if is_account:
        description = f'Last 20 usages for practice account {data["_id"]}'
    else:
        description = f'Last 20 usages for <@{data["_id"]}>'
    embed = Embed(
        colour=Color.blue(),
        title='Last account usages',
        description=description
    )
    if is_account:
        embed.add_field(name="Account used by:",
                        value="\n".join(f'<@{user}>' for user in data["unique_usages"]),
                        inline=False)
    else:
        embed.add_field(name="Accounts used:",
                        value="\n".join(f'Practice account {a_id}' for a_id in data["unique_usages"]),
                        inline=False)

    for use in data["usages"][19::-1]:
        if is_account:
            name = f'User: <@{use["id"]}>'
        else:
            name = f'Practice account {use["id"]}'
        lead_str = tools.time_diff(use["time_stop"]) + " ago"
        embed.add_field(name=lead_str,
                        value=name + f'\nMatch {use["match_id"]}\n'
                                     f'Starting time: {dt.utcfromtimestamp(use["time_start"]).strftime("%Y-%m-%d %H:%M UTC")}\n'
                                     f'Stopping time: {dt.utcfromtimestamp(use["time_stop"]).strftime("%Y-%m-%d %H:%M UTC")}\n',
                        inline=False)
    return embed


def psb_usage(ctx, player, usages):
    string_list = list()
    embed = Embed(
        colour=Color.blue(),
        title='Jaeger participation',
        description=f"Handle: {player.mention}\nName: {player.name}\nID: `{player.id}`\n"
    )
    for use in usages:
        bef = "✅" if use.num else "❌"
        pref = "**" if use.num else ""
        week = f"{use.week_num} week{'s' if use.week_num > 1 else ''} ago" if use.week_num else f"Current week"
        match_str = "matches" if use.num > 1 else "match"
        string_list.append(f"{bef} {pref}{week} "
                           f"[{use.start_str} - {use.end_str}] {use.num} {match_str}{pref}")
    embed.add_field(name="Participation", value="\n".join(string_list), inline=False)

    return embed

def player_stats(ctx, stats, recent_stats):
    embed = Embed(title=f"{stats.name}'s Stats:", colour=Color.blue())
    embed.add_field(name="Recent (last 2 weeks)",
                    value=f"Matches played: {recent_stats.nb_matches_played}\n"
                          f"Play time: {'{:.1f}'.format(recent_stats.time_played / 60)} hours\n"
                          f"Score: {recent_stats.score}\n"
                          f"KDR: {round(recent_stats.kdr, 3)}\n"
                          f"Kills: {recent_stats.kills}\n"
                          f"Deaths: {recent_stats.deaths}\n"
                          f"Times captain: {recent_stats.times_captain}\n"
                          f"Kills per match: {'{:.1f}'.format(recent_stats.kills_per_match)}\n"
                          f"Most played class: {recent_stats.most_played_loadout}",
                    inline=False)
    embed.add_field(name="All time",
                    value=f"Matches played: {stats.nb_matches_played}\n"
                          f"Play time: {'{:.1f}'.format(stats.time_played / 60)} hours\n"
                          f"Total Score: {stats.score}\n"
                          f"KDR: {round(stats.kdr, 3)}\n"
                          f"Total Kills: {stats.kills}\n"
                          f"Total Deaths: {stats.deaths}\n"
                          f"Times captain: {stats.times_captain}\n"
                          f"Kills per match: {'{:.1f}'.format(stats.kills_per_match)}\n"
                          f"Most played class: {stats.most_played_loadout}",
                    inline=False)
    return embed
