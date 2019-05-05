'''
定期保存数据，补充历史回测数据
'''
from common import k_lines
from domain import my_exchange
import threading
from datetime import datetime as dt
import pandas as pd
import copy
from common import utils


doTime = pd.datetime.today().date()  # 记录当前日期
execF = False

eos_df = pd.DataFrame()
eth_df = pd.DataFrame()
btc_df = pd.DataFrame()
ltc_df = pd.DataFrame()
xrp_df = pd.DataFrame()

def get_last_2days_data(temp):
    global doTime
    #获取前两日的历史5min数据
    data_tmp = temp[temp['candle_begin_time_GMT8'] < pd.Timestamp(doTime - pd.Timedelta(days=0))]
    data_2day = data_tmp[data_tmp['candle_begin_time_GMT8'] >= pd.Timestamp(doTime-pd.Timedelta(days=2))]
    return data_2day

def execTask():
    global eos_df, eth_df, btc_df, ltc_df, xrp_df
    # 具体任务执行内容
    data_EOS = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(), 'EOS/USDT', '5m')
    eos_d = get_last_2days_data(data_EOS)
    eos_df = data_merge_2_file(eos_d,eos_df,path='/result/data_EOS.h5')
    '''
    data_ETH = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(), 'ETH/USDT', '5m')
    eth_d = get_last_2days_data(data_ETH)
    eth_df = data_merge_2_file(eth_d,eth_df, path='/result/data_ETH.h5')
    '''
    '''
    data_BTC = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(), 'BTC/USDT', '5m')

    data_LTC = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(), 'LTC/USDT', '5m')
    data_XRP = k_lines.__get_candle_data(my_exchange.bitfinexV2_instance(), 'XRP/USDT', '5m')
    '''
    utils.logger.info('操作执行结束')

def write_2_file_hdf5(kData,path='/result/default.h5'):
    '''
    读写h5文件
    :param kData:df
    :param path:
    :param is_read:
    :return:
    '''
    path_t = utils.project_path()+path
    # HDF5的写入：
    # 压缩格式存储
    h5 = pd.HDFStore(path_t, 'w', complevel=4, complib='blosc')
    h5['data'] = kData
    h5.close()
    utils.logger.info('写入完成')


def data_merge_2_file(df,global_df, path='/result/data_xrp.h5'):
    '''
    按月保存数据，并执行缓存清空操作
    :return:
    '''
    current_t = pd.datetime.today().date() # 记录当前日期
    if current_t.day==1: #月份首日
        _month = current_t.month
        if _month ==1:
            path_s = path[:-2]+str(current_t.year-1)+'_12'+path[-2:0]
        else:
            path_s = path[:-3] +'_'+ str(current_t.year) + '_' + str(_month - 1) + path[-3:]
        #保存
        write_2_file_hdf5(df,path_s)
        #清空
        df.drop(df.index,inplace=True)

    else:
        #进行合并操作
        if global_df.empty:
            global_df = copy.deepcopy(df)
        else:
            global_df = global_df.append(df)

        df.drop(df.index, inplace=True)
        global_df.reset_index(inplace=True, drop=True)
        return global_df



def timerTask():
    global execF
    global doTime
    if execF is False:
        execTask()  # 判断任务是否执行过，没有执行就执行
        execF = True
        utils.logger.info("定时器执行时间：%s" ,dt.now().strftime("%Y-%m-%d %H:%M:%S"))
    else:  # 任务执行过，判断时间是否过了三天。如果是就执行任务
        desTime = pd.datetime.today().date()
        if desTime > doTime+ pd.Timedelta(days=3) or desTime.day==1 :
            execF = False  # 任务执行执行置值为
            doTime = desTime

    timer = threading.Timer(3, timerTask)#递归嵌套等待s
    timer.start()



if __name__ == "__main__":
    timer = threading.Timer(3, timerTask)
    timer.start()



