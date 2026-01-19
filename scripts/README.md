# Funboost Web Manager CLI 工具

本目录包含项目管理脚本和 CLI 工具，提供统一的命令行入口来管理 Funboost Web Manager。

## 目录

- [快速开始](#快速开始)
- [命令参考](#命令参考)
  - [初始化命令](#初始化命令-init)
  - [服务管理](#服务管理-start--stop--status)
  - [日志查看](#日志查看-logs)
  - [数据库管理](#数据库管理-db)
  - [用户管理](#用户管理-user)
  - [项目同步](#项目同步-project)
  - [环境检查](#环境检查-env)
  - [配置管理](#配置管理-config)
- [目录结构](#目录结构)
- [故障排除](#故障排除)

---

## 快速开始

### 使用统一入口（推荐）

```bash
# 交互式菜单
python manage.py

# 一键初始化（首次使用）
python manage.py init

# 启动服务
python manage.py start

# 停止服务
python manage.py stop

# 查看状态
python manage.py status

# 查看帮助
python manage.py --help
```

### 使用快捷脚本

**macOS/Linux:**

```bash
./scripts/setup.sh              # 交互式菜单
./scripts/setup.sh init         # 一键初始化
./scripts/setup.sh start        # 启动服务
```

**Windows:**

```cmd
scripts\setup.bat               # 交互式菜单
scripts\setup.bat init          # 一键初始化
scripts\setup.bat start         # 启动服务
```

---

## 命令参考

### 初始化命令 (init)

一键初始化整个项目环境，包括虚拟环境、依赖安装、数据库初始化和管理员创建。

```bash
# 完整初始化
python manage.py init

# 跳过特定步骤
python manage.py init --skip-venv        # 跳过虚拟环境创建
python manage.py init --skip-deps        # 跳过 Python 依赖安装
python manage.py init --skip-frontend    # 跳过前端依赖安装
python manage.py init --skip-db          # 跳过数据库初始化
python manage.py init --skip-user        # 跳过管理员创建
```

**初始化流程：**

1. 环境检查（Python 版本）
2. 创建虚拟环境
3. 安装 Python 依赖
4. 安装前端依赖
5. 初始化数据库
6. 创建管理员用户

---

### 服务管理 (start / stop / status)

管理后端和前端服务的启动、停止和状态查看。

```bash
# 启动所有服务
python manage.py start

# 只启动后端服务
python manage.py start --backend

# 只启动前端服务
python manage.py start --frontend

# 停止所有服务
python manage.py stop

# 查看服务状态
python manage.py status
```

**服务端口：**

| 服务 | 端口  | 地址                   |
| ---- | ----- | ---------------------- |
| 后端 | 27018 | http://127.0.0.1:27018 |
| 前端 | 3000  | http://127.0.0.1:3000  |

---

### 日志查看 (logs)

查看服务日志，支持实时跟踪、级别过滤和关键词搜索。

```bash
# 列出所有日志文件
python manage.py logs

# 查看后端日志（最后 50 行）
python manage.py logs backend

# 查看前端日志
python manage.py logs frontend

# 实时跟踪日志（类似 tail -f）
python manage.py logs backend -f
python manage.py logs backend --follow

# 指定显示行数
python manage.py logs backend -n 100
python manage.py logs backend --lines 100

# 按日志级别过滤
python manage.py logs backend --level ERROR      # 只显示 ERROR 及以上
python manage.py logs backend --level WARNING    # 只显示 WARNING 及以上
python manage.py logs backend --level INFO       # 只显示 INFO 及以上

# 搜索关键词
python manage.py logs backend --search "error"
python manage.py logs backend -s "connection failed"

# 组合使用
python manage.py logs backend -f --level ERROR --search "database"

# 禁用颜色输出
python manage.py logs backend --no-color
```

**日志级别（从低到高）：**

- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误

---

### 数据库管理 (db)

管理数据库的初始化、迁移、备份和恢复。

```bash
# 初始化数据库（创建表、权限、角色）
python manage.py db init

# 运行数据库迁移
python manage.py db migrate

# 查看数据库状态
python manage.py db status

# 备份数据库
python manage.py db backup
python manage.py db backup --filename my_backup.db

# 恢复数据库
python manage.py db restore <备份文件名>
python manage.py db restore web_manager_users_20240115_103045.db

# 重置数据库（危险操作，会删除所有数据）
python manage.py db reset
```

**备份文件位置：** `backups/` 目录

---

### 用户管理 (user)

管理系统用户，包括创建、删除、重置密码等操作。

```bash
# 交互式创建用户
python manage.py user create

# 从配置文件创建用户
python manage.py user create --config admin_config.json

# 列出所有用户
python manage.py user list

# 重置用户密码
python manage.py user reset-password <用户名>
python manage.py user reset-password admin

# 解锁被锁定的用户
python manage.py user unlock <用户名>
python manage.py user unlock admin

# 删除用户
python manage.py user delete <用户名>
python manage.py user delete testuser

# 清理默认测试用户（Tom, user）
python manage.py user clean-defaults
```

**配置文件格式 (admin_config.json)：**

```json
{
  "admin_user": {
    "username": "admin",
    "email": "admin@example.com",
    "password": "Admin@123456",
    "force_password_change": true
  }
}
```

---

### 项目同步 (project)

管理项目数据，从 Redis 同步队列任务的项目配置。

```bash
# 从 Redis 同步项目
python manage.py project sync

# 列出所有项目
python manage.py project list

# 查看项目详情
python manage.py project info <项目代码>
python manage.py project info my_project

# 清理无效项目（数据库中有但 Redis 中没有的项目）
python manage.py project clean
python manage.py project clean --force    # 强制删除（包括有用户关联的项目）
```

**项目来源：**

项目名称来自队列任务的 `@boost` 装饰器中的 `project_name` 参数：

```python
@boost(BoosterParams(
    queue_name='my_queue',
    project_name='my_project',  # 这个会同步到项目管理
    broker_kind=BrokerEnum.REDIS,
))
def my_task(x: int):
    pass
```

---

### 环境检查 (env)

检查运行环境，包括 Python、Node.js、Redis 和依赖安装状态。

```bash
# 检查所有环境
python manage.py env check

# 检查 Python 版本
python manage.py env python

# 检查 Node.js/npm
python manage.py env node

# 检查 Redis 连接
python manage.py env redis

# 检查 Python 依赖
python manage.py env deps
```

**环境要求：**

| 组件    | 最低版本 | 说明         |
| ------- | -------- | ------------ |
| Python  | 3.9+     | 推荐 3.11    |
| Node.js | 16+      | 推荐 18 LTS  |
| Redis   | 5.0+     | 用于消息队列 |

---

### 配置管理 (config)

管理配置文件和环境变量。

```bash
# 显示所有配置
python manage.py config show

# 显示配置文件内容
python manage.py config show --type config

# 显示环境变量
python manage.py config show --type env

# 以 JSON 格式显示
python manage.py config show --format json

# 获取单个配置值
python manage.py config get admin_user.username
python manage.py config get REDIS_HOST

# 设置配置值
python manage.py config set admin_user.email admin@example.com
python manage.py config set REDIS_HOST 127.0.0.1

# 验证配置
python manage.py config validate

# 初始化配置文件（从示例文件创建）
python manage.py config init
python manage.py config init --force    # 强制覆盖

# 列出所有可用配置项
python manage.py config list-keys

# 导出配置
python manage.py config export
python manage.py config export --output config_backup.json
```

---

## 目录结构

```
scripts/
├── README.md                # 本文档
├── setup.sh                 # macOS/Linux 快捷脚本
├── setup.bat                # Windows 快捷脚本
└── cli/                     # CLI 工具模块
    ├── __init__.py
    ├── main.py              # CLI 主程序（命令路由、交互式菜单）
    ├── commands/            # 命令模块
    │   ├── __init__.py
    │   ├── init.py          # 初始化命令
    │   ├── db.py            # 数据库命令
    │   ├── user.py          # 用户管理命令
    │   ├── service.py       # 服务管理命令
    │   ├── env.py           # 环境检查命令
    │   ├── project.py       # 项目同步命令
    │   ├── config.py        # 配置管理命令
    │   └── logs.py          # 日志查看命令
    └── utils/               # 工具模块
        ├── __init__.py
        ├── console.py       # 控制台输出（彩色、表格、进度条）
        ├── platform.py      # 跨平台工具（路径、命令）
        ├── process.py       # 进程管理（启动、停止、端口检查）
        ├── network.py       # 网络检查（Redis、HTTP 服务）
        └── config.py        # 配置管理工具
```

---

## 故障排除

### 1. Python 版本过低

**错误信息：**

```
Python 版本过低: 3.7.9 (需要 3.9+)
```

**解决方法：**

```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11

# Windows
# 从 https://www.python.org/downloads/ 下载安装
```

---

### 2. Node.js 未安装

**错误信息：**

```
Node.js 未安装
```

**解决方法：**

```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Windows
# 从 https://nodejs.org/ 下载安装

# 推荐使用 nvm 管理版本
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
```

---

### 3. Redis 未启动

**错误信息：**

```
Redis 连接失败: Connection refused
```

**解决方法：**

```bash
# macOS
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis

# Windows
# 启动 Redis 服务

# Docker
docker run -d -p 6379:6379 redis
```

---

### 4. 端口被占用

**错误信息：**

```
端口 27018 已被占用 (PID: 12345)
```

**解决方法：**

```bash
# 方法 1：使用 CLI 停止服务
python manage.py stop

# 方法 2：手动终止进程
# macOS/Linux
kill 12345

# Windows
taskkill /F /PID 12345
```

---

### 5. 数据库不存在

**错误信息：**

```
数据库不存在，请先初始化
```

**解决方法：**

```bash
python manage.py db init
```

---

### 6. 数据库迁移未执行

**错误信息：**

```
no such column: permissions.action_type
```

**解决方法：**

```bash
python manage.py db migrate
```

---

### 7. 用户被锁定

**错误信息：**

```
用户已被锁定，请稍后再试
```

**解决方法：**

```bash
python manage.py user unlock <用户名>
```

---

### 8. 前端依赖未安装

**错误信息：**

```
前端依赖未安装
```

**解决方法：**

```bash
cd web-manager-frontend
npm install
```

或使用 CLI：

```bash
python manage.py init --skip-venv --skip-deps --skip-db --skip-user
```

---

### 9. 权限不完整

**问题：** admin 用户登录后很多功能看不到

**解决方法：**

```bash
# 重新初始化权限
python manage.py db init

# 或手动更新（Python）
python -c "
from funboost.funboost_web_manager.user_models import get_session, Role, Permission
session = get_session('sqlite:///./web_manager_users.db')
admin_role = session.query(Role).filter(Role.name == 'admin').first()
all_permissions = session.query(Permission).all()
admin_role.permissions = all_permissions
session.commit()
session.close()
print('admin 角色权限已更新')
"
```

---

### 10. Cookie 跨域问题（Mac Chrome）

**问题：** 用 Chrome 访问 `localhost:3000` 登录成功后立即跳回登录页

**原因：** Chrome 对 `localhost` 和 `127.0.0.1` 的 Cookie 处理有差异

**解决方法：**

使用 `127.0.0.1` 而不是 `localhost` 访问：

```
http://127.0.0.1:3000
```

---

### 11. 项目同步失败

**错误信息：**

```
Redis 中没有找到项目名称
```

**原因：** 队列任务没有配置 `project_name` 参数

**解决方法：**

在队列任务中添加 `project_name`：

```python
@boost(BoosterParams(
    queue_name='my_queue',
    project_name='my_project',  # 添加这个参数
    broker_kind=BrokerEnum.REDIS,
))
def my_task(x: int):
    pass
```

---

### 12. 日志文件不存在

**错误信息：**

```
日志文件不存在: backend.log
```

**原因：** 服务尚未启动，日志文件在服务启动后自动创建

**解决方法：**

```bash
# 先启动服务
python manage.py start

# 然后查看日志
python manage.py logs backend
```

---

## 旧脚本迁移

如果你之前使用旧脚本，请参考以下迁移表：

| 旧脚本                                 | 新命令                                                    |
| -------------------------------------- | --------------------------------------------------------- |
| `python scripts/init_database.py init` | `python manage.py db init`                                |
| `python scripts/setup_admin.py`        | `python manage.py user create`                            |
| `python scripts/start_services.py`     | `python manage.py start`                                  |
| `python scripts/stop_services.py`      | `python manage.py stop`                                   |
| `python setup_admin_from_config.py`    | `python manage.py user create --config admin_config.json` |
| `python init_roles_permissions.py`     | `python manage.py db init`                                |
| `./start_all.sh`                       | `python manage.py start`                                  |
| `./stop_all.sh`                        | `python manage.py stop`                                   |

---

## 获取帮助

```bash
# 查看所有命令
python manage.py --help

# 查看特定命令帮助
python manage.py db --help
python manage.py user --help
python manage.py logs --help
```

如有问题，请查看 `.kiro/steering/common-pitfalls.md` 文件获取更多踩坑记录和解决方案。
