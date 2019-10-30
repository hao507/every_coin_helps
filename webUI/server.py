
from flask import Flask, render_template, request
from flask import jsonify

import re
from collections import deque
from multiprocessing import Process

from Xbitfinex import orders
from domain import my_exchange
from common.utils import logger
from Xbitfinex.orders import auto_trade_leverage
from tasks.multi_task import start_bitfinex_task

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

# ______________________执行主函数入口___________________________________________

def web_call_service(input_message):
    ans='可执行"查询持仓、下单[平多/平空/空/多,ETH,0.5P,3L]、任务[ETH,0.5P,3L,[90,3.2,0.005,0.015,1.779]]、任务终止-ETH、查询任务、查询历史任务、help"指令'

    if input_message=='查询持仓':
        exchange= my_exchange.bitfinexV2_instance()
        ans= get_pos_info(exchange)
    elif input_message.startswith('下单'):
        ans = play_order(input_message)
    elif input_message.startswith('任务'):
        ans = exec_tasks(input_message)
    elif input_message=='查询任务':
        ans = get_all_tasks()
    elif input_message=='查询历史任务':
        ans = get_tasks_history5()
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

# __________________________下单操作_______________________________________
def play_order(exc='下单'):
    if exc=='下单':
        return '下单指令不完整！'
    #提取指令
    try:
        #exc = '下单[平多,ETH,0.7P,2.1L]'
        ma = re.search('^下单\[((平多)|(平空)|空|多),\s*([A-Z]{2,9}),\s*((0\.){0,1}[0-9]{1,2})P,\s*([0-3](\.[0-9]){0,1})L\s*\]$', exc)
        para1, para2, para3, para4 = ma.group(1), ma.group(4), float(ma.group(5)), float(ma.group(7))
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
    return '已执行任务！若符合持仓条件，执行结果将以邮件下发，请注意查收！'
# __________________________监测信号操作_______________________________________
sub_jobs=[]#进程对象
history_task = deque(maxlen=5) # 历史检测任务的参数

def exec_tasks(exc='任务'):
    global sub_jobs, history_task
    def is_contains(sym='ETH'):
        for name, per_task, note in sub_jobs:
            if name == sym:
                return note
        return -1
    #主线
    if exc == '任务':
        return '任务指令不完整！'
    elif exc.startswith('任务终止-'):
        task_end=exc.split('-')
        if len(task_end)==2:
            # 结束任务，当子进程执行完毕后，会产生一个僵尸进程，其会被join函数回收，或者再有一条进程开启，start函数也会回收僵尸进程，所以不一定需要写join函数。
            end_t =None
            i = 0
            for name, per_task, _ in sub_jobs:
                i+=1
                if name ==task_end[1]:
                    end_t = per_task
                    break
            if end_t is not None and end_t.exitcode is None:
                end_t.terminate()
                end_t.join()
                if end_t.exitcode is not None:
                    del sub_jobs[i-1]
                    return '已终止任务！'
                else:
                    return '未知'
            else:
                return '指定任务不存在！'
            pass
        else:
            return '任务结束指令错误！'
    # 主要监测信号任务
    # 提取指令
    try:
        # exc='任务[ETH,0.5P,3L,[90,3.2,0.005,0.015,1.779]]'
        ma = re.search('^任务\[([A-Z]{2,9}),\s*((0\.){0,1}[0-9]{1,2})P,\s*([0-3](\.[0-9]){0,1})L,\s*\[(.*)\]\s*\]$', exc)
        para1, para2, para3, para4 = ma.group(1), float(ma.group(2)), float(ma.group(4)), ma.group(6)
        strtegy_para = [float(s) for s in para4.split(',')]
    except Exception as e:
        print(e)
        return '正则失败，请检查任务指令是否有误！'

    # 执行任务
    # start_bitfinex_task(symb=para1, percent=para2, multi=para3, strtegy_para=strtegy_para)
    check = is_contains(para1)
    if check!=-1:
        return '已有同名任务正在执行：'+check
    sub_task = Process(target=start_bitfinex_task, args=(para1, para2, para3, strtegy_para), name=para1)
    sub_task.daemon = True#布尔值，指示进程是否是后台进程。当创建它的进程终止时，后台进程会自动终止。并且，后台进程无法创建自己的新进程。
    sub_jobs.append((para1, sub_task, exc))#记录
    sub_task.start()
    history_task.append(exc)
    return '任务执行成功！'
# _________________________查询正在执行的任务________________________________________
def get_all_tasks():
    rs=''
    for name, per_task, note in sub_jobs:
        rs+=note+'</br>'
    if rs=='':
        rs='暂无正在执行的任务！'
    return rs

# _________________________查询历史任务最近5条________________________________________
def get_tasks_history5():
    rs=''
    for name in history_task:
        rs += name+'</br>'
    if rs=='':
        rs='暂无历史任务记录！'
    return rs


# 启动APP
if (__name__ == "__main__"):
    #web_call_service('')
    app.run('0.0.0.0', 5001)


