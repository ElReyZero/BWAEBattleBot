from discord.ext import commands
from logging import getLogger

import modules.config as cfg
import modules.lobby as lobby

from match.classes.match import Match
from display import AllStrings as disp, ContextWrapper
from match import MatchStatus

log = getLogger("pog_bot")


class MatchesCog(commands.Cog, name='common'):
    """
    Register cog, handle the commands in matches channels
    """

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['i'])
    @commands.guild_only()
    async def info(self, ctx):
        if ctx.channel.id == cfg.channels["lobby"]:
            match_list = list()
            for ch in cfg.channels["matches"]:
                match_list.append(Match.get(ch))
            for ch in cfg.channels["matches1v1"]:
                match_list.append(Match.get(ch))
            await disp.GLOBAL_INFO.send(ctx, lobby=lobby.get_all_names_in_lobby(), lobby1v1=lobby.get_all_1v1_names_in_lobby(), lobby_training=lobby.get_all_names_in_training_lobby(), match_list=match_list)
            return

        if ctx.channel.id in cfg.channels["matches"] or ctx.channel.id in cfg.channels["matches1v1"]:
            match = Match.get(ctx.channel.id)
            await match.command.info(ctx)
            return
        await disp.WRONG_CHANNEL_2.send(ctx, ctx.command.name, f"<#{ctx.channel.id}>")


def setup(client):
    client.add_cog(MatchesCog(client))
