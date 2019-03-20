'''
定期保存数据，补充历史回测数据
'''
from common import k_lines
from domain import my_exchange
from strategy import bulin_K
from backtest import evaluate



def test_para_online(data_now,para_now):
    '''
    调参后，在线测试短期收益
    :param data_now:
    :param para_now:
    :return:
    '''
    # 计算交易信号
    df = bulin_K.signal_bolling(data_now.copy(), para_now)
    # 计算资金曲线
    df = evaluate.equity_curve_with_long_and_short(df, leverage_rate=3, c_rate=2.0 / 1000)
    print(para_now, '策略最终收益：', df.iloc[-1]['equity_curve'])

if __name__=='__main__':
    data = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(),'ETH/USDT','15m')
    data.rename(columns={'candle_begin_time_GMT8':'candle_begin_time'},inplace=True)
    test_para_online(data, [100, 3.25, 0.01,0] )#0.0255
    pass