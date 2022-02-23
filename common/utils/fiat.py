#
# Currency exchange methods
#

import json
import os
import traceback

BLOCKCHAIN_PRICES_CACHE_FILE = '/root/.chia/machinaris/dbs/blockchain_prices_cache.json'
EXCHANGE_RATES_CACHE_FILE = '/root/.chia/machinaris/dbs/exchange_rates_cache.json'
LOCALE_SETTINGS = '/root/.chia/machinaris/config/locale_settings.json'

def to_fiat(blockchain, coins):
    if os.path.exists(BLOCKCHAIN_PRICES_CACHE_FILE):
        try:
            with open(BLOCKCHAIN_PRICES_CACHE_FILE) as f:
                data = json.load(f)
                if blockchain in data:
                    if isinstance(coins, str):
                        coins = float(coins.replace(',',''))
                    usd_per_coin = float(data[blockchain])
                    fiat_per_usd = get_fiat_exchange_to_usd()
                    fiat_cur_sym = get_local_currency_symbol().lower()
                    #print("Converting {0} coins of {1} with {2}".format(coins, usd_per_coin, fiat_per_usd))
                    return "{:,.2f} {fiat_cur_sym}".format(usd_per_coin * fiat_per_usd * coins, fiat_cur_sym=fiat_cur_sym)
                return ''
        except Exception as ex:
            print("Unable to convert to fiat because {0}".format(str(ex)))
            traceback.print_exc()
    return ''

def load_exchange_rates_cache():
    data = {}
    if os.path.exists(EXCHANGE_RATES_CACHE_FILE):
        try:
            with open(EXCHANGE_RATES_CACHE_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read exchange rate cache from {0} because {1}".format(EXCHANGE_RATES_CACHE_FILE, str(ex))
            print(msg)
    return data

def get_fiat_exchange_to_usd():
    try:
        local_currency = get_local_currency()
        if local_currency and local_currency != 'usd':
            exchange_rates = load_exchange_rates_cache()
            fiat_rate = exchange_rates[local_currency]
            usd_rate = exchange_rates['usd']
            return float(fiat_rate['value']) / float(usd_rate['value'])
    except Exception as ex:
        print('Failed to convert FIAT to USD due to {0}'.format(str(ex)))
    return 1.0 # Default fiat is $USD

def get_local_currency():
    try:
        with open(LOCALE_SETTINGS) as f:
            data = json.load(f)
            return data['local_currency']
    except Exception as ex:
        msg = "Unable to read exchange rate cache from {0} because {1}".format(LOCALE_SETTINGS, str(ex))
        print(msg)
    return None

def save_local_currency(currency):
    settings = {}
    try:
        with open(LOCALE_SETTINGS) as f:
            settings = json.load(f)
    except:
        pass
    try:
        settings['local_currency'] = currency
        with open(LOCALE_SETTINGS, 'w') as f:
            json.dump(settings, f)
    except Exception as ex:
        msg = "Unable to write local currency setting to {0} because {1}".format(LOCALE_SETTINGS, str(ex))
        print(msg)

def get_local_currency_symbol():
    symbol = "us$" # Default is USD
    try:
        local_currency = get_local_currency()
        if local_currency and local_currency != 'usd':
            exchange_rates = load_exchange_rates_cache()
            return exchange_rates[local_currency]['unit']
    except Exception as ex:
        print('Failed find local currency symbol because {0}'.format(str(ex)))
    return symbol