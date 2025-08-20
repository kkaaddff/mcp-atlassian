好的 👍 我帮你梳理一下官方文档里 **`GET /rest/api/content/{id}`** 的参数说明（Confluence Server / Data Center 7.x 版本 REST API）。

---

## 📘 接口说明

```
GET /rest/api/content/{id}
```

* **作用**：返回指定 **内容项（Content）** 的完整信息
* **Content 类型**：Page、Blogpost、Comment、Attachment 等
* **id**：页面或内容的 ID（URL 中能看到，比如 `/pages/1234567/...` → id=1234567）

---

## 🔹 Query 参数

### 1. `expand`

* **用途**：指定要“展开”的附加信息字段，否则默认只返回部分基础数据。
* **类型**：字符串（多个值用逗号分隔）
* **常用值**：

| expand 值                      | 说明                                                                  |
| ----------------------------- | ------------------------------------------------------------------- |
| `body.view`                   | 页面内容，HTML 渲染好的格式（适合直接展示）                                            |
| `body.storage`                | 页面内容，Confluence 原始存储格式（XML/HTML DSL，适合编辑或迁移）                        |
| `body.export_view`            | 页面内容，导出时的格式（类似 HTML，去掉 UI 装饰）                                       |
| `body.editor`                 | 编辑器用的格式（可能带宏）                                                       |
| `version`                     | 版本信息（version number、when、by whom）                                   |
| `ancestors`                   | 当前页面的父页面链路                                                          |
| `children`                    | 子内容（可细分 `children.page`、`children.attachment`、`children.comment` 等） |
| `descendants`                 | 所有下级内容（比 `children` 更深）                                             |
| `space`                       | 页面所属空间的基本信息                                                         |
| `history`                     | 历史信息（创建人、创建时间等）                                                     |
| `metadata.labels`             | 标签信息                                                                |
| `metadata.properties`         | 自定义元数据                                                              |
| `restrictions`                | 权限限制（查看、编辑等）                                                        |
| `extensions.inlineProperties` | 内联属性扩展                                                              |

👉 例子：

```http
GET /rest/api/content/1234567?expand=body.storage,version,ancestors
```

返回的 JSON 里会附带这些展开的对象。

---

### 2. `status`

* **用途**：过滤内容的状态
* **取值**：`current`（默认）、`draft`、`archived`、`trashed`
* **说明**：

  * `current` → 当前有效的内容
  * `draft` → 草稿
  * `archived` → 已归档
  * `trashed` → 回收站内容

例子：

```http
GET /rest/api/content/1234567?status=current
```

---

### 3. `version`

* **用途**：返回指定版本的内容
* **类型**：整数（版本号）
* **说明**：如果不指定，则返回最新版本。

例子：

```http
GET /rest/api/content/1234567?version=3
```

---

## 📌 常见用法示例

1. **获取页面内容（原始存储格式）**

```bash
curl -u "user:token" \
  "http://your-confluence-host:8090/rest/api/content/1234567?expand=body.storage"
```

2. **获取页面 HTML 渲染结果**

```bash
curl -u "user:token" \
  "http://your-confluence-host:8090/rest/api/content/1234567?expand=body.view"
```

3. **获取页面内容 + 父页面 + 版本信息**

```bash
curl -u "user:token" \
  "http://your-confluence-host:8090/rest/api/content/1234567?expand=body.storage,version,ancestors"
```

---

要不要我帮你画一张 **参数-返回结果结构图**（比如 expand=body.storage 时返回 JSON 的关键字段）？这样你看文档就更直观。
