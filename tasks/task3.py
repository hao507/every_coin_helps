from domain.tasks_main import task_making
from domain import my_exchange
from strategy import bulin_K
from Xbitfinex import orders
'''
bulin_K:
ETH[[100, 3.25, 0.01]   15956.918983]
ETH[[100, 3.25, 0.01,0.0255 ]   35064.8015]
'''
task_making(
    my_exchange.bitfinexV2_instance(),
    bulin_K.signal_bolling, strtegy_para=[395, 3.081812, 0.050710, 0.027049, 1.5],
    func_auto_trade=orders.auto_trade_leverage, order_para=[1.5, 0.5, my_exchange.bitfinex_instance()],
    symbol='ETH/USDT',
    interval_time='15m'
    )