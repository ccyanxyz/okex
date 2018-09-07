import sys
import numpy as np
import time
import arrow
from talib import SMA
import json
import logging
from okexapi.FutureAPI import Future
from base import *

class 3kline(Base):

    def __init__(self,
            api_key,
            secret_key,
            url,
            kline_size,
            kline_num)
    # TODO: rewrite


def get_amount():
    coin_available = future.future_userinfo_4fix()['info'][coin[:3]]['contracts'][0]['available']
    return int(leverage * amount_ratio * coin_available)

def three_up(opens, closes):
    if opens[-4] <= closes[-4] and opens[-3] <= closes[-3] and opens[-2] <= closes[-2]:
	return True
    else:
	return False

def three_down(opens, closes):
    if opens[-4] >= closes[-4] and opens[-3] >= closes[-3] and opens[-2] >= closes[-2]:
	return True
    else:
	return False

while True:
    kline = future.future_kline(coin, contract_type, kline_size, kline_num)
    last_closes = [kline[i][4] for i in range(kline_num)]
    last_opens = [kline[i][1] for i in range(kline_num)]

    long_amount, long_profit, short_amount, short_profit = future.get_position(coin, contract_type)
    logger.info('position: long_amount = %s, long_profit = %s, short_amount = %s, short_profit = %s' % (long_amount, long_profit, short_amount, short_profit))

    coin_available = future.future_userinfo_4fix()['info'][coin[:3]]['contracts'][0]['available']
    logger.info('coin_available = ' + str(coin_available))

    last = kline[-1][4]

    if three_up(last_opens, last_closes) and long_amount < 1:
        logger.info('Three up.')
        if short_amount > 0:
            logger.info('close short, amount: %d' % short_amount)
            future.close_short(coin, contract_type, last, short_amount, leverage, bbo)
        amount = get_amount()
        future.open_long(coin, contract_type, last, amount, leverage, bbo)
        logger.info('open long, amount: %d' % amount)
    elif three_down(last_opens, last_closes) and short_amount < 1:
        logger.info('Three down.')
        if long_amount > 0:
            logger.info('close long, amount: %d' % long_amount)
            future.close_long(coin, contract_type, last, long_amount, leverage, bbo)
        amount = get_amount()
        future.open_short(coin, contract_type, last, amount, leverage, bbo)
        logger.info('open short, amount: %d' % amount)
    else:
	logger.info('no trading signal.')

    time.sleep(15)



if __name__ == '__main__':
    config_path = sys.argv[1]

    f = open('config.json', encoding = 'utf-8')
    config = json.load(f)

    #初始化apikey，secretkey,url
    apikey = config['api_key']
    secretkey = config['secret_key']
    okcoinRESTURL = config['url']


    #期货API
    future = Future(okcoinRESTURL, apikey, secretkey, logger)

    coin = config['coin']
    contract_type = config['contract_type']
    kline_size = config['kline_size']
    kline_num = config['kline_num']
    amount_ratio = config['open_ratio']

    bbo = config['bbo']
    leverage = config['leverage']
    hold_for = config['hold_for']


