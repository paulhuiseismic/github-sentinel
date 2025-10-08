# GitHub Sentinel v0.2.0 Release Notes

**发布日期**: 2024-10-08

## 🚀 主要新功能

### 1. 每日进展汇总
- **扩展GitHub服务**: 新增获取issues和pull requests的API接口
- **智能筛选**: 支持按时间范围和状态筛选（已合并PR、开放Issues等）
- **Markdown导出**: 自动生成格式化的每日进展报告，文件按 `{repo}_{date}.md` 命名
- **紧凑模式**: 默认启用紧凑模式，只显示重要信息以节省资源

### 2. LLM集成模块
- **多提供商支持**: 集成Azure OpenAI和OpenAI，支持可扩展的LLM提供商架构
- **智能摘要生成**: 使用AI分析GitHub进展数据，生成专业的中文项目简报
- **参数优化**: 支持自定义温度、token数量等参数，针对不同场景优化成本
- **错误处理**: 完善的速率限制处理和错误恢复机制

### 3. 增强报告生成
- **完整工作流**: 支持从数据收集到AI分析的完整自动化流程
- **模板系统**: 支持自定义prompt模板，便于不同类型项目的分析
- **批量处理**: 支持同时处理多个仓库，提高工作效率
- **模型对比**: 支持使用不同LLM模型和模板生成报告并对比效果

### 4. 丰富的CLI命令系统
新增8个v0.2专用命令：
- `progress` - 生成仓库每日进展报告
- `summary` - 使用LLM生成智能摘要报告
- `report` - 一键生成完整报告（进展+摘要）
- `batch` - 批量处理多个仓库
- `compare` - 对比不同模板和模型的效果
- `llm` - LLM提供商管理（列表、测试）
- `history` - 查看报告历史记录

### 5. 配置系统升级
- **环境变量支持**: 完整的.env文件支持，便于部署和配置
- **YAML配置**: 支持灵活的YAML配置文件
- **多层配置**: 环境变量、配置文件、默认值的优先级管理

## 💡 使用示例

### 基础使用
```bash
# 生成GitHub仓库的12小时进展报告（节省token）
python -m src.cli.commands progress microsoft vscode --hours 12

# 使用AI生成中文摘要（限制token使用）
python -m src.cli.commands summary microsoft vscode --max-tokens 1000

# 一键生成完整报告
python -m src.cli.commands report microsoft vscode --hours 24
```

### 高级功能
```bash
# 批量处理多个仓库
python -m src.cli.commands batch example_repos.json

# 对比不同AI模型效果
python -m src.cli.commands compare microsoft vscode --providers azure_openai openai

# 管理LLM提供商
python -m src.cli.commands llm list
python -m src.cli.commands llm test azure_openai
```

## 🔧 技术改进

### 性能优化
- **紧凑模式**: 默认开启，减少数据传输和token使用
- **时间范围控制**: 支持6-24小时的灵活时间窗口
- **内容截断**: 自动截断过长内容，避免API限制
- **批量优化**: 批量处理时自动使用更保守的参数

### 错误处理
- **速率限制**: 智能处理Azure OpenAI的token速率限制
- **编码兼容**: 修复Windows系统的Unicode编码问题
- **优雅降级**: 提供多级备用方案，确保功能可用性

### 代码质量
- **模块化架构**: 清晰的服务分层，便于扩展和维护
- **类型注解**: 完整的类型提示，提高代码可读性
- **测试覆盖**: 新增专门的v0.2功能测试套件

## 📊 成本优化

针对Azure OpenAI S0定价层进行了特别优化：
- **默认参数**: max_tokens降至1500，temperature设为0.7
- **紧凑输出**: 只关注已合并PR和活跃Issues
- **时间限制**: 建议使用12小时以内的时间窗口
- **智能截断**: 超长内容自动截断并提醒

## 🧪 测试框架

### 新增测��
- **功能测试**: 完整的v0.2功能测试覆盖
- **集成测试**: CLI命令集成测试，修复了Unicode编码问题
- **最小化测试**: 专为低配额用户设计的轻量级测试
- **错误场景**: 针对速率限制等常见问题的测试覆盖

### 测试命令
```bash
# 运行v0.2功能测试
python tests/test_v02_features.py

# 选择测试模式：
# 1 - 标准测试（完整功能）
# 2 - 最小化测试（适合S0定价层）
# 3 - CLI集成测试
# 4 - 运行所有测试
```

## 📁 项目结构

新增和修改的主要文件：
```
src/services/
├── llm_service.py          # 新增：LLM集成服务
├── github_service.py       # 增强：支持issues/PR获取
└── report_service.py       # 增强：集成LLM功能

src/config/
└── settings.py             # 增强：LLM配置支持

src/cli/
└── commands.py             # 增强：8个新CLI命令

tests/
└── test_v02_features.py    # 新增：v0.2功能测试

配置文件：
├── .env.example            # 新增：环境变量模板
├── example_repos.json      # 新增：批量处理示例
└── README_v0.2.md         # 新增：详细使用文档
```

## 🔄 向后兼容性

- ✅ **完全兼容**: 所有v0.1功能保持不变
- ✅ **CLI兼容**: 原有CLI命令继续正常工作
- ✅ **配置兼容**: 现有配置文件无需修改
- ✅ **数据兼容**: 数据库和文件格式保持兼容

## 🚨 已知问题修复

1. **编码问题**: 修复了Windows系统的Unicode编码错误
2. **配置缺失**: 补充了DatabaseConfig缺少的path属性
3. **CLI响应**: 修复了CLI命令无响应的问题
4. **Token限制**: 优化了Azure OpenAI的速率限制处理

## 📋 升级指南

### 从v0.1升级到v0.2

1. **安装新依赖**:
```bash
pip install -r requirements.txt
```

2. **更新环境变量**:
```bash
cp .env.example .env
# 编辑.env文件，添加Azure OpenAI配置
```

3. **测试新功能**:
```bash
python -m src.cli.commands --help
python tests/test_v02_features.py
```

### 配置LLM服务

在.env文件中配置Azure OpenAI：
```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4o
```

## 🎯 未来规划

v0.3.0计划功能：
- 支持更多LLM提供商（Google AI、Claude等）
- Web界面支持
- 定时任务和自动化报告
- 更多可视化选项
- 团队协作功能

## 🤝 贡献者

感谢所有为v0.2.0做出贡献的开发者！

## 📞 支持

- 文档: [README_v0.2.md](README_v0.2.md)
- 问题反馈: GitHub Issues
- 功能请求: GitHub Discussions

---

**完整更新日志**: [v0.1.0...v0.2.0](https://github.com/your-repo/compare/v0.1.0...v0.2.0)
