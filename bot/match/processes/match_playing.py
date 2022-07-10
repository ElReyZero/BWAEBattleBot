from display import AllStrings as disp, ContextWrapper, views
from asyncio import sleep
from datetime import datetime as dt, timezone as tz
from lib.tasks import Loop, loop
from logging import getLogger
from modules import lobby
from match import MatchStatus
from .process import Process

import modules.config as cfg
import modules.interactions as interactions

from modules.asynchttp import ApiNotReachable
from display.classes import InteractionContext
from match.classes.base_selector import push_last_bases
import modules.census as census
import modules.tools as tools
import modules.image_maker as i_maker
from classes.players import Player

log = getLogger("pog_bot")


class MatchPlaying(Process, status=MatchStatus.IS_STARTING):

    def __init__(self, match, is1v1=False, isTraining=False):
        self.match = match
        self.is1v1 = is1v1
        self.isTraining= isTraining
        self.match_loop = Loop(coro=self.on_match_over, minutes=match.round_length, delay=1, count=2)
        if not is1v1:
            if not self.isTraining:
                self.ih = interactions.InteractionHandler(self.match, views.refresh_button, disable_after_use=False)
            else:
                self.ih = interactions.InteractionHandler(self.match, views.training_buttons, disable_after_use=False)
        else:
            self.ih = interactions.InteractionHandler(self.match, views.buttons_1v1, disable_after_use=False)
        self.info_message = None

        @self.ih.callback('refresh')
        async def refresh(player, interaction_id, interaction, interaction_values):
            await disp.PK_SHOW_TEAMS.edit(self.info_message, match=self.match.proxy)

        @self.ih.callback('endRound')
        async def endRound(player, interaction_id, interaction, interaction_values):
            user = Player.get(interaction.user.id)
            match = user.match
            try:
                if match.objects==self.match:
                    if match.is1v1 or match.isTraining:
                        await match.trigger_next_process()
                    else:
                        i_ctx = InteractionContext(interaction)
                        await disp.CANNOT_END.send(i_ctx) 
                else:
                    i_ctx = InteractionContext(interaction)
                    await disp.CANNOT_END.send(i_ctx)
            except AttributeError:
                i_ctx = InteractionContext(interaction)
                await disp.CANNOT_END.send(i_ctx)

        super().__init__(match)

    @Process.init_loop
    async def init(self):
        if self.match.base_selector:
            self.match.base_selector.clean()
            push_last_bases(self.match.base)
            self.match.base_selector = None
        self.start_match_loop.start()

    @loop(count=1)
    async def start_match_loop(self):
        self.match.plugin_manager.on_match_starting()
        await disp.MATCH_STARTING_1.send(self.match.channel, self.match.round_no, "30")
        await sleep(10)
        await disp.MATCH_STARTING_2.send(self.match.channel, self.match.round_no, "20")
        await sleep(10)
        await disp.MATCH_STARTING_2.send(self.match.channel, self.match.round_no, "10")
        await sleep(10)
        player_pings = [" ".join(tm.all_playing_pings) for tm in self.match.teams]
        await disp.MATCH_STARTED.send(self.match.channel, *player_pings, self.match.round_no)
        self.match.plugin_manager.on_match_started()
        self.match.round_stamps.append(tools.timestamp_now())
        super().change_status(MatchStatus.IS_PLAYING)
        self.match_loop.start()
        self.auto_info_loop.start()
        self.match.status = MatchStatus.IS_PLAYING

    @Process.public
    async def info(self, ctx=None):
        ctx = self.ih.get_new_context(self.match.channel)
        msg = await disp.PK_SHOW_TEAMS.send(ctx, match=self.match.proxy)
        self.info_message = msg

    @loop(seconds=15)
    async def auto_info_loop(self):
        if self.info_message:
            await disp.PK_SHOW_TEAMS.edit(self.info_message, match=self.match.proxy)
        else:
            await self.info()

    @Process.public
    def get_formatted_time_to_round_end(self):
        secs = self.get_seconds_to_round_end()
        return f"{secs // 60}m {secs % 60}s"

    def get_seconds_to_round_end(self):
        time_delta = self.match_loop.next_iteration - dt.now(tz.utc)
        return int(time_delta.total_seconds())

    async def on_match_over(self):
        player_pings = [" ".join(tm.all_playing_pings) for tm in self.match.teams]
        self.auto_info_loop.cancel()
        self.ih.clean()
        self.match.plugin_manager.on_round_over(is1v1=self.is1v1, isTraining=self.isTraining)
        round_no = self.match.round_no
        self.match.ready_next_process(is1v1=self.is1v1, isTraining=self.isTraining)
        await disp.MATCH_ROUND_OVER.send(self.match.channel, *player_pings, round_no)
        try:
            await census.process_score(self.match.data, self.match.last_start_stamp, self.match.channel)
            try:
                await i_maker.publish_match_image(self.match, is1v1=self.is1v1, isTraining=self.isTraining)
            except Exception as e:
                # Should not happen
                log.error(f"Error in publish_match_image : {e}")
                await disp.PUBLISH_ERROR.send(ContextWrapper.channel(cfg.channels["results"]), int(self.match.id), round_no)
        except ApiNotReachable as e:
            log.error(f"ApiNotReachable caught when processing scores : {e.url}")
            await disp.API_SCORE_ERROR.send(ContextWrapper.channel(cfg.channels["results"]), int(self.match.id), round_no)
        lobby._training_unlocked = False
        self.match.start_next_process()

    @Process.public
    def get_current_context(self, ctx):
        return self.ih.get_new_context(ctx)

    @Process.public
    async def clear(self, ctx):
        self.start_match_loop.cancel()
        self.auto_info_loop.cancel()
        self.match_loop.cancel()
        self.ih.clean()
        player_pings = [" ".join(tm.all_playing_pings) for tm in self.match.teams]
        self.match.clean_critical()
        self.match.plugin_manager.on_round_over(is1v1=self.is1v1, matchEnd=True)
        await disp.MATCH_ROUND_OVER.send(self.match.channel, *player_pings, self.match.round_no)
        await disp.MATCH_OVER.send(self.match.channel)
        await self.match.clean_async()
        await disp.MATCH_CLEARED.send(ctx)


