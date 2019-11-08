import threading
import time
import pandas as pd
from common.utils import logger
from common.utils import send_mail
from datetime import datetime
from common import dao

__sqlite = dao.sqlite_cache

def place_order_bitfinex(exchange, order_type, buy_or_sell, symbol, price, amount,comment='下单', record = {'multiple':'0', 'profit':'0', 'profit_percent':'0','signal':'无', 'account':'0'}):
    """
    下单
    :param exchange: 交易所
    :param order_type: limit, market
    :param buy_or_sell: buy, sell
    :param symbol: 买卖品种
    :param price: 当market订单的时候，price无效
    :param amount: 买卖量
    :return:
    """
    logger.info('下单 order_type： %s, buy_or_sell： %s, symbol： %s, price： %s, amount： %s', order_type, buy_or_sell, symbol, price, amount)

    content_txt = '执行时间：' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n持仓情况(损益，损益百分比)：'+comment+'\n 执行参数（价格，数量）：'+str(price)+'，'+str(amount)
    logger.info('邮件正文：%s', content_txt)
    threading.Thread(target=send_mail, args=(buy_or_sell+' '+symbol, content_txt)).start()

    # 记录数据到sqlite
    record_type = str(symbol) # ETH
    trade_signal = record['signal'] #'做空/做多/平仓'
    trade_multiple = record['multiple'] # 倍数
    trade_amount = str(amount) # 量
    trade_profit=record['profit']  # 损益
    trade_profit_percent=record['profit_percent'] # 损益比
    account = record['account'] # 账户余额

    sql = "INSERT INTO history_cache(record_type, trade_signal, trade_multiple, trade_amount, trade_profit, trade_profit_percent, account) VALUES('"\
          +record_type+"', '"+trade_signal+"', '"+trade_multiple+"', '"+trade_amount+"', '"+trade_profit+"', '"+trade_profit_percent+"', '"+account+"')"
    __sqlite.ExecNonQuery(sql)

    order_info = None

    for i in range(5):

        try:
            # 限价单
            if order_type == 'limit':
                # 买
                if buy_or_sell == 'buy':
                    order_info = exchange.create_limit_buy_order(symbol, amount, price, {'type': 'limit'})  # 买单
                # 卖
                elif buy_or_sell == 'sell':
                    order_info = exchange.create_limit_sell_order(symbol, amount, price, {'type': 'limit'})  # 卖单
            # 市价单
            elif order_type == 'market':
                # 买
                if buy_or_sell == 'buy':
                    order_info = exchange.create_market_buy_order(symbol, amount, {'type': 'market'})  # 买单
                # 卖
                elif buy_or_sell == 'sell':
                    order_info = exchange.create_market_sell_order(symbol, amount, {'type': 'market'})  # 卖单
            else:
                pass


            logger.info('下单信息：%s', order_info)
            return order_info

        except Exception as e:
            logger.error('下单报错，1s后重试%s', e)
            time.sleep(1)

    logger.error('下单报错次数过多，程序终止')
    threading.Thread(target=send_mail, args=('下单报错次数过多，程序终止','failed order, time:'+datetime.now().strftime("%Y-%m-%d %H:%M:%S"))).start()
    exit()


def __get_position(exchange):
    """
    查询持仓信息
    :param exchange:
    :return:
    """
    for i in range(5):
        try:
            position = exchange.private_post_auth_r_positions()
            return position

        except Exception as e:
            logger.info('下单查询持仓报错%s', e)
            time.sleep(10)

    logger.error('下单查询多次报错')

# bitfinex合约下单函数
def auto_trade_leverage(exchange_v2, symbol, signal,signal_before, para = list()):
    leverage = para[0] # 杠杆倍数，最高3.3倍
    position_pct = para[1]  # 持仓比重
    exchange_v1 = para[2] #操作资产的exchange
    base_coin = symbol.split('/')[-1]
    trade_coin = symbol.split('/')[0]
    # 对symbol进行命名统一
    if base_coin == 'USDT':
        symbol_temp = 't' + symbol.split('/')[0] + symbol.split('/')[1][:-1]
    if base_coin == 'BTC':
        symbol_temp = 't' + symbol.split('/')[0] + symbol.split('/')[1]

    # 获取仓位信息，需要有仓位才能获取，不然是空白，这里获取的是Margin账户的信息
    position = __get_position(exchange_v2)
    logger.debug('持仓情况%s', position)

    # 用来存储已持仓的币种列表
    position_list = []
    position_all_amount = []
    if len(position) == 0:
        logger.info('当前无持仓')
    if len(position) != 0:
        for p in position:
            position_symbol = p[0][1:-3] #'tBTCUSD'截取一段
            position_list.append(position_symbol)
            position_amount = p[2]
            position_all_amount.append(position_amount)
        logger.info('所有持仓币种：%s',position_list)
        #显示第一位的币种情况
        logger.info('首个持仓币种 %s', position_list[0])
        logger.info('首个持仓数量 %s', position_all_amount[0])

    # 生成平单的注释，邮件中提醒损益情况
    note = ''
    profit_loss = 'null'
    profit_loss_percent = 'null'
    if trade_coin in position_list:
        _index = position_list.index(trade_coin)
        if len(position[_index]) > 7:
            profit_loss = position[_index][6]
            profit_loss_percent = position[_index][7]
            note = str(profit_loss) +'，'+str(profit_loss_percent)
            logger.info('交易注释生成：%s',note)

    #操作下单动作
    loop_count =0
    while loop_count < 5:
        loop_count += 1
        try:
            # 查账户余额【默认USDT用于交易】
            if base_coin == 'USDT':
                balance_total = float(exchange_v1.fetch_balance({'type': 'trading'})['free']['USDT'])
            elif base_coin == 'BTC':
                balance_total = float(exchange_v1.fetch_balance({'type': 'trading'})['free']['BTC'])
            else:
                balance_total = 0.0

            # =====空仓情况下：下多单
            if signal == 1 and signal_before == 0 and trade_coin not in position_list:# in语法 相当于Java里的contains
                # 获取最新的买入价格
                price = exchange_v1.fetch_ticker(symbol)['ask']  # 获取卖一价格

                # 计算买入数量,按总资产的position_pct来计算仓位
                buy_amount = str(balance_total * position_pct * leverage / price)

                # 下单
                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='buy', symbol=symbol,
                                     price=price * 1.01, amount=buy_amount, record = {'multiple':str(leverage), 'profit':profit_loss, 'profit_percent':profit_loss_percent,'signal':'多单', 'account':str(balance_total)})
                logger.info('已下多单')
                time.sleep(5)

            # =====空仓情况下：下空单
            if signal == -1 and signal_before == 0 and trade_coin not in position_list:
                # 获取最新的卖出价格
                price = exchange_v1.fetch_ticker(symbol)['bid']  # 获取买一价格

                # 计算买入数量,按总资产的position_pct来计算仓位
                sell_amount = str(balance_total * position_pct * leverage / price)

                # 下单
                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='sell', symbol=symbol,
                                     price=price * 0.99, amount=sell_amount, record= {'multiple':str(leverage), 'profit':profit_loss, 'profit_percent':profit_loss_percent,'signal':'空单', 'account':str(balance_total)})
                logger.info('已下空单')
                time.sleep(5)

            # =====持仓情况下：平空单
            if signal == 0 and signal_before == -1 and trade_coin in position_list:
                # 获取最新的买入价格
                price = exchange_v1.fetch_ticker(symbol)['ask']  # 获取卖一价格
                # 查询持仓数量
                position_new = __get_position(exchange_v2)
                position_new = pd.DataFrame(position_new)
                buy_amount = str(abs(position_new[position_new[0] == symbol_temp].iloc[0][2]))

                # 下单
                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='buy', symbol=symbol,
                                     price=price * 1.01, amount=buy_amount, comment=note, record={'multiple':'null', 'profit':'null', 'profit_percent':'null','signal':'平空单', 'account':str(balance_total)})
                logger.info('已平空单')
                time.sleep(5)

            # =====持仓情况下：平多单
            if signal == 0 and signal_before == 1 and trade_coin in position_list:
                # 获取最新的卖出价格
                price = exchange_v1.fetch_ticker(symbol)['bid']  # 获取买一价格
                # 查询持仓数量
                position_new = __get_position(exchange_v2)
                position_new = pd.DataFrame(position_new)
                sell_amount = str(position_new[position_new[0] == symbol_temp].iloc[0][2])

                # 下单
                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='sell', symbol=symbol,
                                     price=price * 0.99, amount=sell_amount, comment=note,  record={'multiple':'null', 'profit':'null', 'profit_percent':'null','signal':'平多单', 'account':str(balance_total)})
                logger.info('已平多单')

            # =====持仓情况下：空仓转多仓  【暂时废弃】
            if signal == 1 and signal_before == -1 and trade_coin in position_list:
                # 先买入平仓
                price = exchange_v1.fetch_ticker(symbol)['ask']  # 获取卖一价格
                position_new = __get_position(exchange_v2)
                position_new = pd.DataFrame(position_new)
                buy_amount = str(abs(position_new[position_new[0] == symbol_temp].iloc[0][2]))

                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='buy', symbol=symbol,
                                     price=price * 1.03, amount=buy_amount, comment= note)
                logger.info('已平空单，稍后下多单')

                # 然后下多单
                price = exchange_v1.fetch_ticker(symbol)['ask']  # 获取卖一价格
                if base_coin == 'USDT':
                    balance_total = float(exchange_v1.fetch_balance({'type': 'trading'})['free']['USDT'])
                if base_coin == 'BTC':
                    balance_total = float(exchange_v1.fetch_balance({'type': 'trading'})['free']['BTC'])

                buy_amount = str(balance_total * position_pct * leverage / price)

                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='buy', symbol=symbol,
                                     price=price * 1.02, amount=buy_amount)
                logger.info('已下多单，完成空转多')
                time.sleep(3)

            # =====持仓情况下：多仓转空仓 【暂时废弃】
            if signal == -1 and signal_before == 1 and trade_coin in position_list:
                # 先卖出平仓
                price = exchange_v1.fetch_ticker(symbol)['bid']  # 获取买一价格
                # 查询持仓数量
                position_new = __get_position(exchange_v1)
                position_new = pd.DataFrame(position_new)
                sell_amount = str(position_new[position_new[0] == symbol_temp].iloc[0][2])

                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='sell', symbol=symbol,
                                     price=price * 0.97, amount=sell_amount, comment= note)
                logger.info('已平多单，稍后下空单')

                # 然后下空单
                if base_coin == 'USDT':
                    balance_total = float(exchange_v1.fetch_balance({'type': 'trading'})['free']['USDT'])
                if base_coin == 'BTC':
                    balance_total = float(exchange_v1.fetch_balance({'type': 'trading'})['free']['BTC'])

                price = exchange_v1.fetch_ticker(symbol)['bid']  # 获取买一价格
                sell_amount = str(balance_total * position_pct * leverage / price)

                place_order_bitfinex(exchange_v1, order_type='limit', buy_or_sell='sell', symbol=symbol,
                                     price=price * 0.98, amount=sell_amount)
                logger.info('已下空单，完成多转空')
                time.sleep(3)

            break

        except Exception as e:
            logger.error('下单函数报错，10秒后重试,%s', e)
            time.sleep(10)
