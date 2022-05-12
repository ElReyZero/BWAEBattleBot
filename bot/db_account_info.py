import modules.config as cfg
import datetime
import time

# Elasticsearch account configuration
base = {'check_out': datetime.datetime(2000, 1, 1, 1, 1, 1),
        'check_in': datetime.datetime(2000, 1, 1, 1, 1, 1),
        'checkout_user': '',
        'discord_user_name': '',
        'discord_user_id': 0,
        'account_owner': "discord bot account id",
        'account_alias': 'BWAE',
        'message_id': 0}

# Dictionary containing all of the practice accounts information
userdata = {
    'AccountUsername': {'password': 'password',
                        'character_names': ['BWAExPractice1NC', 'BWAExPractice1VS', 'BWAExPractice1TR',
                                            'BWAExPractice1NS'],
                        'basename': "Practice",
                        'base_account_number': '1'}
}

# Load the information in the elasticsearch db
for user in userdata:
    payload = userdata.get(user)
    payload.update(base)
    res = cfg.es.index(index='accounts', doc_type='account', id=user, body=payload)