#!/bin/bash
# 回归测试运行脚本
# 
# 由于 Flask Blueprint 的限制，这些测试需要在独立的 Python 进程中运行
# 使用方法：
#   chmod +x funboost/funboost_web_manager/tests/run_regression_tests.sh
#   ./funboost/funboost_web_manager/tests/run_regression_tests.sh

echo "运行 Web Manager FaaS 集成回归测试..."
echo "========================================"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/../../.."

# 运行测试
python -m pytest funboost/funboost_web_manager/tests/test_regression.py -v --tb=short

echo ""
echo "========================================"
echo "测试完成"
