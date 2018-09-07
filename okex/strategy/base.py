from okexapi.FutureAPI import Future
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

        self.future = Future(url, api_key, secret_key, logger)

    def get_kline(self, symbol, contract_type, kline_size, kline_num):
        kline = self.future.future_kline(symbol, contract_type, kline_size, kline_num)
        
        return kline

    def get_position(self, symbol, contract_type):
        long_amount, long_profit, short_amount, short_profit = self.future.get_position(symbol, contract_type)
        return long_amount, long_profit, short_amount, short_profit

    def get_available(self, symbol):
        coin_avail = self.future.future_userinfo_4fix()['info'][symbol[:3]]['contracts'][0]['available']
        return coin_avail

    def clear_pending_orders(self, symbol, contract_type):
        order_id = -1 # get orders with specific status
        status = 1 # unfilled orders, 2: filled orders
        page = 1
        page_len = 50 # max 50
        ret = self.future.future_orderinfo(symbol, contract_type, order_id, status, page, page_len)
        orders = ret['orders']
        for order in orders:
            id = order['order_id']
            self.future.future_cancel(symbol, contract_type, id)




