'''
同一交易所，三种币间的套利
操作okex上的 ETH/USDT EOS/USDT EOS/ETH

'''
from domain import my_exchange
from common.utils import log_exp
import time

exchange = my_exchange.okex_instance()
symbol_p1 = 'ETH/USDT'
symbol_p2 = 'EOS/USDT'
symbol_p3 = 'EOS/ETH'


 #计算是否能套利，假设已有100个ETH
def profits_calculte(eth =100):
    p1 = exchange.fetch_ticker(symbol_p1)['bid']  # 获取ETH/U买一价格
    p2 = exchange.fetch_ticker(symbol_p2)['ask']  # 获取EOS/U卖一价格
    p3 = exchange.fetch_ticker(symbol_p3)['ask']  # 获取EOS/ETH买一价格
    #p3为EOS/ETH，通过p1、p2计算出比例ss
    ss = p2/p1
    #手续费为，挂单0.15%, 吃单0.2%, 收费主体是得到的那种币
    #计算正向手续费
    eos_num = (eth/p3)*(1-0.002) #ETH->EOS 要买入，为吃单
    usd_num = (eos_num*p2) *(1-0.0015) #EOS->USDT，要卖出，为挂单
    eth_100_total_usd = eth/(1-0.002)*p1  #USDT->ETH,要买入，为吃单, 这里只需要买回那100个ETH

    profile = usd_num -eth_100_total_usd #利润
    print('利润为 ',profile)
    if profile > 0:
        log_exp.info('可赚 %s', profile)
    pass

if __name__== '__main__':
    while True:
        profits_calculte(eth=10)
        time.sleep(60*15)
