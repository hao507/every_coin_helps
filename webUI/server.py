
from flask import Flask, render_template, request
from flask import jsonify

import re

from Xbitfinex import orders
from domain import my_exchange
from common.utils import logger
from Xbitfinex.orders import auto_trade_leverage

app = Flask(__name__, static_url_path="/static")


@app.route('/message', methods=['POST'])
def reply():
    ask = request.form['msg']
    print('问题：',ask)
    if ask.strip()=='':
        res_msg = '-1'
    else:
        res_msg = web_call_service(ask.strip())
        res_msg = res_msg.strip()

    # 如果接受到的内容为空，则给出相应的恢复
    if res_msg == ' ' or res_msg=='-1':
        res_msg = '问题未收入！请重试。'
    print('答案：',res_msg)
    return jsonify({'text': res_msg})


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")

# _________________________________________________________________


def web_call_service(input_message):
    ans='可执行"查询持仓、下单[平多/平空/空/多,ETH,0.5p,3倍]、help"指令'

    if input_message=='查询持仓':
        exchange= my_exchange.bitfinexV2_instance()
        ans= get_pos_info(exchange)
    elif input_message.startswith('下单'):
        ans = play_order(input_message)
    return ans


# ___________________________查询______________________________________
def get_pos_info(exchange):
    '''
    查询持仓情况和损益等
    :param exchange:
    :return:
    '''
  # 获取仓位信息，需要有仓位才能获取，不然是空白，这里获取的是Margin账户的信息
    position = orders.__get_position(exchange)
    logger.debug('持仓情况%s', position)

    # 用来存储已持仓的币种列表
    position_list = []
    position_all_amount = []
    if len(position) == 0:
        return '当前无持仓'
    if len(position) != 0:
        for p in position:
            position_symbol = p[0][1:-3] #'tBTCUSD'截取一段
            position_list.append(position_symbol)
            position_amount = p[2]
            position_all_amount.append(position_amount)
        logger.info('所有持仓币种：%s',position_list)

    # 生成注释，邮件中提醒损益情况
    note = ''
    for trade_coin in position_list:
        _index = position_list.index(trade_coin)
        if len(position[_index]) > 7:
            profit_loss = position[_index][6]
            profit_loss_percent = position[_index][7]
            note += trade_coin+'[ 利润：$'+str(round(profit_loss,2)) +', 损益：'+str(round(profit_loss_percent,2))+'%]</br>'
    logger.info('查持仓注释生成：%s',note)
    return note

# __________________________操作_______________________________________
def play_order(exc='下单'):
    if exc=='下单':
        return
    #提取指令
    try:
        # exc='下单[平,ETH,0.7p,2倍]'
        ma = re.search('^下单\[((平多)|空|多),\s*([A-Z]{2,9}),\s*((0\.){0,1}[0-9]{1,2})p,\s*([0-3](\.[0-9]){0,1})倍\s*\]$', exc)
        para1, para2, para3, para4 = ma.group(1), ma.group(3), ma.group(4), ma.group(6)
    except Exception as e:
        print(e)
        return '正则失败，请检查下单指令是否有误！'

    #生成操作码
    if para1=='平多':
        sigal, sigal_before = 0, 1
    elif para1=='平空':
        sigal, sigal_before = 0, -1
    elif para1=='空':
        sigal, sigal_before = -1, 0
    elif para1=='多':
        sigal, sigal_before = 1, 0
    else:
        return '只能执行[平多|平空|空|多]之一！'
    # 下单
    auto_trade_leverage(my_exchange.bitfinexV2_instance(), para2 + '/USDT', sigal, sigal_before, para=[para4, para3, my_exchange.bitfinex_instance()])
    return '已执行任务，执行结果将以邮件下发，请注意查收！'

# _________________________________________________________________
# 启动APP
if (__name__ == "__main__"):
    #web_call_service('')
    app.run('0.0.0.0', 5001)


