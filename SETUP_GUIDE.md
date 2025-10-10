# GitHub Sentinel 快速设置指南

## 🔧 GitHub Token 设置

### 1. 获取 GitHub Token
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" (推荐使用 Fine-grained tokens)
3. 选择以下权限：
   - `repo` - 访问仓库
   - `user` - 用户信息
   - `read:org` - 读取组织信息

### 2. 设置环境变量

#### Windows (CMD):
```cmd
set GITHUB_TOKEN=你的token值
```

#### Windows (PowerShell):
```powershell
$env:GITHUB_TOKEN="你的token值"
```

#### Linux/Mac:
```bash
export GITHUB_TOKEN=你的token值
```

### 3. 持久化设置 (推荐)

创建 `.env` 文件在项目根目录：
```env
GITHUB_TOKEN=你的token值
AZURE_OPENAI_API_KEY=你的azure_key(可选)
AZURE_OPENAI_ENDPOINT=你的azure_endpoint(可选)
```

## 🚀 启动应用

### 启动 Web 界面
```bash
python web_app.py
```

或者：
```bash
python src/main.py --web
```

### 启动后台服务
```bash
python src/main.py
```

## ✅ 验证设置

启动后查看日志，如果看到类似信息说明配置正确：
- ✅ GitHub Sentinel Web界面启动成功
- ⚠️ 如果看到 "GitHub Token未设置" 警告，请按上述步骤设置token

## 🎯 使用指南

1. **添加订阅**：在 "订阅管理" 页面添加要监控的 GitHub 仓库
2. **生成报告**：在 "报告生成" 页面选择仓库和时间范围生成智能报告
3. **查看状态**：在 "系统状态" 页面监控系统运行情况

访问地址：http://localhost:7860
