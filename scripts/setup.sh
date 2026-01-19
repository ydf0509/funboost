#!/bin/bash
# -*- coding: utf-8 -*-
# Funboost Web Manager 快速设置脚本 (macOS/Linux)
#
# 使用方法:
#   ./scripts/setup.sh              # 交互式菜单
#   ./scripts/setup.sh init         # 一键初始化
#   ./scripts/setup.sh start        # 启动服务
#   ./scripts/setup.sh stop         # 停止服务
#   ./scripts/setup.sh --help       # 查看帮助

set -e

# 进入项目根目录
cd "$(dirname "$0")/.."

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "错误: 未找到 Python"
    echo "请先安装 Python 3.9+"
    exit 1
fi

# 检查 Python 版本
VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo $VERSION | cut -d. -f1)
MINOR=$(echo $VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
    echo "错误: Python 版本过低 ($VERSION)"
    echo "需要 Python 3.9+"
    exit 1
fi

# 运行 CLI
exec $PYTHON manage.py "$@"
