import numpy as np
import time
import arrow
import talib as tb
import json
import logging
from okexapi.FutureAPI import Future

log_filename = 'trade.log'
logging.basicConfig(
#	filename = './log/' + log_filename + str(time.strftime('%m-%d %H:%M:%S')),
        level = logging.INFO,
        format = '[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filemode = 'a'
)
logger = logging.getLogger('tradebot')

f = open('/root/okex/okex/strategy/grid/config.json', encoding = 'utf-8')
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

bbo = config['bbo']
leverage = config['leverage']

amount = config['amount']
times_atr = config['times_atr']
grid_size = config['grid_size']
clear_interval = config['clear_interval']
amount_ratio = config['amount_ratio']
fast = config['fast_kline']
slow = config['slow_kline']
gap = config['gap']

class Grid:
    def __init__(self, apikey, secretkey, okcoinRESTURL, coin, contract_type, kline_size, kline_num, bbo, leverage, amount, times_atr, grid_size, clear_interval, amount_ratio, fast, slow, gap, use_gap = True, logger = None):
        self.future = Future(okcoinRESTURL, apikey, secretkey, logger)
        self.coin = coin
        self.contract_type = contract_type
        self.kline_size = kline_size
        self.kline_num = kline_num
        self.bbo = bbo
        self.leverage = leverage
        self.amount = amount
        self.times_atr = times_atr
        self.gap = gap
        self.use_gap = use_gap
        self.grid_size = grid_size
        self.amount_ratio = amount_ratio
        self.fast = fast
        self.slow = slow
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('gridbot')

        self.init = True
        self.clear_interval = clear_interval

        self.open_longs = []
        self.close_longs = []
        self.open_shorts = []
        self.close_shorts = []

    def get_last_atr(self):
        kline = self.future.future_kline(self.coin, self.contract_type, self.kline_size, self.kline_num)
        high = [kline[i][2] for i in range(kline_num)]
        low = [kline[i][3] for i in range(kline_num)]
        close = [kline[i][4] for i in range(kline_num)]
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)

        atr = tb.ATR(high, low, close, timeperiod = 14)
        return close[-1], atr[-1]

    def get_position(self):
        long_amount, long_profit, short_amount, short_profit = self.future.get_position(coin, contract_type)
        return long_amount, long_profit, short_amount, short_profit

    def get_available(self):
        coin_available = future.future_userinfo_4fix()['info'][coin[:3]]['contracts'][0]['available']
        return coin_available

    def init_orders(self, last, atr):
        for i in range(self.grid_size):
            if self.use_gap:
                long_price = last - (i + 1) * self.gap
                short_price = last + (i + 1) * self.gap
            else:
                long_price = last - (i + 1) * self.times_atr * atr
                short_price = last + (i + 1) * self.times_atr * atr

            ret = self.future.open_long(self.coin, self.contract_type, long_price, self.amount, self.leverage, bbo = 0)
            self.open_longs.append(ret)

            ret = self.future.open_short(self.coin, self.contract_type, short_price, self.amount, self.leverage, bbo = 0)
            self.open_shorts.append(ret)

            self.logger.info('init: long_order_at: ' + str(round(long_price, 3)) + ', short_order_at: ' + str(round(short_price, 3)))
            time.sleep(1)

    def kline_cross(self):
        kline = self.future.future_kline(self.coin, self.contract_type, self.kline_size, self.kline_num)
        close = [kline[i][4] for i in range(kline_num)]
        close = np.array(close)

        fast_kline = tb.SMA(close, self.fast)
        slow_kline = tb.SMA(close, self.slow)
        if fast_kline[-2] < slow_kline[-2] and fast_kline[-1] > slow_kline[-1]:
            return 'gold'
        elif fast_kline[-2] > slow_kline[-2] and fast_kline[-1] < slow_kline[-1]:
            return 'dead'
        else:
            return 'nothing'


    def clear_orders(self):
        for order in self.open_longs:
            self.future.future_cancel(self.coin, self.contract_type, order)
        for order in self.open_shorts:
            self.future.future_cancel(self.coin, self.contract_type, order)

    def run_forever(self):
        counter = 1
        max_long_profit = 0
        max_short_profit = 0
        long_stop_loss = False
        short_stop_loss = False
        while True:
            # get last, atr
            last, atr = self.get_last_atr()

            # get position
            long_amount, long_profit, short_amount, short_profit = self.get_position()
            self.logger.info('position: long_amount = %s, long_profit = %s, short_amount = %s, short_profit = %s' % (long_amount, long_profit, short_amount, short_profit))

            # get available coin amount
            coin_available = self.get_available()
            self.logger.info('coin_available = ' + str(coin_available))
            self.logger.info('last = ' + str(last))

            # init orders
            if counter == 1:
                self.init_orders(last, atr)

            # adjust orders
            #self.adjust_open_orders(last, atr)
            #self.adjust_close_orders(last, atr, long_amount, short_amount)

            # process long position
            stop_win = 10
            stop_loss = -40

            if long_profit < stop_loss:
                long_stop_loss = True
            if short_profit < stop_loss:
                short_stop_loss = True

            if long_amount > 0 and self.init:
                stop_win -= (long_amount / self.amount - 1) * 1
                if long_profit >= stop_win and not short_stop_loss:
                    ret = self.future.close_long(self.coin, self.contract_type, last, long_amount, self.leverage, bbo = 1)
                # if stop loss, stop grid, open short
                if long_profit < stop_loss:
                    # long stop loss and open short
                    ret = self.future.close_long(self.coin, self.contract_type, last, long_amount, self.leverage, bbo = 1)
                    amount = self.amount_ratio * self.leverage * self.get_available()
                    ret = self.future.open_short(self.coin, self.contract_type, last, amount, self.leverage, bbo = 0)
                    self.init = False
                    long_stop_loss = False


            # process short position
            stop_win = 10
            stop_loss = -40
            if short_amount > 0 and self.init:
                stop_win -= (short_amount / self.amount - 1) * 1
                if short_profit >= stop_win and not long_stop_loss:
                    ret = self.future.close_short(self.coin, self.contract_type, last, short_amount, self.leverage, bbo = 1)
                # if stop loss, stop grid, open long
                if short_profit < stop_loss:
                    # short stop loss and open long
                    ret = self.future.close_short(self.coin, self.contract_type, last, short_amount, self.leverage, bbo = 1)
                    amount = self.amount_ratio * self.leverage * self.get_available()
                    ret = self.future.open_long(self.coin, self.contract_type, last, amount, self.leverage, bbo = 1)
                    self.init = False
                    short_stop_loss = False

            # one way up or down
            if self.init == False:
                if long_amount > 0:
                    # if dead cross, close long, back to grid mode
                    if self.kline_cross() == 'dead':
                        self.future.close_long(self.coin, self.contract_type, last, long_amount, self.leverage, bbo = 1)
                        self.init = True

                if short_amount > 0:
                    # if golden cross, close short, back to grid mode
                    if self.kline_cross() == 'gold':
                        self.future.close_short(self.coin, self.contract_type, last, short_amount, self.leverage, bbo = 1)
                        self.init = True

            if counter % self.clear_interval == 0 and self.init:
                self.clear_orders()
                self.init_orders()

            counter += 1
            time.sleep(15)


bot = Grid(apikey, secretkey, okcoinRESTURL, coin, contract_type, kline_size, kline_num, bbo, leverage, amount, times_atr, grid_size, clear_interval, amount_ratio, fast, slow, gap, use_gap = True, logger = logger)

bot.run_forever()
