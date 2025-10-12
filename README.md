# 🔍 GitHub Sentinel - 智能监控系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GitHub Sentinel 是一个智能的多平台监控和更新通知系统，帮助开发者及时了解GitHub仓库和Hacker News的最新动态。

## ✨ 主要特性

### 🎯 核心功能
- **GitHub监控**: 自动监控 GitHub 仓库的提交、发布、Issues 和 Pull Requests
- **Hacker News监控**: 实时跟踪热门技术话题和讨论
- **守护进程管理**: 跨平台的后台服务管理（Windows/Linux）
- **多频率扫描**: 支持每日、每周和小时级别的监控
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
- **跨平台支持**: Windows 和 Linux 系统完整支持

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

## 🎮 使用方式

### 守护进程管理（推荐）

#### Windows 系统
```cmd
# 启动所有监控服务（GitHub + Hacker News）
.\daemon.bat start

# 查看服务状态
.\daemon.bat status

# 停止所有服务
.\daemon.bat stop

# 重启服务
.\daemon.bat restart

# Hacker News 相关操作
.\daemon.bat hackernews latest --limit 10    # 获取最新热门话题
.\daemon.bat hackernews report --hours 12    # 生成12小时报告
.\daemon.bat hackernews summary              # 生成日度总结
.\daemon.bat hackernews status               # 查看服务状态
.\daemon.bat hackernews history --limit 5    # 查看报告历史
```

#### Linux 系统
```bash
# 启动所有监控服务
./daemon.sh start

# 前台运行模式（用于调试）
./daemon.sh start --foreground

# 查看服务状态和日志
./daemon.sh status

# Hacker News 相关操作
./daemon.sh hackernews latest --limit 10
./daemon.sh hackernews report --hours 12
./daemon.sh hackernews summary
./daemon.sh hackernews status
./daemon.sh hackernews history --limit 5
```

### Web 界面启动

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

### 直接命令行使用

```bash
# 启动后台监控服务
python src/main.py

# Hacker News CLI 操作
python src/cli/hackernews_cli.py latest --limit 20
python src/cli/hackernews_cli.py report --hours 24
python src/cli/hackernews_cli.py summary
python src/cli/hackernews_cli.py status
python src/cli/hackernews_cli.py history --limit 10
```

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
├── daemon.bat                   # Windows 守护进程管理脚本
├── daemon.sh                    # Linux 守护进程管理脚本
├── web_app.py                   # Web界面快速启动脚本
├── requirements.txt             # 依赖包列表
├── README.md                    # 项目文档
├── SETUP_GUIDE.md              # 详细设置指南
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── main.py                 # 主入口文件
│   ├── daemon_process.py       # 守护进程管理器
│   ├── cli/                    # 命令行界面
│   │   ├── commands.py         # GitHub CLI 命令
│   │   └── hackernews_cli.py   # Hacker News CLI 工具
│   ├── config/                 # 配置管理
│   │   ├── config.yaml         # 主配置文件
│   │   └── settings.py         # 配置处理器
│   ├── models/                 # 数据模型
│   │   ├── subscription.py     # 订阅模型
│   │   ├── repository.py       # 仓库模型
│   │   ├── report.py          # 报告模型
│   │   ├── notification.py     # 通知模型
│   │   └── hackernews.py       # Hacker News 模型
│   ├── services/               # 业务服务
│   │   ├── github_service.py           # GitHub API 服务
│   │   ├── hackernews_service.py       # Hacker News API 服务
│   │   ├── hackernews_report_service.py # HN 报告生成服务
│   │   ├── hackernews_update_service.py # HN 更新监控服务
│   │   ├── llm_service.py              # LLM 服务
│   │   ├── notification_service.py     # 通知服务
│   │   ├── report_service.py           # 报告生成服务
│   │   ├── subscription_service.py     # 订阅管理服务
│   │   ├── update_service.py           # 更新检测服务
│   │   └── web_service.py              # Web界面服务
│   └── utils/                  # 工具模块
│       ├── database.py         # 数据库工具
│       ├── logger.py           # 日志工具
│       └── scheduler.py        # 任务调度器
├── tests/                      # 测试文件
│   ├── test_services.py        # 服务测试
│   ├── test_models.py          # 模型测试
│   ├── test_utils.py           # 工具测试
│   └── test_v02_features.py    # v0.2 功能测试
├── data/                       # 数据目录
│   ├── subscriptions.json      # GitHub 订阅数据
│   ├── hackernews_subscriptions.json # HN 订阅数据
│   └── reports/               # 生成的报告
├── daily_progress/            # 日常监控报告
│   ├── hackernews_*.md        # Hacker News 报告
│   └── hackernews_summary_*.md # HN 日度总结
├── logs/                      # 日志文件
│   ├── github_sentinel.log    # 主程序日志
│   ├── daemon.log            # 守护进程日志
│   ├── cli.log               # CLI 工具日志
│   └── web_service.log       # Web 服务日志
├── run/                       # 运行时文件
│   └── github_sentinel.pid    # 守护进程PID文件
├── prompts/                   # LLM 提示词模板
│   ├── github_azure_prompt.txt        # GitHub 报告提示词
│   └── hacker_news_hours_topic_azure_prompt.txt # HN 报告提示词
└── release_notes/             # 版本发布说明
    ├── RELEASE_NOTES_v0.1.0.md
    └── RELEASE_NOTES_v0.2.0.md
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

## 🌟 Hacker News 监控功能

### 核心特性
- **实时热门话题追踪**: 自动抓取和分析 Hacker News 热门内容
- **智能报告生成**: 按时间段生成结构化的话题总结
- **定时监控**: 每小时自动扫描，每日生成总结
- **历史记录管理**: 完整的监控历史和报告归档

### 使用场景
- **技术趋势跟踪**: 了解最新的技术发展和行业动态
- **开发者社区洞察**: 掌握开发者关注的热点话题
- **竞品情报收集**: 监控相关技术和产品的讨论
- **学习资源发现**: 发现高质量的技术文章和资源

### 报告内容
- **话题标题和链接**: 完整的话题信息和访问链接
- **讨论热度**: 评分、评论数等热度指标
- **时间范围**: 可配置的监控时间窗口
- **智能分类**: 基于内容的话题分类和标签

## 🔄 守护进程架构

### 服务组件
- **GitHub 监控服务**: 定期扫描订阅的 GitHub 仓库
- **Hacker News 监控服务**: 实时跟踪热门技术话题
- **任务调度器**: 智能的定时任务管理
- **通知系统**: 多渠道的消息推送服务
- **报告生成器**: 基于 LLM 的智能报告生成

### 运行模式
- **后台守护进程**: 完全自动化的后台运行
- **前台调试模式**: 便于开发和调试的前台运行
- **Web 界面模式**: 图形化的管理和监控界面
- **CLI 工具模式**: 命令行操作和管理工具

## 🚦 服务状态管理

### 启动状态检查
```bash
# Windows
.\daemon.bat status

# Linux  
./daemon.sh status
```

### 日志查看
```bash
# 查看守护进程日志
tail -f logs/daemon.log

# 查看主程序日志
tail -f logs/github_sentinel.log

# 查看 Web 服务日志
tail -f logs/web_service.log
```

### 服务健康检查
- **PID 文件检查**: 验证守护进程是否正在运行
- **日志分析**: 检查最近的错误和警告信息
- **功能测试**: 验证各个服务组件的工作状态
- **资源监控**: 检查内存和CPU使用情况

## 🔧 故障排除

### 常见问题

1. **守护进程启动失败**
   - 检查 Python 环境是否正确安装
   - 确认所有依赖包已安装
   - 查看 `logs/daemon.log` 获取详细错误信息

2. **GitHub API 限制**
   - 确认 GitHub Token 是否有效
   - 检查 API 调用频率是否超限
   - 考虑使用企业级 Token 获得更高限制

3. **Hacker News 连接问题**
   - 检查网络连接是否正常
   - 确认防火墙没有阻止访问
   - 查看相关错误日志信息

4. **LLM 服务配置问题**
   - 验证 LLM API 密钥是否正确
   - 检查模型配置是否支持
   - 查看 LLM 服务的响应日志

### 调试模式

```bash
# 前台运行模式（便于调试）
python src/main.py --config src/config/config.yaml

# 启用详细日志
export LOG_LEVEL=DEBUG
python src/main.py

# Web 界面调试模式
python src/main.py --web --port 7860 --share
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

### GitHub 监控功能

- **提交监控**: 跟踪仓库的最新提交和代码变更
- **发布监控**: 监控新版本发布和 Release Notes
- **Issues 监控**: 跟踪新建和更新的问题
- **Pull Request 监控**: 监控合并请求的状态变化

### Hacker News 监控功能

- **热门话题追踪**: 实时获取评分最高的讨论话题
- **定时报告**: 可配置的时间间隔报告生成（1小时、6小时、12小时、24小时）
- **日度总结**: 每日自动生成的综合性话题总结
- **历史归档**: 完整的历史报告存储和管理

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

## 📈 性能特性

### 系统性能
- **异步架构**: 基于 asyncio 的高并发处理能力
- **资源优化**: 智能的内存和CPU使用管理
- **缓存机制**: 减少重复API调用的缓存系统
- **批量处理**: 高效的批量数据处理能力

### 监控效率
- **增量更新**: 只获取自上次检查以来的新内容
- **智能调度**: 根据仓库活跃度调整监控频率
- **错误恢复**: 自动处理网络异常和API限制
- **资源限制**: 遵守各平台的API调用限制

## 🔐 安全特性

### 数据安全
- **Token 保护**: 安全的API密钥存储和使用
- **本地存储**: 敏感数据仅存储在本地
- **加密传输**: 所有API通信使用HTTPS加密
- **访问控制**: 基于配置的访问权限管理

### 隐私保护
- **最小权限**: 仅请求必要的API权限
- **数据最小化**: 只收集和存储必要的数据
- **定期清理**: 自动清理过期的临时数据
- **透明度**: 完全开源，所有操作透明可见

## 🤝 贡献指南

我们欢迎所有形式的贡献！请遵循以下步骤：

### 代码贡献

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/Github_Sentinel_Learning.git
   cd Github_Sentinel_Learning
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **开发和测试**
   ```bash
   # 安装开发依赖
   pip install -r requirements.txt
   
   # 运行测试
   pytest tests/
   
   # 代码格式化
   black src/ tests/
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m 'Add some amazing feature'
   ```

5. **推送分支**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 详细描述你的更改
   - 确保所有测试通过

### 其他贡献方式

- **报告 Bug**: 在 Issues 中详细描述问题
- **功能建议**: 提出新功能的想法和建议
- **文档改进**: 帮助改进文档和示例
- **社区支持**: 帮助其他用户解决问题

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持和反馈

### 获取帮助
- **GitHub Issues**: [提交问题和Bug报告](https://github.com/your-username/Github_Sentinel_Learning/issues)
- **GitHub Discussions**: [参与社区讨论](https://github.com/your-username/Github_Sentinel_Learning/discussions)
- **邮件支持**: your-email@example.com

### 社区资源
- **Wiki**: 详细的使用指南和最佳实践
- **FAQ**: 常见问题和解决方案
- **示例**: 实际使用场景和配置示例

## 🗺 更新日志

### v0.2.0 (2025-10-12) - 最新版本
- ✨ **新增**: Hacker News 实时监控功能
- ✨ **新增**: 守护进程管理系统（Windows/Linux）
- ✨ **新增**: 跨平台shell脚本管理工具
- ✨ **新增**: Hacker News CLI 工具
- 🎨 **改进**: Web 界面用户体验优化
- 📊 **改进**: 报告生成系统增强
- ⚙️ **改进**: 配置管理系统完善
- 🔧 **修复**: 多项稳定性和性能问题

### v0.1.0 (2025-10-09)
- ✨ **新增**: Gradio Web 图形化界面
- 🎨 **新增**: 订阅管理界面
- 📊 **新增**: 在线报告生成功能
- ⚙️ **新增**: 系统状态监控面板
- 🔧 **改进**: 命令行界面优化

### v0.0.1
- 🎯 **基础**: GitHub 监控功能
- 📧 **基础**: 多渠道通知支持
- 🤖 **基础**: LLM 智能报告生成
- ⏰ **基础**: 定时任务调度

## 🔮 未来规划

### 短期目标 (Q4 2025)
- [ ] **移动端支持**: 开发移动应用和推送通知
- [ ] **Docker支持**: 容器化部署和编排
- [ ] **API接口**: RESTful API 和 WebSocket 支持
- [ ] **数据可视化**: 高级图表和仪表板

### 中期目标 (Q1-Q2 2026)
- [ ] **多平台扩展**: 支持 GitLab、Bitbucket 等平台
- [ ] **AI增强**: 更智能的内容分析和预测
- [ ] **团队协作**: 多用户和权限管理系统
- [ ] **企业功能**: SSO、审计日志、高级分析

### 长期目标 (2026+)
- [ ] **云服务**: SaaS 版本和托管服务
- [ ] **插件生态**: 第三方插件和扩展系统
- [ ] **国际化**: 多语言和本地化支持
- [ ] **机器学习**: 智能推荐和异常检测

## 🌟 致谢

感谢所有为这个项目做出贡献的开发者和用户！

### 技术栈
- **Python**: 核心开发语言
- **Gradio**: Web界面框架
- **AsyncIO**: 异步处理框架
- **Requests**: HTTP客户端库
- **PyYAML**: 配置文件处理
- **APScheduler**: 任务调度框架

### 特别感谢
- GitHub API 团队提供优秀的开发者接口
- Hacker News 社区提供丰富的技术内容
- 所有开源贡献者的无私奉献

---

⭐ **如果这个项目对你有帮助，请给它一个星标！**

📢 **欢迎分享给更多的开发者朋友！**

🚀 **让我们一起构建更好的开发者工具生态！**
