from okexapi.FutureAPI import Future
import json
import time

f = open('../config.json', 'r')
config = json.load(f)

url = config['url']
api_key = config['api_key']
secret_key = config['secret_key']

future = Future(url, api_key, secret_key)

coin = config['coin']
contract_type = config['contract_type']
bbo = config['bbo']
amount = 1
price = 1
leverage = 20

# get position
position = future.get_position(coin, contract_type)
print(position)

# open long
ret = future.open_long(coin, contract_type, price, 100000000, leverage, bbo)
print(ret)
position = future.get_position(coin, contract_type)
print(position)
time.sleep(5)

# close long
ret = future.close_long(coin, contract_type, price, amount, leverage, bbo)
print(ret)
position = future.get_position(coin, contract_type)
print(position)
time.sleep(5)

# open short
ret = future.open_short(coin, contract_type, price, amount, leverage, bbo)
print(ret)
position = future.get_position(coin, contract_type)
print(position)
time.sleep(5)

# close short
ret = future.close_short(coin, contract_type, price, amount, leverage, bbo)
print(ret)
position = future.get_position(coin, contract_type)
print(position)
