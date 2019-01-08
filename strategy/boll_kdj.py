
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


# ===布林线策略
'''
基本稳赚不亏，但是收益不高，命中率低，不太依靠历史数据的形态  注：此策略有问题，反复买卖
参数：
para=EOS/USDT [475, 3.5, 5, 0.01152]
'''
def signal_bolling_kdj(df, para=[100, 2, 5, 10]):
    """
    布林线中轨：n天收盘价的移动平均线
    布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
    布林线上轨：n天收盘价的移动平均线 - m * n天收盘价的标准差

    在一段时间内的波幅很小，反映在布林线上表现位，股价波幅带长期收窄，
    而在某一个交易日，股价在较大的交易量的配合下收盘价突破布林线的阻力线，
    这个时候的布林线就会有收口明显的转为开口，是买入的操作信号，
    因为这个时候股价从弱势转为强势运行，短期内上冲的动力是具有一定的持续性的，短线必然会有新高出现
    :param df:  原始数据
    :param para:  参数，[n, m]
    :return:
    """

    # ===计算指标
    n = para[0]
    m = para[1]
    n_days = para[2] #上下线差值的几日均值作为分析
    threshold = para[3] #

    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean() #n日的均值

    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度
    df['upper'] = df['median'] + m * df['std'] #m倍的自由差
    df['lower'] = df['median'] - m * df['std']


    df['diff_ul'] =df['upper']-df['lower'] #上下线差值
    df['diff_mean'] = df['diff_ul'].rolling(n_days,min_periods=1).mean()
    #生成判定指标
    def apply_calcute(x):
        mean_tmp =x.mean()
        if x[-1] -mean_tmp < threshold:
            return 0
        else:
            return 1 #最后一个异军突起

    df['singal_great_change'] = df['diff_ul'].rolling(n_days,min_periods=1).apply(apply_calcute,raw=True)
    #把上下轨道与收盘价关系标出
    df.loc[df['close'] > df['upper'], 'through'] = 1
    df.loc[df['close'] < df['lower'], 'through'] = -1
    df['through'].fillna(value=0, inplace=True)


    # ===找出做多信号
    #在来到great_change信号，且附近有穿越上轨的情况
    condition1_0 = df['through'].shift(1) == 1
    condition1_1 = df['through'].shift(2) == 1
    condition1_2 = df['through'].shift(3) == 1
    condition1_3 = df['through'].shift(4) == 1
    condition1_4 = df['through'].shift(5) == 1

    condition3 = df['singal_great_change'].shift(1)==0 #通道宽度突变0-1
    condition4 = df['singal_great_change'] == 1
    #穿越上轨道
    df.loc[(condition1_0 | condition1_1 | condition1_2 | condition1_3 | condition1_4) & condition3 & condition4, 'signal'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多
    # 或者 因through下一刻才有穿过上轨，0-1-1时，出现through=1
    condition5 = df['singal_great_change'].shift(2) == 0
    condition6 = df['singal_great_change'].shift(1) == 1
    condition7 = df['through'] == 1

    df.loc[~(condition1_0 | condition1_1 | condition1_2 | condition1_3 | condition1_4) & condition4 & condition5 & condition6 & condition7, 'signal'] = 1

    # ===找出平仓信号
    #通道变宽信号由1变为0时即可
    condition1 = df['singal_great_change'] == 0
    condition2 = df['singal_great_change'].shift(1) == 1  # 通道宽度突变1-0
    df.loc[condition1 & condition2, 'signal'] = 0  # 将产生平仓信号当天的signal设置为10，0代表平仓

    # ===找出做空信号
    # 在来到great_change信号，且附近有穿越下轨的情况
    condition1_0 = df['through'].shift(1) == -1
    condition1_1 = df['through'].shift(2) == -1
    condition1_2 = df['through'].shift(3) == -1
    condition1_3 = df['through'].shift(4) == -1
    condition1_4 = df['through'].shift(5) == -1

    condition3 = df['singal_great_change'].shift(1) == 0  # 通道宽度突变0-1
    condition4 = df['singal_great_change'] == 1

    df.loc[(condition1_0 | condition1_1 | condition1_2 | condition1_3 | condition1_4) & condition3 & condition4, 'signal'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空
    #或者 因through下一刻才有穿过下轨，0-1-1时，出现through=-1
    condition5 = df['singal_great_change'].shift(2) == 0
    condition6 = df['singal_great_change'].shift(1) == 1
    condition7 =df['through'] == -1
    df.loc[~(condition1_0 | condition1_1 | condition1_2 | condition1_3 | condition1_4) & condition4 & condition4 & condition5 & condition6 &condition7, 'signal'] = -1

    #是除去重复信号么？
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['median', 'std', 'upper', 'lower', 'diff_ul','through', 'singal_great_change','diff_mean'], axis=1, inplace=True)

    # ===由signal计算出实际的每天持有仓位
    # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
    df['pos'] = df['signal'].shift(1)
    df['pos'].fillna(method='ffill', inplace=True)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

    return df
