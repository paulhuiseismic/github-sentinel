# GitHub Sentinel

GitHub Sentinel 是一款开源工具类AI Agent，专为开发者和项目管理人员设计，能够定期（每日/每周）自动获取并汇总订阅的GitHub仓库最新动态。

## 🚀 主��功能

- **订阅管理**: 添加、删除、管理GitHub仓库订阅
- **更新获取**: 自动获取仓库的commits、issues、pull requests、releases等更新
- **通知系统**: 支持邮件、Slack、Discord、Webhook等多种通知方式
- **报告生成**: 生成详细的每日/每周更新报告
- **任务调度**: 支持定时任务，自动化监控流程

## 📦 安装

### 1. 克隆项目
```bash
git clone https://github.com/your-username/github-sentinel.git
cd github-sentinel
```

### 2. 创建虚拟环境
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

## ⚙️ 配置

### 1. 环境变量
创建 `.env` 文件或设置以下环境变量：

```bash
# GitHub API Token (必需)
GITHUB_TOKEN=your_github_token_here

# 邮件配置 (可选)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Slack配置 (可选)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Discord配置 (可选)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 2. 配置文件
编辑 `src/config/config.yaml` 文件：

```yaml
github:
  token: null  # 或直接在此设置token
  api_url: https://api.github.com
  rate_limit_per_hour: 5000

notification:
  email_smtp_server: null
  email_port: 587
  slack_webhook_url: null
  discord_webhook_url: null

log_level: INFO
daily_scan_time: "09:00"
weekly_scan_time: "09:00"
weekly_scan_day: monday
```

## 🎯 使用方法

### 命令行界面

#### 添加订阅
```bash
python -m src.cli.commands add https://github.com/owner/repo --frequency daily --notifications email slack
```

#### 列出订阅
```bash
python -m src.cli.commands list
```

#### 立即检查更新
```bash
python -m src.cli.commands check --days 1
```

#### 查看状态
```bash
python -m src.cli.commands status
```

### 启动守护进程
```bash
python -m src.main
```

### Python API

```python
from src.main import GitHubSentinel

# 创建应用实例
app = GitHubSentinel()

# 启动监控
app.start()
```

## 📋 订阅配置

### 支持的更新类型
- `commits`: 代码提交
- `issues`: 问题/议题
- `pull_requests`: 拉取请求
- `releases`: 版本发布
- `all`: 所有类型

### 支持的通知方式
- `email`: 邮件通知
- `slack`: Slack通知
- `discord`: Discord通知
- `webhook`: 自定义Webhook

### 更新频率
- `daily`: 每日检查
- `weekly`: 每周检查
- `both`: 同时支持每日和每周

## 🔧 高级配置

### 过滤器
可以为订阅设置过滤器，只接收感兴趣的更新：

```python
filters = {
    "authors": ["user1", "user2"],  # 只关注特定作者
    "exclude_authors": ["bot"],     # 排除特定作者
    "keywords": ["bug", "fix"],     # 包含关键词
    "exclude_keywords": ["test"],   # 排除关键词
    "update_types": ["commits", "releases"]  # 只关注特定类型
}
```

### 通知配置
每个订阅可以有独立的通知配置：

```python
notification_config = {
    "email_recipients": ["admin@company.com"],
    "webhook_url": "https://your-webhook.com/endpoint"
}
```

## 📊 报告格式

GitHub Sentinel 生成详细的HTML和文本格式报告，包含：

- 📈 更新统计摘要
- 📋 更新类型分布
- 👥 活跃贡献者排行
- 📝 详细更新列表
- 🔗 直接链接到GitHub

## 🏗️ 项目结构

```
github-sentinel/
├── src/
│   ├── config/          # 配置管理
│   ├── models/          # 数据模型
│   ├── services/        # 业务服务
│   ├── utils/           # 工具函数
│   ├── cli/             # 命令行接口
│   └── main.py          # 主入口
├── data/                # 数据存储
├── logs/                # 日志文件
├── tests/               # 测试文件
└── requirements.txt     # 依赖包
```

## 🧪 测试

运行测试套件：

```bash
python -m pytest tests/ -v
```

运行特定测试：

```bash
python -m pytest tests/test_models.py -v
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- GitHub API 提供强大的数据支持
- 感谢所有贡献者的支持

## 📞 支持

如有问题或建议，请：

- 提交 [Issue](https://github.com/your-username/github-sentinel/issues)
- 发送邮件到 support@github-sentinel.com
- 加入我们的 [Discord 社区](https://discord.gg/github-sentinel)

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！
