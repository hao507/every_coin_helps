
def ZigZag(df, Depth =12):
    '''

    :param extDepth: #用于设置高低点是相对与过去多少个Bars
    :param extDeviation: #用于设置重新计算高低点时，与前一高低点的相对点差
    :param extBackstep: #用于设置回退计算的Bars的个数。
    :return:
    '''

    def __apply_calcute(x):
        '''
        计算当前窗口的低点
        :param x:
        :return:
        '''
        c_min = min(x)  # 当前最值
        c_max = max(x)
        if x[-1] == c_min:
            return -1
        elif x[-1] == c_max:
            return 1
        else:
            return 0

    df['zigzag_tmp'] = df['close'].rolling(Depth,min_periods=Depth).apply(__apply_calcute)
    df['zigzag_tmp'].fillna(value=0, inplace=True)
    #移除前面紧邻的拐点
    temp = df[df['zigzag_tmp'].shift(-1)==df['zigzag_tmp']]
    df['zigzag'] =df['zigzag_tmp']-temp['zigzag_tmp']
    df['zigzag'].fillna(value=df['zigzag_tmp'],inplace= True)
    df.drop(['zigzag_tmp'], axis=1, inplace=True)
    for e in rolling_df(df.head(10)):
        print(e)
        print('\n')
    return df

def rolling_df(df,windows=3):
    '''
    对pandans进行滑动窗口生成数据
    :param df:
    :param windows:
    :return:
    '''
    for i in range(0, len(df)):
        result =df.iloc[i:i+windows]
        yield result