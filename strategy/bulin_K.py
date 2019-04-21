
from common import utils
import numpy as np
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)

'''
通过判断布林上下轨，改成判断%b指标，从而多了一个参数th，控制穿过的阈值，同时防止插针K线出现的信号
'''
def signal_bolling(df, para=[100, 2, 0, 0, 1.5]):
    """
    布林线中轨：n天收盘价的移动平均线
    布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
    布林线下轨：n天收盘价的移动平均线 - m * n天收盘价的标准差
    %b值 = (收盘价−布林带下轨值) ÷ (布林带上轨值−布林带下轨值)
    带宽指标值 = (布林带上轨值−布林带下轨值) ÷布林带中轨值

    :param df:  原始数据
    :param para:  参数，[n, m, th,th2], n天均线；m倍自由差；th为阈值，为0时，为标准简单布林; th2为距离中线的阈值；
                th3为#突变穿越上下轨时，该时刻的收盘价与开盘价差占该线的比例值，设置成100以上可以取消该条件.该参数主要防止插针导致的购买信号
    :return:
    """

    # ===计算指标
    n = para[0]
    m = para[1]
    th= para[2]#0时即为简单布林，为穿越上下线
    th2=para[3]#0时即为穿越中线
    th3 = para[4] #突变穿越上下轨时，该时刻的收盘价与开盘价差占该线的比例值

    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean() #n日的均值

    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度,默认为1
    df['upper'] = df['median'] + m * df['std'] #m倍的自由差
    df['lower'] = df['median'] - m * df['std']

    #计算%b
    df['bbPb'] = (df['close']- df['lower'])/(df['upper']-df['lower'])


    # ===找出做多信号
    # k线由下而上穿越（中线+偏移）
    condition1 = df['bbPb'] > (1-th) # 当前K线的收盘价 > %b线的0.6,  0.5为中线,1为上轨，0为下轨
    condition2 = df['bbPb'].shift(1) <= (1-th)  # 前一刻K线的收盘价 <= （中线+偏移）
    condition3 = ((df['close']-df['open'])/(df['upper']-df['median'])) < th3 #穿越必须是慢动作，而不能突变太快
    df.loc[condition1 & condition2 & condition3 , 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # ===找出做多平仓信号
    condition1 = df['bbPb'] < 0.5+th2
    condition2 = df['bbPb'].shift(1) >= 0.5+th2
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # ===找出做空信号
    condition1 = df['bbPb'] < (0+th)
    condition2 = df['bbPb'].shift(1) >= (0+th)
    condition3 = ((df['open'] - df['close']) / (df['median']-df['lower'])) < th3
    df.loc[condition1 & condition2 & condition3, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # ===找出做空平仓信号
    condition1 = df['bbPb'] > 0.5+th2
    condition2 = df['bbPb'].shift(1) <= 0.5+th2
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # ===合并做多做空信号，去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)  # 若pandas版本是最新的，请使用本行代码代替上面一行

    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']
    df.drop(['median', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # ===由signal计算出实际的每天持有仓位
    # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
    df['pos'] = df['signal'].shift()
    df['pos'].fillna(method='ffill', inplace=True)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

    return df
