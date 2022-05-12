# @CHECK 2.0 features OK

from discord.ext import commands
from discord import Status as discord_status
from logging import getLogger
from match.classes.match import Match
from asyncio import TimeoutError
from display import AllStrings as disp, views, ContextWrapper
import modules.config as cfg

from classes import Player

import modules.interactions as interactions
import modules.lobby as lobby

log = getLogger("pog_bot")
queue_context = None

async def check_join_queue(player, ctx, is1v1):
    if not player:
        await disp.EXT_NOT_REGISTERED.send(ctx,  cfg.channels["register"])
        return False
    if not player.is_registered:
        await disp.EXT_NOT_REGISTERED.send(ctx, cfg.channels["register"])
        return False
    accs = player.accounts_flipped
    if len(accs) != 0:
        await disp.CHECK_ACCOUNT.send(ctx, cfg.channels["register"], account_names=accs)
        return False
    if player.is_lobbied:
        await disp.LB_ALREADY_IN.send(ctx)
        return False
    if player.match:
        await disp.LB_IN_MATCH.send(ctx)
        return False
    if lobby.is_lobby_stuck():
        await disp.LB_STUCK_JOIN.send(ctx)
        return False
    if is1v1:
        match = Match.find_ongoing_1v1()
        if match is not None:
            await disp.ONGOING_1V1.send(ctx, match.channel)
            return False
    return True

def _add_ih_callback(ih, ctx):
    @ih.callback('join1v1queue')
    async def on_user_react(p, interaction_id, interaction, interaction_values):
        global queue_context
        nonlocal ctx

        local_context = queue_context
        user = interaction.user
        player = Player.get(user.id)

        if local_context is None:
            local_context = ctx
            
        if not await check_join_queue(player, local_context, True):
            return
        ctx = ih.get_new_context(ctx)
        ctx.author = user
        names = lobby.add_to_1v1_lobby(player)
        await disp.LB_ADDED_1v1.send(ctx, names_in_lobby=names)
        ih.clean()

    @ih.callback('training_config')
    async def on_training_select(p, interaction_id, interaction, values):
        lobby._training_unlocked = True
        try:
            value = int(values[0])
            cfg.general["training_rounds"] = value
            await disp.TRAINING_CONFIG_SUCCESS.send(ctx, value)
        except (ValueError, IndexError):
            await disp.INVALID_VALUE.send(ctx)
            return
        

class LobbyCog(commands.Cog, name='lobby'):
    """
    Lobby cog, handle the commands from lobby channel
    """

    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return ctx.channel.id == cfg.channels['lobby']

    """
    Commands:

    =join
    =leave
    =queue
    =lbsize [size]
    =rndtime [duration]
    =1v1
    """

    @commands.command(aliases=['j'])
    @commands.guild_only()
    async def join(self, ctx):
        """ Join queue
        """
        if lobby.get_lobby_len() > cfg.general["lobby_size"]:  # This should not happen EVER
            await disp.UNKNOWN_ERROR.send(ctx, "Lobby Overflow")
            return
        player = Player.get(ctx.message.author.id)
        if not player:
            await disp.EXT_NOT_REGISTERED.send(ctx,  cfg.channels["register"])
            return
        if not player.is_registered:
            await disp.EXT_NOT_REGISTERED.send(ctx, cfg.channels["register"])
            return
        accs = player.accounts_flipped
        if len(accs) != 0:
            await disp.CHECK_ACCOUNT.send(ctx, cfg.channels["register"], account_names=accs)
            return
        if player.is_lobbied:
            await disp.LB_ALREADY_IN.send(ctx)
            return
        if player.match:
            await disp.LB_IN_MATCH.send(ctx)
            return
        if lobby.is_lobby_stuck():
            await disp.LB_STUCK_JOIN.send(ctx)
            return

        names = lobby.add_to_lobby(player)
        await disp.LB_ADDED.send(ctx, names_in_lobby=names)

    @commands.command(aliases=['rst'])
    @commands.guild_only()
    async def reset(self, ctx):
        """ Join queue
        """
        player = Player.get(ctx.message.author.id)
        if not player or (player and not player.is_lobbied):
            await disp.LB_NOT_IN.send(ctx)
            return
        lobby.reset_timeout(player)
        await disp.LB_REFRESHED.send(ctx)

    @commands.command(aliases=['l'])
    @commands.guild_only()
    async def leave(self, ctx):
        """ Leave queue
        """
        player = Player.get(ctx.message.author.id)
        if not player:
            await disp.LB_NOT_IN.send(ctx)
            return
        if player.is_lobbied:
            is1v1, isTraining = lobby.remove_from_lobby(player)
            if is1v1:
                ih = interactions.InteractionHandler(None, views.join1v1queue, disable_after_use=False)
                _add_ih_callback(ih, ctx)
                ctx = ih.get_new_context(ctx)
                await disp.LB_REMOVED_1v1.send(ctx, names_in_lobby=lobby.get_all_1v1_names_in_lobby())
            elif isTraining:
                await disp.LB_REMOVED_TRAINING.send(ctx, names_in_lobby=lobby.get_all_names_in_training_lobby())
            else:
                await disp.LB_REMOVED.send(ctx, names_in_lobby=lobby.get_all_names_in_lobby())
            return
        
        await disp.LB_NOT_IN.send(ctx)

    @commands.command(aliases=['q'])
    @commands.guild_only()
    async def queue(self, ctx):
        """ disp queue
        """
        if lobby.get_lobby_len() > cfg.general["lobby_size"]:
            await disp.UNKNOWN_ERROR.send(ctx, "Lobby Overflow")
            return
        if lobby.is_lobby_stuck():
            await disp.LB_QUEUE.send(ctx, names_in_lobby=lobby.get_all_names_in_lobby(), names_in_1v1_lobby=lobby.get_all_1v1_names_in_lobby())
            await disp.LB_STUCK.send(ctx)
            return
        await disp.LB_QUEUE.send(ctx, names_in_lobby=lobby.get_all_names_in_lobby(), names_in_1v1_lobby=lobby.get_all_1v1_names_in_lobby())

    @commands.command(aliases=['lbsize','lobbysize'])
    @commands.guild_only()
    async def changeLobbySize(self, ctx, size):
        """Change the lobby size
        """
        try:
            if int(size)<=2:
                raise ValueError
            if len(lobby.get_all_names_in_lobby()) <= int(size):
                cfg.general["lobby_size"] = int(size)
                await disp.LOBBY_SIZE_CHANGED.send(ctx, size)
                return
            else:
                await disp.LOBBY_SIZE_ERR_NOT_EMPTY.send(ctx)
                return
        except ValueError:
            await disp.WRONG_TYPE_ARGS.send(ctx)
            return

    @commands.command(aliases=['trsize','trainingsize'])
    @commands.guild_only()
    async def changeTrainingSize(self, ctx, size):
        """Change the lobby size
        """
        try:
            if int(size)<=2:
                raise ValueError
            if len(lobby.get_all_names_in_lobby()) <= int(size):
                cfg.general["training_lobby_size"] = int(size)
                await disp.TRAINING_SIZE_CHANGED.send(ctx, size)
                return
            else:
                await disp.LOBBY_SIZE_ERR_NOT_EMPTY.send(ctx)
                return
        except ValueError:
            await disp.WRONG_TYPE_ARGS.send(ctx)
            return

    @commands.command(aliases=['rndtime', 'roundtime', 'rndlength'])
    @commands.guild_only()
    async def changeRoundDuration(self, ctx, duration):
        """Change the duration in minutes of a round
        """
        try:
            if int(duration)<=0:
                raise ValueError
            else:
                cfg.general["round_length"] = int(duration)
                await disp.ROUND_LENGTH_CHANGED.send(ctx, duration)
                return
        except ValueError:
            await disp.ROUND_LENGTH_ERROR.send(ctx)
            return

    @commands.command(aliases=['1v1'])
    @commands.guild_only()
    async def queue1v1(self, ctx):
        player = Player.get(ctx.message.author.id)
        if not await check_join_queue(player, ctx, True):
            return
        ih = interactions.InteractionHandler(None, views.join1v1queue, disable_after_use=False)
        _add_ih_callback(ih, ctx)
        global queue_context
        queue_context = ctx
        ctx = ih.get_new_context(ctx)
        names = lobby.add_to_1v1_lobby(player)
        await disp.LB_ADDED_1v1.send(ctx, names_in_lobby=names)

    @commands.command(aliases=['straining', 'training', 'trainingconfig'])
    async def training_config(self, ctx):
        if lobby._training_unlocked:
            await disp.TRAINING_ALREADY_CONFIGURED.send(ctx)
            def check(m):
                return (m.content.lower() == "y" or m.content.lower() == "n" or m.content.lower() == "yes" or m.content.lower() == "no") and m.author == ctx.message.author
            try:
                msg = await ctx.bot.wait_for("message", check=check, timeout=60)
                if msg.content.lower() == "no" or msg.content.lower() == "n":
                    await disp.CONFIG_CANCELED.send(ctx)
                    return
            except TimeoutError:
                await disp.CONFIG_TIMEOUT.send(ctx)
                return

        ih = interactions.InteractionHandler(None, views.training_config, disable_after_use=True)
        _add_ih_callback(ih, ctx)
        ctx = ih.get_new_context(ctx)
        await disp.TRAINING_CONFIG.send(ctx)

    @commands.command(aliases=["jointraining", "tr", "jtraining", "jtr"])
    @commands.guild_only()
    async def queueTraining(self, ctx):
        if not lobby._training_unlocked:
            await disp.TRAINING_NOT_UNLOCKED.send(ctx)
            return
        player = Player.get(ctx.message.author.id)
        if not await check_join_queue(player, ctx, False):
            return
        names = lobby.add_to_lobby(player, training=True)
        await disp.LB_ADDED_TRAINING.send(ctx, names_in_lobby=names)

def setup(client):
    client.add_cog(LobbyCog(client))
