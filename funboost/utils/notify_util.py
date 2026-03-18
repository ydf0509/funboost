import requests
import json
import inspect

from typing import Optional
from funboost.core.loggers import logger_notify

logger = logger_notify

class Notifier:
    """
    企业消息推送工具，支持钉钉、企业微信、飞书机器人。
    """

    def __init__(self,
                 dingtalk_webhook: Optional[str] = None,
                 wechat_webhook: Optional[str] = None,
                 feishu_webhook: Optional[str] = None):
        """
        初始化通知器，可配置各平台的默认 Webhook。

        :param dingtalk_webhook: 钉钉机器人的 Webhook 地址
        :param wechat_webhook:  企业微信机器人的 Webhook 地址
        :param feishu_webhook:  飞书机器人的 Webhook 地址
        """
        self.dingtalk_webhook = dingtalk_webhook
        self.wechat_webhook = wechat_webhook
        self.feishu_webhook = feishu_webhook

    def _get_caller_info(self) -> str:
        """获取调用者的文件路径和行号"""
        try:
            # 获取调用栈，跳过当前方法和发送方法
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back
            
            # 获取文件路径和行号
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            
            # 简化文件路径，只显示最后两层目录
            parts = filename.split('/')
            if len(parts) >= 2:
                short_path = '/'.join(parts[-2:])
            else:
                short_path = filename
            
            return f"{short_path}:{lineno}"
        except Exception:
            return "unknown:0"

    def send_dingtalk(self, message: str, webhook: Optional[str] = None, add_caller_info: bool = True) -> bool:
        """
        发送钉钉文本消息。

        :param message: 消息内容
        :param webhook: 可选，覆盖实例化时的默认 Webhook
        :param add_caller_info: 是否自动添加调用者信息（文件路径和行号），默认 True
        :return: 是否发送成功
        """
        url = webhook or self.dingtalk_webhook
        if not url:
            raise ValueError("钉钉 Webhook 未配置")

        if add_caller_info:
            caller_info = self._get_caller_info()
            message = f"{message}\n\n📍发送位置: {caller_info}"

        logger.warning(f"发送钉钉消息: {message} ")

        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        return self._post(url, payload)

    def send_wechat(self, message: str, webhook: Optional[str] = None, add_caller_info: bool = True) -> bool:
        """
        发送企业微信文本消息。

        :param message: 消息内容
        :param webhook: 可选，覆盖实例化时的默认 Webhook
        :param add_caller_info: 是否自动添加调用者信息（文件路径和行号），默认 True
        :return: 是否发送成功
        """
        url = webhook or self.wechat_webhook
        if not url:
            raise ValueError("企业微信 Webhook 未配置")

        if add_caller_info:
            caller_info = self._get_caller_info()
            message = f"{message}\n\n📍发送位置: {caller_info}"

        logger.warning(f"发送企业微信消息: {message}")

        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        return self._post(url, payload)

    def send_feishu(self, message: str, webhook: Optional[str] = None, add_caller_info: bool = True) -> bool:
        """
        发送飞书文本消息。

        :param message: 消息内容
        :param webhook: 可选，覆盖实例化时的默认 Webhook
        :param add_caller_info: 是否自动添加调用者信息（文件路径和行号），默认 True
        :return: 是否发送成功
        """
        url = webhook or self.feishu_webhook
        if not url:
            raise ValueError("飞书 Webhook 未配置")

        if add_caller_info:
            caller_info = self._get_caller_info()
            message = f"{message}\n\n📍发送位置: {caller_info}"

        logger.warning(f"发送飞书消息: {message} ")

        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        return self._post(url, payload)

    def _post(self, url: str, payload: dict) -> bool:
        """内部方法：发送 POST 请求并检查响应"""
        try:
            headers = {'Content-Type': 'application/json'}
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            resp.raise_for_status()
            result = resp.json()
            # 不同平台的返回格式略有差异，通常 errcode/errcode/code 为 0 表示成功
            if result.get('errcode') == 0 or result.get('code') == 0:
                return True
            # 飞书成功时没有 errcode 字段，而是 StatusCode 0
            if result.get('StatusCode') == 0:
                return True
            # 打印错误信息便于调试
            print(f"发送失败: {result}")
            return False
        except Exception as e:
            print(f"请求异常: {e}")
            return False


# ========== 使用示例 ==========
if __name__ == '__main__':
    # 1. 初始化时配置默认 Webhook
    notifier = Notifier(
        dingtalk_webhook='https://oapi.dingtalk.com/robot/send?access_token=your_token',
        wechat_webhook='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key',
        feishu_webhook='https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook'
    )

    # 2. 发送消息（使用默认配置，自动添加调用者信息）
    # notifier.send_dingtalk("钉钉消息测试")
    notifier.send_wechat("企业微信消息测试")
    # notifier.send_feishu("飞书消息测试")

    # 3. 也可以临时指定不同 Webhook 覆盖默认值
    # notifier.send_dingtalk("临时消息", webhook="https://另一个钉钉机器人")

    # 4. 可以关闭自动添加调用者信息
    # notifier.send_wechat("不显示位置的消息", add_caller_info=False)
