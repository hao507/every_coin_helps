
from sanic import Sanic
from sanic.response import json as sanic_json
from sanic import response
from jinja2 import Template
from common.utils import project_path
from .web_call_service import web_call_main
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
    app.run('0.0.0.0', 443)


