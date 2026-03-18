from funboost.utils.notify_util import Notifier

from dotenv import load_dotenv
import os
load_dotenv('/my_dotenv.env')

notifier = Notifier(
    wechat_webhook=os.getenv('QYWEIXIN_WEBHOOK')
)

# 2. 发送消息（使用默认配置，自动添加调用者信息）
# notifier.send_dingtalk("钉钉消息测试")
notifier.send_wechat("企业微信消息测试")