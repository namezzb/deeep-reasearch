# 招聘信息智能采集系统 - 产品规格

## 1. 产品概述

### 1.1 目标用户
- 求职者（校招/社招）
- 需要监控竞品招聘动态的HR
- 猎头/招聘顾问

### 1.2 核心价值
自动化采集、清洗、聚合多渠道招聘资讯，让用户不错过任何心仪岗位。

### 1.3 数据源矩阵

| 渠道类型 | 代表平台 | 数据类型 | 优先级 |
|---------|---------|---------|--------|
| 招聘平台 | BOSS直聘、拉勾、猎聘、智联、前程无忧 | 职位详情 JD | P0 |
| 社交媒体 | 微信公众号、微博、小红书、抖音 | 内推/急招帖 | P1 |
| 校园招聘 | 高校就业网、企业校招官网 | 校招/实习信息 | P1 |
| 通用搜索 | Google/Bing/百度 | 补充抓取 | P2 |

---

## 2. 功能架构

### 2.1 功能模块图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层 (UI)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 报告展示  │  │ 筛选搜索  │  │ 收藏对比  │  │ 配置管理  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         业务处理层 (Processing)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 数据标准化 │  │ 智能去重  │  │ 关键词提取 │  │ 时间线重建 │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         数据采集层 (Collection)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ BOSS采集 │  │ 拉勾采集  │  │ 社媒采集  │  │ 校招采集  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐                                      │
│  │ Web搜索  │  │ 通用采集  │                                      │
│  └──────────┘  └──────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         系统能力层 (System)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 增量更新 │  │ 代理IP池  │  │ 频率控制  │  │ 断点续传  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐                                      │
│  │ 持久化   │  │ 定时调度  │                                      │
│  └──────────┘  └──────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 详细功能说明

### 3.1 意向岗位配置 (job-001)

**功能描述**: 用户定义期望的搜索条件

**配置项**:
```yaml
job_preferences:
  keywords:
    - "Python开发"
    - "后端工程师"
    exclude:
      - "实习"
      - "外包"
  locations:
    - "北京"
    - "上海"
  salary_min: 20000  # 月薪，单位元
  experience: "1-3年"
  education: "本科"
  tags:
    - "五险一金"
    - "弹性工作"
```

**关键逻辑**:
- 关键词支持 AND/OR 组合
- 排除词精准过滤
- 配置热更新，无需重启

---

### 3.2 BOSS直聘采集器 (job-002)

**数据字段**:
| 字段 | 说明 |
|-----|------|
| platform | "boss" |
| job_id | 平台职位ID |
| title | 职位名称 |
| company | 公司名称 |
| salary | 薪资范围 |
| location | 工作地点 |
| experience | 经验要求 |
| education | 学历要求 |
| tags | 福利标签 |
| description | 职位描述 |
| recruiter | 招聘者信息 |
| publish_time | 发布时间 |
| url | 原始链接 |

**反爬策略**:
- 代理IP轮换
- 请求间隔随机化 (1-3秒)
- User-Agent 随机
- Cookie 刷新机制

---

### 3.3 职位信息标准化 (proc-001)

**统一数据格式**:
```json
{
  "id": "hash(job_id + platform)",
  "platform": "string",
  "title": "string",
  "company": {
    "name": "string",
    "size": "string",
    "stage": "string",
    "industry": "string"
  },
  "salary": {
    "min": 20000,
    "max": 35000,
    "currency": "CNY",
    "period": "month"
  },
  "location": {
    "city": "string",
    "district": "string"
  },
  "requirements": {
    "experience_min": 1,
    "experience_max": 3,
    "education": "本科"
  },
  "skills": ["Python", "Go", "MySQL"],
  "description": "string",
  "highlights": ["弹性工作", "团队氛围好"],
  "source_url": "string",
  "published_at": "datetime"
}
```

---

### 3.4 智能去重与合并 (proc-002)

**去重算法**:
1. **精确去重**: job_id + platform 相同
2. **模糊去重**: 公司名 + 职位名 + 薪资 相似度 > 0.85

**合并策略**:
- 以最新发布时间为主
- 保留所有来源URL
- 更新时间线

---

### 3.5 报告生成器 (ui-001)

**报告格式**:

**Markdown 格式**:
```markdown
# 招聘信息汇总报告

## 基本信息
- 采集时间: 2026-04-15
- 关键词: Python开发
- 采集平台: BOSS直聘、拉勾
- 总职位数: 156

## 薪资分布
[图表]

## 地点分布
[图表]

## 职位列表
### 1. 公司名 - 职位名
- 薪资: 20k-35k
- 地点: 北京·朝阳区
- 经验: 1-3年
- 链接: https://...
```

---

## 4. 数据流设计

### 4.1 采集流程

```
用户配置 → 关键词生成 → 平台分发 → 采集器执行
                                      ↓
                              原始数据存储
                                      ↓
                              标准化处理
                                      ↓
                              去重合并
                                      ↓
                              SQLite/JSON存储
                                      ↓
                              报告生成 → 用户展示
```

### 4.2 存储设计

**SQLite 数据库**:
```sql
-- 职位主表
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    original_id TEXT,
    title TEXT NOT NULL,
    company_name TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    city TEXT,
    district TEXT,
    experience TEXT,
    education TEXT,
    description TEXT,
    source_url TEXT,
    published_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0
);

-- 关键词表
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    is_exclude INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 采集记录表
CREATE TABLE collection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT,
    status TEXT,
    items_collected INTEGER,
    started_at DATETIME,
    finished_at DATETIME,
    error_message TEXT
);

-- 收藏表
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

---

## 5. 系统架构

### 5.1 核心类设计

```
collectors/
├── __init__.py
├── base.py           # CollectorBase 抽象基类
├── boss.py           # BOSS直聘采集器
├── lagou.py          # 拉勾采集器
├── social.py         # 社交媒体采集器
├── campus.py         # 校园招聘采集器
└── web_search.py     # Web搜索采集器

processors/
├── __init__.py
├── normalizer.py     # 数据标准化
├── deduplicator.py   # 去重处理
├── extractor.py      # 关键词提取
└── timeline.py       # 时间线重建

storage/
├── __init__.py
├── database.py       # SQLite 操作
├── cache.py          # 缓存管理
└── persistence.py    # 持久化

ui/
├── __init__.py
├── reporter.py       # 报告生成
├── search.py         # 筛选搜索
└── favorites.py      # 收藏对比

system/
├── __init__.py
├── proxy_pool.py     # 代理池
├── rate_limiter.py   # 频率控制
├── checkpoint.py     # 断点续传
├── scheduler.py      # 定时调度
└── notifier.py      # 通知推送

config/
├── __init__.py
├── settings.py       # 配置管理
└── preferences.py    # 用户偏好
```

---

## 6. 实现优先级

### Phase 1: MVP (核心采集)
1. job-001: 意向岗位配置
2. job-002: BOSS直聘采集器
3. proc-001: 职位信息标准化
4. proc-002: 智能去重与合并
5. ui-001: 报告生成器

### Phase 2: 扩展采集
6. job-003: 拉勾采集器
7. job-004: 其他招聘平台
8. sys-001: 增量更新引擎
9. sys-003: 请求频率控制

### Phase 3: 社交媒体
10. job-005: 社交媒体采集器
11. job-006: 校园招聘采集器
12. sys-002: 代理IP池

### Phase 4: 高级功能
13. ui-002: 筛选与搜索
14. ui-003: 收藏与对比
15. sys-004: 断点续传
16. sys-005: 多会话持久化
17. sys-006: 定时任务调度
18. sys-007: 通知推送

---

## 7. 验收标准

### 7.1 功能验收
- [ ] 单次采集成功率 > 95%
- [ ] 数据字段完整率 > 98%
- [ ] 去重准确率 > 90%
- [ ] 报告生成完整性 100%

### 7.2 性能验收
- [ ] 单平台采集 < 5分钟 (100条职位)
- [ ] 内存占用 < 500MB
- [ ] 支持断网恢复

### 7.3 安全验收
- [ ] API Key 不硬编码
- [ ] 代理请求加密
- [ ] 敏感信息脱敏

---

## 8. 后续扩展方向

1. **AI智能匹配**: 基于用户简历推荐岗位
2. **薪资预测**: 评估职位薪资合理性
3. **竞争分析**: 同岗位投递热度
4. **趋势分析**: 招聘趋势时序分析
5. **导出同步**: 同步到 Notion/Airtable
