#!/usr/bin/python
# -*- coding: utf-8 -*-
from .HttpMD5Util import buildMySign,httpGet,httpPost
import logging

class Spot:

    def __init__(self, url, apikey, secretkey, logger = None):
        self.__url = url
        self.__apikey = apikey
        self.__secretkey = secretkey
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('tradebot')

    #获取OKCOIN现货行情信息
    def ticker(self,symbol = ''):
        TICKER_RESOURCE = "/api/v1/ticker.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return httpGet(self.__url,TICKER_RESOURCE,params)

    #获取OKCOIN现货市场深度信息
    def depth(self,symbol = ''):
        DEPTH_RESOURCE = "/api/v1/depth.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return httpGet(self.__url,DEPTH_RESOURCE,params)

    #获取OKCOIN现货历史交易信息
    def trades(self,symbol = ''):
        TRADES_RESOURCE = "/api/v1/trades.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return httpGet(self.__url,TRADES_RESOURCE,params)

    # get kline
    def spot_kline(self, symbol, type_, size = None, since = None):
        KLINE_RESOURCE = "/api/v1/kline.do"
        params = 'symbol=' + symbol + '&type=' + type_
        if size:
            params += '&size=' + str(size)
        if since:
            params += '&since=' + str(since)
        return httpGet(self.__url, KLINE_RESOURCE, params)



    #获取用户现货账户信息
    def userinfo(self):
        USERINFO_RESOURCE = "/api/v1/userinfo.do"
        params ={}
        params['api_key'] = self.__apikey
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,USERINFO_RESOURCE,params)

    #现货交易
    def trade(self, symbol, trade_type, price, amount):
        TRADE_RESOURCE = "/api/v1/trade.do"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'type':trade_type
        }
        if price:
            params['price'] = str(price)
        if amount:
            params['amount'] = str(amount)

        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,TRADE_RESOURCE,params)

    #现货批量下单
    def batch_trade(self,symbol,tradeType,orders_data):
        BATCH_TRADE_RESOURCE = "/api/v1/batch_trade.do"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'type':tradeType,
            'orders_data':orders_data
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,BATCH_TRADE_RESOURCE,params)

    #现货取消订单
    def cancel_order(self, symbol, orderId):
        CANCEL_ORDER_RESOURCE = "/api/v1/cancel_order.do"
        params = {
             'api_key':self.__apikey,
             'symbol':symbol,
             'order_id':orderId
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,CANCEL_ORDER_RESOURCE,params)

    #现货订单信息查询
    def order_info(self,symbol,orderId):
         ORDER_INFO_RESOURCE = "/api/v1/order_info.do"
         params = {
             'api_key':self.__apikey,
             'symbol':symbol,
             'order_id':orderId
         }
         params['sign'] = buildMySign(params,self.__secretkey)
         return httpPost(self.__url,ORDER_INFO_RESOURCE,params)

    #现货批量订单信息查询
    def orders_info(self,symbol,orderId,tradeType):
         ORDERS_INFO_RESOURCE = "/api/v1/orders_info.do"
         params = {
             'api_key':self.__apikey,
             'symbol':symbol,
             'order_id':orderId,
             'type':tradeType
         }
         params['sign'] = buildMySign(params,self.__secretkey)
         return httpPost(self.__url,ORDERS_INFO_RESOURCE,params)

    #现货获得历史订单信息
    def order_history(self,symbol,status,currentPage,pageLength):
           ORDER_HISTORY_RESOURCE = "/api/v1/order_history.do"
           params = {
              'api_key':self.__apikey,
              'symbol':symbol,
              'status':status,
              'current_page':currentPage,
              'page_length':pageLength
           }
           params['sign'] = buildMySign(params,self.__secretkey)
           return httpPost(self.__url,ORDER_HISTORY_RESOURCE,params)


    def buy(self, symbol, price, amount, bbo = 0):
        trade_type = 'buy'
        if bbo == 1:
            # 市价买单传price作为买入金额
            trade_type = 'buy_market'
            ret = self.trade(symbol, trade_type, price = amount, amount = None)
        elif bbo == 0:
            trade_type = 'buy'
            ret = self.trade(symbol, trade_type, price = price, amount = None)

        self.logger.info(str(ret))
        if ret['result'] == True:
            return ret['order_id']
        else:
            self.logger.error('buy order failed.')
            self.logger.error(str(ret))
            return ''

    def sell(self, symbol, price, amount, bbo = 0):
        trade_type = 'sell'
        if bbo == 1:
            # 市价卖单不传price
            trade_type = 'sell_market'
            ret = self.trade(symbol, trade_type, price = None, amount = amount)
        elif bbo == 0:
            trade_type = 'sell'
            ret = self.trade(symbol, trade_type, price = price, amount = None)

        if ret['result'] == True:
            return ret['order_id']
        else:
            self.logger.error('sell order failed.')
            self.logger.error(str(ret))
            return ''
