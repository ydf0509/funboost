@echo off
chcp 65001 >nul
REM Funboost Web Manager 快速设置脚本 (Windows)
REM
REM 使用方法:
REM   scripts\setup.bat              # 交互式菜单
REM   scripts\setup.bat init         # 一键初始化
REM   scripts\setup.bat start        # 启动服务
REM   scripts\setup.bat stop         # 停止服务
REM   scripts\setup.bat --help       # 查看帮助

REM 进入项目根目录
cd /d "%~dp0\.."

REM 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python
    echo 请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 检查 Python 版本
for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set VERSION=%%i
echo Python 版本: %VERSION%

REM 运行 CLI
python manage.py %*
