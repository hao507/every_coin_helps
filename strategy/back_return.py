
from common import utils
import numpy as np
import math
from common.utils import logger
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


class BollingAdvanced:
    """
    1. 通过判断布林上下轨，改成判断%b指标，从而多了一个参数th，控制穿过的阈值，同时防止插针K线出现的信号
    2. 如果插针太严重，肯定会反弹，故反弹选择穿越上轨却做空的思路
    3. 根据同参数每日的情况，来确定开口大小和方向，由此确定开单倍数
    """
    def __init__(self):
        """
                       布林线中轨：n天收盘价的移动平均线
                       布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
                       布林线下轨：n天收盘价的移动平均线 - m * n天收盘价的标准差
                       %b值 = (收盘价−布林带下轨值) ÷ (布林带上轨值−布林带下轨值)
                       带宽指标值 = (布林带上轨值−布林带下轨值) ÷布林带中轨值

                       :param para:  参数，[n, m, th,th2], n天均线；m倍自由差；th为阈值，为0时，为标准简单布林; th2为距离中线的阈值；
                                   th3为#突变穿越上下轨时，该时刻的收盘价与开盘价差占该线的比例值，设置成100以上可以取消该条件.该参数主要防止插针导致的购买信号
                       :return:
                       """
        # ===计算指标
        self.n = 0  # n天移动均线
        self.m = 0  # m倍自由差
        self.th = 0  # 穿越上下线的偏差控制；0为下线，1为上线
        self.th2 = 0  # 中线的偏差控制；0时即为穿越中线 偏差控制在0.001
        self.th3 = 0  # 突变穿越上下轨时，该时刻的柱线和影线的最大差占该线的比例值
        self.th4 = 0  # 止损跌幅阈值
        self.df = None # 处理数据源

    def set_para(self, para):
        # ===计算指标
        self.n = math.floor(para[0])
        self.m = para[1]
        self.th = para[2]
        self.th2 = para[3]
        self.th3 = para[4]
        self.th4 = para[5]
        self.df = None

    def signal_bolling(self, df_source, para=[91, 2.9, 0, 0.055, 1.984, 0.3]):
        self.set_para(para)
        self.df = df_source.copy(deep=True) # 使用副本进行操作
        # 计算均线
        self.df['median'] = self.df['close'].rolling(self.n, min_periods=1).mean() #n日的均值

        # 计算上轨、下轨道
        self.df['std'] = self.df['close'].rolling(self.n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度,默认为1
        self.df['upper'] = self.df['median'] + self.m * self.df['std']  # m倍的自由差
        self.df['lower'] = self.df['median'] - self.m * self.df['std']

        # 计算带宽%b
        self.df['bbPb'] = (self.df['close']- self.df['lower'])/(self.df['upper']-self.df['lower'])  # 0.5为中线,1为上轨，0为下轨

        # 计算开仓位置
        self.judge_buy(df_buy=self.df)

        # 计算平仓位置
        self.judge_sell(df_sell=self.df)

        # 一些其他处理
        self.df['signal_sell'].fillna(value=0, inplace=True, downcast='infer')
        '''
        # 测试：重载数据
        # self.df.to_excel(utils.project_path() + '/excel_output02.xls', sheet_name='biu02')  # 保存分析
        self.df = pd.read_excel(utils.project_path() + '/excel_output02.xls', sheet_name='biu02')
        '''
        # 合并买卖信号
        self.df['signal_source'] = self.df['signal_buy']+self.df['signal_sell']
        self.df.loc[self.df['signal_sell'] != 0, 'signal_source'] = self.df['signal_sell']
        # 剔除重复信号
        signal_sell = self.df.loc[(self.df['signal_source'] >= 10) | (self.df['signal_source'] <= -10)].index.values.tolist()
        flag = 0  # 标记末尾是不是平仓信号
        if not (self.df.tail(1)['signal_source'].values[0] >= 10 or self.df.tail(1)['signal_source'].values[0] <= -10):  # 最后一个不是平仓信号
            flag = 1
            signal_sell.append(self.df.tail(1).index.values[0])  # 尾部作为平仓信号，去筛选一个买入信号
        for i in range(len(signal_sell)):
            it = signal_sell[i]
            if i == 0:
                it_before = 0
            else:
                it_before = signal_sell[i-1]

            val = self.df.iloc[it]['signal_source']
            if flag == 1 and i == (len(signal_sell)-1): # 最后一个元素
                buy_s = self.df.loc[(it_before < self.df['signal_source'].index) & (self.df['signal_source'].index < it)].loc[((self.df['signal_source'] > -10) | (self.df['signal_source'] < 10)) & (self.df['signal_source'] != 0)]['signal_source']
                if len(buy_s) != 0:
                    # 清空其他信号
                    buy_min = min(buy_s.index.values.tolist())
                    self.df.loc[(buy_min < self.df['signal_source'].index) & (self.df['signal_source'].index < it), 'signal_source'] = 0
            else:  # 常规
                buy_val = int(str(val)[:-1])
                buy_s = self.df.loc[(it_before < self.df['signal_source'].index) & (self.df['signal_source'].index < it)].loc[self.df['signal_source'] == buy_val]['signal_source']
                if len(buy_s) != 0:
                    # 清空其他信号
                    buy_min = min(buy_s.index.values.tolist())
                    self.df.loc[(buy_min < self.df['signal_source'].index) & (self.df['signal_source'].index < it), 'signal_source'] = 0
            pass

        self.df.loc[self.df['signal_source'] == 0, 'signal_source'] = np.NaN

        self.df.loc[(self.df['signal_source'] > 0) & (self.df['signal_source'] < 10), 'signal'] = 1
        self.df.loc[(self.df['signal_source'] < 0) & (self.df['signal_source'] > -10), 'signal'] = -1
        self.df.loc[(self.df['signal_source'] >= 10) | (self.df['signal_source'] <= -10), 'signal'] = 0
        # ===由signal计算出实际的每天持有仓位
        # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
        self.df['pos'] = self.df['signal'].shift()
        self.df['pos'].fillna(method='ffill', inplace=True)
        self.df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0
        # 保存分析
        # self.df.to_excel(utils.project_path() + '/excel_output05.xls', sheet_name='biu')
        # 精简表
        self.df.drop(['median', 'std', 'upper', 'lower', 'bbPb'], axis=1, inplace=True)
        return self.df

    def judge_buy(self, df_buy):
        # df_buy = df_in.copy(deep=True) # 使用副本进行操作
        df_buy['signal_buy'] = 0
        # ===找出做多信号
        # k线由下而上穿越（上线-偏移）; 慢穿越
        condition1 = df_buy['bbPb'] > (1 - self.th)  # 当前K线的收盘价 > %b线的0.6,  0.5为中线,1为上轨，0为下轨
        condition2 = df_buy['bbPb'].shift(1) <= (1 - self.th)  # 前一刻K线的收盘价 <= （中线+偏移）
        condition3 = ((df_buy['high'] - df_buy['open']) / (df_buy['upper'] - df_buy['median'])) < self.th3  # 穿越必须是慢动作，而不能突变太快
        df_buy.loc[condition1 & condition2 & condition3, 'signal_buy'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

        # ***** k线由下而上穿越（上线+偏移）; 快穿越 反向做空*****
        df_buy.loc[condition1 & condition2 & (~condition3), 'signal_buy'] = -2  # 将产生做多信号的那根K线的signal设置为-2，-2代表做空2类

        # 找出做空信号
        condition1 = df_buy['bbPb'] < (0 + self.th)
        condition2 = df_buy['bbPb'].shift(1) >= (0 + self.th)
        condition3 = ((df_buy['open'] - df_buy['low']) / (df_buy['upper'] - df_buy['median'])) < self.th3
        df_buy.loc[condition1 & condition2 & condition3, 'signal_buy'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空
        # ***** k线由上而下穿越（下线+偏移）; 快穿越 反向做多*****
        df_buy.loc[(condition1 & condition2 & (~condition3)), 'signal_buy'] = 2  # 做多2类
        pass
        # df_buy.to_excel(utils.project_path()+'/excel_output.xls', sheet_name='biubiu')# 保存分析

    def judge_sell(self, df_sell):
        df_copy = df_sell.copy(deep=True)  # 深度备份买入信号, 用于遍历和查询。
        state = (0, 0, 0)  # 下单状态 0无1多-1空 【前一持仓状态】[index, 空/多，平]

        for index, row in df_copy.iterrows():
            if index == 0:  # 略过第一维度
                continue

            if row['signal_buy'] == 0: # row['signal_buy'] 只代表穿越信号导致的下单状态
                state = self.__sell_find(flag=0, index=index, df_copy=df_copy, df_sell=df_sell, state=state)
                pass

            elif row['signal_buy'] < 0:
                if state[1] == 0:  # 做空信号，并且当前已无仓
                    state = (index, row['signal_buy'], 0)
                else:
                    # 有买信号，但是持仓。这帧数据一样要考虑平仓
                    state = self.__sell_find(flag=-1, index=index, df_copy=df_copy, df_sell=df_sell, state=state)

            elif row['signal_buy'] > 0:
                if state[1] == 0:  # 做多信号，并且当前已无仓
                    state = (index, row['signal_buy'], 0)
                else:
                    state = self.__sell_find(flag=1, index=index, df_copy=df_copy, df_sell=df_sell, state=state)

    def __sell_find(self, flag, index, df_copy, df_sell, state):
        """
        对当前index帧数据执行判定； 【1.无信号、持仓未知，看是否要平仓；2. 有信号、有持仓，看是否要平仓】时，会被执行此函数
        :param index: 传值
        :param df_copy: 引用，直接改变原来dataframe；复制表，辅助循环和查询
        :param df_sell: 引用，直接改变原来dataframe；原始表，修改数据
        :param state: 传值
        :return: state
        """
        if state[1] == -1:  # 有持空仓
            if flag == 0: # 当前无信号
                # ===找出中线平仓信号
                if (df_copy.loc[index, 'bbPb'] > (0.5 + self.th2)) and (df_copy.loc[index - 1, 'bbPb'] <= (0.5 + self.th2)):
                    df_sell.loc[index, 'signal_sell'] = -10
                    state = (0, 0, -10)  # 平仓掉了之前的状态
            elif flag == -1 or flag == 2: # 依然是做空，则继续
                logger.debug('持空仓信号为%d,当前信号为%d, 继续做空！', state[1], flag)
            elif flag == -2:
                logger.error('持有空仓；由下而上快穿越上线，反向做空信号。该信号不存在，因为中线附近已平仓，请检查！')

        elif state[1] == 1:  # 持多仓
            if flag == 0:
                # ===找出做多中线平仓信号
                if (df_copy.loc[index, 'bbPb'] < (0.5 - self.th2)) and (df_copy.loc[index - 1, 'bbPb'] >= (0.5 - self.th2)):
                    df_sell.loc[index, 'signal_sell'] = 10
                    state = (0, 0, 10)  # 平仓掉了之前的状态
            elif flag == 1 or flag == -2:  # 依然是做多，则继续 【-2本质还是穿越上线】
                logger.debug('持多仓信号为%d,当前信号为%d, 继续做多！', state[1], flag)
            elif flag == 2:
                logger.error('持有多仓；由上而下快穿越下线，反向做多信号。该信号不存在，因为中线附近已平仓，请检查！')

        elif state[1] == 2:  # 持仓状态为2
            if flag == 0 or flag == -1 or flag == 2:
                # ===止损：跌幅达到一定量就平
                if ((df_copy.loc[index, 'close'] - df_copy.loc[state[0], 'close'])/df_copy.loc[state[0], 'close']) < -self.th4:
                    df_sell.loc[index, 'signal_sell'] = 20
                    state = (0, 0, 20)  # 平仓掉了之前的状态
                else:  # 智能止盈，由上往下穿越中线并达到波动量则平仓
                    if (df_copy.loc[index, 'bbPb'] >= 0.5) and (df_copy.loc[index - 1, 'bbPb'] < 0.5):
                        df_sell.loc[index, 'signal_sell'] = 20
                        state = (0, 0, 20)  # 平仓掉了之前的状态
            elif flag == -2 or flag == 1: # 【穿越下线的两种形态】
                logger.debug('持多仓信号为%d,当前信号为%d, 继续做多！', state[1], flag)

        elif state[1] == -2:  # 迁移状态为-2
            if flag == 0 or flag == 1 or flag == -2:
                # ===止损：涨幅达到一定量就平
                if ((df_copy.loc[index, 'close'] - df_copy.loc[state[0], 'close']) / df_copy.loc[state[0], 'close']) > self.th4:
                    df_sell.loc[index, 'signal_sell'] = -20
                    state = (0, 0, -20)  # 平仓掉了之前的状态
                else:  # 智能止盈，由下往上穿越中线并达到波动量则平仓
                    if (df_copy.loc[index, 'bbPb'] <= 0.5) and (df_copy.loc[index - 1, 'bbPb'] > 0.5):
                        df_sell.loc[index, 'signal_sell'] = -20
                        state = (0, 0, -20)  # 平仓掉了之前的状态
            elif flag == 2 or flag == -1:  # 【穿越下线的两种形态】
                logger.debug('持空仓信号为%d,当前信号为%d, 继续做空！', state[1], flag)
            pass

        return state


if __name__=='__main__':
    para_now = [90, 3.2, 0.04, 0.05, 1.4, 0.15]
    data = pd.read_excel(utils.project_path()+'/excel_output.xls', sheet_name='src')
    # 计算交易信号
    ins = BollingAdvanced()
    df = ins.signal_bolling(data,para=para_now)
    pass
