from logging import getLogger
from classes.players import ActivePlayer
from display import views as v
from lib.tasks import loop
from display.strings import AllStrings as disp
from classes import Base, Team, TeamScore
import modules.database as db
import modules.roles as roles
import modules.config as cfg
import modules.accounts_handler as accounts
from modules.tools import UnexpectedError
import modules.lobby as lobby
import modules.stat_processor as stat_processor
from display import InteractionFollowup, InteractionContext
from match.processes import CaptainSelection, PlayerPicking, FactionPicking, BasePicking, GettingReady, MatchPlaying
from match.commands import CommandFactory
from match.match_status import MatchStatus
from .base_selector import on_match_over
from match.plugins.manager import PluginManager
import modules.interactions as interactions

log = getLogger("pog_bot")

def _add_ih_callback(ih, ctx, matchClass, player, match, faction1, faction2):
    @ih.callback('faction1')
    async def on_f1_select(p, interaction_id, interaction, interaction_values):
        await interaction.response.defer()
        await matchClass.add_player_to_match(ctx, interaction, player, match, 0, faction1, ih)

    @ih.callback('faction2')
    async def on_f2_select(p, interaction_id, interaction, interaction_values):
        await interaction.response.defer()
        await matchClass.add_player_to_match(ctx, interaction, player, match, 1, faction2, ih)

    @ih.callback('cancel')
    async def on_cancel(p, interaction_id, interaction, interaction_values):
        if interaction.user.id == player.get_id() and not player.match:
            await disp.JOIN_CANCELED.send(ctx)
            ih.clean()
        else:
            i_ctx = InteractionContext(interaction, ephemeral=True)
            await disp.CANNOT_CHOOSE_FOR_OTHER_PLAYER.send(i_ctx)
            

class Match:
    __bound_matches = dict()
    __bound_1v1_matches = dict()
    _last_match_id = 0

    @classmethod
    def get(cls, ch_id: int):
        if ch_id in cls.__bound_matches:
            return cls.__bound_matches[ch_id]
        elif ch_id in cls.__bound_1v1_matches:
            return cls.__bound_1v1_matches[ch_id]
        else:
            raise UnexpectedError(f"Can't find bound match {ch_id}")

    @classmethod
    def init_channels(cls, client, ch_list: list, ch_1v1_list:list):
        for ch_id in ch_list:
            channel = client.get_channel(ch_id)
            instance = cls()
            instance.bind(channel)
            cls.__bound_matches[ch_id] = instance

        for ch_id in ch_1v1_list:
            channel = client.get_channel(ch_id)
            instance = cls()
            instance.bind(channel)
            cls.__bound_1v1_matches[ch_id] = instance
        cls._last_match_id = db.get_field("restart_data", 0, "last_match_id")

    @classmethod
    def find_empty(cls, is_1v1=False):
        if is_1v1:
            for match in cls.__bound_1v1_matches.values():
                if match.status is MatchStatus.IS_FREE:
                    return match
        for match in cls.__bound_matches.values():
            if match.status is MatchStatus.IS_FREE:
                return match
        return None

    @classmethod
    def find_ongoing_1v1(cls):
        for match in cls.__bound_1v1_matches.values():
            if match.status is not MatchStatus.IS_FREE:
                return match

    @classmethod
    async def get_from_database(cls, m_id: int):
        data = await db.async_db_call(db.get_element, "matches", m_id)
        instance = cls(data)
        return instance

    def __init__(self, data=None):
        self.__data = MatchData(self, data)
        self.__objects = None
        self.__is1v1 = False
        self.__isTraining = False

    def bind(self, channel):
        self.__objects = MatchObjects(self, self.__data, channel)
        self.__objects.delayed_init()

    # TODO: dev, remove
    @property
    def data(self):
        return self.__data


    @property
    def is1v1(self):
        return self.__is1v1
    
    @is1v1.setter
    def is1v1(self, value):
        self.__is1v1 = value

    @property
    def isTraining(self):
        return self.__isTraining
    
    @isTraining.setter
    def isTraining(self, value):
        self.__isTraining = value

    @property
    def channel(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound,\
                                  no attribute 'channel'")
        return self.__objects.channel

    @property
    def status(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'status'")
        return self.__objects.status

    @property
    def next_status(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'status'")
        return self.__objects.next_status

    @property
    def status_str(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'status_str'")
        return self.__objects.status_str

    @property
    def id(self):
        return self.__data.id

    @property
    def teams(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'teams'")
        return self.__objects.teams

    @property
    def round_no(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'round_no'")
        return self.__objects.round_no
    
    @property
    def objects(self):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'objects'")
        return self.__objects

    @property
    def base(self):
        return self.__data.base

    @property
    def round_stamps(self):
        return self.__data.round_stamps

    @property
    def round_length(self):
        return self.__data.round_length

    async def join(self, ctx, player, match):
        teams = self.__data.teams
        if teams[0] is None or teams[1] is None:
            await disp.CANNOT_JOIN_NOT_PLAYING.send(ctx)
            return

        team_list = [tm.get_data() for tm in teams]
        cfg.join_factions["faction1"] = team_list[0]["faction_id"]
        cfg.join_factions["faction2"] = team_list[1]["faction_id"]
        ih = interactions.InteractionHandler(None, v.joinCurrentMatch_buttons, disable_after_use=False)
        if cfg.join_factions["faction1"] == 1:
            faction1 = 'VS'
        elif cfg.join_factions["faction1"] == 2:
            faction1 = 'NC'
        else:
            faction1 = 'TR'

        if cfg.join_factions["faction2"] == 1:
            faction2 = 'VS'
        elif cfg.join_factions["faction2"] == 2:
            faction2 = 'NC'
        else:
            faction2 = 'TR'
        _add_ih_callback(ih,ctx, self, player, match, faction1, faction2)
        new_ctx = ih.get_new_context(ctx)
        await disp.CHOOSE_FACTION.send(new_ctx)
        
    async def add_player_to_match(self, ctx, interaction, player, match, teamNum, faction, ih):
        if interaction.user.id == player.get_id() and not player.match:
                await player.on_match_selected(match)
                player.active = match.__objects.teams[teamNum].add_player_return(ActivePlayer, player)
                active = player.active
                if not active.has_own_account:
                    await self.try_remove_account(player.active, match.__objects)
                    await self.give_account(active, match.__objects)
                match.__objects.plugin_manager.on_teams_updated()
                active.on_match_starting()
                player.match = match  
                i_ctx = InteractionFollowup(interaction, ephemeral=False)
                await disp.FACTION_SELECTED.send(i_ctx, faction)
                await match.command.info(ctx)
                ih.clean()
        else:
            i_ctx = InteractionFollowup(interaction, ephemeral=True)
            await disp.CANNOT_CHOOSE_FOR_OTHER_PLAYER.send(i_ctx)

    async def try_remove_account(self, a_player, match, update=False):
        if a_player.account:
            await accounts.terminate_account(a_player)
            match.players_with_account.remove(a_player)
        if update:
            match.plugin_manager.on_teams_updated()

    async def give_account(self, a_player, match, update=False):
        success = await accounts.give_account(a_player)
        if success:
            match.players_with_account.append(a_player)
            await accounts.send_account(match.channel, a_player, self.is1v1)
            await disp.ACC_GIVING.send(match.channel, a_player.mention)
            if update:
                match.plugin_manager.on_teams_updated()
        else:
            await disp.ACC_NOT_ENOUGH.send(match.channel)
            return

    def change_check(self, arg):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'change_check'")
        if arg == "online":
            self.__objects.check_offline = not self.__objects.check_offline
            return self.__objects.check_offline
        elif arg == "account":
            self.__objects.check_validated = not self.__objects.check_validated
            return self.__objects.check_validated
        else:
            raise KeyError

    def spin_up(self, p_list, is1v1=False, training=False):
        if not self.__objects:
            raise AttributeError("Match instance is not bound, no attribute 'spin_up'")
        Match._last_match_id += 1
        if is1v1:
            self.is1v1 = True
            self.__objects.on_spin_up_1v1(p_list)
        elif training:
            self.isTraining = True
            self.__objects.on_spin_up_training(p_list)
        else:
            self.__objects.on_spin_up(p_list)
        db.set_field("restart_data", 0, {"last_match_id": Match._last_match_id})

    async def trigger_next_process(self):
        try:
            if self.__objects.status == MatchStatus.IS_PLAYING:
                current_process = self.__objects.get_current_process()
                current_process.start_match_loop.cancel()
                current_process.match_loop.cancel()
                await current_process.on_match_over()
            else:
                await disp.CANNOT_END_MATCH_NOT_PLAYING.send(self.channel)
        except AttributeError as e:
            print(e.with_traceback())
            await disp.CANNOT_END_MATCH_NOT_PLAYING.send(self.channel)

    @property
    def command(self):
        if not self.__objects:
            raise AttributeError(f"Match instance is not bound, no attribute 'command'")
        return self.__objects.command

    @property
    def bases_list(self):
        if not self.__objects:
            raise AttributeError(f"Match instance is not bound, no attribute 'bases_list'")
        return self.__objects.base_selector.bases_list

    def __getattr__(self, name):
        if not self.__objects:
            raise AttributeError(f"Match instance is not bound, no attribute '{name}'")
        return self.__objects.get_process_attr(name)


class MatchData:
    def __init__(self, match: Match, data: dict):
        self.match = match
        if data:
            self.id = data["_id"]
            self.teams = [TeamScore.from_data(0, match, data["teams"][0]),
                          TeamScore.from_data(1, match, data["teams"][1])]
            self.base = Base.get(data["base_id"])
            self.round_length = data["round_length"]
            self.round_stamps = data["round_stamps"]
        else:
            self.id = 0
            self.teams = [None, None]
            self.base = None
            self.round_length = 0
            self.round_stamps = list()

    def get_data(self):
        dta = dict()
        dta["_id"] = self.id
        dta["round_stamps"] = self.round_stamps
        dta["round_length"] = self.round_length
        dta["base_id"] = self.base.id
        dta["teams"] = [tm.get_data() for tm in self.teams]
        return dta

    def reset_score(self):
        for tm in self.teams:
            tm.reset_score()

    def round_update(self, round_no):
        for tm in self.teams:
            tm.round_update(round_no)

    def clean(self):
        self.id = 0
        self.teams = [None, None]
        self.base = None
        self.round_stamps.clear()
        self.round_length = 0

    async def push_db(self):
        await db.async_db_call(db.set_element, "matches", self.id, self.get_data())
        stat_processor.add_match(self)
        if self.teams[0].score == self.teams[1].score:
            self.teams[0].set_winner()
            self.teams[1].set_winner()
        elif self.teams[0].score > self.teams[1].score:
            self.teams[0].set_winner()
        else:
            self.teams[1].set_winner()
        for tm in self.teams:
            for p in tm.players:
                await p.db_update_stats()


_process_list = [CaptainSelection, PlayerPicking, FactionPicking, BasePicking, GettingReady, MatchPlaying,
                 GettingReady, MatchPlaying]

def change_process_lists(is1v1=False, isTraining=False, training_rounds=1):
    global _process_list
    if is1v1:
        _process_list = [CaptainSelection, PlayerPicking, FactionPicking, BasePicking, GettingReady, MatchPlaying]
    elif isTraining:
        _process_list = [CaptainSelection, PlayerPicking, FactionPicking, BasePicking, GettingReady, MatchPlaying]
        if training_rounds != 1:
            for _ in range(1, training_rounds):
                _process_list.append(GettingReady)
                _process_list.append(MatchPlaying)
    elif not is1v1 and not isTraining and len(_process_list) != 8:
        _process_list = [CaptainSelection, PlayerPicking, FactionPicking, BasePicking, GettingReady, MatchPlaying,
                GettingReady, MatchPlaying]


class MatchObjects:
    def __init__(self, match: Match, data: MatchData, channel: int):
        self.__status = MatchStatus.IS_FREE
        self.data = data
        self.proxy = match
        self.teams = [None, None]
        self.channel = channel
        self.current_process = None
        self.base_selector = None
        self.progress_index = 0
        self.result_msg = None
        self.check_offline = True
        self.check_validated = True
        self.players_with_account = list()
        self.command_factory = CommandFactory(self)
        self.plugin_manager = None
        self.clean_channel.start(display=False)
        self.is1v1 = match.is1v1

    def delayed_init(self):
        self.plugin_manager = PluginManager(self.proxy)

    def get_current_process(self):
        return self.current_process    

    @property
    def status(self):
        return self.__status

    @property
    def round_no(self):
        if self.next_status in (MatchStatus.IS_WAITING, MatchStatus.IS_STARTING):
            return len(self.data.round_stamps) + 1
        else:
            return len(self.data.round_stamps)
    
    @property
    def last_start_stamp(self):
        return self.data.round_stamps[-1]

    @status.setter
    def status(self, value):
        self.__status = value
        if self.__status is not MatchStatus.IS_RUNNING:
            self.command_factory.on_status_update(value)
        
    def ready_next_process(self, *args, is1v1=False, isTraining=False):
        self.status = MatchStatus.IS_RUNNING
        if self.progress_index == len(_process_list):
            self.current_process = None
            self.plugin_manager.on_match_over()
            self.clean_critical()
        else:
            self.current_process = _process_list[self.progress_index](self, *args, is1v1=is1v1, isTraining=isTraining)
        self.progress_index += 1

    def start_next_process(self):
        if self.current_process:
            self.current_process.initialize()
        else:
            self.match_over_loop.start()

    def on_spin_up(self, p_list):
        self.data.id = Match._last_match_id
        self.data.round_length = cfg.general["round_length"]
        change_process_lists()
        self.ready_next_process(p_list)
        self.clean_channel.cancel()
        self.plugin_manager.on_match_launching()
        self.start_next_process()

    def on_spin_up_1v1(self, p_list):
        self.data.id = Match._last_match_id
        self.data.round_length = 150
        change_process_lists(is1v1=True)
        self.ready_next_process(p_list, is1v1=True)
        self.clean_channel.cancel()
        self.plugin_manager.on_match_launching()
        self.start_next_process()

    def on_spin_up_training(self, p_list):
        self.data.id = Match._last_match_id
        self.data.round_length = 60
        change_process_lists(isTraining=True, training_rounds=cfg.general["training_rounds"])
        self.ready_next_process(p_list, isTraining=True)
        self.clean_channel.cancel()
        self.plugin_manager.on_match_launching()
        self.start_next_process()

    @loop(count=1)
    async def match_over_loop(self):
        await disp.MATCH_OVER.send(self.match.channel)
        if not self.is1v1:
            await self.data.push_db()
        await self.clean_async()
        await disp.MATCH_CLEARED.send(self.match.channel)

    @property
    def command(self):
        return self.command_factory

    def get_process_attr(self, name):
        if name in self.current_process.attributes:
            return self.current_process.attributes[name]
        else:
            raise AttributeError(f"Current process has no attribute '{name}'")

    def clean_critical(self):
        self.plugin_manager.on_clean()
        self.status = MatchStatus.IS_RUNNING
        self.command_factory.on_clean()
        if self.base_selector:
            self.base_selector.clean()
            self.base_selector = None
        for tm in self.teams:
            if tm is not None:
                tm.clean()
        self.teams = [None, None]
        self.current_process = None

    async def clean_all_auto(self):
        self.clean_critical()
        await self.clean_async()

    async def clean_async(self):
        await self.plugin_manager.async_clean()
        on_match_over(self.data.id)
        for a_player in self.players_with_account:
            await accounts.terminate_account(a_player)
        self.data.clean()
        self.players_with_account = list()
        self.result_msg = None
        self.check_offline = True
        self.check_validated = True
        self.clean_channel.change_interval(minutes=2)
        self.clean_channel.start(display=True)
        self.progress_index = 0
        self.status = MatchStatus.IS_FREE
        lobby.on_match_free()

    @loop(count=2, delay=1)
    async def clean_channel(self, display):
        if display:
            await disp.MATCH_CHANNEL_OVER.send(self.channel)
        await roles.modify_match_channel(self.match.channel, view=False)

    @property
    def status_str(self):
        return self.next_status.value

    @property
    def next_status(self):
        if not self.current_process:
            return MatchStatus.IS_FREE
        else:
            return self.current_process.status

    def __getattr__(self, name):
        try:
            return getattr(self.data, name)
        except AttributeError:
            raise AttributeError(f"'MatchObjects' object has no attribute '{name}'")
