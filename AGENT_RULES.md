# 代理使用规则

## Python环境管理

**重要规则**: 本项目使用conda管理Python环境，所有Python相关操作都必须先激活conda环境。

### 环境激活命令
```bash
conda activate mcp-atlassian
```

### 使用规则
1. **所有Python命令执行前**，必须先运行 `conda activate mcp-atlassian`
2. **所有pip安装操作**，必须在激活conda环境后执行
3. **所有Python模块测试**，必须在激活conda环境后执行
4. **所有服务器启动操作**，必须在激活conda环境后执行

### 示例
```bash
# ✅ 正确用法
conda activate mcp-atlassian && python3 -m app.server

# ❌ 错误用法
python3 -m app.server  # 未激活conda环境

# ✅ 正确用法
conda activate mcp-atlassian && pip install package_name

# ❌ 错误用法
pip install package_name  # 未激活conda环境
```

### 环境信息
- **环境名称**: mcp-atlassian
- **Python版本**: 3.12.11
- **包管理器**: conda
- **项目类型**: HTTP服务器（重构自MCP项目）

### 注意事项
- 不要使用 `python3 -m venv` 创建虚拟环境
- 不要使用 `source venv/bin/activate` 激活环境
- 始终使用 `conda activate mcp-atlassian` 激活环境
- 如果遇到模块导入错误，首先检查是否已激活正确的conda环境

---

**规则创建时间**: 2025年1月
**规则适用范围**: 所有使用此项目的AI代理
**规则优先级**: 最高优先级，必须严格遵守
