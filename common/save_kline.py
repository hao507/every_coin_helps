'''
定期保存数据，补充历史回测数据
'''
from common import k_lines
from domain import my_exchange
if __name__=='__main__':

    data = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(),'BTC/USDT','15m')

    pass