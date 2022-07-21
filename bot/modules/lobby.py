import modules.config as cfg
from display import AllStrings as disp, ContextWrapper, views, InteractionContext

from lib.tasks import Loop, loop
from logging import getLogger

import modules.tools as tools
import modules.interactions as interactions

log = getLogger("pog_bot")

_lobby_list = list()
_lobby_list_1v1 = list()
_training_list = list()
_lobby_stuck = False
_MatchClass = None
_client = None
_warned_players = dict()
_original_lbsize = None
_original_rndtime = None
_training_unlocked = False
_original_trsize = None


def reset_timeout(player):
    _remove_from_warned(player)
    player.reset_lobby_expiration()


def init(m_cls, client):
    global _MatchClass
    global _client
    global _original_lbsize
    global _original_rndtime
    global _original_trsize
    global _training_unlocked
    
    _MatchClass = m_cls
    _client = client
    _original_lbsize = cfg.general["lobby_size"]
    _original_rndtime = cfg.general["round_length"]
    _original_trsize = cfg.general["training_lobby_size"]
    _training_unlocked = False

    _lobby_loop.start()
    _1v1_lobby_loop.start()
    _lbsize_and_rndtime_reset_loop.start()
    _show_player_scores_reset_loop.start()


def _remove_from_warned(p):
    if p in _warned_players:
        _warned_players[p].clean()
        del _warned_players[p]


def _clear_warned():
    for k in list(_warned_players.values()):
        k.clean()
    _warned_players.clear()


def _add_ih_callback(ih, player):
    @ih.callback('reset')
    async def on_user_react(p, interaction_id, interaction, interaction_values):
        user = interaction.user
        if user.id == player.id:
            ctx = ContextWrapper.channel(cfg.channels["lobby"])
            ctx.author = user
            reset_timeout(player)
            await disp.LB_REFRESHED.send(ctx, names_in_lobby=get_all_names_in_lobby())
        else:
            i_ctx = InteractionContext(interaction)
            await disp.LB_REFRESH_NO.send(i_ctx)
            raise interactions.InteractionNotAllowed


def is_lobby_stuck():
    return _lobby_stuck


def _set_lobby_stuck(bl):
    global _lobby_stuck
    _lobby_stuck = bl


# 7800, 7200
@loop(minutes=1)
async def _lobby_loop():
    for p in _lobby_list:
        if p.is_lobby_expired:
            remove_from_lobby(p)
            await disp.LB_TOO_LONG.send(ContextWrapper.channel(cfg.channels["lobby"]), p.mention,
                                        names_in_lobby=get_all_names_in_lobby())
        elif p.should_be_warned and p not in _warned_players:
            ih = interactions.InteractionHandler(p, views.reset_button)
            _warned_players[p] = ih
            _add_ih_callback(ih, p)
            ctx = ih.get_new_context(ContextWrapper.channel(cfg.channels["lobby"]))
            await disp.LB_WARNING.send(ctx, p.mention)

@loop(minutes=5)
async def _1v1_lobby_loop():
    for p in _lobby_list_1v1:
        now = tools.timestamp_now()
        # Testing (Would like to check the time)
        if p.lobby_stamp < (now - 1800):
            remove_from_lobby(p)
            await disp.LB_TOO_LONG_1v1.send(ContextWrapper.channel(cfg.channels["lobby"]), p.mention, names_in_lobby=get_all_1v1_names_in_lobby())


@loop(minutes=60)
async def _lbsize_and_rndtime_reset_loop():
    if cfg.general["lobby_size"] != _original_lbsize:
        cfg.general["lobby_size"] = _original_lbsize
    if cfg.general["round_length"] != _original_rndtime:
        cfg.general["round_length"] = _original_rndtime
    if cfg.general["training_lobby_size"] != _original_trsize:
        cfg.general["training_lobby_size"] = _original_trsize
    try:
        if _training_unlocked:
            _training_unlocked = False
    except UnboundLocalError:
        pass

@loop(hours=2)
async def _show_player_scores_reset_loop():
    if cfg.general["show_player_scores"]!=True:
        cfg.general["show_player_scores"] = True

def _auto_ping_threshold():
    thresh = cfg.general["lobby_size"] - cfg.general["lobby_size"] // 3
    return thresh


def _auto_ping_cancel():
    _auto_ping.cancel()
    _auto_ping.already = False


def get_sub(player):
    # Check if someone in lobby, if not return player (might be None)
    if len(_lobby_list) == 0:
        return player
    # If player is None, take first player in queue
    if not player:
        player = _lobby_list[0]
    # If player chosen is in lobby, remove
    if player.is_lobbied:
        _lobby_list.remove(player)
        _on_lobby_remove()
        _remove_from_warned(player)
    return player


def add_to_lobby(player, training=False, expiration=0):
    if training:
        _training_list.append(player)
        all_names = get_all_names_in_training_lobby()
        player.on_lobby_add(expiration)
    else:
        _lobby_list.append(player)
        player.on_lobby_add(expiration)
        all_names = get_all_names_in_lobby()
    if training:
        if len(_training_list) == cfg.general["training_lobby_size"]:
            _start_match_from_full_lobby(training=True)
    else:
        if len(_lobby_list) == cfg.general["lobby_size"]:
            _start_match_from_full_lobby()
        elif len(_lobby_list) >= _auto_ping_threshold():
            if not _auto_ping.is_running() and not _auto_ping.already:
                _auto_ping.start()
                _auto_ping.already = True
    return all_names

def add_to_1v1_lobby(player):
    _lobby_list_1v1.append(player)
    all_1v1_names = get_all_1v1_names_in_lobby()
    player.on_lobby_add()
    if len(_lobby_list_1v1) == 2:
        _start_match_from_1v1_lobby()
    return all_1v1_names

async def force_match_start(ctx):
    if len(_lobby_list) <= 2:
        await disp.LB_CANNOT_FORCE_START_MATCH.send(ctx)
        return False
    cfg.general["lobby_size"] = len(_lobby_list)
    _start_match_from_full_lobby()
    return True

async def force_training_start(ctx):
    if len(_training_list) <= 2:
        await disp.LB_CANNOT_FORCE_START_MATCH.send(ctx)
        return False
    cfg.general["training_lobby_size"] = len(_training_list)
    _start_match_from_full_lobby(training=True)
    return True

@loop(minutes=3, delay=1, count=2)
async def _auto_ping():
    if _MatchClass.find_empty() is None:
        return
    await disp.LB_NOTIFY.send(ContextWrapper.channel(cfg.channels["lobby"]), f'<@&{cfg.roles["notify"]}>',
                              get_lobby_len(), cfg.general["lobby_size"])


_auto_ping.already = False


def get_lobby_len():
    return len(_lobby_list)


def get_all_names_in_lobby():
    names = [f"{p.mention} ({p.name}) (auto leave in {p.lobby_remaining})" for p in _lobby_list]
    return names

def get_all_1v1_names_in_lobby():
    names = [f"{p.mention} ({p.name})" for p in _lobby_list_1v1]
    return names

def get_all_names_in_training_lobby():
    names = [f"{p.mention} ({p.name})" for p in _training_list]
    return names

def get_all_ids_in_lobby():
    ids = [p.id for p in _lobby_list]
    return ids


def remove_from_lobby(player):
    _remove_from_warned(player)
    is1v1 = False
    isTraining = False
    try:
        _lobby_list.remove(player)
    except ValueError:
        try:
            _lobby_list_1v1.remove(player)
            is1v1 = True
        except ValueError:
            _training_list.remove(player)
            isTraining = True
    _on_lobby_remove()
    player.on_lobby_leave()
    return is1v1, isTraining


def on_match_free():
    _auto_ping.already = False
    if len(_lobby_list) == cfg.general["lobby_size"]:
        _start_match_from_full_lobby()


def _on_lobby_remove():
    _set_lobby_stuck(False)
    if len(_lobby_list) < _auto_ping_threshold():
        _auto_ping_cancel()


def _start_match_from_full_lobby(training=False):
    match = _MatchClass.find_empty()
    _auto_ping_cancel()
    if match is None:
        _set_lobby_stuck(True)
        Loop(coro=_send_stuck_msg, count=1).start()
    else:
        _set_lobby_stuck(False)
        if training:
            match.spin_up(_training_list.copy(), training=True)
            _training_list.clear()
        else:
            match.spin_up(_lobby_list.copy())
        _lobby_list.clear()
        _clear_warned()

def _start_match_from_1v1_lobby():
    match = _MatchClass.find_empty(is_1v1=True)
    if match is None:
        _set_lobby_stuck(True)
        Loop(coro=_send_stuck_msg, count=1).start()
    else:
        _set_lobby_stuck(False)
        match.spin_up(_lobby_list_1v1.copy(), is1v1=True)
        _lobby_list_1v1.clear()
        _clear_warned()

async def _send_stuck_msg():
    await disp.LB_STUCK.send(ContextWrapper.channel(cfg.channels["lobby"]))


def clear_lobby():
    if len(_lobby_list) == 0:
        return False
    for p in _lobby_list:
        p.on_lobby_leave()
    _lobby_list.clear()
    _clear_warned()
    _on_lobby_remove()
    return True

def clear_1v1_lobby():
    if len(_lobby_list_1v1) == 0:
        return False
    for p in _lobby_list_1v1:
        p.on_lobby_leave()
    _lobby_list_1v1.clear()
    _clear_warned()
    _on_lobby_remove()
    return True

def clear_training_lobby():
    if len(_training_list) == 0:
        return False
    for p in _training_list:
        p.on_lobby_leave()
    _training_list.clear()
    _clear_warned()
    _on_lobby_remove()
    return True

def get_training_list_size():
    return len(_training_list)