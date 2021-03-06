import pandas as pd
from backtest import evaluate
from common import utils
import numpy as np
import warnings
from hyperopt.pyll import scope
import math
from hyperopt import fmin, tpe, hp, Trials

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)

from strategy import gmma
from strategy import bulin_K

# =====寻找最优参数
def get_data(data_name='bitfinex_dataETHUSD.h5',rule_type = '15T'):
    '''
    读取数据
    :return:
    '''
    # 导入数据
    all_data = pd.read_hdf(utils.project_path()+'/data/'+data_name, key='data')
    # 转换数据周期
    all_data = evaluate.transfer_to_period_data(all_data, rule_type)
    # 选取时间段
    all_data = all_data[all_data['candle_begin_time'] >= pd.to_datetime('2018-11-01')]
    all_data.reset_index(inplace=True, drop=True)
    return all_data
#拿取数据
all_data = get_data(data_name='bitfinex_dataETHUSD.h5',rule_type = '15T')


def dest_fuc(space):
    '''
    寻参目标：简单参数寻找
    :param x:
    :param y:
    :param m:
    :param n:
    :return:
    '''
    x, y, m, n, h = space['x'], space['y'], space['m'], space['n'], space['h']
    x_ = math.floor(x)
    para = [x_, y, m, n, h]
    #para = [100, 3.25, 0.01, 0.0255,100]
    df = bulin_K.signal_bolling(all_data.copy(), para)
    # 计算资金曲线
    df = evaluate.equity_curve_with_long_and_short(df, leverage_rate=3, c_rate=2.0 / 1000)
    equity_curve =df.iloc[-1]['equity_curve']
    return -equity_curve #求min,故要取反

def para_optimizer(is_test=False):
    '''
    # x=[10, 500],
      # y=[1, 30],
      # m=[0.005,0.1],
      # n=[0.001,0.1],
      #f=[0.001, 1.5]
    :param data:
    :return:
    '''


    space = {
        'x': 10+hp.randint('x', 350),
        'y': hp.uniform('y', 1, 30),
        'm': hp.uniform('m', 0, 0.3),
        'n': hp.uniform('n', 0, 0.3),
        'h': hp.uniform('h', 0.01, 2)
    }
    #trials = Trials()
    #best = fmin(fn=dest_fuc, space=space, algo=tpe.suggest, max_evals=100,trials=trials)
    best = fmin(fn=dest_fuc, space=space, algo=tpe.suggest, max_evals=10000)
    print(best['x'], best['y'], best['m'], best['n'], best['h'])
    # for trial in trials.trials[:2]:
    #     print(trial)


if __name__ == '__main__':
    para_optimizer()


'''
bulin：
BTC[[425, 1.75]  9.220954e+01]
EOS[[475, 3.5]   2.958260e+01]
ETH[[100, 3.25]  8.258343e+03]

bulin_K:
BTC[[425, 1.75, 0.058]   1.311452e+02]
ETH[[100, 3.25, 0.01]   15956.918983]  
ETH[[100, 3.25, 0.01,0.0255 ]   35064.8015] 
ETH_5:[275, 3.25, 0.008]  3927
eth[395,3.155035,0.061513,0.026644,1.008809] <19.151917>

boll_kdj:
EOS[[475, 3.5, 5, 0.01152]    9.806154]
'''



'''
    # 构建参数候选组合 bulin
    m_list = np.arange(10, 500, 5)
    n_list = np.arange(1, 30, 0.5)
    #bulin_k
    h_list = np.arange(1,10, 1)
    k_list = np.arange(0.01,2, 0.005)
    #测试参数
    # para = [425, 1.75, 5, 2]
    # n_list=m_list=[1]

    # 遍历所有参数组合
    rtn = pd.DataFrame()
    # for m in m_list:
    #     for n in n_list:
    #         for h in h_list:
    for k in k_list:
        para = [100, 3.25, 0.01, 0.0255, k]#[3,30,3,5]
        # 计算交易信号
        df = bulin.signal_bolling(all_data.copy(),para)
        # 计算资金曲线
        df = evaluate.equity_curve_with_long_and_short(df, leverage_rate=3, c_rate=2.0 / 1000)
        print(para, '策略最终收益：', df.iloc[-1]['equity_curve'])
        # utils.file_obj_convert(fileName='data_ETH.df',obj=df)
        # 存储数据
        rtn.loc[str(para), '收益'] = df.iloc[-1]['equity_curve']

    print(rtn.sort_values(by='收益', ascending=True))
'''