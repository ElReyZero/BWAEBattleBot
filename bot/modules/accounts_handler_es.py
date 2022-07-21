"""
| This module handle the POG Jaeger accounts.
| Initialize or reload the module with :meth:`init`.
| Then call :meth:`give_account` and :meth:`send_account` to hand an account to an in-match player.
| Use :meth:`terminate_account` to remove the account from the player.
"""

# External imports
from logging import getLogger
from gspread import service_account
from numpy import array
import discord.errors
from datetime import datetime, timedelta
import time
from classes.accounts import Account
import copy
import asyncio

# Internal imports
import classes
from display import AllStrings as disp, ContextWrapper
import modules.database as db
import modules.config as cfg
from modules.tools import UnexpectedError
import os

log = getLogger("pog_bot")

# Will hold the Jaeger accounts
_busy_accounts = dict()
_available_accounts = dict()

# Offsets in the google sheet
X_OFFSET = 1
Y_OFFSET = 2


# Will be called at bot init or on account reload
def init(secret_file: str):
    """
    Initialize the accounts from the google sheet.
    If called later, reload the account usernames and passwords.

    :param secret_file: Name of the gspread authentication json file.
    """
    # Open the google sheet:
    try:
        gc = service_account(filename=secret_file)
    except FileNotFoundError:
        gc = service_account(filename=os.getcwd()+r"\bot\google_api_secret_test.json")
    sh = gc.open_by_key(cfg.database["accounts"])
    raw_sheet = sh.worksheet("1")
    sheet_tab = array(raw_sheet.get_all_values())

    # Get total number of accounts
    num_accounts = sheet_tab.shape[0] - Y_OFFSET

    # Add accounts one by one
    for i in range(num_accounts):
        # Get account data
        a_id_str = sheet_tab[i + Y_OFFSET][X_OFFSET]
        a_username = sheet_tab[i + Y_OFFSET][X_OFFSET + 1]
        a_password = sheet_tab[i + Y_OFFSET][X_OFFSET + 2]
        a_id = int(a_id_str)

        # Update account
        if a_id in _available_accounts:
            _available_accounts[a_id].update(a_username, a_password)
        elif a_id in _busy_accounts:
            _busy_accounts[a_id].update(a_username, a_password)
        else:
            # If account doesn't exist already, initialize it
            unique_usages = db.get_field("accounts_usage", a_id, "unique_usages")
            if unique_usages is None:
                raise UnexpectedError(f"Can't find usage for account {a_id}")
            _available_accounts[a_id] = classes.Account(a_id_str, a_username, a_password, unique_usages)

def get_available_accounts(acct_index, account_owner):
    """
    The check_in time indicates when an account is available again. check_in is created as a future date so accounts
    being used are excluded from the query.
    :param acct_index: string: an elasticsearch index
    :param account_owner: string: the unique identifier associated with the account owner
    :return: An elastic list
    """
    res = cfg.es.search(
        index=acct_index,
        body={
            "size": 10000,
            "sort": {"check_out": "desc"},
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "account_owner.keyword": account_owner
                            }
                        },
                        {
                            "range": {
                                "check_in": {
                                    "gte": datetime(1990, 1, 1, 1, 1, 1),
                                    "lt": datetime.now().utcnow()
                                }
                            }
                        }
                    ]
                }
            }
        }
    )

    return res

def get_account(acct_index, user_uuid):
    """
    This function is intended to find all accounts checked out by a single user.
    :param acct_index: string: an elasticsearch index
    :param user_uuid: string: any qualified username
    :return:
    """
    res = cfg.es.search(index=acct_index, body={
        "size": 10000,
        "query": {
            "match": {
                "checkout_user": {
                    "query": user_uuid
                }
            }
        }
    })
    return res

def turn_in_accounts(acct_index, account_owner):
    """
    This function looks for and turns in accounts that have an expired check_in time.
    :param acct_index: string: an elasticsearch index
    :param account_owner: string: the unique identifier associated with the account owner
    :return:
    """
    discord_names = list()
    accounts = get_available_accounts(acct_index, account_owner).get('hits').get('hits')
    for account in accounts:
        checkout = account.get('_source')
        if checkout.get('checkout_user') and datetime.fromisoformat(
                checkout.get('check_in').split('.')[0]) < datetime.now().utcnow():
            checkout['checkout_user'] = ''
            checkout['discord_user_id'] = 0
            checkout['discord_user_name'] = ''
            cfg.es.index(index='accounts', doc_type='account', id=account.get('_id'), body=checkout)
            print('Account Returned {0}'.format(checkout))
    return discord_names

def checkout_account(acct_index, username, user_id, discriminator, checkout_timeout, account_owner):
    """
    This function assigns and properly fills out the documents needed to assign an account to a user
    :param acct_index: string: an elasticsearch index
    :param username: string: any unique value for identifying a singular user
    :param user_id: string: a second unique value identifying the user.
    (for discord this would be the value tied to the users account vs the visible name they use)
    :param checkout_timeout: int: defines the number of hours the account will be assigned to a user
    :param account_owner: string: the unique identifier associated with the account owner
    :return: json document or a string: The account information as a json document, or an error indicator.
    """
    user_uuid = f"{username}#{discriminator}_{user_id}"

    # Handle Account Return
    turn_in_accounts(acct_index, account_owner)

    # Handle Checkout time limits
    if checkout_timeout >= cfg.max_checkout:
        checkout_timeout = cfg.max_checkout

    # Handle Existing account
    existing_checkout = get_account(acct_index, user_uuid)
    checkout = existing_checkout.get('hits').get('hits')
    if len(checkout) == 1:
        print([checkout[0].get('_source').get('checkout_user'), user_uuid])
        if checkout[0].get('_source').get('checkout_user') == user_uuid:
            return checkout[0]
    if len(checkout) > 1:
        print('Yo, WTF more than one checkout!: {0}'.format(checkout))

    # Lookup Available Accounts
    accounts = get_available_accounts(acct_index, account_owner)
    acts = accounts.get('hits').get('hits')

    # Checkout Account
    if len(acts) > 0:
        checkout = acts[0]
        checkout['_source']['check_out'] = datetime.now().utcnow().replace(microsecond=0)
        checkout['_source']['check_in'] = datetime.now().utcnow() + timedelta(hours=checkout_timeout)
        checkout['_source']['checkout_user'] = user_uuid
        checkout['_source']['discord_user_id'] = user_id
        checkout['_source']['discord_user_name'] = f"{username}#{discriminator}"
        cfg.es.index(index='accounts',
                     doc_type='account',
                     id=checkout.get('_id'),
                     body=checkout.get('_source'))

        # this is part of the magic timings that go into ensuring the
        # async nature of the discord bot doesn't cause incorrect assignment
        time.sleep(2)
        checkout = cfg.es.get(index='accounts', doc_type='account', id=checkout.get('_id'))
        return checkout
    else:
        return None

async def give_account(a_player: classes.ActivePlayer) -> bool:
    """
    Give an account to a_player. We want each player to use as little accounts as possible.
    So we try to give an account the player already used.

    :param a_player: Player to give account to.
    :return: True is account given, False if not enough accounts available.
    """
    unique_usages = await db.async_db_call(db.get_field, "accounts_usage", a_player.id, "unique_usages")     
    if not unique_usages:         
        unique_usages = list()
    
    # Set player usages in the player object
    a_player.unique_usages = unique_usages
    
    user_uuid = "{0}#{1}_{2}".format(a_player.name, a_player.discriminator, a_player.id)
    n = 0
    checkout_owner = ""

    while user_uuid != checkout_owner:
        checked_acc = checkout_account(cfg.acct_index, a_player.name, a_player.id, a_player.discriminator, 8, cfg.acct_owner)
        if checked_acc:
            checkout_owner = checked_acc.get('_source').get('checkout_user')
            n += 1
            if n > 5:
                raise Exception("Failed receive a document with a matching username, I'm stuck please help step-admin!")

    acc_id = checked_acc["_id"]
    acc_source = checked_acc["_source"]
    
    acc_obj = Account(acc_source["base_account_number"], acc_id, acc_source["password"], [[]])
    _set_account(acc_obj, a_player)
    return True


def _set_account(acc: classes.Account, a_player: classes.ActivePlayer):
    """
    Set player's account.

    :param acc: Account to give.
    :param a_player: Player who will receive the account.
    """
    log.info(f"Give account [{acc.id}] to player: id:[{a_player.id}], name:[{a_player.name}]")

    # Put account in the busy dictionary
    del _available_accounts[acc.id]
    _busy_accounts[acc.id] = acc

    # Set account
    acc.a_player = a_player
    acc.add_usage(a_player.id, a_player.match.id)
    a_player.account = acc

async def clearMatch(channel, ctx):
    from match.classes.match import Match
    await asyncio.sleep(10)
    match = Match.get(channel.id)
    db.set_field("restart_data", 0, {"last_match_id": Match._last_match_id-1})
    await match.command.clear(ctx)
    return


async def send_account(channel: discord.TextChannel, a_player: classes.ActivePlayer, is1v1):
    """
    Actually send its account to the player.

    :param channel: Current match channel.
    :param a_player: Player to send the account to.
    """
    msg = None
    # Try 3 times to send a DM:
    ctx = a_player.account.get_new_context(await ContextWrapper.user(a_player.id))
    for _ in range(3):
        try:
            msg = await disp.ACC_UPDATE.send(ctx, account=a_player.account)
            break
        except discord.errors.Forbidden:
            pass
    if not msg:
        # Else validate the account and send it to staff channel instead
        await disp.ACC_CLOSED.send(channel, a_player.mention)
        await a_player.account.validate()
        if is1v1:
            await disp.CLEARING_MATCH_NO_ACC.send(ContextWrapper.channel(channel.id), a_player.mention)
            asyncio.get_event_loop().create_task(clearMatch(channel, ContextWrapper.channel(channel.id)))
        else:
            msg = await disp.ACC_STAFF.send(ContextWrapper.channel(cfg.channels["staff"]),
                                            f'<@&{cfg.roles["admin"]}>', a_player.mention, account=a_player.account)
    # Set the account message, log the account:
    a_player.account.message = [msg]
    await disp.ACC_LOG.send(ContextWrapper.channel(cfg.channels["spam"]), a_player.name, a_player.id, a_player.account.id)


async def terminate_account(a_player: classes.ActivePlayer):
    """
    Terminate the account: ask the user to log off and remove the reaction.

    :param a_player: Player whose account should be terminated.
    """
    # Get account and terminate it
    acc = a_player.account
    acc.terminate()

    # Remove the reaction handler and update the account message
    try:
        await disp.ACC_UPDATE.edit(acc.message[0], account=acc)
    except AttributeError:
        pass
    if len(acc.message) != 1:
        for i in range(1,len(acc.message)):
            await acc.message[i].delete()
    # If account was validated, ask the player to log off:
    try:
        if acc.is_validated and acc.message[0].channel.id != cfg.channels["staff"]:
            await disp.ACC_OVER.send(await ContextWrapper.user(acc.a_player.id))
    except AttributeError:
        pass

    # If account was validated, update the db with usage
    if acc.is_validated:
        # Prepare data
        p_usage = {
            "id": acc.id,
            "time_start": acc.last_usage["time_start"],
            "time_stop": acc.last_usage["time_stop"],
            "match_id": a_player.match.id
        }
        # Update the account element
        await db.async_db_call(db.push_element, "accounts_usage", acc.id, {"usages": acc.last_usage})
        try:
            # Update the player element
            await db.async_db_call(db.push_element, "accounts_usage", a_player.id, {"usages": p_usage})
        except db.DatabaseError:
            # If the player element doesn't exist, create it
            data = dict()
            data["_id"] = a_player.id
            data["unique_usages"] = a_player.unique_usages
            data["usages"] = [p_usage]
            await db.async_db_call(db.set_element, "accounts_usage", a_player.id, data)

    # Reset the account state
    acc.clean()
    #Uncomment this if using elasticsearch checkin_account(cfg.acct_index, a_player.name, a_player.id, a_player.discriminator, cfg.acct_owner)
    del _busy_accounts[acc.id]
    _available_accounts[acc.id] = acc

def checkin_account(acct_index, username, user_id, discriminator, account_owner):
    """
    This function manually checks in a single account.
    :param acct_index: string: an elasticsearch index
    :param username: string: any unique value for identifying a singular user
    :param user_id: string: a second unique value identifying the user.
    (for discord this would be the value tied to the users account vs the visible name they use)
    :param account_owner: string: the unique identifier associated with the account owner
    :return: string: a generic text indicating a human readable account status
    """
    user_uuid = f"{username}#{discriminator}_{user_id}"
    turn_in_accounts(acct_index, account_owner)
    existing_checkout = get_account(acct_index, user_uuid)
    checkout = existing_checkout.get('hits').get('hits')

    # Check in Account
    if len(checkout) == 0:
        return "No Account Assigned"

    for co in checkout:
        # Update history document
        co['_source']['check_in'] = datetime.now().utcnow()
        historical_account = copy.deepcopy(co)
        upload_history(historical_account)

        # Check in account document
        co['_source']['checkout_user'] = ''
        co['_source']['discord_user_id'] = 0
        co['_source']['discord_user_name'] = ''
        cfg.es.index(index='accounts', doc_type='account', id=co.get('_id'), body=co.get('_source'))

    if len(checkout) == 1:
        return "Returned {0} Account".format(len(checkout))
    else:
        return "Returned {0} Accounts".format(len(checkout))

def upload_history(account, history_index=cfg.history_index, password_censor=True):
    """
    This function simply uploads the account into the history index and censors the password
    :param account: dict: an account document
    :param history_index: string: an elastic index used to store the historical state of an account
    :param password_censor: boolean: if true this will scrub the password field from the historical document
    :return: string: a human readable message indicating the document has been submitted
    """
    if '_source' in account and password_censor:
        if 'password' in account.get('_source'):
            account['_source']['password'] = 'scrubbed'
    cfg.es.index(index=history_index,
                 doc_type='account',
                 id=account.get('_id') + "_" + str(account['_source']['check_out']),
                 body=account.get('_source'))
    return "History Submitted"


def get_not_validated_accounts(team: classes.Team) -> list:
    """
    Find all the accounts that were not validated within the team.

    :param team: Team to check
    :return: List containing the players who didn't accept their accounts.
    """
    not_ready = list()
    for p in team.players:
        if p.has_own_account:
            continue
        if p.is_benched:
            continue
        if p.account is None:
            log.error(f"Debug: {p.name} has no account")  # Should not happen
        if not p.account.is_validated:
            not_ready.append(p)
    return not_ready

