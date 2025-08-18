# MCP Confluence

![PyPI Version](https://img.shields.io/pypi/v/mcp-confluence)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mcp-confluence)
![PePy - Total Downloads](https://static.pepy.tech/personalized-badge/mcp-confluence?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Total%20Downloads)
[![Run Tests](https://github.com/sooperset/mcp-confluence/actions/workflows/tests.yml/badge.svg)](https://github.com/sooperset/mcp-confluence/actions/workflows/tests.yml)
![License](https://img.shields.io/github/license/sooperset/mcp-confluence)

Confluence 的模型上下文协议 (MCP) 服务器。此集成支持 Confluence Cloud 和 Server/Data Center 部署。

## 使用示例

向您的 AI 助手询问：

- **🔍 AI 驱动的 Confluence 搜索** - "在 Confluence 中找到我们的 OKR 指南并总结它"
- **📄 内容创建与管理** - "为 XYZ 功能创建技术设计文档"
- **📚 空间管理** - "列出我们 Confluence 实例中的所有空间"
- **🏷️ 页面组织** - "使用会议笔记更新项目文档"

### 功能演示

https://github.com/user-attachments/assets/7fe9c488-ad0c-4876-9b54-120b666bb785

### 兼容性

| 产品 | 部署类型 | 支持状态 |
|------|----------|----------|
| **Confluence** | Cloud | ✅ 完全支持 |
| **Confluence** | Server/Data Center | ✅ 支持（版本 6.0+） |

## 快速开始指南

### 🔐 1. 身份验证设置

MCP Confluence 支持两种身份验证方法：

#### A. API 令牌身份验证（Cloud）- **推荐**

1. 访问 https://id.atlassian.com/manage-profile/security/api-tokens
2. 点击 **创建 API 令牌**，为其命名
3. 立即复制令牌

#### B. 个人访问令牌（Server/Data Center）

1. 访问您的个人资料（头像）→ **个人资料** → **个人访问令牌**
2. 点击 **创建令牌**，命名，设置过期时间
3. 立即复制令牌

### ⚙️ 2. 环境配置

在项目根目录创建 `.env` 文件：

```bash
# 对于 Confluence Cloud（API 令牌）
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your_api_token_here

# 对于 Confluence Server/Data Center（个人访问令牌）
CONFLUENCE_URL=https://confluence.your-company.com
CONFLUENCE_PERSONAL_TOKEN=your_personal_access_token_here

# 可选：按特定空间过滤（逗号分隔）
CONFLUENCE_SPACES_FILTER=DEV,TEAM,DOC
```

### 🚀 3. 运行服务器

#### 标准 MCP 模式
```bash
# 使用 uv（推荐）
uv run mcp-confluence

# 使用 pip
pip install mcp-confluence
mcp-confluence
```

#### HTTP 服务模式
用作具有可配置基础 URL 和基于请求认证的独立 HTTP 服务：

```bash
# 启动 HTTP 服务
mcp-confluence --http-service --host 0.0.0.0 --port 8000

# 服务将在以下地址可用：
# - http://localhost:8000/confluence/execute - 执行操作
# - http://localhost:8000/health - 健康检查
```

#### HTTP 服务 API
HTTP 服务接受对 `/confluence/execute` 的 POST 请求，具有以下结构：

```json
{
  "base_url": "https://your-company.atlassian.net/wiki",
  "auth_type": "basic|pat",
  "username": "your.email@company.com",  # 基础认证用
  "api_token": "your_api_token",        # 基础认证用
  "personal_token": "your_pat",          # PAT 认证用
  "operation": "get_page|search_pages|get_space|list_spaces|create_page|update_page",
  "parameters": {
    "page_id": "12345",
    "query": "搜索词",
    "space_key": "TEAM",
    "limit": 50,
    "title": "页面标题",
    "content": "页面内容",
    "parent_id": "123"
  }
}
```

## 配置选项

### 环境变量

| 变量 | 描述 | 必需 |
|------|------|------|
| `CONFLUENCE_URL` | Confluence 实例的基础 URL | ✅ |
| `CONFLUENCE_USERNAME` | Cloud 身份验证的邮箱/用户名 | ✅ (Cloud) |
| `CONFLUENCE_API_TOKEN` | Cloud 身份验证的 API 令牌 | ✅ (Cloud) |
| `CONFLUENCE_PERSONAL_TOKEN` | Server/DC 的个人访问令牌 | ✅ (Server/DC) |
| `CONFLUENCE_SPACES_FILTER` | 用于过滤的逗号分隔空间键 | ❌ |
| `CONFLUENCE_SSL_VERIFY` | 验证 SSL 证书（true/false） | ❌ |

### 命令行选项

```bash
mcp-confluence [选项]

选项：
  -v, --verbose                       增加详细程度
  --env-file PATH                     .env 文件的路径
  --confluence-url TEXT                Confluence URL
  --confluence-username TEXT           Confluence 用户名/邮箱
  --confluence-token TEXT              Confluence API 令牌
  --confluence-personal-token TEXT     Confluence 个人访问令牌
  --confluence-spaces-filter TEXT      空间过滤器
  --read-only                         以只读模式运行
  --transport [stdio|sse|streamable-http]  传输类型
  --port INTEGER                       HTTP 传输的端口
  --host TEXT                          HTTP 传输的主机
  --http-service                       作为 HTTP 服务运行
  --help                              显示帮助消息
```

## 可用操作

### Confluence 操作
- **搜索内容**：查找页面、博客和附件
- **页面管理**：创建、读取、更新页面
- **空间操作**：列出空间、获取空间详情
- **评论**：添加和检索页面评论
- **标签**：管理页面标签
- **附件**：处理页面附件
- **用户信息**：获取用户详情和权限

## 功能

### 🔒 安全性
- 多种身份验证方法
- 令牌验证和刷新
- SSL 证书验证
- 基于请求的身份验证（HTTP 服务模式）

### 🚀 性能
- 连接池
- 响应缓存
- 高效数据模型
- 批量操作支持

### 🛠️ 可扩展性
- 工具过滤系统
- 只读模式
- 可配置的空间过滤器
- 用于集成的 HTTP 服务模式

## 开发

### 设置开发环境
```bash
# 克隆仓库
git clone https://github.com/sooperset/mcp-confluence.git
cd mcp-confluence

# 安装依赖
uv sync

# 设置预提交钩子
pre-commit install

# 复制环境模板
cp .env.example .env
```

### 运行测试
```bash
# 运行所有测试
uv run pytest

# 运行覆盖率测试
uv run pytest --cov=mcp_confluence

# 运行特定测试文件
uv run pytest tests/unit/confluence/test_client.py

# 使用详细输出运行
uv run pytest -v
```

### 代码质量
```bash
# 运行所有预提交检查
pre-commit run --all-files

# 运行特定工具
uv run ruff check .
uv run ruff format .
uv run mypy .
```

## 故障排除

### 常见问题

1. **身份验证失败**
   - 验证您的 API 令牌是否有效且未过期
   - 检查您的 Confluence URL 是否正确
   - 确保您的用户/令牌具有适当的权限

2. **SSL 证书问题**
   - 对于自签名证书，设置 `CONFLUENCE_SSL_VERIFY=false`
   - 确保您的证书链完整

3. **权限被拒绝**
   - 验证您的用户在 Confluence 中具有必要权限
   - 检查空间和页面级权限

4. **HTTP 服务问题**
   - 确保提供了所有必需的身份验证参数
   - 检查基础 URL 是否可访问
   - 验证操作和参数是否正确

### 调试模式
启用详细日志记录来排查问题：

```bash
mcp-confluence -vv --env-file .env
```

## 贡献

我们欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

## 许可证

此项目根据 MIT 许可证授权 - 详情请参见 [LICENSE](LICENSE) 文件。

## 支持

- 📚 [文档](https://github.com/sooperset/mcp-confluence/wiki)
- 🐛 [报告问题](https://github.com/sooperset/mcp-confluence/issues)
- 💬 [讨论](https://github.com/sooperset/mcp-confluence/discussions)

---

**为 Confluence 社区用 ❤️ 构建**