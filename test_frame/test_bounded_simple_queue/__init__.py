# -*- coding: utf-8 -*-
"""
有界 SimpleQueue 作为 Broker 的动态扩展示例

按照 funboost 文档 4.21 章节，演示如何动态扩展 broker：
1. 不修改 funboost/publishers 和 funboost/consumers 目录
2. 使用 register_custom_broker 动态注册
3. Publisher 和 Consumer 类定义在用户代码中
"""
