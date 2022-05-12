import discord
from discord import ui, SelectOption, ButtonStyle
import operator
import modules.config as cfg


def _view(func):
    def view_func(ctx):
        ui_elements = func(ctx)
        if not isinstance(ui_elements, list):
            ui_elements = [ui_elements]
        ui_view = ui.View(timeout=None)
        for ui_element in ui_elements:
            ui_element.callback = ctx.interaction_payload.callback
            ui_view.add_item(ui_element)
        return ui_view
    return view_func

@_view
def joinCurrentMatch_buttons(ctx):
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

    button1 = ui.Button(label=faction1, style=discord.ButtonStyle.grey, emoji=cfg.emojis[faction1], custom_id="faction1")
    button2 = ui.Button(label=faction2, style=discord.ButtonStyle.grey, emoji=cfg.emojis[faction2], custom_id="faction2")
    button3 = ui.Button(label='Cancel', style=discord.ButtonStyle.grey, emoji='❌', custom_id="cancel")
    return [button1, button2, button3]
    

@_view
def bases_selection(ctx):
    """ Returns a list of bases currently selected
    """

    options = list()

    bases_list = sorted(ctx.interaction_payload.owner.bases_list, key=operator.itemgetter('name'))

    for base in bases_list:
        description_args = list()
        emoji = '🟩'
        if base['was_played_recently']:
            emoji = '🟦'
            description_args.append("Recently played!")
        if base['is_booked']:
            emoji = '🟥'
            description_args.append("Currently booked!")

        if description_args:
            description = " ".join(description_args[::-1])
        else:
            description = None

        options.append(SelectOption(label=base['name'], description=description, emoji=emoji, value=base['id']))

    return ui.Select(placeholder='Choose a base...', options=options, custom_id='base_selector')

@_view
def training_config(ctx):
    """Returns a list containing all available configs
    """
    options = list()
    for i in range(6):      
        options.append(SelectOption(label=str(i+1), value=i+1,))
    return ui.Select(placeholder='Choose the number of rounds...', options=options, custom_id='training_config')
        

@_view
def validation_buttons(ctx):
    decline = ui.Button(label="Decline", style=ButtonStyle.red, custom_id='decline')
    accept = ui.Button(label="Accept", style=ButtonStyle.green, custom_id='accept')

    return [decline, accept]


@_view
def players_buttons(ctx):
    players = ctx.interaction_payload.owner.get_left_players()
    if players:
        return [ui.Button(label=p.name, style=ButtonStyle.gray, custom_id=str(p.id)) for p in players]


@_view
def join1v1queue(ctx):
    return ui.Button(label="Join 1v1 Queue", style=ButtonStyle.green, custom_id="join1v1queue")

@_view
def volunteer_button(ctx):
    return ui.Button(label="Volunteer", style=ButtonStyle.gray, custom_id='volunteer', emoji="🖐️")


@_view
def faction_buttons(ctx):
    buttons = list()
    picked_faction = ctx.interaction_payload.owner.get_picked_faction()
    for faction in ['VS', 'TR', 'NC']:
        if cfg.i_factions[faction] != picked_faction:
            kwargs = {
                'label': faction,
                'style': ButtonStyle.grey,
                'custom_id': faction,
            }
            if cfg.emojis[faction]:
                kwargs['emoji'] = cfg.emojis[faction]
            buttons.append(ui.Button(**kwargs))
    return buttons


@_view
def ready_button(ctx):
    return ui.Button(label="Ready", style=ButtonStyle.green, custom_id='ready')


@_view
def refresh_button(ctx):
    return ui.Button(label="Refresh", style=ButtonStyle.blurple, custom_id='refresh')

@_view
def buttons_1v1(ctx):
    buttons = list()
    buttons.append(ui.Button(label="Refresh", style=ButtonStyle.blurple, custom_id='refresh'))
    buttons.append(ui.Button(label="End 1v1", style=ButtonStyle.red, custom_id='endRound'))
    return buttons

@_view
def training_buttons(ctx):
    buttons = list()
    buttons.append(ui.Button(label="Refresh", style=ButtonStyle.blurple, custom_id='refresh'))
    buttons.append(ui.Button(label="End Round", style=ButtonStyle.red, custom_id='endRound'))
    return buttons

@_view
def accept_button(ctx):
    return ui.Button(label="Accept", style=ButtonStyle.green, custom_id='accept')

@_view
def accept_rules_buttons(ctx):
    buttons = list()
    buttons.append(ui.Button(label="Accept", style=ButtonStyle.green, custom_id='accept', disabled=False))
    buttons.append(ui.Button(label="Help", style=ButtonStyle.blurple, custom_id='help', disabled=False))
    return buttons

@_view
def reset_button(ctx):
    return ui.Button(label="Reset timeout", style=ButtonStyle.blurple, custom_id='reset')
