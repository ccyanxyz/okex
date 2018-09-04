import numpy as np
import time
import json
import talib as tb
import logging
from okexapi.FutureAPI import Future


logging.basicConfig(
       # filename = './atr_loss_control.log',
        level = logging.INFO,
        format = '[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filemode = 'a'
)
logger = logging.getLogger('controler')

f = open('config.json', 'r')
config = json.load(f)

url = config['url']
api_key = config['api_key']
secret_key = config['secret_key']

future = Future(url, api_key, secret_key, logger)

coin = config['coin']
contract_type = config['contract_type']
kline_size = config['kline_size']
kline_num = config['kline_num']

while True:

    kline = future.future_kline(coin, contract_type, kline_size, kline_num)
    high = [kline[i][2] for i in range(kline_num)]
    low = [kline[i][3] for i in range(kline_num)]
    close = [kline[i][4] for i in range(kline_num)]

    high = np.array(high)
    low = np.array(low)
    close = np.array(close)

    atr = tb.ATR(high, low, close, timeperiod = 14)

    last = close[-1]
    
    logger.info('last: ' + str(last) + ', atr[-1]: ' + str(atr[-1]))
    logger.info('3atr: ' + str(3 * atr[-1]))
    logger.info('+3atr: ' + str(last + 3 * atr[-1]) + ', -3atr: ' + str(last - 3 * atr[-1]))


    time.sleep(3)

