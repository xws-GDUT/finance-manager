# 💰 家庭财务管理系统

> Django 5 + React 18 + Ant Design 5 + SQLite + Render

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Django 5.x + DRF 3.15 | ORM + REST API + Admin |
| 数据库 | SQLite（本地）/ Persistent Disk（Render） | 单文件零配置 |
| 前端框架 | React 18 + TypeScript | 组件化 SPA |
| 构建工具 | Vite 5 | HMR + Tree-shaking |
| UI 组件库 | Ant Design 5.x | Table / Form / Modal / Tree |
| 图表 | Recharts | 仪表盘可视化 |
| 日期处理 | dayjs | 轻量日期库 |
| PDF 解析 | pdfplumber | 银行账单解析 |
| Excel 解析 | openpyxl | 微信账单解析 |
| 部署 | Render | Web Service + Static Site + Persistent Disk |

## 项目结构

```
finance-manager/
├── backend/                      # Django 后端
│   ├── config/                   # 项目配置
│   │   ├── settings.py           # SQLite/Persistent Disk 切换
│   │   ├── urls.py               # API 路由分发
│   │   ├── wsgi.py / asgi.py
│   ├── apps/
│   │   ├── transactions/         # 交易流水（模型/API/筛选/统计）
│   │   ├── rules/                # 有效规则 + 无效规则
│   │   ├── settlements/          # 退款配对 + 垫付结算
│   │   ├── categories/           # 分类管理（31个预置）
│   │   ├── accounts/             # 账户管理（8个预置）
│   │   └── imports/              # 流水导入 + 解析引擎
│   ├── utils/                    # 共享工具
│   ├── manage.py
│   └── requirements.txt
├── frontend/                     # React 前端
│   ├── vite.config.ts            # Vite 配置（含 API 代理）
│   ├── tsconfig.json
│   └── src/
│       ├── App.tsx               # 路由配置
│       ├── components/           # 共享组件（布局/规则管理器）
│       ├── pages/                # 9 个业务页面
│       ├── api/                  # Axios API 调用层
│       └── types/                # TypeScript 类型定义
└── render.yaml                   # Render 一键部署
```

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate          # 建表 + 预置数据
python manage.py createsuperuser  # 创建管理员（可选）
python manage.py runserver        # http://127.0.0.1:8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

前端开发服务器自动代理 `/api` 到后端 `127.0.0.1:8000`。

### 访问

- **前端应用**：http://localhost:5173
- **后端 API**：http://127.0.0.1:8000/api/
- **管理后台**：http://127.0.0.1:8000/admin/

## 预置数据

| 数据 | 数量 | 说明 |
|------|------|------|
| 分类 | 31 | 17 父分类 + 14 子分类 |
| 账户 | 8 | 储蓄卡/信用卡/支付平台 |
| 有效规则 | 10 | 自动判定有效交易 |
| 无效规则 | 17 | 排除非消费类交易 |

## 功能清单

| 模块 | 功能 | 页面 |
|------|------|------|
| 📊 仪表盘 | 统计总览 / 月度趋势图 / 分类排行 | Dashboard |
| 📋 交易明细 | 表格筛选排序 / 编辑分类 / 软删除 | Transactions |
| 📥 流水导入 | 拖拽上传 / 自动识别来源 / 去重 / 导入历史 | Import |
| ✅ 有效规则 | CRUD / 测试匹配 / 重新应用 | ValidRules |
| 🚫 无效规则 | CRUD / 测试匹配 / 重新应用 / 对手方匹配 | InvalidRules |
| 🔄 退款配对 | 自动配对 / 手动配对 / AA 扫描 / 一键结算 | RefundPairs |
| 💼 垫付结算 | 结算组管理 / 关闭/重开 / 候选搜索 | Settlements |
| 🏷️ 分类管理 | 树形展示 / 预置 31 个分类 | Categories |
| 💳 账户管理 | 列表展示 / 交易统计 | Accounts |

## API 接口（43 个端点）

### 流水导入
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/import/upload` | 单文件导入 |
| POST | `/api/import/batch` | 批量导入 |
| GET | `/api/import/history` | 导入历史 |

### 交易查询
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/transactions/` | 交易列表（分页/筛选/排序） |
| POST | `/api/transactions/` | 创建交易 |
| GET | `/api/transactions/{id}/` | 交易详情 |
| PUT | `/api/transactions/{id}/` | 更新交易 |
| DELETE | `/api/transactions/{id}/` | 软删除 |
| GET | `/api/transactions/filter_values/` | 筛选字段值 |

### 统计分析
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats/overview` | 总览统计 |
| GET | `/api/stats/monthly` | 月度趋势 |
| GET | `/api/stats/category` | 分类统计 |
| GET | `/api/stats/daily` | 每日趋势 |

### 规则引擎
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/valid-rules/` | 有效规则列表/创建 |
| GET/PUT/DELETE | `/api/valid-rules/{id}/` | 有效规则 CRUD |
| POST | `/api/valid-rules/test/` | 测试匹配 |
| POST | `/api/valid-rules/apply/` | 重新应用 |
| GET/POST | `/api/invalid-rules/` | 无效规则列表/创建 |
| GET/PUT/DELETE | `/api/invalid-rules/{id}/` | 无效规则 CRUD |
| POST | `/api/invalid-rules/test/` | 测试匹配 |
| POST | `/api/invalid-rules/apply/` | 重新应用 |

### 退款配对
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/refund-pairs/` | 配对列表/手动创建 |
| POST | `/api/refund-pairs/auto/` | 自动配对 |
| GET/DELETE | `/api/refund-pairs/{id}/` | 详情/解除 |
| GET | `/api/refund-pairs/aa_scan/` | AA 扫描 |
| POST | `/api/refund-pairs/aa_create/` | 创建 AA 结算 |

### 垫付结算
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/settlements/` | 结算组列表/创建 |
| GET/PUT/DELETE | `/api/settlements/{id}/` | 结算组 CRUD |
| POST | `/api/settlements/{id}/close/` | 关闭结算 |
| POST | `/api/settlements/{id}/reopen/` | 重开结算 |
| GET/POST | `/api/settlements/{id}/items/` | 结算明细 |
| DELETE | `/api/settlements/{id}/items/{item_id}/` | 移除明细 |
| POST | `/api/settlements/{id}/add_item/` | 添加交易 |
| GET | `/api/settlements/candidates/` | 候选交易搜索 |

### 其他
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/categories` | 分类树形列表 |
| GET | `/api/accounts` | 账户列表（含统计） |

## Render 部署

项目根目录 `render.yaml` 包含完整的 Render Blueprint 配置：

- **finance-manager-api**（Web Service）：Django + Gunicorn
- **finance-manager-web**（Static Site）：React 构建产物
- **finance-data**（Persistent Disk）：1GB，SQLite 持久化存储

### 部署步骤

1. 将项目推送到 GitHub
2. 在 [Render Dashboard](https://dashboard.render.com) 选择 "New Blueprint Instance"
3. 连接 GitHub 仓库，选择 `render.yaml`
4. 等待自动部署完成

部署后访问 Static Site URL 即可使用。

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DJANGO_SECRET_KEY` | 密钥 | Render 自动生成 |
| `DJANGO_DEBUG` | 调试模式 | `False`（生产） |
| `DJANGO_ALLOWED_HOSTS` | 允许主机 | `.onrender.com` |
| `DATA_DIR` | 数据库目录 | `/data`（Render）/ 项目目录（本地） |

## 数据来源支持

| 来源 | 格式 | 自动识别 |
|------|------|----------|
| 支付宝 | CSV | ✅ 文件名/内容 |
| 京东 | CSV | ✅ 文件名 |
| 美团 | CSV | ✅ 文件名 |
| 微信支付 | XLSX | ✅ 文件名 |
| 交通银行储蓄卡 | PDF | ✅ 文件名 |
| 招商银行储蓄卡 | PDF | ✅ 文件名 |
| 中信信用卡 | PDF | ✅ 文件名 |
| 招商银行信用卡 | PDF | ✅ 文件名 |
| 抖音月付 | PDF | ✅ 文件名 |
