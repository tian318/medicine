import logging
import sys
import os
from datetime import datetime
# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from my_email import Mailer
    MAILER_AVAILABLE = True
except ImportError:
    print(f"Warning: Cannot import Mailer from my_email. Looking in: {current_dir}")
    print("Mail functionality will be disabled, but logging will still work.")
    MAILER_AVAILABLE = False
"""
my_log参数:
    log_name: 日志显示的名字
    log_path: 日志保存位置
"""


# 输入为日志名字,日志保存位置
def my_log(log_name, log_path):
    # 创建一个logger
    logger = logging.getLogger(log_name)

    # 设置日志级别
    logger.setLevel(logging.INFO)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(log_path, encoding='utf-8')
    ch = logging.StreamHandler()
    # 定义handler的输出格式
    formatter = logging.Formatter(
        # 时间格式
        datefmt='%Y-%m-%d %H:%M:%S',
        # 日志格式
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # 给logger添加handler
    logger.addHandler(fh)
    logger.addHandler(ch)
    # 返回函数
    return logger


class Mail_log:
    def __init__(self, log_name):
        self.mail_text = ""
        self.log_name = log_name

    def log(self, mail_text, levelname="error"):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.mail_text += f"{current_time} - {self.log_name} - {levelname} - {mail_text}\n"

    def mail_send(self, target, title):
        if self.mail_text != "":
            if MAILER_AVAILABLE:
                mailer = Mailer()
                mailer.send_mail(target, title, self.mail_text)
            else:
                print(f"Mail functionality is disabled. Would have sent to: {target}, title: {title}")
                print("Mail content:")
                print(self.mail_text)
