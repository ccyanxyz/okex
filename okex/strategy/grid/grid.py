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

bbo = config['bbo']
leverage = config['leverage']

amount = config['amount']
times_atr = config['times_atr']
grid_size = config['grid_size']

class Grid:
    def __init__(self, apikey, secretkey, okcoinRESTURL, coin, contract_type, kline_size, kline_num, bbo, leverage, amount, times_atr, grid_size, logger = None):
        self.future = Future(okcoinRESTURL, apikey, secretkey, logger)
        self.coin = coin
        self.contract_type = contract_type
        self.kline_size = kline_size
        self.kline_num = kline_num
        self.bbo = bbo
        self.leverage = leverage
        self.amount = amount
        self.times_atr = times_atr
        self.grid_size = grid_size
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('gridbot')

        self.init = True

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
            long_price = last - (i + 1) * self.times_atr * atr
            short_price = last + (i + 1) * self.times_atr * atr

            ret = self.future.open_long(self.coin, self.contract_type, long_price, self.amount, self.leverage, bbo = 0)
            self.open_longs.append(ret)

            ret = self.future.open_short(self.coin, self.contract_type, short_price, self.amount, self.leverage, bbo = 0)
            self.open_shorts.append(ret)

            self.logger.info('init: long_order_at: ' + str(long_price) + 'short_order_at: ' + str(short_price))
            time.sleep(1)


    def adjust_open_orders(self, last, atr):
        # check order status
        for order in self.open_longs:
            order_info = self.future.future_orderinfo(self.coin, self.contract_type, order, 2, 1, 50)['orders'][0]
            status = order_info['status']
            order_price = order_info['price']
            low_limit = last - (self.grid_size + 2) * self.times_atr * atr
            if status == '1' or status == '2' or order_price < low_limit:
                if status == '1' or order_price < low_limit:
                    self.future.future_cancel(self.coin, self.contract_type, order)
                idx = self.open_longs.index(order)
                price = last  - (idx + 1) * self.times_atr * atr
                ret = self.future.open_long(self.coin, self.contract_type, price, self.amount, self.leverage, bbo = 0)
                self.open_longs[idx] = ret
        
        for order in self.open_shorts:
            ret = self.future.future_orderinfo(self.coin, self.contract_type, order, 2, 1, 50)
            print(ret)
            order_info = self.future.future_orderinfo(self.coin, self.contract_type, order, 2, 1, 50)['orders'][0]
            status = order_info['status']
            order_price = order_info['price']
            up_limit = last + (self.grid_size + 2) * self.times_atr * atr
            if status == '1' or status == '2' or order_price > up_limit:
                if status == '1' or order_price > up_limit:
                    self.future.future_cancel(self.coin, self.contract_type, order)
                idx = self.open_shorts.index(order)
                price = last  + (idx + 1) * self.times_atr * atr
                ret = self.future.open_short(self.coin, self.contract_type, price, self.amount, self.leverage, bbo = 0)
                self.open_shorts[idx] = ret
        
    def adjust_close_orders(self, last, atr, long_amount, short_amount):
        to_del = []
        for order in self.close_longs:
            order_info = self.future.future_orderinfo(self.coin, self.contract_type, order, 2, 1, 50)['orders'][0]
            status = order_info['status']
            order_price = order_info['price']
            up_limit = last + (self.grid_size + 2) * self.times_atr * atr
            if status == '2' or order_price > up_limit:
                self.future.future_cancel(self.coin, self.contract_type, order)
                idx = self.close_longs.index(order)
                to_del.append(idx)

        for i in to_del:
            del self.cloes_longs[i]

        i = 1
        while long_amount > 0:
            price = last + self.times_atr * atr * i
            if long_amount > self.amount:
                ret = self.future.close_long(self.coin, self.contract_type, price, self.amount, self.leverage, bbo = 0)
                self.close_longs.append(ret)
                long_amount -= self.amount
            else:
                ret = self.future.close_long(self.coin, self.contract_type, price, long_amount, self.leverage, bbo = 0)
                self.close_longs.append(ret)
                long_amount = 0
            i += 1

        to_del.clear()
        for order in self.close_shorts:
            order_info = self.future.future_orderinfo(self.coin, self.contract_type, order, 2, 1, 50)['orders'][0]
            status = order_info['status']
            order_price = order_info['price']
            up_limit = last - (self.grid_size + 2) * self.times_atr * atr
            if status == '2' or order_price < up_limit:
                self.future.future_cancel(self.coin, self.contract_type, order)
                idx = self.close_shorts.index(order)
                to_del.append(idx)

        for i in to_del:
            del self.cloes_shorts[i]

        i = 1
        while short_amount > 0:
            price = last - self.times_atr * atr * i
            if short_amount > self.amount:
                ret = self.future.close_short(self.coin, self.contract_type, price, self.amount, self.leverage, bbo = 0)
                self.close_shorts.append(ret)
                short_amount -= self.amount
            else:
                ret = self.future.close_short(self.coin, self.contract_type, price, long_amount, self.leverage, bbo = 0)
                self.close_shorts.append(ret)
                short_amount = 0
            i += 1

    def run_forever(self):
        # get last, atr
        last, atr = self.get_last_atr()

        # get position
        long_amount, long_profit, short_amount, short_profit = self.get_position()
        self.logger.info('position: long_amount = %s, long_profit = %s, short_amount = %s, short_profit = %s' % (long_amount, long_profit, short_amount, short_profit))

        # get available coin amount
        coin_available = self.get_available()
        self.logger.info('coin_available = ' + str(coin_available))

        # init orders
        if self.init:
            self.init_orders(last, atr)
            self.init = False

        # adjust orders
        self.adjust_open_orders(last, atr)
        self.adjust_close_orders(last, atr, long_amount, short_amount)

        time.sleep(15)


bot = Grid(apikey, secretkey, okcoinRESTURL, coin, contract_type, kline_size, kline_num, bbo, leverage, amount, times_atr, grid_size, logger = logger)

bot.run_forever()
