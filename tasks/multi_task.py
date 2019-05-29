from domain.tasks_main import task_making
from domain import my_exchange
from strategy import bulin_K
from Xbitfinex import orders
#对固定的策略和bitfinex，使用进程管理的功能函数
def start_bitfinex_task(symb='ETH', percent=0.5, multi=2, strtegy_para=[395, 3.081812, 0.050710, 0.027049, 1.5]):
    task_making(
        my_exchange.bitfinexV2_instance(),
        bulin_K.signal_bolling, strtegy_para=strtegy_para,
        func_auto_trade=orders.auto_trade_leverage, order_para=[multi, percent, my_exchange.bitfinex_instance()],
        symbol=symb+'/USDT',
        interval_time='15m'
        )
