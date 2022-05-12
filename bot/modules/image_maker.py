"""
This module handles the creation of score images
"""

# External imports
import discord
from PIL import Image, ImageDraw, ImageFont
from asyncio import get_event_loop
from datetime import datetime as dt
import os

# Internal imports
from display.strings import AllStrings as display
from display.classes import ContextWrapper
import modules.config as cfg
import modules.tools as tools

# Fonts we will use
# Change path if needed
big_font = ImageFont.truetype("/home/bwae-services/fonts/OpenSans2.ttf", 100)
font = ImageFont.truetype("/home/bwae-services/fonts/OpenSans2.ttf", 80)
small_font = ImageFont.truetype("/home/bwae-services/fonts/OpenSans2.ttf", 60)


# Colors we will use
white = (255, 255, 255)
yellow = (254, 227, 76)
grey1 = (219, 219, 219)
grey2 = (178, 178, 178)
yellow_light = (254, 244, 186)

# Constant spacings we will use
Y_SPACING = 120
Y_BIG_SPACE = 150
X_OFFSET = 100

offsets = [300, 300, 300, 400, 300]


# Utility functions:

def _draw_score_line(draw: ImageDraw.ImageDraw, x_start: int, y: int, values: list, d_font: ImageFont,
                     fill_color: tuple):
    """
    Draw several text elements on the same line.

    :param draw: ImageDraw object to draw on.
    :param x_start: x coordinate in pixel, to start drawing from.
    :param y: y coordinate in pixel for the elements to draw.
    :param values: list of strings: elements to draw.
    :param d_font: Font used for drawing the elements.
    :param fill_color: Tuple: RGB color of the elements.
    """
    off = 0
    for i in range(len(values)):
        draw.text((x_start + off, y), values[i], font=d_font, fill=fill_color)
        off += offsets[i]


def _cut_off_string(text: str, d_font: ImageFont, threshold: int) -> str:
    """
    Cut a text string depending on a maximum length:
    If the text length is more than the threshold, the text will be cut.

    Example: "MyVeryLongName" will become "MyVeryL...", while "ShorterName" will not be changed.

    Returns the result text.

    :param text: Text to process.
    :param d_font: Font for drawing the text.
    :param threshold: The text returned length will not be more than this threshold.
    :return: The cut text if it doesn't fit the threshold, the full text if it does.
    """

    # We use binary search to find the proper length
    def _binary_search(base: int, i: int):
        # Get current size
        size = d_font.getsize(text[:base + i] + "...")[0]
        # Get next size
        size1 = d_font.getsize(text[:base + i + 1] + "...")[0]
        # If target is between both sizes, return
        if size <= threshold <= size1:
            return base + i
        # If we reached the minimum resolution, return (one letter)
        if i == 1:
            return base + i + 1
        # Else if text is too big, try smaller
        if size >= threshold:
            return _binary_search(base, i // 2)
        # Else if text is too small, try bigger
        if size <= threshold:
            return _binary_search(base + i, i // 2)

    # If the text already fits the threshold, return it
    if d_font.getsize(text)[0] <= threshold:
        return text

    # Else find where to cut the text off
    res = _binary_search(0, len(text))
    # Return the cut text
    return text[:res] + "..."


def _team_display(img: Image, draw: ImageDraw, team: 'classes.TeamScore', y_offset: int, is1v1=False):
    """
    Draw one team score.

    :param img: Image to draw on.
    :param draw: Draw object.
    :param team: TeamScore object.
    :param y_offset: y coordinate to start drawing score from
    """
    # Draw Titles:
    _draw_score_line(draw, X_OFFSET + 2200, y_offset, ["Score", "Net", "Kills", "Deaths", "HSR"], font, yellow)

    # Draw team scores:
    scores = [str(team.score), str(team.net), str(team.kills), str(team.deaths), f"{int(team.hsr * 100)}%"]
    _draw_score_line(draw, X_OFFSET + 2200, Y_SPACING + y_offset, scores, big_font, white)

    # Draw team name:
    draw.text((X_OFFSET, Y_SPACING + y_offset),
              f'{team.name} ({cfg.factions[team.faction]})', font=big_font, fill=white)

    # Color tuple, to change if there is need for color alternation between each line
    color = (white, white)

    if cfg.general["show_player_scores"] or is1v1:
        # For each player
        for i in range(len(team.players)):
            # Get current player
            player = team.players[i]

            # Draw scores:
            scores = [str(player.score), str(player.net), str(player.kills), str(player.deaths), f"{int(player.hsr * 100)}%"]
            _draw_score_line(draw, X_OFFSET + 2200, Y_BIG_SPACE * 2 + Y_SPACING * i + y_offset, scores,
                            font, color[i % 2])

            # Get resized name and in-game name:
            name = _cut_off_string(player.name, font, 900)
            ig_name = _cut_off_string(player.ig_name, font, 900)

            # Draw in-game name and name
            draw.text((X_OFFSET + 250, Y_BIG_SPACE * 2 + Y_SPACING * i + y_offset), name, font=font, fill=color[i % 2])
            draw.text((X_OFFSET + 1100 + 130, Y_BIG_SPACE * 2 + Y_SPACING * i + y_offset), ig_name, font=font,
                    fill=color[i % 2])

            # Get two main classes (loadouts) the player used
            loadouts = player.get_main_loadouts()

            # Draw loadouts icons
            for j in range(len(loadouts)):
                # Get loadout icon
                loadout_img = Image.open(f"/home/bwae-services/media/{loadouts[j]}.png")
                loadout_img = loadout_img.resize((80, 80))
                if len(loadouts) == 1:
                    # If only one loadout used, we put the icon in the middle
                    off = 90 // 2
                else:
                    off = 90 * j
                # Draw loadout icon
                img.paste(loadout_img, (35 + X_OFFSET + off, Y_BIG_SPACE * 2 + Y_SPACING * i + y_offset + 25), loadout_img)


def _make_image(match: 'match.classes.MatchData', is1v1, isTraining):
    """
    Create the match image, save it as '../../BattleBot-Data/matches/match_{match.id}.png'

    :param match: MatchData object to take the match results from
    """

    # Return y-coordinate offset depending on the team
    def get_y_off(team_id):
        y_space = 0
        # Calculate spacing depending on the number of players of each team
        for k in range(team_id):
            y_space += Y_SPACING * match.teams[k].nb_players + 480
        return 325 + Y_SPACING * 4 + y_space

    # Create image
    y_max = get_y_off(len(match.teams))
    x_max = 4000
    img = Image.new('RGB', (x_max, y_max), color=(17, 0, 68))

    # Add POG logo
    logo = Image.open("/home/bwae-services/logos/bot2.png")
    logo = logo.resize((600, 600))
    img.paste(logo, (180, 100), logo)

    # Get draw object and x offset
    draw = ImageDraw.Draw(img)


    # Draw general information
    x_title = (x_max - big_font.getsize(f"BWAE Internals - Match {match.id}")[0]) // 2
    x = x_title + 100
    draw.text((x_title, 100), f"BWAE Internals - Match {match.id}", font=big_font, fill=white)
    draw.text((x, 200 + 100), f"Base: {match.base.name}", font=small_font, fill=white)

    # Draw round stamps times
    if not isTraining:
        for i in range(len(match.round_stamps)):
            rs = match.round_stamps[i]
            text = dt.fromtimestamp(rs).strftime("%Y-%m-%d %H:%M")
            draw.text((x, 200 + 100 * (2 + i)), f"Round {i + 1}: {text}", font=small_font, fill=white)
    else:
        if len(match.round_stamps) == cfg.general["training_rounds"]:
            # draw round 1
            rs = match.round_stamps[0]
            text = dt.fromtimestamp(rs).strftime("%Y-%m-%d %H:%M")
            draw.text((x, 200 + 100 * (2)), f"Round 1: {text}", font=small_font, fill=white)

            rs = match.round_stamps[-1]
            text = dt.fromtimestamp(rs).strftime("%Y-%m-%d %H:%M")
            draw.text((x, 200 + 100 * (2 + 1)), f"Round {cfg.general['training_rounds']}: {text}", font=small_font, fill=white)
        elif len(match.round_stamps) < 4:
            for i in range(len(match.round_stamps)):
                rs = match.round_stamps[i]
                text = dt.fromtimestamp(rs).strftime("%Y-%m-%d %H:%M")
                draw.text((x, 200 + 100 * (2 + i)), f"Round {i + 1}: {text}", font=small_font, fill=white)
        else:
            for i in range(3):
                rs = match.round_stamps[i]
                text = dt.fromtimestamp(rs).strftime("%Y-%m-%d %H:%M")
                draw.text((x, 200 + 100 * (2 + i)), f"Round {i + 1}: {text}", font=small_font, fill=white)

    # If match is still ongoing, draw Round 2 as "In progress..."
    if not isTraining:
        if len(match.round_stamps) < 2 and not is1v1:
            draw.text((x, 200 + 100 * 3), f"Round 2: ", font=small_font, fill=white)
            draw.text((x + small_font.getsize(f"Round 2: ")[0], 200 + 100 * 3), f"In progress...", font=small_font,
                    fill=yellow)


    # Draw round length
    if is1v1:
        start_stamp = match.round_stamps[0]
        start = dt.fromtimestamp(start_stamp)
        end_stamp = tools.timestamp_now()
        end = dt.fromtimestamp(end_stamp)
        round_length = (end - start).total_seconds()
        minutes = int((round_length % 3600) // 60)
        seconds = int(round_length % 60)
        draw.text((x_title, (200 + 100 * 4)-15), f"Round length: {minutes} minutes and {seconds} seconds", font=small_font, fill=white)
    elif not isTraining:
        draw.text((x, 200 + 100 * 4), f"Round length: {match.round_length} minutes", font=small_font, fill=white)

    # Draw enclosing square
    b_thickness = 25
    draw.line([b_thickness, 0, b_thickness, y_max], fill=(0, 0, 0), width=b_thickness * 2)
    draw.line([0, b_thickness, x_max, b_thickness], fill=(0, 0, 0), width=b_thickness * 2)
    draw.line([0, y_max - b_thickness, x_max, y_max - b_thickness], fill=(0, 0, 0), width=b_thickness * 2)
    draw.line([x_max - b_thickness, 0, x_max - b_thickness, y_max], fill=(0, 0, 0), width=b_thickness * 2)

    # Team lines
    for tm in match.teams:
        y_offset = get_y_off(tm.id)
        draw.line([b_thickness * 2, y_offset - 20, x_max - b_thickness * 2, y_offset - 20], fill=white, width=10)
        draw.line([100, y_offset + Y_BIG_SPACE * 2 - 20, x_max - 100, y_offset + Y_BIG_SPACE * 2 - 20],
                  fill=yellow, width=10)

    # Draw captures points information
    draw.text((x + 1100, 200 + 100), f"Captures:", font=small_font, fill=white)
    for tm in match.teams:
        draw.text((x + 1100, 200 + 100 * (tm.id + 2)), f"{tm.name}: {tm.cap} points", font=small_font,
                  white=white)
        # Draw teams and players score
        _team_display(img, draw, tm, get_y_off(tm.id), is1v1=is1v1)

    # Save the image
    try:
        os.makedirs('/home/bwae-services/BattleBot-Data/matches')
    except FileExistsError:
        pass
    img.save(f'/home/bwae-services/BattleBot-Data/matches/match_{match.id}.png')


async def publish_match_image(match: 'match.classes.Match', is1v1=False, isTraining=False):
    """
    Display the match score sheet in the result channel.

    :param match: Match object
    """
    # Make image
    loop = get_event_loop()
    await loop.run_in_executor(None, _make_image, match.data, is1v1, isTraining)

    # If already posted once
    if match.result_msg:
        try:
            await match.result_msg.delete()
        except discord.NotFound:
            pass

    # If end of match image
    if is1v1:
        player_pings = " ".join([" ".join([p.mention for p in tm.players]) for tm in (match.data.teams)])
        match.result_msg = await display.SC_RESULT_1v1.image_send(ContextWrapper.channel(cfg.channels["results"]),
                                                              f'/home/bwae-services/BattleBot-Data/matches/match_{match.id}.png', match.id, player_pings)
    elif isTraining and len(match.round_stamps) == cfg.general["training_rounds"]:
        match.result_msg = await display.SC_RESULT.image_send(ContextWrapper.channel(cfg.channels["results"]),
                                                              f'/home/bwae-services/BattleBot-Data/matches/match_{match.id}.png', match.id)
    elif len(match.round_stamps) == 2 and not isTraining:
        match.result_msg = await display.SC_RESULT.image_send(ContextWrapper.channel(cfg.channels["results"]),
                                                              f'/home/bwae-services/BattleBot-Data/matches/match_{match.id}.png', match.id)
    else:  # Else it is the half-match image
        match.result_msg = await display.SC_RESULT_HALF.image_send(ContextWrapper.channel(cfg.channels["results"]),
                                                                   f'/home/bwae-services/BattleBot-Data/matches/match_{match.id}.png',
                                                                   match.id)
