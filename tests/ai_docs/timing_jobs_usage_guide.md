# Funboost 定时任务管理界面使用说明

## 🎉 功能已完成！

定时任务管理功能已经完整集成到 Funboost 管理界面中！

## 📁 已创建/修改的文件

### 1. 新增文件
- `funboost/funboost_web_manager/templates/timing_jobs_management.html` - 定时任务管理页面

### 2. 修改文件
- `funboost/funboost_web_manager/templates/index.html` - 导航栏添加"定时任务管理"菜单项
- `funboost/funboost_web_manager/app.py` - 已注册 flask_blueprint（你自己添加的）
- `funboost/faas/flask_adapter.py` - 已添加7个定时任务接口

## 🚀 如何使用

### 启动服务

你已经在 `app.py` 中注册了 `flask_blueprint`，所以直接启动 Flask 服务即可：

```python
from funboost.funboost_web_manager.app import start_funboost_web_manager

start_funboost_web_manager(
    host="0.0.0.0",
    port=27018,
    debug=False
)
```

或者直接运行：
```bash
python -m funboost.funboost_web_manager.app
```

### 访问界面

1. 打开浏览器访问: `http://localhost:27018`
2. 使用账号登录 (admin/123456 或 user/mtfy123)
3. 点击左侧导航栏的 **"定时任务管理"** 菜单（时钟图标）

## 📖 功能说明

### 1. 任务列表
- 显示所有定时任务
- 支持按队列名、任务ID搜索
- 支持按队列筛选
- 自动刷新功能（10秒间隔）

### 2. 添加任务
点击 **"添加任务"** 按钮，支持三种触发器：

#### 一次性任务 (date)
```
触发器: date
执行时间: 2025-12-15 10:00:00
说明: 在指定时间执行一次后自动删除
```

#### 间隔执行 (interval)
```
触发器: interval
示例1: 每10分钟 → 分钟: 10
示例2: 每2小时 → 小时: 2
示例3: 每天 → 天: 1
```

#### 定时执行 (cron)
```
触发器: cron
示例1: 每天上午9点 → 时:9 分:0 秒:0
示例2: 每2小时 → 时:*/2 分:0
示例3: 工作日上午10点 → 星期:0-4 时:10 分:0

Cron语法:
* = 任意值
*/n = 每n个单位
1-5 = 范围
1,3,5 = 列举
```

### 3. 任务操作
每个任务都可以进行以下操作：
- **详情**: 查看任务的详细信息
- **暂停**: 暂停任务执行
- **删除**: 删除任务（不可撤销）

### 4. 批量操作
- **删除所有任务**: 可以删除指定队列或所有队列的任务

## 🎨 界面特点

### 1. 与现有管理界面完全统一
- 使用相同的 Bootstrap 3.3.7 主题
- 使用相同的 Tabulator 5.5.0 表格
- 使用相同的配色方案和图标
- 使用相同的模态框交互模式

### 2. 友好的用户体验
- 智能表单：根据触发器类型动态显示配置项
- 实时验证：添加任务前验证必填项
- 操作确认：危险操作（删除）需要二次确认
- 状态提示：所有操作都有成功/失败提示

### 3. 响应式设计
- 表格支持横向滚动
- 分页显示，默认每页50条
- 支持排序和搜索

## 📊 数据流程

```
用户操作 → 前端页面 → AJAX请求 
→ Flask Blueprint (/funboost/*) 
→ ApsJobAdder 
→ APScheduler 
→ Redis/Memory
```

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Bootstrap 3.3.7 |
| 表格组件 | Tabulator 5.5.0 |
| 图标库 | Font Awesome 4.7.0 |
| AJAX | jQuery 1.11.0 |
| 后端框架 | Flask |
| 后端接口 | Flask Blueprint |
| 定时任务 | APScheduler |
| 任务存储 | Redis / Memory |

## 🎯 接口列表

所有接口都在 `/funboost/` 路径下：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /funboost/add_timing_job | 添加定时任务 |
| GET | /funboost/get_timing_jobs | 获取任务列表 |
| GET | /funboost/get_timing_job | 获取任务详情 |
| DELETE | /funboost/delete_timing_job | 删除任务 |
| DELETE | /funboost/delete_all_timing_jobs | 删除所有任务 |
| POST | /funboost/pause_timing_job | 暂停任务 |
| POST | /funboost/resume_timing_job | 恢复任务 |

## 💡 使用示例

### 示例1：每10分钟执行数据同步
```
队列名称: data_sync_queue
触发器类型: interval
分钟: 10
存储方式: Redis
```

### 示例2：每天凌晨2点备份数据
```
队列名称: backup_queue
触发器类型: cron
时: 2
分: 0
秒: 0
存储方式: Redis
```

### 示例3：明天上午10点发送通知
```
队列名称: notification_queue
触发器类型: date
执行时间: 2025-12-12 10:00:00
存储方式: Redis
```

## ⚠️ 注意事项

### 1. 队列必须存在
添加定时任务前，确保队列已通过 `@boost` 装饰器注册。

### 2. 存储方式选择
- **Redis** (推荐): 支持分布式，任务持久化，多进程共享
- **Memory**: 仅内存存储，进程重启后任务丢失，适合测试

### 3. 任务ID
- 留空自动生成
- 自定义时建议使用有意义的命名
- 相同ID会覆盖（需勾选"替换"选项）

### 4. 时区设置
默认使用系统时区，可在 `funboost_config.py` 中配置：
```python
from funboost.funboost_config_deafult import FunboostCommonConfig
FunboostCommonConfig.TIMEZONE = 'Asia/Shanghai'
```

### 5. 分布式部署
多个进程使用相同的 Redis 存储时，任务只会执行一次（自动去重）。

## 🐛 常见问题

### Q1: 添加任务后不执行？
**A**: 检查以下几点：
1. 确保消费者进程正在运行
2. 检查任务的下次执行时间是否正确
3. 查看消费者日志是否有错误

### Q2: 任务ID填错了怎么办？
**A**: 删除任务重新添加，或者勾选"替换"选项重新添加同ID任务

### Q3: 如何查看任务执行历史？
**A**: 当前版本不支持，可以查看消费函数的执行日志

### Q4: 可以修改已存在的任务吗？
**A**: 当前不支持直接修改，需要删除后重新添加，或勾选"替换"选项添加同ID任务

## 📚 相关文档

- [接口使用文档](./flask_timing_job_api_usage.md)
- [界面设计文档](./timing_jobs_ui_design.md)

## 🎊 完成清单

✅ 定时任务管理页面 (`timing_jobs_management.html`)
✅ 导航栏菜单项（时钟图标）
✅ 7个后端接口（Flask Blueprint）
✅ 任务列表表格（Tabulator）
✅ 添加任务模态框（三种触发器）
✅ 任务详情查看
✅ 暂停/删除任务
✅ 批量删除任务
✅ 搜索和筛选功能
✅ 自动刷新功能
✅ 与现有风格完全统一

---

## 🚀 现在就可以使用了！

启动 Flask 服务，访问管理界面，点击"定时任务管理"菜单，开始管理你的定时任务吧！🎉
