'''
布林线+带宽指标+%b指标
'''

from common import utils
import numpy as np
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


# ===布林线策略
'''
借助%b指标得到超买超卖的信号，然后由bbw指标研判开口大小
'''
def signal_bolling(df, para=[100, 2, 0.1]):
    """
    布林线中轨：n天收盘价的移动平均线
    布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
    布林线下轨：n天收盘价的移动平均线 - m * n天收盘价的标准差
    %b值 = (收盘价−布林带下轨值) ÷ (布林带上轨值−布林带下轨值)
    带宽指标值 = (布林带上轨值−布林带下轨值) ÷布林带中轨值
    乖离率=[(当日收盘价-N日平均价)/N日平均价]*100% ；其中N，一般5、6、10、12、24、30和72。在实际运用中，短线使用6日乖离率较为有效，中线则放大为10日或12日。
    :param df:  原始数据
    :param para:  参数，[n, m]
    :return:
    """

    # ===计算指标
    n = para[0]
    m = para[1]
    th= para[2]
    bias_th = 6
    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean() #n日的均值

    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度,默认为1
    df['upper'] = df['median'] + m * df['std'] #m倍的自由差
    df['lower'] = df['median'] - m * df['std']

    #计算带宽、%b
    df['bbw'] = (df['upper'] - df['lower'])/df['median']#上下轨间距占中线的比重
    df['bbPb'] = (df['close']- df['lower'])/(df['upper']-df['lower'])

    #乖离率,表示股价偏离趋向指标的百分比值。
    df['bias_mean'] = df['close'].rolling(bias_th,min_periods=1).mean()
    df['bias'] = (df['close']- df['bias_mean'])/df['bias_mean']


    # ===找出做多信号
    # k线由下而上穿越（中线+偏移）
    condition1 = df['bbPb'] > (1-th) # 当前K线的收盘价 > %b线的0.6,  0.5为中线
    condition2 = df['bbPb'].shift(1) <= (1-th)  # 前一刻K线的收盘价 <= （中线+偏移）

    df.loc[condition1 & condition2 , 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # ===找出做多平仓信号
    condition1 = df['bbPb'] < 0.5
    condition2 = df['bbPb'].shift(1) >= 0.5
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # ===找出做空信号
    condition1 = df['bbPb'] < (0+th)
    condition2 = df['bbPb'].shift(1) >= (0+th)
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # ===找出做空平仓信号
    condition1 = df['bbPb'] > 0.5
    condition2 = df['bbPb'].shift(1) <= 0.5
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # ===合并做多做空信号，去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)  # 若pandas版本是最新的，请使用本行代码代替上面一行

    #连着同一个信号，则只留上一个，防止出现-1信号后来个-1
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
