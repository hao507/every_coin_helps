import ccxt
import platform
#ccxt (1.17.545)
print('ccxt_version:',ccxt.__version__)
print('python_version:',platform.python_version())

#生成自己的okex实例
def okex_instance():
    params = {
        'proxies': {
            'http': 'http://127.0.0.1:1087',  # these proxies won't work for you, they are here for yuan
            'https': 'https://127.0.0.1:1087',
            },
        'apiKey': '',
        'secret': '',
        'verbose': False
    }
    exchange = getattr(ccxt, 'okex')(params)
    return exchange


# bitfinex无法查到当前的k线数据，但能查资产
def bitfinex_instance():
    params = {
        'proxies': {
            'http': 'http://127.0.0.1:1087',  # these proxies won't work for you, they are here for yuan
            'https': 'https://127.0.0.1:1087',
            },
        'apiKey': '',
        'secret': '',
        'rateLimit': 10000,
        'enableRateLimit': True,
        'verbose': False
    }
    exchange = getattr(ccxt, 'bitfinex')(params)
    return exchange

#bitfinex2在获取资产时，会缺少数据，但可以查k线
def bitfinexV2_instance():
    params = {
        'proxies': {
            'http': 'http://127.0.0.1:1087',  # these proxies won't work for you, they are here for yuan
            'https': 'https://127.0.0.1:1087',
            },
        'apiKey': '',
        'secret': '',
        'rateLimit': 10000,
        'enableRateLimit': True,
        'verbose': False
    }
    exchange = getattr(ccxt, 'bitfinex2')(params)
    return exchange


# exchange = bitfinexV2_instance()
# position = exchange.private_post_auth_r_positions()
#
# sunyi = position[0][6]
# sunyi_p = position[0][7]
# # 用来存储已持仓的币种列表
# position_list = []
# position_all_amount = []
#
# if len(position) != 0:
#     for p in position:
#         position_symbol = p[0][1:-3]  # 'tBTCUSD'截取一段
#         position_list.append(position_symbol)
#         position_amount = p[2]
#         position_all_amount.append(position_amount)
#     print(position_list)
#
#  #生成平单的注释，提醒损益情况
#     note = ''
#     trade_coin ='BTC'
#     if trade_coin in position_list:
#         _index = position_list.index(trade_coin)
#         if len(position[_index]) > 7:
#             profit_loss = position[_index][6]
#             profit_loss_percent = position[_index][7]
# balance_total = exchange.fetch_balance({'type': 'trading'})
pass