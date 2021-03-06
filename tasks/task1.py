
from domain.tasks_main import task_making
from domain import my_exchange
from strategy import bulin_K
from Xbitfinex import orders

task_making(
    my_exchange.bitfinexV2_instance(),
    bulin_K.signal_bolling, strtegy_para=[475, 3.5, 5, 0.01152],
    func_auto_trade=orders.auto_trade_leverage, order_para=[3, 0.7, my_exchange.bitfinex_instance()],
    symbol='EOS/USDT',
    interval_time='15m'
)