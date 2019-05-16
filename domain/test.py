import threading
from common.utils import send_mail
import optunity
from common import utils
import pandas as pd

def run_d():
    print('start')
    threading.Thread(target=send_mail, args=('test','xxx')).start()
    print('nihoa ')


if __name__== '__main__':
    # print('!')
    # run_d()
    # print("over")
    all_data = pd.read_hdf('/Users/lensonyuan/gitLocal/every_coin_helps/result/data_EOS_2019_4.h5', key='data')

    optimal_rbf_pars, info, _ = optunity.maximize(lambda x, y: x * y,
                                                  num_evals=500,
                                                  solver_name='particle swarm',
                                                  x=[0, 10],
                                                  y=[-5, 5])  # default: 'particle swarm'

    print(optimal_rbf_pars)
    print(info.optimum)
    df = optunity.call_log2dataframe(info.call_log)
    print(df.sort_values('value', ascending=False)[:10])
