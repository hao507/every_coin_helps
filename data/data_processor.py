
import pandas as pd
from common import utils


if __name__=='__main__':
    all_data = pd.read_hdf(utils.project_path()+'/data/next/bitfinex_dataXRPUSD.h5')
    #temp_data = pd.read_hdf(utils.project_path()+'/data/bitfinex_dataETH.h5')
    all_data.rename(columns={'开盘时间':'candle_begin_time', '开盘价':'open','最高价':'high','最低价':'low','收盘价':'close', '交易数量':'volume'},inplace=True)
    all_data.drop(['交易品种'],axis=1,inplace=True)
    all_data.reset_index(inplace=True, drop=True)
    # 压缩格式存储
    h5 = pd.HDFStore(utils.project_path()+'/data/bitfinex_dataXRPUSD.h5', 'w', complevel=4, complib='blosc')
    h5['data'] = all_data
    h5.close()
    pass
