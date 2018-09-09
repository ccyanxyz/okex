import sys
import numpy as np
import time
import arrow
from talib import SMA
import json
import logging
from okexapi.FutureAPI import Future
from base import *


class Ma(Base):

    def __init__(self,
            api_key,
            secret_key,
            url,
            coin,
            contract_type,
            kline_size, # kline size, 15min
            kline_num, # number of klines to get
            amount_ratio, # percentage of available coins
            bbo, # 1: market price, 0: use given price
            leverage, # leverage, 10 or 20
            fast, # fast kline period, 5
            slow, # slow kline period, 20
            interval,
            stop_loss,
            logger = None):

        super(Ma, self).__init__(api_key, secret_key, url, logger)
        self.coin = coin
        self.contract_type = contract_type
        self.kline_size = kline_size
        self.kline_num = kline_num
        self.amount_ratio = amount_ratio
        self.bbo = bbo
        self.leverage = leverage
        self.fast = fast
        self.slow = slow
        self.interval = interval
        self.stop_loss = stop_loss


    def get_amount(self):
        coin_available = self.get_available(self.coin, self.contract_type)

        return int(self.leverage * amount_ratio * coin_available)

    def ma_cross(self):
        kline = self.get_kline(self.coin, self.contract_type, self.kline_size, self.kline_num)
        close = np.array([kline[i][4] for i in range(self.kline_num)])

        fast_ma = tb.SMA(close, self.fast)
        slow_ma = tb.SMA(close, self.slow)

        '''
        # stable version
        if fast_ma[-3] < slow_ma[-3] and fast_ma[-2] >= slow_ma[-2]:
            return 'gold'
        elif fast_ma[-3] > slow_ma[-3] and fast_ma[-2] <= slow_ma[-2]:
            return 'dead'
        else:
            return 'nothing'
        '''

        # unstable version
        if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] >= slow_ma[-1]:
            return 'gold'
        elif fast_ma[-2] > slow_ma[-2] and fast_ma[-1] <= slow_ma[-1]:
            return 'dead'
        else:
            return 'nothing'


    def get_last(self):
        kline = self.get_kline(self.coin, self.contract_type, self.kline_size, 1)
        return kline[0][4]

    def update_stop_loss(self, stop_loss, current_profit):
        if current_profit < 10:
            return stop_loss
        elif current_profit >= 10 and current_profit < 60:
            if current_profit * 0.5 > stop_loss:
                return current_profit * 0.5
            else:
                return stop_loss
        elif current_profit >= 60 and current_profit < 100:
            if current_profit * 0.6 > stop_loss:
                return current_profit * 0.6
            else:
                return stop_loss
        elif current_profit >= 100 and current_profit < 150:
            if current_profit * 0.7 > stop_loss:
                return current_profit * 0.7
            else:
                return stop_loss
        else:
            if current_profit * 0.8 > stop_loss:
                return current_profit * 0.8
            else:
                return stop_loss

    def run_forever(self):
        stop_loss = self.stop_loss

        while True:
            long_amount, long_profit, short_amount, short_profit = self.get_position(self.coin, self.contract_type)
            logger.info('position: long_amount = %s, long_profit = %s, short_amount = %s, short_profit = %s' % (long_amount, long_profit, short_amount, short_profit))

            coin_available = self.get_available(self.coin)
            logger.info('coin_available = ' + str(coin_available))

            last = self.get_last()

            current_profit = 0
            if long_amount > 0:
                current_profit  = long_profit
            if short_amount > 0:
                current_profit = short_profit
            if current_profit == 0:
                stop_loss = self.stop_loss
            stop_loss = self.update_stop_loss(stop_loss, current_profit)

            self.logger.info('stop_loss: ' + str(stop_loss))
            print(self.coin, self.contract_type, last, long_amount, self.leverage, self.bbo)
            print(self.coin, self.contract_type, last, short_amount, self.leverage, self.bbo)

            if long_profit < stop_loss and long_amount > 0:
                self.future.close_long(self.coin, self.contract_type, last, long_amount, self.leverage, self.bbo)
                stop_loss = self.stop_loss
                self.logger.info('close long at: ' + str(last) + ', amount: ' + str(long_amount))

            if short_profit < stop_loss and short_amount > 0:
                self.future.close_short(self.coin, self.contract_type, last, short_amount, self.leverage, self.bbo)
                stop_loss = self.stop_loss
                self.logger.info('close short at: ' + str(last) + ', amount: ' + str(short_amount))


            cross = self.ma_cross()
            if cross == 'gold' and long_amount < 10:
                logger.info('golden cross.')
                if short_amount > 0:
                    logger.info('close short at: %f, amount: %d' % (last, short_amount))
                    stop_loss = self.stop_loss
                    self.future.close_short(self.coin, self.contract_type, last, short_amount, self.leverage, self.bbo)
                amount = self.get_amount()
                self.future.open_long(self.coin, self.contract_type, last, amount, self.leverage, self.bbo)
                logger.info('open long at: %f, amount: %d' % (last, amount))
            elif cross == 'dead' and short_amount < 10:
                logger.info('dead cross.')
                if long_amount > 0:
                    logger.info('close long at: %f, amount: %d' % (last, long_amount))
                    stop_loss = self.stop_loss
                    self.future.close_long(self.coin, self.contract_type, last, long_amount, self.leverage, self.bbo)
                amount = get_amount()
                self.future.open_short(self.coin, self.contract_type, last, amount, self.leverage, self.bbo)
                logger.info('open short at: %f, amount: %d' % (last, amount))
            else:
                logger.info('No trading signal.')

            time.sleep(self.interval)


if __name__ == '__main__':

    config_path = sys.argv[1]

    f = open(config_path, encoding = 'utf-8')
    config = json.load(f)

    api_key = config['api_key']
    secret_key = config['secret_key']
    url = config['url']

    coin = config['coin']
    contract_type = config['contract_type']
    kline_size = config['kline_size']
    kline_num = config['kline_num']
    amount_ratio = config['amount_ratio']
    slow = config['slow']
    fast = config['fast']
    interval = config['interval']

    bbo = config['bbo']
    leverage = config['leverage']
    stop_loss = config['stop_loss']

    logger = get_logger()

    ma_bot = Ma(api_key,
            secret_key,
            url,
            coin,
            contract_type,
            kline_size,
            kline_num,
            amount_ratio,
            bbo,
            leverage,
            fast,
            slow,
            interval,
            stop_loss,
            logger = logger)

    ma_bot.run_forever()


