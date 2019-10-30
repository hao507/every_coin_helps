import pandas as pd
from backtest import evaluate
from common import utils
import numpy as np
import warnings
from multiprocessing import Pool, Manager #进程
from multiprocessing.managers import Namespace
from multiprocessing.dummy import Pool as ThreadPool#线程

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)

from strategy import bulin_K


# =====寻找最优参数
def get_data(data_name='bitfinex_dataETHUSD.h5', rule_type='15T'):
    '''
    读取数据
    :return:
    '''
    # 导入数据
    all_data = pd.read_hdf(utils.project_path() + '/data/' + data_name, key='data')
    # 转换数据周期
    all_data = evaluate.transfer_to_period_data(all_data, rule_type)
    # 选取时间段
    all_data = all_data[all_data['candle_begin_time'] >= pd.to_datetime('2017-12-01')]
    all_data = all_data[all_data['candle_begin_time'] < pd.to_datetime('2019-2-01')]
    all_data.reset_index(inplace=True, drop=True)
    return all_data


# 拿取数据
all_data = get_data(data_name='bitfinex_dataETHUSD.h5', rule_type='15T')

manager = Manager()
dic = manager.dict()
dic['curve']= 0.0
dic['space']= []


def BulinParaOptimizer(space):
    '''
    寻参目标：简单参数寻找
    :param x:
    :param y:
    :param m:
    :param n:
    :return:
    '''
    global dic
    x, y, m, n, h = space['x'], space['y'], space['m'], space['n'], space['h']
    para = [x, y, m, n, h]
    # para = [100, 3.25, 0.01, 0.0255,100]
    df = bulin_K.signal_bolling(all_data.copy(), para)
    # 计算资金曲线
    df = evaluate.equity_curve_with_long_and_short(df, leverage_rate=3, c_rate=2.0 / 1000)
    equity_curve = df.iloc[-1]['equity_curve']
    if equity_curve > dic['curve']:
        dic['curve'] = equity_curve
        dic['space'] = space
        #print(dic['curve'],dic['space'])


def soup(para):
    process_pool = Pool()
    process_pool.map_async(BulinParaOptimizer, para)
    process_pool.close()
    process_pool.join()
    print('进程汇总：', dic['curve'], dic['space'])


#224.26199402036414 {'x': 365, 'y': 3.5, 'm': 0.13, 'n': 0.14, 'h': 1.3549999999999989}EOS
#36952.86186159719 {'x': 90, 'y': 3.200000000000002, 'm': 0.005, 'n': 0.015, 'h': 1.7789999999999986}ETH
#最优： 19.291647830587838 {'x': 148, 'y': 4.800000000000003, 'm': 0.0, 'n': 0.115, 'h': 1.101999999999999}BTC
if __name__=='__main__':
    #test
    # spac = {'x': 90, 'y': 4.0, 'm': 0.035, 'n': 0.115, 'h': 1.5359999999999987}
    # BulinParaOptimizer(spac)

    #寻x,y
    s_xy = [{'x': x, 'y': y, 'm': 0, 'n': 0, 'h': 100} for x in np.arange(20, 150, 1) for y in np.arange(1, 7, 0.1)]
    soup(s_xy)
    # 寻m,n
    x, y = dic['space']['x'], dic['space']['y']
    s_xy = [{'x': x, 'y': y, 'm': m, 'n': n, 'h': 100} for m in np.arange(0, 0.3, 0.005) for n in np.arange(0, 0.3, 0.005)]
    soup(s_xy)
    m, n =dic['space']['m'], dic['space']['n']
    #寻优h
    s_xy = [{'x': x, 'y': y, 'm': m, 'n': n, 'h': h} for h in np.arange(0.01, 2, 0.001)]
    soup(s_xy)

    print('最优：', dic['curve'], dic['space'])
    pass


#并行计算
# slice = 100
# s_xy = [sd[slice*i:slice*(i+1)] for i in range(0, sd.__len__()//slice +1, 1)]

# thread_pool =ThreadPool()
# def thread_work(ss):
#     thread_pool.map(BulinParaOptimizer, ss)





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