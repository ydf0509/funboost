# Funboost Web Manager 使用指南

Funboost Web Manager 是一个基于 Web 的管理界面，用于监控和管理 Funboost 分布式任务队列。

## 快速开始

### 1. 激活虚拟环境

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. 初始化数据库

```bash
python -m funboost.funboost_web_manager.cli db init
```

### 3. 启动服务

```bash
python -m funboost.funboost_web_manager.cli start
```

服务启动后：

- 后端 API: http://127.0.0.1:27018
- 前端界面: http://127.0.0.1:3000

## CLI 命令参考

### 交互式菜单

```bash
python -m funboost.funboost_web_manager.cli
```

### 一键初始化

```bash
python -m funboost.funboost_web_manager.cli init
```

可选参数：

- `--skip-venv`: 跳过虚拟环境创建
- `--skip-deps`: 跳过依赖安装
- `--skip-frontend`: 跳过前端初始化
- `--skip-db`: 跳过数据库初始化
- `--skip-user`: 跳过用户创建

### 服务管理

```bash
# 启动所有服务
python -m funboost.funboost_web_manager.cli start

# 只启动后端
python -m funboost.funboost_web_manager.cli start --backend

# 只启动前端
python -m funboost.funboost_web_manager.cli start --frontend

# 停止所有服务
python -m funboost.funboost_web_manager.cli stop
```

### 数据库管理

```bash
# 初始化数据库
python -m funboost.funboost_web_manager.cli db init

# 运行迁移
python -m funboost.funboost_web_manager.cli db migrate

# 查看状态
python -m funboost.funboost_web_manager.cli db status

# 备份数据库
python -m funboost.funboost_web_manager.cli db backup

# 恢复数据库
python -m funboost.funboost_web_manager.cli db restore <filename>

# 重置数据库
python -m funboost.funboost_web_manager.cli db reset
```

### 用户管理

```bash
# 创建用户（交互式）
python -m funboost.funboost_web_manager.cli user create

# 从配置文件创建用户
python -m funboost.funboost_web_manager.cli user create --config users.json

# 列出所有用户
python -m funboost.funboost_web_manager.cli user list

# 重置密码
python -m funboost.funboost_web_manager.cli user reset-password <username>

# 解锁用户
python -m funboost.funboost_web_manager.cli user unlock <username>

# 删除用户
python -m funboost.funboost_web_manager.cli user delete <username>

# 清理默认用户
python -m funboost.funboost_web_manager.cli user clean-defaults
```

## 配置

### 环境变量

可以通过 `.env` 文件或环境变量配置：

| 变量名                  | 默认值    | 说明               |
| ----------------------- | --------- | ------------------ |
| `FUNBOOST_WEB_HOST`     | `0.0.0.0` | 监听地址           |
| `FUNBOOST_WEB_PORT`     | `27018`   | 监听端口           |
| `FUNBOOST_DEBUG`        | `False`   | 调试模式           |
| `FUNBOOST_SECRET_KEY`   | -         | Flask 密钥（必填） |
| `FUNBOOST_PROJECT_ROOT` | 自动检测  | 项目根目录         |

### 项目根目录

CLI 会自动检测项目根目录，查找顺序：

1. 环境变量 `FUNBOOST_PROJECT_ROOT`
2. 向上遍历查找包含 `funboost_config.py`、`.git`、`setup.py` 或 `pyproject.toml` 的目录
3. 当前工作目录

## 目录结构

```
funboost/funboost_web_manager/
├── cli/                    # CLI 命令行工具
│   ├── __init__.py
│   ├── __main__.py        # 入口点
│   ├── main.py            # 主程序
│   ├── commands/          # 命令模块
│   │   ├── db.py          # 数据库命令
│   │   ├── user.py        # 用户命令
│   │   ├── service.py     # 服务命令
│   │   └── init.py        # 初始化命令
│   └── utils/             # 工具模块
│       ├── console.py     # 控制台输出
│       ├── platform.py    # 跨平台工具
│       ├── process.py     # 进程管理
│       ├── network.py     # 网络检查
│       └── config.py      # 配置管理
├── app.py                 # Flask 应用
├── config.py              # 配置
├── database.py            # 数据库
├── user_models.py         # 用户模型
├── models/                # 数据模型
├── routes/                # API 路由
├── services/              # 业务服务
└── static/                # 静态文件
```

## 常见问题

### ModuleNotFoundError: No module named 'nb_log'

确保在虚拟环境中运行：

```bash
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

### 数据库不存在

运行初始化命令：

```bash
python -m funboost.funboost_web_manager.cli db init
```

### 端口被占用

停止现有服务后重新启动：

```bash
python -m funboost.funboost_web_manager.cli stop
python -m funboost.funboost_web_manager.cli start
```

