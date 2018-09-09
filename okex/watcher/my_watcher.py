from okexapi.FutureAPI import Future
import talib as tb
import numpy as np
import logging
import json
import os
import sys
import time
import re
import _thread


class Watcher:

    def __init__(self, api_key, secret_key, url, symbol, contract_type, leverage, kline_size, kline_num, logger = None):
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.url = url
        self.symbol = symbol
        self.contract_type = contract_type
        self.leverage = leverage
        self.kline_size = kline_size
        self.kline_num = kline_num

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('tradebot')

        self.future = Future(url, api_key, secret_key, logger)

    def get_kline(self):
        kline = self.future.future_kline(self.symbol, self.contract_type, self.kline_size, self.kline_num)

        return kline

    def get_position(self):
        long_amount, long_profit, short_amount, short_profit = self.future.get_position(self.symbol, self.contract_type)
        return long_amount, long_profit, short_amount, short_profit

    def get_available(self):
        coin_avail = self.future.future_userinfo_4fix()['info'][self.symbol[:3]]['contracts'][0]['available']
        return coin_avail

    def get_last(self):
        kline = self.get_kline()
        return kline[-1][4]

    def open_long(self, price, amount, bbo):
        ret = self.future.open_long(self.symbol, self.contract_type, price, amount, self.leverage, bbo)
        return ret

    def close_long(self, price, amount, bbo):
        ret = self.future.close_long(self.symbol, self.contract_type, price, amount, self.leverage, bbo)
        return ret

    def open_short(self, price, amount, bbo):
        ret = self.future.open_short(self.symbol, self.contract_type, price, amount, self.leverage, bbo)
        return ret

    def close_short(self, price, amount, bbo):
        ret = self.future.close_short(self.symbol, self.contract_type, price, amount, self.leverage, bbo)

    def watch_forever(self, upper, lower):

        while True:
            last = watcher.get_last()
            if last >= upper:
                cmd = "osascript -e 'display notification \"" + 'last price: ' + str(last)  + ' > upper: ' + str(upper) + "\" with title \"okex\" ' "

                os.system(cmd)

            if last <= lower:
                cmd = "osascript -e 'display notification \"" + 'last price: ' + str(last)  + ' < lower: ' + str(lower) + "\" with title \"okex\" ' "

                os.system(cmd)

            self.logger.info('last = ' + str(last))

            time.sleep(15)

    def control(self, nothing):
        
        amount_matcher = re.compile('\d{1, 10}')

        while True:

            cmd = input('~>')

            bbo = 1
            price = self.get_last()
            amount = int(amount_matcher.findall(cmd)[0])
            
            if 'open long' in cmd:
                self.open_long(price, amount, bbo)
            elif 'close long' in cmd:
                self.close_long(price, amount, bbo)
            elif 'open short' in cmd:
                self.open_short(price, amount, bbo)
            elif 'close short' in cmd:
                self.close_short(price, amount, bbo)
            else:
                print('wrong command.')


def get_logger():
    logging.basicConfig(
    #   filename = './log/' + log_filename + str(time.strftime('%m-%d %H:%M:%S')),
            level = logging.INFO,
            format = '[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
            datefmt = '%Y-%m-%d %H:%M:%S',
            filemode = 'a'
    )
    return logging.getLogger('tradebot')

if __name__ == '__main__':
    
    config_path = './watcher.json'
    f = open(config_path, 'r')
    config = json.load(f)

    api_key = config['api_key']
    secret_key = config['secret_key']
    url = config['url']
    symbol = config['coin']
    contract_type = config['contract_type']
    kline_size = config['kline_size']
    kline_num = config['kline_num']
    leverage = config['leverage']

    upper = config['upper']
    lower = config['lower']

    logger = get_logger()
    watcher = Watcher(api_key, secret_key, url, symbol, contract_type, leverage, kline_size, kline_num, logger)
    
    # upper = float(input('~> upper limit:'))
    # lower = float(input('~> lower limit:'))
    # lower = float(sys.argv[1])
    # upper = float(sys.argv[2])

    watcher.watch_forever(upper, lower)
    '''
    _thread.start_new_thread(watcher.watch_forever, (upper, lower))
    _thread.start_new_thread(watcher.control, ('nothing', ))
    '''
