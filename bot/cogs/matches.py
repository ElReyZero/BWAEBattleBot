from discord.ext import commands
from classes.players import Player
import modules.config as cfg
from match.classes import Match
from classes import Base
from display import AllStrings as disp

class MatchesCog(commands.Cog, name='matches'):
    """
    Matches cog, handle the user commands in matches channels
    """

    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        # Check if right channel
        return ctx.channel.id in cfg.channels['matches'] or ctx.channel.id in cfg.channels['matches1v1']

    """
    commands:

    =captain
    =sub
    =pick
    =base
    =ready
    =squittal
    =end1v1
    =join1v1
    """
    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def end1v1(self, ctx):
        if ctx.channel.id in cfg.channels['matches1v1']:
            match = Match.get(ctx.channel.id)
            await match.trigger_next_process()
        else:
            await disp.WRONG_CHANNEL_2.send(ctx, ctx.command.name, f"<#{ctx.channel.id}>")  
    
    @commands.command(aliases=["join1v1", "j1v1", "joinTraining", "joinTr", "letmein", 'joinFightClub', 'joinFC', 'joinfc', 'jfc', 'joinfightclub'])
    @commands.guild_only()
    async def joinMatch(self, ctx):
        player = Player.get(ctx.message.author.id)
        match = Match.get(ctx.channel.id)
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
        if ctx.channel.id in cfg.channels['matches1v1'] or match.isTraining:
            await match.join(ctx, player, match)  
        else:
            await disp.WRONG_CHANNEL_2.send(ctx, ctx.command.name, f"<#{ctx.channel.id}>") 

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def sub(self, ctx, *args):
        match = Match.get(ctx.channel.id)
        await match.command.sub(ctx, args)

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def swap(self, ctx, *args):
        match = Match.get(ctx.channel.id)
        await match.command.swap(ctx, args)

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def bench(self, ctx, *args):
        match = Match.get(ctx.channel.id)
        await match.command.bench(ctx, args, bench=True)

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def unbench(self, ctx, *args):
        match = Match.get(ctx.channel.id)
        await match.command.bench(ctx, args, bench=False)

    @commands.command(aliases=['p'])
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def pick(self, ctx, *args):
        match = Match.get(ctx.channel.id)
        arg = " ".join(args)

        # To allow changing base with =p:
        if arg not in ("vs", "tr", "nc", "help", "h"):  # Those args are reserved for =p
            # bl is True if arg is detected to relate to base picking
            bl = arg in ("list", "l")
            bl = bl or Base.get_bases_from_name(arg, base_pool=True)
            if bl:
                await match.command.base(ctx, args)
                return
        await match.command.pick(ctx, args)

    @commands.command(aliases=['b', 'map'])
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def base(self, ctx, *args):
        match = Match.get(ctx.channel.id)
        await match.command.base(ctx, args)

    @commands.command(aliases=['rdy'])
    @commands.guild_only()
    @commands.max_concurrency(number=1, wait=True)
    async def ready(self, ctx):  # when ready
        match = Match.get(ctx.channel.id)
        await match.command.ready(ctx)

    @commands.command()
    @commands.guild_only()
    async def squittal(self, ctx):
        match = Match.get(ctx.channel.id)
        await match.command.squittal(ctx)


def setup(client):
    client.add_cog(MatchesCog(client))

