
from sanic import Sanic
from sanic.response import json as sanic_json
from sanic import response
from jinja2 import Template
from common.utils import project_path,log_exp
from webUI.web_call_service import web_call_main
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy import parse_message
from wechatpy.replies import TextReply, ImageReply


app = Sanic()


@app.route('/message', methods=['POST'])
async def reply(request):
    res = request_para(request)
    ask = res.get('question')
    print('问题：',ask)
    if ask.strip()=='':
        res_msg = '-1'
    else:
        res_msg = web_call_main(ask.strip())
        res_msg = res_msg.strip()

    # 如果接受到的内容为空，则给出相应的恢复
    if res_msg == ' ' or res_msg=='-1':
        res_msg = '问题未收入！请重试。'
    print('答案：',res_msg)
    return sanic_json({'text': res_msg})


@app.route('/weixin', methods=['GET', 'POST'])
async def weixin_reply(request):
    if request.method == 'GET':
        res = request_para(request)
        sign_ture = res.get('signature')
        time_stamp = res.get('timestamp')
        nonce_ = res.get('nonce')
        echo_str = res.get('echostr')
        try:
            check_signature(token='4725471112', signature=sign_ture, timestamp=time_stamp, nonce=nonce_)
            return_str = echo_str
        except InvalidSignatureException:
            log_exp.error('InvalidSignatureException')
            return_str = 'InvalidSignatureException'
        return response.text(body=return_str)
    elif request.method == 'POST':
        xml = request.body
        msg = parse_message(xml)
        if msg.type == 'text' and msg.source == 'opfB6w88fRxMh6DJirlzW8biOFNw': # 固定1148270327这个用户
            res_msg = web_call_main(msg.content.strip())
            reply = TextReply(content=res_msg, message=msg)
            xml = reply.render()
            return response.text(body=xml, status=200)
        else:
            return response.text(body='NaN')
    else:
        return response.text(body='NaN')



@app.route("/", methods=['GET'])
async def index(request):
    with open(project_path() + '/webUI/templates/search.html', encoding='utf-8') as html_file:
        template = Template(html_file.read())
        return response.html(template.render(name='index2'))


def request_para(request):
    """
    依据get、post参数不同位置，进行解析出标准请求参数
    :param request: sanic 请求对象, 目前参数要求是str
    :return: dict
    """
    if request.method.lower() == 'get':
        data = request.args
        pass
    elif request.method .lower() == 'post':
        data = request.form
        pass
    else:
        raise EOFError
    # 被json化的数据是在单独的字段中
    if data is None or len(data) == 0:
        data = request.json
    return data


# 启动APP
if (__name__ == "__main__"):
    #web_call_service('')
    app.run('0.0.0.0', 80)


