import threading
from common.utils import send_mail

def run_d():
    print('start')
    threading.Thread(target=send_mail, args=('test','xxx')).start()
    print('nihoa ')


if __name__== '__main__':
    print('!')
    run_d()
    print("over")
