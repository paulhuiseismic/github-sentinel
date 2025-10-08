# GitHub Sentinel v0.2 功能文档

## 新功能概述

v0.2版本新增了以下主要功能：

1. **每日进展汇总** - 获取订阅仓库的issues和pull requests，导出为Markdown文件
2. **LLM集成** - 支持Azure OpenAI和OpenAI，实现智能报告生成
3. **增强报告生成** - 使用LLM和prompt模板生成项目简报
4. **可扩展性设计** - 支持多种LLM模型和模板对比测试

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 2. 环境变量配置

在 `.env` 文件中配置以下变量：

```env
# GitHub API Token (必需)
GITHUB_TOKEN=your_github_token_here

# Azure OpenAI 配置 (推荐)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4

# 或者使用 OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
```

## 主要功能使用

### 1. 生成每日进展报告

获取仓库的issues和pull requests，生成结构化的Markdown报告：

```bash
# 生成单个仓库的进展报告
python -m src.cli.commands progress microsoft vscode

# 输出文件: daily_progress/vscode_20241008.md
```

### 2. 生成LLM智能摘要

基于进展报告，使用LLM生成中文摘要：

```bash
# 生成智能摘要报告
python -m src.cli.commands summary microsoft vscode

# 使用特定模板和提供商
python -m src.cli.commands summary microsoft vscode --template github_azure_prompt.txt --provider azure_openai
```

### 3. 生成完整报告

同时生成进展报告和智能摘要：

```bash
# 一键生成完整报告
python -m src.cli.commands report microsoft vscode

# 自定义参数
python -m src.cli.commands report microsoft vscode --template custom_prompt.txt --temperature 0.5
```

### 4. 批量处理多个仓库

使用JSON文件批量处理多个仓库：

```bash
# 批量生成报告
python -m src.cli.commands batch example_repos.json

# 自定义并发数
python -m src.cli.commands batch example_repos.json --concurrent 5
```

`example_repos.json` 文件格式：
```json
[
  {
    "owner": "microsoft",
    "repo": "vscode"
  },
  {
    "owner": "facebook", 
    "repo": "react"
  }
]
```

### 5. 对比不同模型和模板

测试不同LLM模型和prompt模板的效果：

```bash
# 对比不同模板
python -m src.cli.commands compare microsoft vscode --templates github_azure_prompt.txt custom_prompt.txt

# 对比不同提供商
python -m src.cli.commands compare microsoft vscode --providers azure_openai openai
```

### 6. LLM提供商管理

```bash
# 列出所有配置的LLM提供商
python -m src.cli.commands llm list

# 测试LLM提供商
python -m src.cli.commands llm test azure_openai
python -m src.cli.commands llm test azure_openai --prompt "请介绍一下GitHub"
```

### 7. 查看报告历史

```bash
# 查看指定仓库的报告历史
python -m src.cli.commands history vscode --limit 5
```

## 配置文件

项目支持YAML配置文件 `src/config/config.yaml`：

```yaml
github:
  token: "${GITHUB_TOKEN}"
  api_url: "https://api.github.com"
  rate_limit_per_hour: 5000

llm_providers:
  - name: "azure_openai"
    type: "azure_openai"
    model_name: "gpt-4"
    api_key: "${AZURE_OPENAI_API_KEY}"
    azure_endpoint: "${AZURE_OPENAI_ENDPOINT}"
    is_default: true
    temperature: 0.7

report:
  daily_progress_dir: "daily_progress"
  default_template: "github_azure_prompt.txt"
  enable_llm_summary: true
```

## 自定义Prompt模板

在 `prompts/` 目录下创建自定义模板：

```text
# prompts/my_custom_prompt.txt
你是一个专业的技术分析师。请根据以下GitHub项目进展信息，生成一份专业的技术分析报告。

报告应包含：
1. 项目概述
2. 技术亮点
3. 发展趋势
4. 建议关注点

请用中文回复，保持专业和客观的语调。
```

## 输出文件结构

```
daily_progress/
├── vscode_20241008.md              # 原始进展报告
├── vscode_summary_20241008_143022.md  # LLM摘要报告
├── react_20241008.md
└── react_summary_20241008_143156.md

data/reports/
├── daily_report_20241008_121348.json  # 传统格式报告
└── weekly_report_20241007_001234.json
```

## 报告示例

### 原始进展报告格式
```markdown
# vscode 项目每日进展

## 时间周期：2024-10-07 至 2024-10-08

## Issues 更新 (5 个)

### #12345 修复编辑器性能问题
- **状态**: open
- **创建者**: developer1
- **更新时间**: 2024-10-08T10:30:00Z
- **链接**: [https://github.com/microsoft/vscode/issues/12345]

## Pull Requests 更新 (3 个)

### #54321 新增主题支持
- **状态**: merged
- **创建者**: contributor1  
- **分支**: feature/themes → main
- **合并时间**: 2024-10-08T09:15:00Z
```

### LLM生成的摘要报告格式
```markdown
# VSCode 项目进展

## 时间周期：2024-10-07至2024-10-08

## 新增功能
- 新增主题支持功能，提升用户个性化体验
- 添加新的编辑器扩展API

## 主要改进  
- 优化编辑器性能，提升响应速度
- 改进内存使用效率

## 修复问题
- 修复编辑器在大文件下的性能问题
- 解决插件兼容性问题
```

## 最佳实践

1. **API限制管理**: GitHub API有速率限制，大量仓库请分批处理
2. **LLM成本控制**: 合理设置max_tokens和temperature参数
3. **模板优化**: 根据不同项目类型使用不同的prompt模板
4. **定期清理**: 定期清理历史报告文件避免磁盘占用过多

## 故障排除

### 常见问题

1. **GitHub API认证失败**
   ```
   错误: GitHub API访问被拒绝: 403
   解决: 检查GITHUB_TOKEN是否正确配置
   ```

2. **LLM API调用失败**  
   ```
   错误: Azure OpenAI API调用失败
   解决: 检查API密钥、端点和模型名称配置
   ```

3. **文件权限问题**
   ```
   错误: 无法创建输出目录
   解决: 检查daily_progress目录的写入权限
   ```

## 扩展开发

### 添加新的LLM提供商

1. 在 `src/services/llm_service.py` 中继承 `BaseLLMProvider`
2. 实现 `generate_completion` 和 `generate_chat_completion` 方法
3. 在配置中添加新提供商配置

### 自定义报告格式

1. 继承 `ReportService` 类
2. 重写 `_generate_progress_markdown` 方法
3. 添加新的输出格式支持

## 版本兼容性

- v0.1功能完全兼容，可以继续使用传统命令
- 新功能需要Python 3.8+和相应的依赖包
- 建议使用最新版本的openai包 (>=1.3.0)
