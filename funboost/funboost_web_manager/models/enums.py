# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
权限系统枚举类型模块

本模块定义权限系统使用的枚举类型和常量映射。

Exports:
    - ActionType: 标准操作类型枚举
    - ACTION_TYPE_DISPLAY: 操作类型显示名称映射字典
"""

from enum import Enum


class ActionType(str, Enum):
    """标准操作类型枚举
    
    定义权限系统支持的标准操作类型，用于细粒度权限控制。
    继承自 str 和 Enum，使得枚举值可以直接作为字符串使用。
    
    Attributes:
        CREATE: 创建操作
        READ: 读取/查看操作
        UPDATE: 更新/编辑操作
        DELETE: 删除操作
        EXECUTE: 执行操作（如执行任务、运行命令等）
        EXPORT: 导出操作
    """
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    EXECUTE = 'execute'
    EXPORT = 'export'


# 操作类型显示名称映射
ACTION_TYPE_DISPLAY = {
    'create': '创建',
    'read': '查看',
    'update': '编辑',
    'delete': '删除',
    'execute': '执行',
    'export': '导出',
}
