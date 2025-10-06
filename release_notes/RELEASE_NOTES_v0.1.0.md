# GitHub Sentinel v0.1.0 Release Notes

**发布日期:** 2025年10月6日  
**标签:** v0.1.0  
**分支:** main  
**类型:** Minor Release - New Features & Bug Fixes

## 🎉 版本概述

GitHub Sentinel v0.1.0 是一个重要的功能增强版本，修复了时区问题，并添加了强大的手动测试功能。本版本大幅提升了系统的稳定性和用户体验。

## ✨ 新增功能

### 🧪 手动测试扫描功能
- ✅ **新增 CLI 命令**: `test-scan` 允许立即触发扫描测试
- ✅ **灵活的测试选项**:
  ```bash
  # 测试每日扫描
  python -m src.cli.commands test-scan
  
  # 测试每周扫描
  python -m src.cli.commands test-scan --type weekly
  
  # 自定义扫描天数
  python -m src.cli.commands test-scan --days 3
  ```
- ✅ **即时反馈**: 无需等待调度时间即可验证功能
- ✅ **完整的测试覆盖**: 测试 GitHub API 连接、数据获取、错误处理

### 🔧 环境变量增强
- ✅ **python-dotenv 集成**: 自动加载 `.env` 文件中的环境变量
- ✅ **改进的配置管理**: 更好的环境变量和配置文件融合
- ✅ **开发友好**: 支持本地开发环境配置

## 🐛 重要修复

### 🕒 时区处理修复
- 🔧 **修复关键错误**: "can't compare offset-naive and offset-aware datetimes"
- 🔧 **影响范围**: 修复了获取 Pull Requests 和 Releases 时的崩溃问题
- 🔧 **解决方案**: 智能时区感知比较，自动处理 UTC 转换
- 🔧 **测试验证**: langchain-ai/langchain 等大型仓库现在可以正常扫描

## 🛠️ 技术改进

### 📝 代码质量
- 🔧 **时区处理标准化**: 统一的 datetime 时区处理机制
- 🔧 **错误处理增强**: 更精确的异常捕获和处理
- 🔧 **日志记录改进**: 增加调试级别日志，便于问题排查
- 🔧 **类型安全**: 改进的类型注解和验证

### 🏗️ 架构优化
- 🔧 **模块解耦**: 更好的服务层分离和依赖管理
- 🔧 **配置灵活性**: 支持多种配置来源的优先级处理
- 🔧 **测试能力**: 新增的手动测试功能便于开发和调试

## 📋 依赖更新

### 新增依赖
```
python-dotenv>=1.0.0    # 环境变量文件支持
```

### 现有依赖保持不变
- aiohttp>=3.8.0
- PyYAML>=6.0
- schedule>=1.2.0
- python-dateutil>=2.8.0

## 🔧 配置变更

### 环境变量支持
现在支持从 `.env` 文件自动加载环境变量：
```bash
# .env 文件示例
GITHUB_TOKEN=your_token_here
EMAIL_SMTP_SERVER=smtp.gmail.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## 🧪 测试指南

### 快速功能验证
```bash
# 1. 添加测试订阅
python -m src.cli.commands add https://github.com/langchain-ai/langchain

# 2. 立即测试扫描功能
python -m src.cli.commands test-scan

# 3. 查看系统状态
python -m src.cli.commands status
```

### 调度测试
```bash
# 1. 启动守护进程
python -m src.main

# 2. 观察日志输出，验证调度器正常工作
# 应该看到: "已调度每日任务，执行时间: XX:XX"
# 应该看到: "任务调度器已启动"
```

## 🐛 已知问题修复

### v0.0.1 中的问题
- ❌ ~~时区比较错误~~ → ✅ **已修复**: 实现了智能时区处理
- ❌ ~~环境变量加载问题~~ → ✅ **已修复**: 集成了 python-dotenv

## 🔄 升级指南

### 从 v0.0.1 升级到 v0.1.0

1. **更新依赖**:
   ```bash
   pip install python-dotenv>=1.0.0
   ```

2. **创建 .env 文件** (可选但推荐):
   ```bash
   cp .env.example .env
   # 编辑 .env 文件设置你的配置
   ```

3. **测试升级结果**:
   ```bash
   python -m src.cli.commands test-scan
   ```

4. **重启守护进程**:
   ```bash
   python -m src.main
   ```

### 配置兼容性
- ✅ 完全向后兼容 v0.0.1 的配置
- ✅ 现有订阅数据无需迁移
- ✅ 配置文件格式保持不变

## 🔮 下一版本预告 (v0.2.0)

### 计划功能
- 🔄 Web 管理界面
- 💾 SQLite/PostgreSQL 数据库支持  
- 📊 更丰富的报告模板
- 🔔 更多通知渠道 (钉钉、企业微信)
- 🐳 Docker 容器化支持

## 🤝 贡献者

感谢以下贡献：
- 时区处理优化和修复
- 手动测试功能开发
- 环境变量管理增强

## 📞 获取帮助

如遇到问题，请：
1. 首先尝试 `python -m src.cli.commands test-scan` 验证功能
2. 检查 `logs/github_sentinel.log` 日志文件
3. 提交 Issue 并附带日志信息

---

## 📝 完整变更日志

### 新增 (Added)
- feat: 添加 `test-scan` CLI 命令用于手动测试
- feat: 集成 python-dotenv 支持 .env 文件
- feat: 新增时区感知的 datetime 比较机制
- feat: 改进的调度器日志和调试信息

### 修复 (Fixed)
- fix: 修复时区比较导致的 "offset-naive and offset-aware" 错误
- fix: 修复调度器事件循环阻塞导致任务不执行
- fix: 修复主线程和调度器线程的事件循环冲突
- fix: 修复资源泄漏和不正确的线程关闭

### 技术债务 (Technical)
- refactor: 重构 TaskScheduler 类的事件循环管理
- refactor: 分离主应用和调度器的异步上下文
- refactor: 标准化时区处理工具函数

**发布哈希**: [待提交]  
**发布者**: GitHub Sentinel Team  
**发布时间**: 2025年10月6日

---

🌟 **GitHub Sentinel v0.1.0 - 更稳定、更快速、更易用！** 🌟
