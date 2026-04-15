# DeepResearch - 招聘信息智能采集系统

## 项目概述

这是一个基于 Claude 的深度研究智能体系统，专注于**招聘信息智能采集**，支持从多渠道（BOSS直聘、招聘平台、社交媒体、校园招聘等）自动抓取、清洗、聚合职位资讯。

## 核心功能

| 模块 | 功能 |
|-----|------|
| **数据采集** | 多平台适配、代理轮换、频率控制 |
| **智能处理** | 数据标准化、去重合并、关键词提取 |
| **用户交互** | 报告生成、筛选搜索、收藏对比 |
| **系统能力** | 增量更新、断点续传、多会话持久化 |

## 长时间运行模式

### 核心机制

| 文件 | 用途 |
|------|------|
| `init.sh` | 初始化开发环境 |
| `resume.sh` | 恢复工作状态（每次会话开始执行） |
| `feature_list.json` | 功能需求清单，追踪完成状态 |
| `claude-progress.txt` | 进度记录，支持会话间恢复 |

### 会话工作流

1. **进入状态**: 每次会话开始运行 `bash resume.sh`
2. **选择功能**: 从 `feature_list.json` 选择一个 `passes: false` 的功能
3. **增量开发**: 每次只完成**一个功能**
4. **提交保存**: 结束前提交 git 并更新进度文件
5. **环境清洁**: 确保代码可合并到主分支

### 功能状态更新规范

- 功能列表**仅修改** `passes` 字段（true/false）
- **禁止**删除功能条目
- 每次更新记录到 `claude-progress.txt`

### 会话结束检查清单

- [ ] 目标功能实现并测试通过
- [ ] `feature_list.json` 中对应功能标记 `passes: true`
- [ ] `claude-progress.txt` 记录完成状态
- [ ] Git 提交（描述性提交消息）
- [ ] 代码可编译/运行，无 major bugs

## 开发命令

```bash
# 初始化环境
bash init.sh

# 恢复工作状态（每次会话开始）
bash resume.sh

# 运行测试
pytest tests/ -v

# 启动采集
python main.py collect --keywords "Python开发" --cities 北京上海
```

## 项目结构

```
deeep-reasearch/
├── collecters/          # 采集器模块
│   ├── base.py          # 采集器基类
│   ├── boss.py         # BOSS直聘
│   ├── lagou.py        # 拉勾网
│   └── ...
├── processors/         # 处理器模块
│   ├── normalizer.py   # 数据标准化
│   ├── deduplicator.py # 去重合并
│   └── extractor.py    # 关键词提取
├── storage/            # 存储模块
│   ├── database.py     # SQLite操作
│   └── persistence.py  # 持久化
├── ui/                 # 用户交互
│   ├── reporter.py     # 报告生成
│   └── search.py       # 筛选搜索
├── system/             # 系统能力
│   ├── proxy_pool.py   # 代理池
│   ├── rate_limiter.py # 频率控制
│   └── scheduler.py    # 定时调度
├── config/             # 配置
│   └── preferences.py  # 用户偏好
├── main.py            # 入口
├── tests/             # 测试
└── docs/              # 文档
```

## 产品路线图

### Phase 1: MVP
- [x] core-001 项目基础架构
- [ ] job-001 意向岗位配置
- [ ] job-002 BOSS直聘采集器
- [ ] proc-001 职位信息标准化
- [ ] proc-002 智能去重合并
- [ ] ui-001 报告生成器

### Phase 2: 扩展
- [ ] job-003 拉勾采集器
- [ ] job-004 其他招聘平台
- [ ] sys-001 增量更新

### Phase 3: 社交媒体
- [ ] job-005 社交媒体采集
- [ ] job-006 校园招聘采集
