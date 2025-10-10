# 🔍 GitHub Sentinel - 智能仓库监控系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GitHub Sentinel 是一个智能的 GitHub 仓库监控和更新通知系统，帮助开发者及时了解关注仓库的最新动态。

## ✨ 主要特性

### 🎯 核心功能
- **智能监控**: 自动监控 GitHub 仓库的提交、发布、Issues 和 Pull Requests
- **多频率扫描**: 支持每日、每周和自定义频率的监控
- **智能报告**: 使用 LLM 生成结构化的更新报告和摘要
- **多渠道通知**: 支持邮件、Webhook、Slack、Discord 等多种通知方式

### 🌐 Web 界面
- **友好的图形化界面**: 基于 Gradio 的现代化 Web 界面
- **订阅管理**: 直观的仓库订阅添加、删除和管理功能
- **报告生成**: 在线生成和查看监控报告
- **系统监控**: 实时查看系统状态和执行手动扫描

### 🛠 技术特性
- **异步处理**: 基于 asyncio 的高性能异步架构
- **灵活配置**: YAML 配置文件支持个性化设置
- **数据持久化**: SQLite 数据库存储订阅和历史数据
- **定时任务**: 智能任务调度器自动执行监控任务

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Git

### 安装

1. **克隆仓库**
```bash
git clone https://github.com/your-username/Github_Sentinel_Learning.git
cd Github_Sentinel_Learning
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置设置**
```bash
# 复制配置文件模板
cp src/config/config.yaml.example src/config/config.yaml

# 编辑配置文件，添加你的 GitHub Token 和其他设置
# 详见配置说明部分
```

### 启动 Web 界面

#### 方法 1: 使用专用启动脚本
```bash
python web_app.py
```

#### 方法 2: 使用命令行参数
```bash
python src/main.py --web --port 7860 --host 0.0.0.0
```

#### 方法 3: 创建公共分享链接
```bash
python src/main.py --web --share
```

启动后访问: `http://localhost:7860`

### 启动后台服务

```bash
python src/main.py
```

## 🎛 Web 界面使用指南

### 📚 订阅管理

1. **添加新订阅**
   - 输入 GitHub 仓库 URL (如: `https://github.com/microsoft/vscode`)
   - 选择更新频率: 每日、每周或两者
   - 选择通知方式: 邮件、Webhook、Slack、Discord
   - 选择监控内容: 提交、Issues、PR、发布或全部

2. **管理现有订阅**
   - 查看所有订阅的状态和详细信息
   - 通过订阅 ID 删除不需要的订阅
   - 实时刷新订阅列表

### 📊 报告生成

1. **即时报告生成**
   - 每日报告: 过去24小时的更新
   - 每周报告: 过去7天的更新汇总
   - 自定义报告: 指定天数范围的更新

2. **历史报告查看**
   - 浏览之前生成的所有报告
   - 查看报告生成时间和文件大小

### ⚙️ 系统监控

1. **系统状态查看**
   - 当前订阅数量和活跃状态
   - 系统运行时间和最后检查时间
   - 订阅详细信息预览

2. **手动扫描执行**
   - 立即执行每日或每周扫描任务
   - 查看扫描结果和处理状态

## 📋 CLI 使用指南

### 基本命令

```bash
# 启动 Web 界面
python src/main.py --web

# 启动后台监控服务
python src/main.py

# 使用自定义配置文件
python src/main.py --config /path/to/config.yaml

# 指定 Web 界面端口和主机
python src/main.py --web --port 8080 --host 127.0.0.1

# 创建公共分享链接
python src/main.py --web --share
```

### 命令行参数

- `--config, -c`: 指定配置文件路径
- `--web`: 启动 Web 界面模式
- `--port`: Web 界面端口 (默认: 7860)
- `--host`: Web 界面主机 (默认: 0.0.0.0)
- `--share`: 创建 Gradio 公共分享链接

## ⚙️ 配置说明

### 配置文件结构 (config.yaml)

```yaml
# GitHub API 配置
github:
  token: "your_github_token_here"  # GitHub Personal Access Token
  api_url: "https://api.github.com"

# 数据库配置
database:
  path: "data/subscriptions.json"  # 数据存储路径

# LLM 配置
llm:
  provider: "openai"  # LLM 提供者
  model: "gpt-3.5-turbo"  # 使用的模型
  api_key: "your_openai_api_key"  # API 密钥

# 调度配置
scheduler:
  daily_scan_time: "09:00"    # 每日扫描时间
  weekly_scan_day: "monday"   # 每周扫描日期
  weekly_scan_time: "10:00"   # 每周扫描时间

# 通知配置
notifications:
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "your_email@gmail.com"
    password: "your_app_password"
  
  slack:
    webhook_url: "https://hooks.slack.com/services/..."
  
  discord:
    webhook_url: "https://discord.com/api/webhooks/..."

# 日志配置
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/github_sentinel.log"
```

### 获取 GitHub Token

1. 访问 GitHub Settings > Developer settings > Personal access tokens
2. 点击 "Generate new token"
3. 选择所需权限: `repo`, `user`, `read:org`
4. 复制生成的 token 到配置文件

## 📁 项目结构

```
Github_Sentinel_Learning/
├── src/                     # 源代码目录
│   ├── __init__.py
│   ├── main.py             # 主入口文件
│   ├── cli/                # 命令行界面
│   ├── config/             # 配置管理
│   ├── models/             # 数据模型
│   ├── services/           # 业务服务
│   │   ├── github_service.py      # GitHub API 服务
│   │   ├── llm_service.py         # LLM 服务
│   │   ├── notification_service.py # 通知服务
│   │   ├── report_service.py      # 报告生成服务
│   │   ├── subscription_service.py # 订阅管理服务
│   │   ├── update_service.py      # 更新检测服务
│   │   └── web_service.py         # Web界面服务
│   └── utils/              # 工具模块
├── tests/                  # 测试文件
├── data/                   # 数据目录
│   ├── subscriptions.json  # 订阅数据
│   └── reports/            # 生成的报告
├── logs/                   # 日志文件
├── web_app.py             # Web界面快速启动脚本
├── requirements.txt       # 依赖包列表
└── README.md             # 项目文档
```

## 🔧 开发指南

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/ tests/
```

### 类型检查

```bash
mypy src/
```

## 📊 功能特性详解

### 监控功能

- **提交监控**: 跟踪仓库的最新提交和代码变更
- **发布监控**: 监控新版本发布和 Release Notes
- **Issues 监控**: 跟踪新建和更新的问题
- **Pull Request 监控**: 监控合并请求的状态变化

### 报告生成

- **智能摘要**: 使用 LLM 生成易读的更新摘要
- **分类整理**: 按类型和重要性对更新进行分类
- **多格式输出**: 支持 Markdown、HTML、JSON 等格式
- **历史归档**: 自动保存和管理历史报告

### 通知系统

- **多渠道支持**: 邮件、Slack、Discord、Webhook
- **智能过滤**: 基于规则和优先级的通知过滤
- **批量发送**: 高效的批量通知处理
- **失败重试**: 自动重试失败的通知

## 🤝 贡献指南

欢迎贡献代码! 请遵循以下步骤:

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持和反馈

- **Issues**: [GitHub Issues](https://github.com/your-username/Github_Sentinel_Learning/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-username/Github_Sentinel_Learning/discussions)
- **邮件**: your-email@example.com

## 🗺 更新日志

### v0.2.0 (2025-10-09)
- ✨ 新增 Gradio Web 图形化界面
- 🎨 订阅管理界面
- 📊 在线报告生成功能
- ⚙️ 系统状态监控面板
- 🔧 改进的命令行界面

### v0.1.0
- 🎯 基础监控功能
- 📧 多渠道通知支持
- 🤖 LLM 智能报告生成
- ⏰ 定时任务调度

## 🔮 未来计划

- [ ] 支持更多 Git 平台 (GitLab, Bitbucket)
- [ ] 移动端推送通知
- [ ] 高级数据分析和可视化
- [ ] API 接口开放
- [ ] Docker 容器化部署
- [ ] 多用户管理系统

---

⭐ 如果这个项目对你有帮助，请给它一个星标！
