# 股票爬虫系统需求规格说明书

**版本**: v1.0  
**日期**: 2026-05-07  
**状态**: 待评审  

---

## 目录

1. [引言](#1-引言)
2. [总体描述](#2-总体描述)
3. [功能需求](#3-功能需求)
4. [非功能需求](#4-非功能需求)
5. [数据需求](#5-数据需求)
6. [接口需求](#6-接口需求)
7. [附录](#7-附录)

---

## 1. 引言

### 1.1 目的

本文档详细描述了股票爬虫系统的功能需求、技术架构和实现规范，旨在为软件开发团队提供明确、可执行的设计和开发指导。

### 1.2 范围

本系统是一个股票信息监控与数据采集平台，主要功能包括：
- 上市公司关键指标监测（股息率、市盈率等）
- 实时交易数据监测（30秒级别）
- 财报、研报、新闻、论坛、董秘发言等多维度信息监测
- 数据清洗与格式转换（PDF转Markdown/JSON）
- LLM智能分析接口

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| **强配置** | 绝对要素提取，由人为手动指定的明确属性 |
| **弱配置** | 下载网页原始文件，包含链接、日期、数据集，后置分析 |
| **30秒级别** | 固定30秒轮询频率获取实时交易数据 |
| **前向拉取** | 首次关注股票时，拉取最近十年的历史数据 |
| **按需存储** | 根据数据类型选择存储位置（PostgreSQL或文件） |

### 1.4 参考资料

- AkShare API文档
- Tushare Pro文档
- Baostock API文档
- FastAPI官方文档
- PostgreSQL 15文档

---

## 2. 总体描述

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESTful API 层 (FastAPI)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  任务管理API │  │  数据查询API │  │  配置管理API │  │  LLM分析API        │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                           调度管理层 (Scheduler)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 定时任务调度 │  │ 任务队列管理 │  │ 任务状态监控 │  │ 多账号轮换调度     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                           数据采集层 (Crawlers)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     数据源适配器工厂 (DataSourceFactory)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ AkShare适配器 │ │ Tushare适配器 │ │ Baostock适配器│ │ 财经网站爬虫组   │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ 东方财富爬虫  │ │  雪球爬虫    │  │ 同花顺爬虫   │  │  新闻源爬虫     │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                           数据处理层 (Processors)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ PDF转Markdown│  │ 数据清洗    │  │ 数据标准化  │  │ 内容去重           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                           LLM分析层 (AI Analysis)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 情感分析    │  │ 事件抽取    │  │ 趋势预测    │  │ 风险识别           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                           存储层 (Storage)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   PostgreSQL        │  │   文件存储          │  │   Redis缓存         │  │
│  │  (结构化数据)        │  │  (PDF/Markdown/JSON)│  │  (热点数据/队列)    │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 运行环境

| 组件 | 版本要求 | 用途 |
|------|---------|------|
| Python | 3.11+ | 开发语言 |
| PostgreSQL | 15+ | 主数据存储 |
| Redis | 7+ | 缓存与队列 |
| Chrome | 最新版 | 浏览器自动化 |
| Docker | 24+ | 容器化部署 |

### 2.3 技术栈

- **Web框架**: FastAPI + Uvicorn
- **数据库ORM**: SQLAlchemy 2.0 + asyncpg
- **任务队列**: Celery + Redis
- **浏览器自动化**: Playwright
- **配置管理**: Pydantic Settings
- **数据验证**: Pydantic
- **日志**: Loguru
- **监控**: Prometheus + Grafana

---

## 3. 功能需求

### 3.1 RESTful API控制模块 (FR-001)

#### 3.1.1 增加信息获取的网站地址

**需求编号**: FR-001-001  
**优先级**: 高  
**描述**: 通过API动态添加新的数据源网站地址

**输入**:
```json
{
  "source_name": "xueqiu_forum",
  "source_type": "forum",
  "base_url": "https://xueqiu.com",
  "config": {
    "list_url_pattern": "/query/v1/symbol/search.json",
    "detail_url_pattern": "/{stock_code}",
    "headers": {...},
    "rate_limit": 10
  },
  "is_active": true
}
```

**处理逻辑**:
1. 验证URL格式和可访问性
2. 检查数据源名称唯一性
3. 存储到数据源配置表
4. 注册到数据源工厂

**输出**:
```json
{
  "source_id": "uuid",
  "status": "created",
  "test_result": "success"
}
```

**异常处理**:
- URL不可访问：返回400错误，提示检查网络或URL
- 名称重复：返回409错误，提示更换名称

#### 3.1.2 增加关注的上市公司

**需求编号**: FR-001-002  
**优先级**: 高  
**描述**: 添加需要监测的上市公司，触发历史数据前向拉取

**输入**:
```json
{
  "stock_code": "000001",
  "stock_name": "平安银行",
  "exchange": "SZSE",
  "monitor_config": {
    "realtime_quotes": true,
    "financial_reports": true,
    "research_reports": true,
    "forum_posts": true,
    "news": true,
    "secretary_replies": true
  },
  "data_sources": ["akshare", "tushare", "xueqiu"],
  "priority": 1
}
```

**处理逻辑**:
1. 验证股票代码格式和有效性
2. 写入companies表
3. 触发异步任务：前向拉取最近十年交易数据
4. 创建各类型监测任务

**输出**:
```json
{
  "company_id": 1,
  "stock_code": "000001",
  "status": "monitoring",
  "backfill_task_id": "task_uuid",
  "estimated_completion": "2026-05-08T10:00:00Z"
}
```

**前向拉取逻辑**:
- 交易数据：拉取最近10年日K线
- 财报数据：拉取最近10年年报和季报
- 研报数据：拉取最近5年研报
- 论坛/新闻：拉取最近1年历史数据

#### 3.1.3 作废关注的上市公司

**需求编号**: FR-001-003  
**优先级**: 高  
**描述**: 停止对指定上市公司的监测

**输入**:
```json
{
  "stock_code": "000001",
  "action": "deactivate",
  "reason": "optional"
}
```

**处理逻辑**:
1. 标记company记录为inactive
2. 暂停所有相关定时任务
3. 保留历史数据
4. 可选：归档数据到冷存储

**输出**:
```json
{
  "stock_code": "000001",
  "status": "deactivated",
  "tasks_stopped": 5,
  "data_retained": true
}
```

### 3.2 关键指标监测模块 (FR-002)

#### 3.2.1 全体上市公司关键指标检测

**需求编号**: FR-002-001  
**优先级**: 高  
**描述**: 定期检测全体A股上市公司的关键财务指标

**监测指标**:
| 指标名称 | 计算方式 | 数据来源 | 更新频率 |
|---------|---------|---------|---------|
| 股息率 | 年度分红/当前股价 | 财报数据+行情数据 | 每日 |
| 市盈率(PE) | 股价/每股收益 | 行情数据+财报数据 | 每日 |
| 市净率(PB) | 股价/每股净资产 | 行情数据+财报数据 | 每日 |
| 市销率(PS) | 市值/营业收入 | 行情数据+财报数据 | 每日 |
| ROE | 净利润/净资产 | 财报数据 | 季报 |
| 毛利率 | (营收-成本)/营收 | 财报数据 | 季报 |
| 负债率 | 总负债/总资产 | 财报数据 | 季报 |

**处理逻辑**:
1. 每日定时任务计算全市场指标
2. 对比历史数据识别异常波动
3. 生成指标分布报告
4. 存储到indicators表

**输出**:
```json
{
  "calculation_date": "2026-05-07",
  "total_stocks": 5200,
  "indicators": {
    "dividend_yield": {
      "avg": 2.35,
      "median": 1.89,
      "top10": [...],
      "bottom10": [...]
    },
    "pe_ratio": {...}
  }
}
```

### 3.3 实时交易监测模块 (FR-003)

#### 3.3.1 实时交易数据监测

**需求编号**: FR-003-001  
**优先级**: 高  
**描述**: 对关注股票进行30秒级别的实时交易数据监测

**监测内容**:
- 最新价格、涨跌幅
- 成交量、成交额
- 买卖五档盘口
- 分时成交明细

**技术实现**:
- 固定30秒轮询频率
- 多数据源并行采集
- Redis缓存实时数据（5分钟过期）
- PostgreSQL持久化历史数据

**数据融合策略**:
1. 同时从AkShare、Tushare、Baostock获取数据
2. 对比校验，取多数一致的数据
3. 标记数据来源和置信度
4. 异常数据触发告警

**存储策略**:
- 实时数据：Redis Hash，Key: `quote:realtime:{stock_code}`
- 历史数据：PostgreSQL分区表，按日期分区

### 3.4 财报研报监测模块 (FR-004)

#### 3.4.1 财报监测与拉取

**需求编号**: FR-004-001  
**优先级**: 高  
**描述**: 监测上市公司财报发布，拉取原始文档

**监测范围**:
- 年度报告
- 半年度报告
- 季度报告
- 业绩预告
- 业绩快报

**数据来源**:
- 上交所/深交所官网
- 东方财富网
- 巨潮资讯网

**处理流程**:
1. 定时扫描公告列表
2. 识别财报类型和报告期
3. 下载PDF原始文件
4. PDF转换为Markdown
5. 提取关键财务数据
6. 存储到数据库和文件系统

**文件存储路径**:
```
storage/documents/financial_reports/{stock_code}/{year}/
  - annual_report.pdf
  - annual_report.md
  - quarterly_q1.pdf
  - quarterly_q1.md
```

#### 3.4.2 研报监测与拉取

**需求编号**: FR-004-002  
**优先级**: 高  
**描述**: 监测券商、投行、第三方机构研报

**监测来源**:
- 券商研究所（中金、中信、华泰等）
- 投行研报
- Wind、Choice等数据终端
- 东方财富研报中心

**研报元数据**:
- 标题、发布机构、分析师
- 评级、目标价
- 发布日期、摘要

**存储结构**:
```json
{
  "report_id": "uuid",
  "stock_code": "000001",
  "title": "平安银行2026年业绩点评",
  "institution": "中金公司",
  "analyst": "张三",
  "rating": "买入",
  "target_price": 15.80,
  "publish_date": "2026-05-07",
  "summary": "...",
  "file_path": "/storage/research_reports/000001/中金公司/20260507_业绩点评.pdf",
  "markdown_path": "/storage/research_reports/000001/中金公司/20260507_业绩点评.md"
}
```

### 3.5 论坛监测模块 (FR-005)

#### 3.5.1 关键论坛监测

**需求编号**: FR-005-001  
**优先级**: 高  
**描述**: 监测雪球、东方财富股吧等论坛的讨论内容

**监测平台**:
- 雪球网 (xueqiu.com)
- 东方财富股吧
- 同花顺圈子

**采集内容**:
- 帖子标题、内容
- 作者、发布时间
- 浏览量、评论数、点赞数
- 评论内容

**弱配置策略**:
- 下载网页原始HTML
- 保留完整链接、日期、数据集
- 后置分析提取结构化数据
- 日期+校验和去重

**存储格式**:
```json
{
  "raw_html_path": "/storage/raw_data/forum/xueqiu/20260507/post_12345.html",
  "extracted_data": {
    "post_id": "12345",
    "stock_code": "000001",
    "platform": "xueqiu",
    "author": "user123",
    "title": "平安银行分析",
    "content": "...",
    "post_time": "2026-05-07T14:30:00",
    "view_count": 1234,
    "comment_count": 56,
    "like_count": 78,
    "url": "https://xueqiu.com/12345"
  },
  "checksum": "md5_hash",
  "crawl_time": "2026-05-07T15:00:00"
}
```

### 3.6 董秘发言监测模块 (FR-006)

#### 3.6.1 董秘发言及回复监测

**需求编号**: FR-006-001  
**优先级**: 高  
**描述**: 监测上市公司董秘在互动平台的回复

**监测平台**:
- 上交所e互动
- 深交所互动易
- 北交所投资者互动平台

**采集内容**:
- 投资者提问
- 董秘回复内容
- 提问时间、回复时间
- 问题分类标签

**数据处理**:
1. 提取问答对
2. 情感分析
3. 关键主题提取
4. 关联股票代码

### 3.7 新闻监测模块 (FR-007)

#### 3.7.1 上市公司新闻监测

**需求编号**: FR-007-001  
**优先级**: 高  
**描述**: 监测与关注上市公司相关的新闻资讯

**新闻来源**:
- 东方财富新闻
- 新浪财经
- 财联社
- 证券时报
- 上海证券报

**新闻分类**:
- 公司公告类
- 行业动态类
- 市场评论类
- 政策影响类

**重要度评级**:
- 1级：极重要（直接影响股价）
- 2级：重要（重大事件）
- 3级：一般（常规报道）
- 4级：次要（行业新闻）
- 5级：参考（背景信息）

### 3.8 数据存储模块 (FR-008)

#### 3.8.1 按需存储策略

**需求编号**: FR-008-001  
**优先级**: 高  
**描述**: 根据数据类型选择适当的存储方式

**存储决策矩阵**:

| 数据类型 | PostgreSQL | 原始文件 | Markdown+JSON | 说明 |
|---------|-----------|---------|--------------|------|
| 实时行情 | ✓ | - | - | 结构化数据，高频写入 |
| 历史行情 | ✓ | - | - | 结构化数据，分区存储 |
| 财报元数据 | ✓ | - | - | 结构化索引数据 |
| 财报PDF | - | ✓ | ✓ | 原始文件+转换后Markdown |
| 研报元数据 | ✓ | - | - | 结构化索引数据 |
| 研报PDF | - | ✓ | ✓ | 原始文件+转换后Markdown |
| 论坛帖子 | ✓ | ✓ | ✓ | 元数据存PG，原始HTML存文件 |
| 新闻资讯 | ✓ | - | ✓ | 结构化数据+原始内容JSON |
| 董秘问答 | ✓ | - | ✓ | 结构化数据+原始内容JSON |
| LLM分析结果 | ✓ | - | ✓ | 结果存PG，详细分析存JSON |

### 3.9 数据清洗模块 (FR-009)

#### 3.9.1 PDF转Markdown/JSON

**需求编号**: FR-009-001  
**优先级**: 中  
**描述**: 将PDF文档转换为Markdown和JSON格式

**转换工具**:
- pdfplumber / PyMuPDF：PDF解析
- markdownify：HTML转Markdown
- 自定义提取器：表格、图表识别

**输出格式**:
```markdown
# 平安银行2025年年度报告

## 一、重要提示
...

## 二、主要财务数据
| 项目 | 2025年 | 2024年 | 同比变化 |
|-----|-------|-------|---------|
| 营业收入 | xxx | xxx | xx% |
...
```

```json
{
  "document_type": "annual_report",
  "stock_code": "000001",
  "report_year": 2025,
  "extracted_data": {
    "revenue": 169389000000.00,
    "net_profit": 45500000000.00,
    "total_assets": 5500000000000.00,
    ...
  },
  "tables": [...],
  "sections": [...]
}
```

#### 3.9.2 数据去重与校验

**需求编号**: FR-009-002  
**优先级**: 高  
**描述**: 基于日期和校验和进行数据去重

**去重策略**:
1. 文件级去重：MD5校验和
2. 内容级去重：相似度检测
3. 时间级去重：同一来源同一时间段只保留最新

**校验规则**:
- 文件完整性校验（MD5/SHA256）
- 数据格式校验（JSON Schema）
- 业务逻辑校验（数值范围、关联关系）

### 3.10 LLM分析模块 (FR-010)

#### 3.10.1 LLM分析接口

**需求编号**: FR-010-001  
**优先级**: 中  
**描述**: 提供LLM分析抽象接口，支持多提供商扩展

**接口设计**:
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        pass
    
    @abstractmethod
    async def extract_events(self, text: str) -> List[Dict]:
        """事件抽取"""
        pass
    
    @abstractmethod
    async def generate_report(self, data: Dict) -> str:
        """生成分析报告"""
        pass
```

**分析类型**:
- 情感分析：对帖子、新闻进行情感打分
- 事件抽取：识别重大事件（并购、业绩、政策等）
- 趋势预测：基于历史数据预测走势
- 风险识别：识别潜在风险因素

**输出格式**:
```json
{
  "analysis_type": "sentiment",
  "target": "forum_post_12345",
  "result": {
    "sentiment": "positive",
    "score": 0.75,
    "confidence": 0.92,
    "keywords": ["业绩增长", "分红"],
    "summary": "用户对平安银行业绩表示乐观"
  },
  "model": "provider_name",
  "created_at": "2026-05-07T15:00:00"
}
```

### 3.11 股票算法模块 (FR-011)

#### 3.11.1 算法API接口

**需求编号**: FR-011-001  
**优先级**: 中  
**描述**: RESTful API形式提供股票相关算法

**算法列表**:

| 算法名称 | 输入 | 输出 | 说明 |
|---------|------|------|------|
| 股息率计算 | 分红数据、股价 | 股息率 | 年度分红/当前股价 |
| 日振幅计算 | 日K线数据 | 振幅百分比 | (最高-最低)/昨收 |
| 周振幅计算 | 周K线数据 | 振幅百分比 | 周内最大波动 |
| 月振幅计算 | 月K线数据 | 振幅百分比 | 月内最大波动 |
| 相关性分析 | 多只股票价格序列 | 相关系数矩阵 | 皮尔逊相关系数 |
| 波动率计算 | 收益率序列 | 年化波动率 | 标准差计算 |
| 技术指标 | 价格序列 | MACD/KDJ/RSI | 技术分析指标 |

**API示例**:
```
POST /api/v1/algorithms/correlation
{
  "stock_codes": ["000001", "000002", "600000"],
  "start_date": "2025-01-01",
  "end_date": "2026-05-07",
  "method": "pearson"
}

Response:
{
  "correlation_matrix": {
    "000001": {"000001": 1.0, "000002": 0.65, "600000": 0.78},
    "000002": {"000001": 0.65, "000002": 1.0, "600000": 0.52},
    "600000": {"000001": 0.78, "000002": 0.52, "600000": 1.0}
  }
}
```

---

## 4. 非功能需求

### 4.1 性能需求

| 指标 | 目标值 | 说明 |
|------|-------|------|
| API响应时间 | P95 < 200ms | 常规查询接口 |
| 实时数据延迟 | < 35秒 | 从数据源到API |
| 并发请求处理 | 1000 QPS | 系统整体 |
| 历史数据查询 | < 2秒 | 10年数据范围 |
| 数据写入吞吐 | 10000条/秒 | 批量写入 |

### 4.2 可靠性需求

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 系统可用性 | 99.9% | 年度可用时间 |
| 数据完整性 | 99.99% | 不丢失已确认数据 |
| 故障恢复时间 | < 5分钟 | 自动故障转移 |
| 数据备份频率 | 每日 | 全量备份 |

### 4.3 安全性需求

- API认证：JWT Token
- 敏感数据加密：账号配置加密存储
- 访问控制：基于角色的权限管理
- 审计日志：所有操作记录
- 限流保护：防止API滥用

### 4.4 可扩展性需求

- 支持水平扩展：无状态API服务
- 新数据源接入：< 1天开发时间
- 新LLM提供商接入：< 半天开发时间
- 数据存储扩展：支持分库分表

### 4.5 可维护性需求

- 代码覆盖率：> 80%
- 文档完整度：所有API有OpenAPI文档
- 监控覆盖：所有关键路径有指标监控
- 日志规范：结构化日志，支持追踪

---

## 5. 数据需求

### 5.1 数据模型

#### 5.1.1 公司信息表 (companies)

```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) UNIQUE NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    exchange VARCHAR(20),
    industry VARCHAR(100),
    market_cap DECIMAL(20,2),
    is_active BOOLEAN DEFAULT TRUE,
    monitor_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.2 实时行情表 (stock_quotes)

```sql
CREATE TABLE stock_quotes (
    id BIGSERIAL,
    stock_code VARCHAR(20) NOT NULL,
    quote_time TIMESTAMP NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    change_percent DECIMAL(5,2),
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, quote_time)
) PARTITION BY RANGE (quote_time);
```

#### 5.1.3 财报信息表 (financial_reports)

```sql
CREATE TABLE financial_reports (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    report_year INTEGER NOT NULL,
    report_type VARCHAR(20) NOT NULL,
    report_title VARCHAR(500),
    release_date DATE,
    revenue DECIMAL(20,2),
    net_profit DECIMAL(20,2),
    total_assets DECIMAL(20,2),
    total_liabilities DECIMAL(20,2),
    file_path VARCHAR(500),
    markdown_path VARCHAR(500),
    data_source VARCHAR(50),
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.4 研报信息表 (research_reports)

```sql
CREATE TABLE research_reports (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20),
    report_title VARCHAR(500) NOT NULL,
    institution VARCHAR(200),
    analyst VARCHAR(100),
    rating VARCHAR(50),
    target_price DECIMAL(10,2),
    publish_date DATE,
    summary TEXT,
    file_path VARCHAR(500),
    markdown_path VARCHAR(500),
    data_source VARCHAR(50),
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.5 论坛帖子表 (forum_posts)

```sql
CREATE TABLE forum_posts (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20),
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(100) UNIQUE NOT NULL,
    author VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    post_time TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    sentiment_score DECIMAL(3,2),
    raw_file_path VARCHAR(500),
    checksum VARCHAR(64),
    is_analyzed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.6 董秘发言表 (secretary_replies)

```sql
CREATE TABLE secretary_replies (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    platform VARCHAR(50),
    question_id VARCHAR(100) UNIQUE NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    question_time TIMESTAMP,
    reply_time TIMESTAMP,
    sentiment_score DECIMAL(3,2),
    key_topics JSONB,
    raw_data JSONB,
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.7 新闻资讯表 (news_articles)

```sql
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20),
    news_title VARCHAR(500) NOT NULL,
    news_content TEXT,
    source VARCHAR(100),
    publish_time TIMESTAMP,
    url VARCHAR(500),
    sentiment_score DECIMAL(3,2),
    importance_level INTEGER DEFAULT 3,
    raw_data JSONB,
    checksum VARCHAR(64),
    is_analyzed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.8 账号配置表 (account_configs)

```sql
CREATE TABLE account_configs (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    config_json JSONB DEFAULT '{}',
    daily_quota INTEGER,
    used_quota INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.9 任务调度表 (crawler_tasks)

```sql
CREATE TABLE crawler_tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    stock_codes TEXT[],
    schedule_cron VARCHAR(100),
    data_sources TEXT[],
    config_json JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5.1.10 LLM分析结果表 (llm_analysis)

```sql
CREATE TABLE llm_analysis (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(100) NOT NULL,
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    model_name VARCHAR(100),
    raw_response JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 索引设计

```sql
-- 行情数据索引
CREATE INDEX idx_quotes_stock_time ON stock_quotes(stock_code, quote_time DESC);
CREATE INDEX idx_quotes_time ON stock_quotes(quote_time DESC);

-- 帖子索引
CREATE INDEX idx_posts_stock_time ON forum_posts(stock_code, post_time DESC);
CREATE INDEX idx_posts_platform ON forum_posts(platform, post_time DESC);
CREATE INDEX idx_posts_analyzed ON forum_posts(is_analyzed) WHERE is_analyzed = FALSE;

-- 全文搜索索引
CREATE INDEX idx_news_search ON news_articles USING gin(to_tsvector('chinese', news_title || ' ' || COALESCE(news_content, '')));
CREATE INDEX idx_posts_search ON forum_posts USING gin(to_tsvector('chinese', title || ' ' || COALESCE(content, '')));

-- 复合索引
CREATE INDEX idx_reports_stock_year ON financial_reports(stock_code, report_year DESC);
CREATE INDEX idx_analysis_target ON llm_analysis(target_type, target_id, created_at DESC);
CREATE INDEX idx_news_stock_time ON news_articles(stock_code, publish_time DESC);
CREATE INDEX idx_secretary_stock_time ON secretary_replies(stock_code, reply_time DESC);
```

### 5.3 文件存储结构

```
storage/
├── documents/
│   ├── financial_reports/
│   │   └── {stock_code}/
│   │       └── {year}/
│   │           ├── annual_report.pdf
│   │           ├── annual_report.md
│   │           └── quarterly_{q}.pdf/.md
│   ├── research_reports/
│   │   └── {stock_code}/
│   │       └── {institution}/
│   │           └── {date}_{title}.pdf/.md
│   └── announcements/
│       └── {stock_code}/
│           └── {year}/
│               └── {date}_{type}.pdf
├── raw_data/
│   ├── forum_posts/
│   │   └── {platform}/
│   │       └── {date}/
│   │           └── posts_{timestamp}.jsonl
│   ├── news/
│   │   └── {source}/
│   │       └── {date}/
│   │           └── news_{timestamp}.jsonl
│   └── quotes/
│       └── {date}/
│           └── quotes_{stock_code}_{timestamp}.parquet
└── exports/
    ├── analysis_reports/
    │   └── {date}/
    │       └── analysis_{stock_code}_{timestamp}.md
    └── backups/
        └── {date}/
```

---

## 6. 接口需求

### 6.1 RESTful API规范

#### 6.1.1 任务管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/tasks | 创建爬虫任务 |
| GET | /api/v1/tasks | 获取任务列表 |
| GET | /api/v1/tasks/{task_id} | 获取任务详情 |
| PUT | /api/v1/tasks/{task_id} | 更新任务 |
| DELETE | /api/v1/tasks/{task_id} | 删除任务 |
| POST | /api/v1/tasks/{task_id}/trigger | 手动触发任务 |
| POST | /api/v1/tasks/{task_id}/pause | 暂停任务 |
| POST | /api/v1/tasks/{task_id}/resume | 恢复任务 |

#### 6.1.2 公司管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/companies | 添加关注公司 |
| GET | /api/v1/companies | 获取公司列表 |
| GET | /api/v1/companies/{stock_code} | 获取公司详情 |
| PUT | /api/v1/companies/{stock_code} | 更新公司配置 |
| DELETE | /api/v1/companies/{stock_code} | 停止关注 |
| POST | /api/v1/companies/{stock_code}/backfill | 触发历史数据补全 |

#### 6.1.3 数据查询接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/quotes/realtime | 获取实时行情 |
| GET | /api/v1/quotes/history | 获取历史行情 |
| GET | /api/v1/financial-reports | 获取财报列表 |
| GET | /api/v1/financial-reports/{id}/content | 获取财报内容 |
| GET | /api/v1/research-reports | 获取研报列表 |
| GET | /api/v1/forum-posts | 获取论坛帖子 |
| GET | /api/v1/news | 获取新闻资讯 |
| GET | /api/v1/secretary-replies | 获取董秘发言 |

#### 6.1.4 LLM分析接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/analysis/sentiment | 情感分析 |
| POST | /api/v1/analysis/stock | 股票综合分析 |
| GET | /api/v1/analysis/tasks/{task_id} | 获取分析任务状态 |
| GET | /api/v1/analysis/report/{report_id} | 获取分析报告 |

#### 6.1.5 算法接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/algorithms/dividend-yield | 股息率计算 |
| POST | /api/v1/algorithms/amplitude | 振幅计算 |
| POST | /api/v1/algorithms/correlation | 相关性分析 |
| POST | /api/v1/algorithms/volatility | 波动率计算 |
| POST | /api/v1/algorithms/technical | 技术指标计算 |

#### 6.1.6 配置管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/accounts | 获取账号列表 |
| POST | /api/v1/accounts | 添加账号 |
| PUT | /api/v1/accounts/{id} | 更新账号 |
| DELETE | /api/v1/accounts/{id} | 删除账号 |
| POST | /api/v1/accounts/{id}/test | 测试账号连接 |
| GET | /api/v1/config/crawler | 获取爬虫配置 |
| PUT | /api/v1/config/crawler | 更新爬虫配置 |
| GET | /api/v1/config/llm | 获取LLM配置 |
| PUT | /api/v1/config/llm | 更新LLM配置 |

### 6.2 请求/响应格式

#### 6.2.1 标准响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "request_id": "uuid"
}
```

#### 6.2.2 错误响应格式

```json
{
  "code": 400,
  "message": "Invalid stock code format",
  "error_type": "validation_error",
  "details": {
    "field": "stock_code",
    "issue": "Stock code must be 6 digits"
  },
  "request_id": "uuid"
}
```

---

## 7. 附录

### 7.1 数据源配置

#### 7.1.1 AkShare配置

```yaml
akshare:
  accounts:
    - name: "akshare_default"
      priority: 1
      rate_limit: 100  # 每分钟请求数
  endpoints:
    realtime_quotes: "stock_zh_a_spot_em"
    history_quotes: "stock_zh_a_hist"
    financial_reports: "stock_financial_report_sina"
```

#### 7.1.2 Tushare配置

```yaml
tushare:
  accounts:
    - name: "tushare_pro"
      api_key: "${TUSHARE_API_KEY}"
      priority: 2
      daily_quota: 5000
  endpoints:
    realtime_quotes: "daily"
    history_quotes: "daily"
    financial_reports: "income"
```

#### 7.1.3 Baostock配置

```yaml
baostock:
  accounts:
    - name: "baostock_default"
      username: "${BAOSTOCK_USER}"
      password: "${BAOSTOCK_PASS}"
      priority: 3
  endpoints:
    realtime_quotes: "query_all_stock"
    history_quotes: "query_history_k_data_plus"
```

#### 7.1.4 财经网站配置

```yaml
websites:
  xueqiu:
    base_url: "https://xueqiu.com"
    list_url: "/query/v1/symbol/search.json"
    rate_limit: 10
    headers:
      User-Agent: "Mozilla/5.0..."
  eastmoney:
    base_url: "https://emweb.securities.eastmoney.com"
    rate_limit: 20
  tonghuashun:
    base_url: "https://q.10jqka.com.cn"
    rate_limit: 15
```

### 7.2 错误码定义

| 错误码 | 描述 | HTTP状态码 |
|-------|------|-----------|
| 200 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未授权 | 401 |
| 403 | 禁止访问 | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突 | 409 |
| 429 | 请求过于频繁 | 429 |
| 500 | 服务器内部错误 | 500 |
| 503 | 服务不可用 | 503 |

### 7.3 监控指标

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| crawler_task_total | Counter | 爬虫任务总数 |
| crawler_task_duration | Histogram | 任务执行时长 |
| crawler_success_rate | Gauge | 爬虫成功率 |
| data_source_latency | Histogram | 数据源响应延迟 |
| api_request_total | Counter | API请求总数 |
| api_response_time | Histogram | API响应时间 |
| db_connection_pool | Gauge | 数据库连接池使用率 |
| queue_depth | Gauge | 任务队列深度 |

---

**文档结束**
