# API4CLIx

**API Layer for AI Programming Assistant CLI Tools**

API4CLIx 是一个统一的 REST API 层，为各种 AI 编程助手 CLI 工具（如 Copilot CLI、Codex、Claude Code 等）提供统一的接口。通过这个 API 层，您可以轻松地通过 REST API 调用这些强大的 AI 编程助手，实现对话、代码修改、提交等操作。

## ✨ 特性

- 🔌 **统一接口**: 为多种 AI 编程助手提供统一的 REST API 接口
- 🚀 **异步处理**: 基于 FastAPI 的高性能异步处理
- 📝 **自动文档**: 自动生成的 API 文档（Swagger UI 和 ReDoc）
- 🔧 **易于扩展**: 模块化设计，易于添加新的 AI 助手适配器
- 🧪 **完整测试**: 包含完整的测试用例
- 📊 **健康检查**: 提供服务健康状况监控

## 🎯 当前支持的 AI 助手

- ✅ **GitHub Copilot CLI** (`copilot`)
- 🚧 **Claude Code** (计划中)
- 🚧 **OpenAI Codex** (计划中)

## 📦 安装

### 前置要求

- Python 3.8+
- GitHub Copilot CLI (`copilot`)（如果要使用 Copilot 功能）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd API4CLIx
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **设置 GitHub Copilot CLI**（可选）
   ```bash
   # 安装 GitHub Copilot CLI
   # 请参考官方文档: https://github.com/github/copilot-cli

   # 验证安装
   copilot --version

   # 如果需要认证，请按照 CLI 提示进行
   ```

## 🚀 快速开始

### 启动服务器

```bash
# 使用默认设置启动
python run.py

# 自定义端口和启用自动重载（开发模式）
python run.py --port 8080 --reload --log-level debug
```

服务器启动后，您可以访问：

- **API 文档 (Swagger UI)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### API 使用示例

#### 1. 健康检查

```bash
curl http://localhost:8000/health
```

#### 2. 与 AI 助手对话

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何在 Python 中创建一个类？",
    "assistant_type": "copilot"
  }'
```

#### 3. 解释代码

```bash
curl -X POST "http://localhost:8000/code/explain" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "operation": "explain",
    "language": "python",
    "assistant_type": "copilot"
  }'
```

#### 4. 修改代码

```bash
curl -X POST "http://localhost:8000/code/modify" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello World\")",
    "operation": "modify",
    "message": "使其更加友好和个性化",
    "language": "python",
    "assistant_type": "copilot"
  }'
```

#### 5. 生成提交信息

```bash
curl -X POST "http://localhost:8000/git/commit" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_type": "copilot"
  }'
```

## 📁 项目结构

```
API4CLIx/
├── src/
│   └── api4clix/
│       ├── __init__.py          # 包初始化
│       ├── main.py              # FastAPI 应用入口
│       ├── models/              # Pydantic 数据模型
│       │   ├── requests.py      # 请求模型
│       │   └── responses.py     # 响应模型
│       ├── adapters/            # AI 助手适配器
│       │   ├── base.py         # 基础适配器类
│       │   └── copilot.py      # Copilot CLI 适配器
│       ├── services/           # 业务逻辑服务
│       │   └── assistant_manager.py  # 助手管理器
│       └── utils/              # 工具函数
│           └── logging_config.py     # 日志配置
├── tests/                      # 测试用例
│   ├── test_main.py           # 主应用测试
│   └── test_copilot_adapter.py # Copilot 适配器测试
├── requirements.txt           # Python 依赖
├── run.py                    # 启动脚本
└── README.md                 # 本文档
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_main.py

# 运行测试并显示覆盖率
pytest --cov=src/api4clix
```

## 🔧 开发

### 添加新的 AI 助手适配器

1. 在 `src/api4clix/adapters/` 中创建新的适配器文件
2. 继承 `BaseAdapter` 类并实现必需的方法
3. 在 `assistant_manager.py` 中注册新的适配器
4. 编写相应的测试用例

### 示例适配器结构

```python
from .base import BaseAdapter

class NewAssistantAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("New Assistant", "command-name")

    async def chat(self, message: str, context=None, **kwargs):
        # 实现聊天功能
        pass

    async def explain_code(self, code: str, language=None, **kwargs):
        # 实现代码解释功能
        pass

    async def modify_code(self, code: str, instruction: str, language=None, **kwargs):
        # 实现代码修改功能
        pass
```

## 📝 API 文档

启动服务器后，完整的 API 文档可在以下地址查看：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 主要端点

- `GET /health` - 健康检查
- `GET /assistants` - 列出可用的 AI 助手
- `POST /chat` - 与 AI 助手对话
- `POST /code/explain` - 请求代码解释
- `POST /code/modify` - 请求代码修改
- `POST /git/commit` - 生成 Git 提交信息

## 🚨 故障排除

### 常见问题

1. **Copilot CLI 不可用**
   - 确保已安装 GitHub CLI: `gh --version`
   - 确保已安装 Copilot 扩展: `gh extension list`
   - 确保已认证: `gh auth status`

2. **端口被占用**
   - 使用不同端口: `python run.py --port 8080`

3. **模块导入错误**
   - 确保在项目根目录运行
   - 确保已安装所有依赖

## 🤝 贡献

欢迎贡献！请查看我们的贡献指南了解更多信息。

## 📄 许可证

本项目采用 MIT 许可证。查看 [LICENSE](LICENSE) 文件了解更多信息。

## 🔗 相关链接

- [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Claude Code](https://claude.ai/claude-code)