
import logging
import os
import pickle
import re
import time

import smtplib
from email.header import Header
from email.mime.text import MIMEText

from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


def singleton (cls, *args, **kwargs):
    '''
    static singleton mode wraper
    :param cls:
    :param args:
    :param kwargs:
    :return:
    '''
    instances = {}
    def get_instance (*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
            return instances[cls]
        else :
            return instances[cls]
    return get_instance

@singleton
class Debug_hangder(object):
    '''通过继承实现的单例模式是有点突出的。因为它跟其他方式有点不同，它是通过new方法的改造实现的。如果之前有就返回之前的实例；如果没有，就创建新的实例。'''
    # def __new__(cls, *args, **kwargs):
    #     # singleton mode
    #     if not hasattr(cls, '_instance'):
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(self):
        print('init Debug_hangder...')
        self.log = self.make_hander('utils')

    def get_logger(self, name= None):
        if name is None:
            return self.log
        else:
            return self.make_hander(name)

    def make_hander(self, log_name):
        print('make new debug hander: ',log_name)
        logger = logging.getLogger(log_name)
        logger.setLevel(logging.DEBUG)

        # 创建一个handler，用于写入日志文件
        log_path =os.path.abspath(os.path.join(os.path.dirname(__file__), "../loginfo"))
        name = log_path + '/' + time.strftime("%Y%m%d") + '.log'
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        fh = TimedRotatingFileHandler(filename=name, when='D', interval=1, backupCount=30, encoding="utf-8")
        fh.setLevel(logging.INFO)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)# 服务器运行时改成info

        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)-8s %(filename)-8s %(levelname)-8s %(name)-12s [line:%(lineno)d]  %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger


log_exp = Debug_hangder().get_logger()

# sleep
def next_run_time(time_interval):
    if time_interval.endswith('m'):
        now_time = datetime.now()
        time_interval = int(time_interval.strip('m'))

        target_min = (int(now_time.minute / time_interval) + 1) * time_interval
        if target_min < 60:
            target_time = now_time.replace(minute=target_min, second=0, microsecond=0)
        else:
            if now_time.hour == 23:
                target_time = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
                target_time += timedelta(days=1)
            else:
                target_time = now_time.replace(hour=now_time.hour + 1, minute=0, second=0, microsecond=0)

        log_exp.debug('下次运行时间%s', target_time)
        return target_time
    else:
        exit('time_interval doesn\'t end with m')
        
#解析小时分钟等字符串
def time_span(stamp = '1h'):
    mc = re.search('([0-9]+)([a-z])',stamp)
    if mc:
        unit = mc.group(2)
        val = mc.group(1)
        if unit == 'm':
            return timedelta(minutes=int(val))
        elif unit == 'h':
            return timedelta(hours=int(val))
    else:
        raise Exception


#获取项目路径
def project_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),'../'))


# def exterme_point(x=np.array([0, 6, 25 ])):
#     x= x[-100:]
#     plt.figure(figsize=(16,4))
#     plt.plot(np.arange(len(x)),x)
#     # print(x[signal.argrelextrema(x, np.greater)])
#     # print(signal.argrelextrema(x, np.greater))
#
#     plt.plot(signal.argrelextrema(x,np.greater)[0],x[signal.argrelextrema(x, np.greater)],'o')
#     plt.plot(signal.argrelextrema(-x,np.greater)[0],x[signal.argrelextrema(-x, np.greater)],'+')
#     # plt.plot(peakutils.index(-x),x[peakutils.index(-x)],'*')
#     plt.show()


'''
发送邮件函数，默认使用163smtp
:param mail_host: 邮箱服务器，16邮箱host: smtp.163.com
:param port: 端口号,163邮箱的默认端口是 25
:param username: 邮箱账号 xx@163.com
:param passwd: 邮箱密码(不是邮箱的登录密码，是邮箱的授权码)
:param recv: 邮箱接收人地址，多个账号以逗号隔开
:param title: 邮件标题
:param content: 邮件内容
:return:
'''
'''
  #使用多线程执行更方便。协程容易出问题。另外，阿里云服务器吧25端口封禁了，只能采用ssl加密的465端口, 主题不能为敏感词test等
'''
def send_mail(title, content, username='a1148270327@126.com', passwd='Aa110998', recv='15000959076@163.com', mail_host='smtp.126.com', port=465):

    msg = MIMEText(content, _subtype='plain', _charset='utf-8')  # 邮件内容
    msg['Subject'] = Header(title,'utf-8' ) # 邮件主题
    msg['From'] = 'every_coin_helps<'+username+'>'  # 发送者账号
    msg['To'] = 'yuan<'+recv+'>'  # 接收者账号列表

    flag = True
    i =0
    while flag and i <4:
        try:
            #smtp = smtplib.SMTP(mail_host, port=port)  # 连接邮箱，传入邮箱地址，和端口号，smtp的端口号是25
            smtp = smtplib.SMTP_SSL(host=mail_host, port=port)  # 连接邮箱，传入邮箱地址，和端口号，smtp_ssl的端口号是465
            smtp.login(username, passwd)  # 登录发送者的邮箱账号，密码
            # 参数分别是 发送者，接收者，第三个是把上面的发送邮件的 内容变成字符串
            smtp.sendmail(username, recv, msg.as_string())
            smtp.quit()  # 发送完毕后退出smtp
            flag = False

        except Exception as e:
            log_exp.error('email 重发第%s次，info：%s', str(i), e)
            i+=1
            time.sleep(60)
    if flag:
        log_exp.info('email send failed.')
    else:
        log_exp.info('email send success.')

'''
通过上面的方式来新建一个run函数来驱动协程函数发送邮件：
'''
# def run_async_email(title,content):
#     try:
#         send_mail(str(title), str(content)).send(None)
#         print("emain")
#     except StopIteration as e:
#         return e.value

#序列化到文件
def file_obj_convert(fileName='/data/k_df.pkl',obj = None):
    path = project_path()+fileName
    if obj is not None:
        print('开始写入文件：'+path)
        # 序列化
        with open(path, 'wb') as f:
            pickle.dump(obj, f)
    else:
        print('开始读取数据：' + path)
        # 反序列化
        with open(path, 'rb') as f:
            Person = pickle.load(f)
        print('读取完毕')
        return Person

if __name__=='__main__':
    log_exp.debug('run wo')