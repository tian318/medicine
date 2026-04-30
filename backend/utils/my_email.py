import os
import yaml
import smtplib
from email.mime.text import MIMEText

# 使用相对路径读取配置文件
config_path = os.path.join(os.path.dirname(__file__), 'my_email.yaml')
with open(config_path, 'r') as stream:
    config = yaml.safe_load(stream)

"""
邮箱发送模块,使用QQ邮箱发送邮件
配置文件在modules_conf/my_email.yaml
send_mail参数:
    receiver: 收件人邮箱
    subject: 邮件主题
    content: 邮件内容

"""

class Mailer:
    def __init__(self):
        self.sender = config['user']
        self.password = config['passwd']
    # 输入为发送到邮箱,邮箱题目,邮箱内容
    def send_mail(self, receiver, subject, content):
        msg = MIMEText(content, 'plain', 'utf-8')
        # msg['From'] = formataddr(["搜书", self.sender])
        # msg['To'] = formataddr(["test", receiver])
        msg['From'] = self.sender
        msg['To'] = receiver
        msg['Subject'] = subject
        try:
            server = smtplib.SMTP_SSL("smtp.qq.com", 465)
            server.login(self.sender, self.password)
            server.sendmail(self.sender, [receiver], msg.as_string())
            server.quit()
            print("邮件发送成功")
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False








