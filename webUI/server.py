
from flask import Flask, render_template, request
from flask import jsonify

import time
import threading

from Xbitfinex import orders
from domain import my_exchange
from common.utils import logger


def heartbeat():
    print(time.strftime('%Y-%m-%d %H:%M:%S - heartbeat', time.localtime(time.time())))
    timer = threading.Timer(60, heartbeat)
    timer.start()


timer = threading.Timer(60, heartbeat)
timer.start()

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
    ans=''
    if input_message=='help':
        ans='可执行"查询持仓、help"指令'
    elif input_message.startswith('查询持仓'):
        exchange= my_exchange.bitfinexV2_instance()
        ans= get_pos_info(exchange)
    else:
        ans='-1'
    return ans


# _________________________________________________________________e
def get_pos_info(exchange):
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
# 启动APP
if (__name__ == "__main__"):
    #web_call_service('')
    app.run('127.0.0.1', 5001)


