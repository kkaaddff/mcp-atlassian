# TFA算法服务器

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI Version](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

TFA算法服务器是一个基于FastAPI的HTTP服务器，提供Confluence集成的RESTful API服务。此项目从原有的MCP（Model Context Protocol）架构重构而来，专注于提供简单、高效的HTTP API接口。

## 🚀 快速开始

### 启动服务器

```bash
# 使用模块方式启动（推荐）
python3 -m app.server -name tfa-algorithm-server

# 或直接运行
python3 app/server.py

# 指定自定义参数
python3 -m app.server -name my-server --host 127.0.0.1 --port 9000 --log-level DEBUG
```

### 启动参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `-name, --name` | 服务器名称 | `tfa-algorithm-server` |
| `--host` | 服务器主机地址 | `0.0.0.0` |
| `--port` | 服务器端口 | `8000` |
| `--log-level` | 日志级别 | `INFO` |
| `--reload` | 启用自动重载（开发模式） | `False` |

## 📋 功能特性

### 🔍 Confluence集成
- **页面管理**: 获取、搜索页面内容
- **空间管理**: 列出空间、获取用户空间
- **内容搜索**: 支持CQL查询语言
- **多格式支持**: HTML和Markdown格式转换

### 🛡️ 安全特性
- **多种认证方式**: Bearer Token、Personal Access Token
- **中间件支持**: 认证、日志记录、CORS
- **环境配置**: 支持.env文件配置

### 🚀 技术特性
- **FastAPI框架**: 高性能异步Web框架
- **自动文档**: 内置Swagger UI和ReDoc
- **类型安全**: 完整的类型注解和验证
- **中间件架构**: 可扩展的中间件系统

## 🏗️ 项目架构

```
app/
├── __init__.py          # 应用包初始化
├── __main__.py          # 模块启动入口
├── server.py            # 主服务器入口
├── core/                # 核心模块
│   ├── __init__.py
│   ├── config.py        # 配置管理
│   └── application.py   # FastAPI应用创建
├── api/                 # API路由
│   ├── __init__.py
│   └── confluence.py    # Confluence API
├── services/            # 业务逻辑层
│   ├── __init__.py
│   └── confluence_service.py  # Confluence服务
├── middleware/          # 中间件
│   ├── __init__.py
│   ├── auth.py          # 认证中间件
│   └── logging.py       # 日志中间件
└── utils/               # 工具模块
    ├── __init__.py
    └── logging.py       # 日志配置
```

## 🔧 配置

### 环境变量

创建 `.env` 文件在项目根目录：

```bash
# Confluence配置
CONFLUENCE_URL=https://confluence.your-company.com
CONFLUENCE_USERNAME=your.username
CONFLUENCE_API_TOKEN=your_api_token
CONFLUENCE_PERSONAL_TOKEN=your_personal_token
CONFLUENCE_SSL_VERIFY=true
CONFLUENCE_SPACES_FILTER=DEV,TEAM,DOC

# 代理配置（可选）
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1

# 其他配置
READ_ONLY_MODE=false
ENABLED_TOOLS=search,spaces,pages
```

### 配置说明

| 变量 | 描述 | 必需 | 默认值 |
|------|------|------|--------|
| `CONFLUENCE_URL` | Confluence实例URL | ✅ | - |
| `CONFLUENCE_USERNAME` | 用户名（基本认证） | ❌ | - |
| `CONFLUENCE_API_TOKEN` | API令牌（基本认证） | ❌ | - |
| `CONFLUENCE_PERSONAL_TOKEN` | 个人访问令牌 | ❌ | - |
| `CONFLUENCE_SSL_VERIFY` | SSL验证 | ❌ | `true` |
| `CONFLUENCE_SPACES_FILTER` | 空间过滤器 | ❌ | - |

## 📚 API文档

### 基础端点

- **健康检查**: `GET /health`
- **API文档**: `GET /docs` (Swagger UI)
- **ReDoc文档**: `GET /redoc`

### Confluence API

#### 获取页面内容
```http
GET /api/v1/confluence/pages/{page_id}?convert_to_markdown=true
Authorization: Bearer {token}
```

#### 搜索内容
```http
POST /api/v1/confluence/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "cql": "type=page AND space=TEAM",
  "limit": 10,
  "spaces_filter": "DEV,TEAM"
}
```

#### 获取空间列表
```http
GET /api/v1/confluence/spaces?start=0&limit=10
Authorization: Bearer {token}
```

#### 获取用户空间
```http
GET /api/v1/confluence/spaces/user?limit=250
Authorization: Bearer {token}
```

### 认证方式

#### Bearer Token
```http
Authorization: Bearer your_api_token_here
```

#### Personal Access Token
```http
Authorization: Token your_personal_token_here
```

## 🚀 开发指南

### 环境设置

```bash
# 克隆项目
git clone <repository-url>
cd mcp-atlassian

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 开发依赖
pip install -r requirements-dev.txt
```

### 运行开发服务器

```bash
# 启用自动重载
python3 -m app.server --reload --log-level DEBUG

# 指定端口和主机
python3 -m app.server --host 127.0.0.1 --port 9000 --reload
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/

# 覆盖率测试
pytest --cov=app
```

### 代码质量

```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/
mypy app/
```

## 🔍 故障排除

### 常见问题

1. **模块导入错误**
   - 确保在虚拟环境中运行
   - 检查依赖是否正确安装

2. **Confluence连接失败**
   - 验证URL和认证信息
   - 检查网络连接和代理设置
   - 确认SSL证书配置

3. **权限问题**
   - 验证用户权限
   - 检查空间访问权限

### 调试模式

```bash
# 启用详细日志
python3 -m app.server --log-level DEBUG

# 查看日志输出
tail -f logs/app.log
```

## 📦 部署

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python3", "-m", "app.server", "--host", "0.0.0.0", "--port", "8000"]
```

### 系统服务

创建systemd服务文件：

```ini
[Unit]
Description=TFA Algorithm Server
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/tfa-server
Environment=PATH=/opt/tfa-server/venv/bin
ExecStart=/opt/tfa-server/venv/bin/python -m app.server
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

- 📚 [API文档](http://localhost:8000/docs)
- 🐛 [报告问题](https://github.com/your-repo/issues)
- 💬 [讨论](https://github.com/your-repo/discussions)

---

**为TFA算法社区用 ❤️ 构建**