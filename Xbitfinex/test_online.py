from common import k_lines
from domain import my_exchange
from strategy import bulin_K, back_return
from backtest import evaluate

def test_para_online():
    '''
    调参后，在线测试短期收益
    :return:
    '''
    #'x': 360, 'y': 3.0, 'm': 0.01, 'n': 0.0, 'h': 1.028
    #'x': 380, 'y': 3.0, 'm': 0.015, 'n': 0.02, 'h': 100
    #101.1435778634197 {'x': 90, 'y': 4.0, 'm': 0.035, 'n': 0.115, 'h': 1.5359999999999987}XRP
    #4.815276995447291 {'x': 100, 'y': 3.25, 'm': 0.01, 'n': 0.045, 'h': 1.8159999999999985}eth
    #最优： 19.291647830587838 {'x': 148, 'y': 4.800000000000003, 'm': 0.0, 'n': 0.115, 'h': 1.101999999999999}btc
    #{'x': 70, 'y': 5.400000000000004, 'm': 0.0, 'n': 0.045, 'h': 1.101999999999999}btc
    para_now = [90, 3.2, 0.005, 0.015, 1.0, 0.2]
    data = k_lines.get_candle_data(my_exchange.bitfinexV2_instance(), 'ETH/USDT', '15m')

    data.rename(columns={'candle_begin_time_GMT8': 'candle_begin_time'}, inplace=True)
    # 计算交易信号
    df = back_return.BollingAdvanced().signal_bolling(data, para=para_now)
    # 计算资金曲线
    df = evaluate.equity_curve_with_long_and_short(df, leverage_rate=3, c_rate=2.0 / 1000)
    print(para_now, '策略最终收益：', df.iloc[-1]['equity_curve'])

if __name__=='__main__':
    test_para_online()