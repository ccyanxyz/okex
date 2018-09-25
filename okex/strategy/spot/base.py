from okexapi.SpotAPI import Spot
import talib as tb
import numpy as np
import logging


class Base:

    def __init__(self, api_key, secret_key, url, logger = None):
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.url = url
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('tradebot')

        self.spot = Spot(url, api_key, secret_key, logger)

    def get_kline(self, symbol, kline_size, kline_num = None, since = None):
        kline = self.spot.spot_kline(symbol, kline_size, kline_num)

        return kline

    def get_available(self, coin):
        userinfo = self.spot.userinfo()
        coin_avail = userinfo['info']['funds']['free'][coin]

        return float(coin_avail)

    def get_order_info(self, symbol, order_id):
        ret = self.spot.order_info(symbol, order_id)
        return ret

    def get_last(self, symbol):
        kline = self.get_kline(symbol, '1min', 1)
        return kline[-1][4]

    def clear_pending_orders(self, symbol):
        order_id = -1 # get unfilled or partially filled orders
        orders = self.get_order_info(symbol, order_id)['orders']
        for order in orders:
            id = order['order_id']
            self.spot.cancel_order(symbol, id)

def get_logger():
    logging.basicConfig(
    #   filename = './log/' + log_filename + str(time.strftime('%m-%d %H:%M:%S')),
            level = logging.INFO,
            format = '[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
            datefmt = '%Y-%m-%d %H:%M:%S',
            filemode = 'a'
    )
    return logging.getLogger('tradebot')
