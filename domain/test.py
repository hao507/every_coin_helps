import threading
from common.utils import send_mail
import optunity


def run_d():
    print('start')
    threading.Thread(target=send_mail, args=('test','xxx')).start()
    print('nihoa ')


if __name__== '__main__':
    # print('!')
    # run_d()
    # print("over")

    optimal_rbf_pars, info, _ = optunity.maximize(lambda x, y: x * y,
                                                  num_evals=500,
                                                  solver_name='particle swarm',
                                                  x=[0, 10],
                                                  y=[-5, 5])  # default: 'particle swarm'

    print(optimal_rbf_pars)
    print(info.optimum)
    df = optunity.call_log2dataframe(info.call_log)
    print(df.sort_values('value', ascending=False)[:10])
