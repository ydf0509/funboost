# Funboost Web Manager 前端

基于 Next.js 16 的 Funboost Web Manager 前端应用。

## 环境要求

### Node.js 版本
- **Node.js**: 20.x 或更高版本
- **npm**: 随 Node.js 自动安装

### 推荐的 Node.js 安装方式

#### macOS
```bash
# 使用 Homebrew 安装
brew install node@20
```

#### Linux (Ubuntu/Debian)
```bash
# 使用 NodeSource 仓库安装
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Windows
从 [Node.js 官网](https://nodejs.org/) 下载并安装 LTS 版本。

## 开发顺序

### 1. 安装依赖

```bash
# 进入前端目录
cd web-manager-frontend

# 安装项目依赖
npm install
```

### 2. 配置后端数据库

在使用前端之前，需要先配置并初始化后端数据库。

#### 2.1 配置数据库 URL

在 `funboost/funboost_config_deafult.py` 中配置数据库 URL：

```python
class FunboostCommonConfig:
    # 使用 SQLite（默认）
    WEB_MANAGER_DB_URL = 'sqlite:///./web_manager_users.db'

    # 或使用 MySQL
    # WEB_MANAGER_DB_URL = 'mysql+pymysql://user:password@localhost:3306/funboost_web_manager'

    # 或使用 PostgreSQL
    # WEB_MANAGER_DB_URL = 'postgresql://user:password@localhost:5432/funboost_web_manager'
```

#### 2.2 初始化数据库

使用管理工具初始化数据库：

```bash
# 在项目根目录执行
python set_web_manage.py db init
```

这会执行以下操作：
- 创建数据库表结构
- 运行数据库迁移
- 初始化默认权限

#### 2.3 创建管理员用户

```bash
# 创建管理员用户
python set_web_manage.py user create
```

按照提示输入用户名、密码等信息。

### 3. 启动开发服务器

```bash
# 启动前端开发服务器
npm run dev
```

前端将在 `http://127.0.0.1:3000` 启动。

### 4. 启动后端服务

在另一个终端中：

```bash
# 启动后端服务
python set_web_manage.py start --backend
```

后端将在 `http://127.0.0.1:27018` 启动。

## 生产构建

### 构建并部署前端

```bash
# 构建前端并复制到 Flask 静态目录
npm run build:deploy
```

构建产物将输出到 `../funboost/funboost_web_manager/static/frontend` 目录。

### 仅构建（不部署）

```bash
npm run build
```

构建产物将输出到本地 `out/` 目录。

### 启动生产服务

```bash
# 启动所有服务（前端 + 后端）
python set_web_manage.py start
```

## 环境变量

前端支持以下环境变量：

- `BACKEND_PORT`: 后端端口，默认 27018
- `ALLOWED_HOSTS`: 允许的主机名列表，逗号分隔，默认 "localhost,127.0.0.1"

在 `.env.local` 文件中配置：

```env
BACKEND_PORT=27018
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

## 可用命令

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 构建并部署到 Flask 静态目录
npm run build:deploy

# 启动生产服务器
npm start

# 代码检查
npm run lint

# 运行测试
npm test

# 运行测试（监视模式）
npm run test:watch
```

## 项目结构

```
web-manager-frontend/
├── src/              # 源代码目录
├── public/           # 静态资源
├── next.config.ts    # Next.js 配置
├── package.json      # 项目依赖和脚本
├── tsconfig.json     # TypeScript 配置
└── tailwind.config.ts # Tailwind CSS 配置
```

## 常见问题

### Q: 构建时出现 Node 版本错误
A: 请确保使用 Node.js 20.x 或更高版本。可以使用 `nvm` 管理多个 Node 版本。

### Q: 前端无法连接后端 API
A: 检查以下几点：
1. 后端服务是否已启动
2. BACKEND_PORT 环境变量是否正确
3. ALLOWED_HOSTS 是否包含当前访问的域名

### Q: 数据库初始化失败
A: 确保：
1. 数据库 URL 配置正确
2. 数据库服务已启动（如使用 MySQL/PostgreSQL）
3. 有足够的数据库操作权限

## 技术栈

- **框架**: Next.js 16
- **UI**: React 19
- **样式**: Tailwind CSS 4
- **图表**: ECharts
- **图标**: Lucide React
- **测试**: Vitest + Testing Library
- **语言**: TypeScript
