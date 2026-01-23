# Funboost Web Manager 前端

基于 Next.js 16 的 Funboost Web Manager 可视化管理界面。

## 🖥️ 功能预览

Funboost Web Manager 提供强大的监控与运维能力：

| 功能模块     | 说明                                                                  |
| :----------- | :-------------------------------------------------------------------- |
| **函数结果** | 查看和搜索函数实时消费状态和结果                                      |
| **队列操作** | 清空、暂停消费、恢复消费、调整 QPS 和并发                             |
| **消费曲线** | 查看历史运行次数、失败次数、近10秒完成/失败、平均耗时、剩余消息数量等 |
| **RPC 调用** | 在网页上对 30 种消息队列发布消息并获取函数执行结果                    |
| **定时任务** | 管理 APScheduler 定时任务，支持启动/暂停/删除                         |

## 🚀 快速开始

### 环境要求

- **Node.js**: 20.x 或更高版本
- **Python**: 3.8+ (后端)

### 1. 安装依赖

```bash
cd web-manager-frontend
npm install
```

### 2. 配置后端数据库

在 `funboost_config.py` 中配置数据库 URL：

```python
class FunboostCommonConfig:
    # SQLite（默认）
    WEB_MANAGER_DB_URL = 'sqlite:///./web_manager_users.db'

    # 或 MySQL
    # WEB_MANAGER_DB_URL = 'mysql+pymysql://user:password@localhost:3306/funboost_web_manager'
```

初始化数据库并创建管理员：

```bash
python set_web_manage.py db init
python set_web_manage.py user create
```

### 3. 启动服务

**开发模式**（前后端分离）：

```bash
# 终端 1：启动前端
npm run dev

# 终端 2：启动后端
python set_web_manage.py start --backend
```

**生产模式**（一键启动）：

```bash
# 构建前端并部署到 Flask 静态目录
npm run build:deploy

# 启动服务
python set_web_manage.py start
```

## 📦 可用命令

| 命令                   | 说明                        |
| :--------------------- | :-------------------------- |
| `npm run dev`          | 开发模式，热更新            |
| `npm run build`        | 构建生产版本                |
| `npm run build:deploy` | 构建并部署到 Flask 静态目录 |
| `npm run lint`         | 代码检查                    |
| `npm test`             | 运行测试                    |

## 🔧 环境变量

在 `.env.local` 中配置：

```env
BACKEND_PORT=27018
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

## 🛠️ 技术栈

- **框架**: Next.js 16 + React 19
- **样式**: Tailwind CSS 4
- **图表**: ECharts
- **图标**: Lucide React
- **测试**: Vitest + Testing Library
- **语言**: TypeScript

## ❓ 常见问题

**Q: 前端无法连接后端 API**

检查：

1. 后端服务是否已启动 (`python set_web_manage.py start --backend`)
2. `BACKEND_PORT` 环境变量是否正确
3. `ALLOWED_HOSTS` 是否包含当前访问的域名

**Q: 数据库初始化失败**

确保：

1. 数据库 URL 配置正确
2. 数据库服务已启动（如使用 MySQL/PostgreSQL）
3. 有足够的数据库操作权限

## 📚 更多文档

- [Funboost 完整文档](https://funboost.readthedocs.io/zh-cn/latest/index.html)
- [Web Manager 使用指南](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html)
- [AI 辅助学习指南](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html)

