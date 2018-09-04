import numpy as np
import time
import arrow
from talib import SMA
import json
import logging
from okexapi.FutureAPI import Future

log_filename = 'trade.log'
logging.basicConfig(
	filename = './log/' + log_filename + str(time.strftime('%m-%d %H:%M:%S')),
        level = logging.INFO,
        format = '[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filemode = 'a'
)
logger = logging.getLogger('tradebot')

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
slow_ma = config['slow_ma']
fast_ma = config['fast_ma']

bbo = config['bbo']
leverage = config['leverage']

def get_amount():
    coin_available = future.future_userinfo_4fix()['info'][coin[:3]]['contracts'][0]['available']
    return int(10 * amount_ratio * coin_available)

while True:
    kline = future.future_kline(coin, contract_type, kline_size, kline_num)
    last_closes = [kline[i][4] for i in range(kline_num)]
    close = np.array(last_closes)
    fast = SMA(close, timeperiod = fast_ma)
    slow = SMA(close, timeperiod = slow_ma)

    long_amount, long_profit, short_amount, short_profit = future.get_position(coin, contract_type)
    logger.info('position: long_amount = %s, long_profit = %s, short_amount = %s, short_profit = %s' % (long_amount, long_profit, short_amount, short_profit))

    coin_available = future.future_userinfo_4fix()['info'][coin[:3]]['contracts'][0]['available']
    logger.info('coin_available = ' + str(coin_available))

    last = kline[-1][4]

    if fast[-2] > slow[-2] and long_amount < 1 and fast[-3] <= slow[-3]:
        logger.info('golden cross.')
        if short_amount > 0:
            logger.info('close short, amount: %d' % short_amount)
            future.close_short(coin, contract_type, last, short_amount, leverage, bbo)
        amount = get_amount()
        future.open_long(coin, contract_type, last, amount, leverage, bbo)
        logger.info('open long, amount: %d' % amount)
    elif fast[-2] < slow[-2] and short_amount < 1 and fast[-3] >= slow[-3]:
        logger.info('dead cross.')
        if long_amount > 0:
            logger.info('close long, amount: %d' % long_amount)
            future.close_long(coin, contract_type, last, long_amount, leverage, bbo)
        amount = get_amount()
        future.open_short(coin, contract_type, last, amount, leverage, bbo)
        logger.info('open short, amount: %d' % amount)
    else:
        logger.info('fast[-2]:' + str(fast[-2]) + ', slow[-2] = ' + str(slow[-2]))
        logger.info('fast[-3]:' + str(fast[-3]) + ', slow[-3] = ' + str(slow[-3]))

    time.sleep(15)
