# A股实时数据爬虫 — 产品需求文档 (PRD)

**版本**: v1.0  
**日期**: 2026-05-14  
**状态**: 待评审  
**数据源验证基准**: AkShare v1.16+ / Baostock v0.9.10 / 东方财富 REST API

---

## 目录

1. [引言](#1-引言)
2. [产品概述](#2-产品概述)
3. [功能需求](#3-功能需求)
4. [数据结构设计](#4-数据结构设计)
5. [非功能需求](#5-非功能需求)
6. [验收标准](#6-验收标准)
7. [环境与部署](#7-环境与部署)
8. [辅助文件](#8-辅助文件)
9. [待验证任务清单](#9-待验证任务清单)
10. [附录](#10-附录)

---

## 1. 引言

### 1.1 目的

本文档为"A股实时数据爬虫"系统的产品需求文档，旨在为开发团队提供明确、可执行的开发指导。所有需求均基于对 AkShare、Baostock、东方财富 API 的实际验证结果，确保技术可行性。

### 1.2 范围

本系统是一个 A 股分钟级全量数据采集引擎，核心能力包括：
- 分钟级 K 线数据采集（1分钟实时 + 5分钟历史）
- 日 K 线数据回溯（2016年至今）
- 五档买卖盘口数据采集（指定股票，上限100支可配置）
- ST/退市风险/港股特化标记
- 实时指数监控（每分钟刷新上证/深证指数）
- 数据完整性自动检查与补全
- 无人值守后台长期运行

**不在范围内**：LLM 分析、论坛监测、新闻采集、研报管理、Web API 服务。

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| **1分钟K线** | 通过 AkShare `stock_zh_a_hist_min_em` 获取，仅覆盖最近5个交易日 |
| **5分钟K线** | 通过 Baostock `query_history_k_data_plus` 获取，可回溯至2020-01-02 |
| **日线** | 通过 AkShare/Baostock 获取，可回溯至1990年 |
| **五档盘口** | 通过 AkShare `stock_bid_ask_em` 获取，实际返回10档数据 |
| **特化标记** | ST/*ST/退市风险/同时有港股等特殊分类标记 |
| **断点续传** | 采集进度持久化，异常恢复后从上次中断位置继续 |
| **数据完整性检查** | 启动时对比交易日历，识别并补全缺失数据 |

### 1.4 参考资料与验证依据

| 资料 | 链接 | 验证状态 |
|------|------|----------|
| AkShare 官方文档 | https://akshare.akfamily.xyz/introduction.html | 已验证接口可用性 |
| Baostock API 文档 | https://baostock.com/mainContent?file=pythonAPI.md | 已验证接口可用性 |
| 东方财富行情 API | https://push2.eastmoney.com/api/qt/stock/get | PoC 已通过 |
| AkShare 分钟线限制 | 官方文档 + PoC 验证：1分钟仅5天 | ✅ 已确认 |
| Baostock 分钟线范围 | 官方声称2019年起，实测最早2020-01-02 | ✅ 已确认 |
| 东方财富反爬阈值 | PoC 测试：5-10次/分钟安全 | ✅ 已确认 |

---

## 2. 产品概述

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     调度引擎 (SchedulerEngine)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ 分钟K线  │ │ 日线采集 │ │ 盘口采集 │ │ 指数监控 Job     │   │
│  │ 采集 Job │ │ Job      │ │ Job      │ │ (每分钟)         │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │ 特化标记 │ │ 完整性   │ │ 进度管理 │                        │
│  │ Job      │ │ 检查 Job │ │ Job      │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
├─────────────────────────────────────────────────────────────────┤
│                     数据源适配层 (Adapters)                       │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ AkShare      │ │ Baostock     │ │ 东方财富 API           │  │
│  │ Adapter      │ │ Adapter      │ │ Adapter                │  │
│  │ (实时+盘口)  │ │ (历史K线+ST) │ │ (指数实时)             │  │
│  └──────────────┘ └──────────────┘ └────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ DataSourceFactory — 配置驱动切换、降级回退                  │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     基础设施层                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ 限流器   │ │ 账号管理 │ │ 日志系统 │ │ 邮件通知         │  │
│  │ (令牌桶) │ │ (轮换)   │ │ (5级)    │ │ (CRITICAL触发)   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     存储层 (PostgreSQL)                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ 分钟K线表    │ │ 日K线表      │ │ 盘口快照表           │   │
│  │ (按月分区)   │ │              │ │                      │   │
│  └──────────────┘ └──────────────┘ └──────────────────────┘   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ 特化标记表   │ │ 指数行情表   │ │ 采集进度表           │   │
│  └──────────────┘ └──────────────┘ └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
交易时段启动
    │
    ├── 1分钟K线采集 (AkShare) ──→ minute_klines 表 (frequency=1)
    │       每1分钟轮询，仅最近5个交易日
    │
    ├── 5分钟K线增量 (Baostock) ──→ minute_klines 表 (frequency=5)
    │       盘后20:00后拉取当日5分钟数据
    │
    ├── 五档盘口采集 (AkShare) ──→ bid_ask_snapshots 表
    │       指定股票列表，上限100支，可配置间隔
    │
    ├── 指数实时监控 (东方财富API) ──→ index_quotes 表
    │       每60秒刷新上证/深证指数
    │
    └── 非交易时段
            ├── 日线数据补全 (Baostock/AkShare)
            ├── ST/退市/港股标记更新
            └── 数据完整性检查与修复
```

### 2.3 数据源分工策略

| 数据类型 | 主数据源 | 备用数据源 | 说明 |
|----------|----------|-----------|------|
| 1分钟K线（实时） | AkShare | 东方财富API | AkShare仅5天深度 |
| 5分钟K线（历史） | Baostock | AkShare | Baostock可回溯2020年 |
| 日K线 | Baostock | AkShare | 均可回溯1990年 |
| 实时行情 | 东方财富API | AkShare | 东方财富延迟~100ms |
| 五档盘口 | AkShare | 无 | 唯一免费来源 |
| ST标记 | Baostock(isST) | AkShare(名称) | 双重验证 |
| 港股数据 | AkShare | 无 | 唯一免费来源 |
| 指数实时 | 东方财富API | AkShare | 东方财富响应最快 |
| 交易日历 | Baostock | AkShare | 判断交易日 |

---

## 3. 功能需求

### 3.1 FR-001: 双数据源适配器

#### 3.1.1 需求描述

系统提供统一的数据源适配器接口，支持 AkShare、Baostock、东方财富 API 三个数据源，实现配置驱动的切换和降级回退。

#### 3.1.2 适配器接口定义

```python
class BaseDataAdapter(ABC):
    @abstractmethod
    async def get_minute_kline(
        self, stock_code: str, frequency: str,
        start_date: str, end_date: str
    ) -> pd.DataFrame:
        """获取分钟K线数据"""

    @abstractmethod
    async def get_daily_kline(
        self, stock_code: str,
        start_date: str, end_date: str
    ) -> pd.DataFrame:
        """获取日K线数据"""

    @abstractmethod
    async def get_realtime_quote(
        self, stock_code: str
    ) -> dict[str, object]:
        """获取实时行情"""

    @abstractmethod
    async def get_stock_list(self) -> pd.DataFrame:
        """获取全量A股列表"""

    @abstractmethod
    async def health_check(self) -> bool:
        """数据源健康检查"""
```

#### 3.1.3 AkShare 适配器能力

| 接口方法 | AkShare 函数 | 频率限制 | 数据范围 |
|----------|-------------|----------|----------|
| 1分钟K线 | `stock_zh_a_hist_min_em` | ≥3秒/次 | 最近5个交易日 |
| 5分钟K线 | `stock_zh_a_hist_min_em(period=5)` | ≥3秒/次 | 单次~20000条 |
| 日K线 | `stock_zh_a_hist` | ≥3秒/次 | 1990年至今 |
| 实时行情 | `stock_zh_a_spot_em` | ≥6秒/次 | 全市场5400+只 |
| 五档盘口 | `stock_bid_ask_em` | ≥3秒/只 | 单只查询 |
| ST列表 | `stock_zh_a_st_em` | ≥3秒/次 | 全市场 |
| 港股行情 | `stock_hk_spot_em` | ≥3秒/次 | 港股全量 |
| 股票列表 | `stock_info_a_code_name` | ≥3秒/次 | A股全量 |

**依据**: AkShare 官方文档 + PoC 验证（[poc_akshare_api.py](file:///poc_akshare_api.py)）

#### 3.1.4 Baostock 适配器能力

| 接口方法 | Baostock 函数 | 频率限制 | 数据范围 |
|----------|-------------|----------|----------|
| 5分钟K线 | `query_history_k_data_plus(freq=5)` | ≥0.3秒/次 | 2020-01-02至今 |
| 日K线 | `query_history_k_data_plus(freq=d)` | ≥0.3秒/次 | 1990年至今 |
| ST标记 | 日线 `isST` 字段 | ≥0.3秒/次 | 日线数据附带 |
| 股票列表 | `query_all_stock` | ≥0.3秒/次 | 全量（不含北交所） |
| 交易日历 | `query_trade_dates` | ≥0.3秒/次 | 全量 |
| 退市信息 | `query_stock_basic` | ≥0.3秒/次 | 含 `outDate` |

**限制**:
- 不支持1分钟K线
- 不支持实时行情（分钟数据当日20:00后入库）
- 不支持五档盘口
- 不支持港股数据
- 不支持指数分钟线
- 单进程仅允许1个活跃TCP连接
- 单连接建议≤5000次查询后重新登录

**依据**: Baostock 官方文档 + PoC 验证（[poc_baostock.py](file:///poc_baostock.py)）

#### 3.1.5 东方财富 API 适配器能力

| 接口方法 | API 端点 | 频率限制 | 数据范围 |
|----------|---------|----------|----------|
| 实时行情 | `push2.eastmoney.com/api/qt/stock/get` | 5-10次/分钟 | 全市场 |
| 指数列表 | `push2.eastmoney.com/api/qt/clist/get` | 5-10次/分钟 | 全部指数 |
| K线数据 | `push2his.eastmoney.com/api/qt/stock/kline/get` | 5-10次/分钟 | 各周期 |
| 分时线 | `push2his.eastmoney.com/api/qt/stock/trends2/get` | 5-10次/分钟 | 当日/5日 |

**secid 编码规则**: 沪市前缀 `1.`，深市前缀 `0.`（代码以6/9开头为沪市）

**依据**: PoC 验证（[poc_eastmoney.py](file:///poc_eastmoney.py)），响应时间~96ms

#### 3.1.6 降级回退策略

```
请求 → 主数据源 → 成功 → 返回数据
                → 失败/限流 → 备用数据源 → 成功 → 返回数据 + 记录降级日志
                                          → 失败 → 记录ERROR + 等待冷却重试
```

### 3.2 FR-002: 分钟级K线数据采集

#### 3.2.1 需求描述

采集 A 股全量分钟级 K 线数据，采用 1 分钟 + 5 分钟混合策略：
- **1分钟K线**: 交易时段通过 AkShare 实时采集，覆盖最近5个交易日
- **5分钟K线**: 通过 Baostock 批量拉取，回溯至 2020-01-02

#### 3.2.2 采集字段

| 字段名 | 类型 | 说明 | 来源 |
|--------|------|------|------|
| stock_code | VARCHAR(20) | 股票代码 | 统一格式 |
| trade_time | TIMESTAMP | 交易时间 | 精确到分钟 |
| open | DECIMAL(10,4) | 开盘价 | - |
| high | DECIMAL(10,4) | 最高价 | - |
| low | DECIMAL(10,4) | 最低价 | - |
| close | DECIMAL(10,4) | 收盘价 | - |
| volume | BIGINT | 成交量 | 单位：股 |
| amount | DECIMAL(20,2) | 成交额 | 单位：元 |
| change_pct | DECIMAL(6,3) | 涨跌幅(%) | - |
| amplitude | DECIMAL(6,3) | 振幅(%) | - |
| turnover | DECIMAL(6,3) | 换手率(%) | Baostock日线有，分钟线无 |
| frequency | VARCHAR(5) | 频率标记 | "1"或"5" |
| data_source | VARCHAR(20) | 数据来源 | "akshare"/"baostock" |

#### 3.2.3 1分钟K线采集策略

- **触发时机**: 交易时段（9:30-11:30, 13:00-15:00），每1分钟轮询
- **数据源**: AkShare `stock_zh_a_hist_min_em(period=1)`
- **覆盖范围**: 仅最近5个交易日
- **采集顺序**: 按股票代码分批，每批50只，批次间隔≥1秒
- **全量估算**: 5400只 × 5天 × 240条/天 = 648万条（初始回填）
- **增量估算**: 5400只 × 1条/分钟 × 240分钟/天 = 129.6万条/天

#### 3.2.4 5分钟K线采集策略

- **触发时机**: 盘后20:00后批量拉取当日数据；首次启动全量回溯
- **数据源**: Baostock `query_history_k_data_plus(frequency=5)`
- **覆盖范围**: 2020-01-02 至今
- **全量估算**: 5400只 × 6年 × 250天 × 48条/天 ≈ 38.88亿条
- **分批策略**: 按月分批，每只股票按月查询
- **限流控制**: 请求间隔≥0.3秒，单连接≤5000次后重登录

#### 3.2.5 首次全量回溯流程

```
启动 → 检查数据库是否有数据
    → 无数据 → 启动全量回溯
        ├── 日线: 2016-01-01 至今 (Baostock/AkShare)
        ├── 5分钟K线: 2020-01-02 至今 (Baostock)
        └── 1分钟K线: 最近5个交易日 (AkShare)
    → 有数据 → 启动增量更新
        ├── 检查最新时间点
        └── 仅采集缺失时段
```

#### 3.2.6 断点续传机制

- 采集进度持久化到 `crawl_progress` 表
- 记录维度: stock_code + frequency + last_trade_time
- 异常恢复后从上次记录位置继续
- 全量回溯支持按月粒度断点

### 3.3 FR-003: 日K线数据采集

#### 3.3.1 需求描述

采集 A 股全量日 K 线数据，回溯至 2016-01-01，作为分钟级数据的历史补充。

#### 3.3.2 采集策略

- **主数据源**: Baostock（含 isST 字段）
- **备用数据源**: AkShare
- **触发时机**: 每日收盘后增量更新
- **首次回溯**: 2016-01-01 至今

#### 3.3.3 日线附加字段

除标准 OHLCV 外，日线额外采集：
- `is_st`: ST标记（Baostock独有）
- `pre_close`: 昨收价
- `change_pct`: 涨跌幅
- `turnover`: 换手率
- `pe_ttm`: 滚动市盈率
- `pb_mrq`: 市净率

### 3.4 FR-004: 五档买卖盘口数据采集

#### 3.4.1 需求描述

对指定股票列表（上限100支，可配置）采集实时五档买卖盘口数据。

#### 3.4.2 采集策略

- **数据源**: AkShare `stock_bid_ask_em`（实际返回10档数据）
- **触发时机**: 交易时段（9:30-11:30, 13:00-15:00）
- **采集间隔**: 可配置，默认60秒
- **股票列表**: 配置文件指定，上限100支
- **单只耗时**: ~3秒
- **100支总耗时**: ~5分钟/轮

#### 3.4.3 盘口数据字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| stock_code | VARCHAR(20) | 股票代码 |
| snapshot_time | TIMESTAMP | 快照时间 |
| bid1-bid10_price | DECIMAL(10,4) | 买1-10价 |
| bid1-bid10_volume | BIGINT | 买1-10量 |
| ask1-ask10_price | DECIMAL(10,4) | 卖1-10价 |
| ask1-ask10_volume | BIGINT | 卖1-10量 |
| limit_up | DECIMAL(10,4) | 涨停价 |
| limit_down | DECIMAL(10,4) | 跌停价 |
| inner_vol | BIGINT | 内盘 |
| outer_vol | BIGINT | 外盘 |

**依据**: AkShare `stock_bid_ask_em` PoC 验证，实际返回10档数据

### 3.5 FR-005: ST/退市/港股特化标记

#### 3.5.1 需求描述

对 A 股进行特化标准标记，包括 ST、退市风险、同时有港股等分类。

#### 3.5.2 标记来源

| 标记类型 | 主来源 | 备用来源 | 说明 |
|----------|--------|----------|------|
| ST/*ST | Baostock `isST` 字段 | AkShare 股票名称匹配 | 双重验证 |
| 退市风险 | Baostock `outDate` 字段 | AkShare `stock_zh_a_stop_em` | outDate非空=已退市 |
| A+H股 | AkShare 港股接口交叉比对 | 手动配置 | 同时在A股和港股上市 |
| 退市整理期 | AkShare 名称含"退" | 交易所公告 | 最后交易阶段 |

#### 3.5.3 标记更新策略

- **ST标记**: 每日收盘后随日线数据更新
- **退市风险**: 每周检查一次
- **A+H股**: 每月更新一次港股关联

### 3.6 FR-006: 实盘指数监控

#### 3.6.1 需求描述

每分钟刷新上证指数和深证成指的实时行情数据。

#### 3.6.2 技术方案

- **数据源**: 东方财富 REST API（无需浏览器自动化）
- **上证指数**: `secid=1.000001`
- **深证成指**: `secid=0.399001`
- **刷新频率**: 每60秒（交易时段内）
- **响应时间**: ~96ms（PoC 已验证）

**依据**: 东方财富 API PoC 验证（[poc_eastmoney.py](file:///poc_eastmoney.py)），HTTP REST API 直连即可，无需 Selenium/Playwright

#### 3.6.3 采集字段

| 字段编码 | 含义 | 存储字段名 |
|----------|------|-----------|
| f43 | 最新价 | latest_price |
| f44 | 最高 | high_price |
| f45 | 最低 | low_price |
| f46 | 今开 | open_price |
| f47 | 成交量 | volume |
| f48 | 成交额 | amount |
| f57 | 代码 | index_code |
| f58 | 名称 | index_name |
| f60 | 昨收 | pre_close |
| f168 | 换手率 | turnover |
| f169 | 涨跌额 | change_amount |
| f170 | 涨跌幅(%) | change_pct |
| f171 | 振幅(%) | amplitude |

#### 3.6.4 东方财富子目录数据资源

| 子页面 | 对应API | 可获取数据 |
|--------|---------|-----------|
| 指数详情 | `push2.eastmoney.com/api/qt/stock/get` | 实时行情 |
| 分时图 | `push2his.eastmoney.com/api/qt/stock/trends2/get` | 分钟级分时 |
| K线图 | `push2his.eastmoney.com/api/qt/stock/kline/get` | 各周期K线 |
| 资金流向 | `push2.eastmoney.com/api/qt/stock/fflow/daykline/get` | 主力/散户资金 |
| 指数成分 | `push2.eastmoney.com/api/qt/clist/get` | 成分股列表 |

**依据**: 东方财富页面逆向分析 + PoC 验证

#### 3.6.5 降级策略

- 主: 东方财富 REST API
- 备: AkShare `stock_zh_index_spot_em`
- 连续失败3次: WARNING 日志
- 连续失败5次: ERROR 日志 + 邮件通知

### 3.7 FR-007: 数据完整性检查

#### 3.7.1 需求描述

系统启动时自动检查数据完整性，发现缺失数据时自动补全。

#### 3.7.2 检查策略

```
启动 → 加载交易日历 (Baostock query_trade_dates)
    → 对比每个交易日的预期数据量 vs 实际数据量
        → 缺失 → 触发补全任务
            ├── 分钟K线缺失: Baostock 5分钟回填
            ├── 日线缺失: Baostock/AkShare 回填
            └── 盘口数据缺失: 标记为不可补全（历史盘口无法回溯）
        → 完整 → 正常启动增量更新
```

#### 3.7.3 检查维度

| 维度 | 检查方式 | 补全能力 |
|------|----------|----------|
| 交易日缺失 | 对比交易日历 | 可补全（K线/日线） |
| 股票缺失 | 对比全量股票列表 | 可补全 |
| 时段缺失 | 对比预期条数 vs 实际条数 | 分钟K线可补全 |
| 数据异常 | 价格/成交量合理性检查 | 标记异常，人工确认 |

### 3.8 FR-008: 配置管理

#### 3.8.1 需求描述

所有运行参数通过 JSON 配置文件管理，支持环境变量覆盖敏感信息。

#### 3.8.2 配置文件结构

```json
{
    "data_sources": {
        "akshare": {
            "enabled": true,
            "rate_limit_per_second": 0.33,
            "batch_size": 50,
            "batch_interval_seconds": 1
        },
        "baostock": {
            "enabled": true,
            "rate_limit_per_second": 3.0,
            "max_queries_per_connection": 5000,
            "reconnect_interval_seconds": 300
        },
        "eastmoney": {
            "enabled": true,
            "rate_limit_per_minute": 8,
            "index_codes": ["1.000001", "0.399001"]
        }
    },
    "schedule": {
        "minute_kline_1m": {
            "enabled": true,
            "trading_hours_only": true,
            "interval_seconds": 60
        },
        "minute_kline_5m": {
            "enabled": true,
            "run_after_market_close": true,
            "market_close_offset_minutes": 30
        },
        "daily_kline": {
            "enabled": true,
            "run_after_market_close": true,
            "market_close_offset_minutes": 60
        },
        "bid_ask": {
            "enabled": true,
            "trading_hours_only": true,
            "interval_seconds": 60,
            "max_stocks": 100
        },
        "index_monitor": {
            "enabled": true,
            "trading_hours_only": true,
            "interval_seconds": 60
        },
        "stock_marks": {
            "enabled": true,
            "schedule": "daily",
            "run_after_market_close": true
        },
        "integrity_check": {
            "enabled": true,
            "on_startup": true,
            "schedule": "weekly"
        }
    },
    "database": {
        "host": "${DB_HOST}",
        "port": 5432,
        "database": "${DB_NAME}",
        "user": "${DB_USER}",
        "password": "${DB_PASSWORD}",
        "pool_size": 10,
        "max_overflow": 20
    },
    "bid_ask_stocks": {
        "stock_codes": [],
        "max_count": 100,
        "config_source": "file"
    },
    "notification": {
        "smtp_host": "${SMTP_HOST}",
        "smtp_port": 465,
        "smtp_user": "${SMTP_USER}",
        "smtp_password": "${SMTP_PASSWORD}",
        "recipients": [],
        "enabled": true
    },
    "logging": {
        "level": "INFO",
        "file_path": "logs/stock_spider.log",
        "max_file_size_mb": 100,
        "backup_count": 10
    },
    "history": {
        "daily_start_date": "2016-01-01",
        "minute_5m_start_date": "2020-01-02",
        "minute_1m_depth_days": 5
    }
}
```

#### 3.8.3 敏感信息管理

- 数据库密码、SMTP 密码等通过环境变量注入
- 配置文件中使用 `${ENV_VAR}` 占位符
- `.env` 文件仅在本地使用，禁止提交到代码仓库
- Baostock 无需账号，AkShare 无需账号，东方财富 API 无需账号

### 3.9 FR-009: 日志与告警

#### 3.9.1 日志分级

| 级别 | 触发场景 | 示例 |
|------|----------|------|
| DEBUG | 开发调试细节 | 请求参数、响应原始数据 |
| INFO | 关键步骤 | 采集启动、数据更新完成、配置加载 |
| WARNING | 可恢复错误 | 频率限制触发、账号切换、数据缺失 |
| ERROR | 功能受损 | 单次采集失败、网络超时、DB写入失败 |
| CRITICAL | 程序即将退出 | 数据源不可用、DB连接断开、进程异常 |

#### 3.9.2 日志格式

```
%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s
```

#### 3.9.3 邮件通知

- 触发条件: CRITICAL 级别日志
- 发送方式: 异步非阻塞（不阻塞主循环）
- 邮件内容: 错误详情、时间戳、系统状态
- 日志轮转: 单文件上限 100MB，保留 10 个备份

### 3.10 FR-010: 后台运行与部署

#### 3.10.1 需求描述

支持在 macOS 和 Ubuntu 上无界面后台运行，无人值守长期自动运行。

#### 3.10.2 macOS 部署

- 使用 launchd plist 配置
- 开机自启
- 异常退出自动重启（KeepAlive + RunAtLoad）
- 日志输出到统一日志文件

#### 3.10.3 Ubuntu 部署

- 使用 systemd service 配置
- 开机自启
- 异常退出自动重启（Restart=always）
- 支持 `systemctl start/stop/status`

#### 3.10.4 信号处理

- SIGTERM: 优雅退出（完成当前采集、保存进度、关闭连接）
- SIGHUP: 重新加载配置
- 进程异常退出后从断点位置继续采集

---

## 4. 数据结构设计

### 4.1 分钟K线表 (minute_klines)

```sql
CREATE TABLE minute_klines (
    id BIGSERIAL,
    stock_code VARCHAR(20) NOT NULL,
    trade_time TIMESTAMP NOT NULL,
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4),
    close DECIMAL(10,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    change_pct DECIMAL(6,3),
    amplitude DECIMAL(6,3),
    turnover DECIMAL(6,3),
    frequency VARCHAR(5) NOT NULL,
    data_source VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, trade_time)
) PARTITION BY RANGE (trade_time);

-- 按月分区示例
CREATE TABLE minute_klines_2020_01 PARTITION OF minute_klines
    FOR VALUES FROM ('2020-01-01') TO ('2020-02-01');

-- 索引
CREATE INDEX idx_minute_stock_time ON minute_klines(stock_code, trade_time DESC);
CREATE INDEX idx_minute_frequency ON minute_klines(frequency, trade_time DESC);
```

**数据量估算**:
- 5分钟K线: 5400只 × 6年 × 250天 × 48条 ≈ 38.88亿条
- 1分钟K线: 5400只 × 5天 × 240条 ≈ 648万条（滚动窗口）
- 单条大小: ~100字节
- 5分钟K线总存储: ~388GB（需分区+压缩策略）

### 4.2 日K线表 (daily_klines)

```sql
CREATE TABLE daily_klines (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4),
    close DECIMAL(10,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    pre_close DECIMAL(10,4),
    change_pct DECIMAL(6,3),
    turnover DECIMAL(6,3),
    is_st BOOLEAN DEFAULT FALSE,
    pe_ttm DECIMAL(10,2),
    pb_mrq DECIMAL(10,2),
    data_source VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, trade_date)
);

CREATE INDEX idx_daily_stock_date ON daily_klines(stock_code, trade_date DESC);
CREATE INDEX idx_daily_is_st ON daily_klines(is_st) WHERE is_st = TRUE;
```

**数据量估算**: 5400只 × 10年 × 250天 ≈ 1350万条

### 4.3 五档盘口快照表 (bid_ask_snapshots)

```sql
CREATE TABLE bid_ask_snapshots (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    bid1_price DECIMAL(10,4), bid1_volume BIGINT,
    bid2_price DECIMAL(10,4), bid2_volume BIGINT,
    bid3_price DECIMAL(10,4), bid3_volume BIGINT,
    bid4_price DECIMAL(10,4), bid4_volume BIGINT,
    bid5_price DECIMAL(10,4), bid5_volume BIGINT,
    bid6_price DECIMAL(10,4), bid6_volume BIGINT,
    bid7_price DECIMAL(10,4), bid7_volume BIGINT,
    bid8_price DECIMAL(10,4), bid8_volume BIGINT,
    bid9_price DECIMAL(10,4), bid9_volume BIGINT,
    bid10_price DECIMAL(10,4), bid10_volume BIGINT,
    ask1_price DECIMAL(10,4), ask1_volume BIGINT,
    ask2_price DECIMAL(10,4), ask2_volume BIGINT,
    ask3_price DECIMAL(10,4), ask3_volume BIGINT,
    ask4_price DECIMAL(10,4), ask4_volume BIGINT,
    ask5_price DECIMAL(10,4), ask5_volume BIGINT,
    ask6_price DECIMAL(10,4), ask6_volume BIGINT,
    ask7_price DECIMAL(10,4), ask7_volume BIGINT,
    ask8_price DECIMAL(10,4), ask8_volume BIGINT,
    ask9_price DECIMAL(10,4), ask9_volume BIGINT,
    ask10_price DECIMAL(10,4), ask10_volume BIGINT,
    limit_up DECIMAL(10,4),
    limit_down DECIMAL(10,4),
    inner_vol BIGINT,
    outer_vol BIGINT,
    data_source VARCHAR(20) DEFAULT 'akshare',
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (snapshot_time);

CREATE INDEX idx_bidask_stock_time ON bid_ask_snapshots(stock_code, snapshot_time DESC);
```

**数据量估算**: 100只 × 240条/天 × 250天 ≈ 600万条/年

### 4.4 股票特化标记表 (stock_marks)

```sql
CREATE TABLE stock_marks (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),
    is_st BOOLEAN DEFAULT FALSE,
    st_type VARCHAR(10),
    delist_risk BOOLEAN DEFAULT FALSE,
    delist_date DATE,
    has_hk BOOLEAN DEFAULT FALSE,
    hk_code VARCHAR(20),
    mark_date DATE NOT NULL,
    data_source VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, mark_date)
);

CREATE INDEX idx_marks_st ON stock_marks(is_st) WHERE is_st = TRUE;
CREATE INDEX idx_marks_delist ON stock_marks(delist_risk) WHERE delist_risk = TRUE;
CREATE INDEX idx_marks_hk ON stock_marks(has_hk) WHERE has_hk = TRUE;
```

### 4.5 指数行情表 (index_quotes)

```sql
CREATE TABLE index_quotes (
    id BIGSERIAL PRIMARY KEY,
    index_code VARCHAR(20) NOT NULL,
    index_name VARCHAR(50),
    quote_time TIMESTAMP NOT NULL,
    latest_price DECIMAL(10,4),
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    pre_close DECIMAL(10,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    change_amount DECIMAL(10,4),
    change_pct DECIMAL(6,3),
    amplitude DECIMAL(6,3),
    turnover DECIMAL(6,3),
    data_source VARCHAR(20) DEFAULT 'eastmoney',
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (quote_time);

CREATE INDEX idx_index_code_time ON index_quotes(index_code, quote_time DESC);
```

**数据量估算**: 2只 × 240条/天 × 250天 ≈ 12万条/年

### 4.6 采集进度表 (crawl_progress)

```sql
CREATE TABLE crawl_progress (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    frequency VARCHAR(5) NOT NULL,
    last_trade_time TIMESTAMP,
    last_trade_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    records_fetched BIGINT DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, frequency)
);

CREATE INDEX idx_progress_status ON crawl_progress(status) WHERE status != 'completed';
```

### 4.7 交易日历表 (trade_calendar)

```sql
CREATE TABLE trade_calendar (
    trade_date DATE PRIMARY KEY,
    is_trading_day BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. 非功能需求

### 5.1 性能要求

| 指标 | 目标值 | 依据 |
|------|-------|------|
| 1分钟K线采集延迟 | < 60秒（从数据源到入库） | AkShare延迟3-15秒 + 处理时间 |
| 5分钟K线批量拉取 | ≤ 5400只/天（盘后20:00-次日8:00） | 0.3秒/次 × 5400 ≈ 27分钟 |
| 指数监控响应 | < 5秒（端到端） | 东方财富API ~96ms |
| 五档盘口采集 | 100只/5分钟 | 3秒/只 |
| 数据库批量写入 | ≥ 10000条/秒 | psycopg2 execute_values |
| 日线全量回溯 | ≤ 3天完成（2016年至今） | 5400只 × 10年，分批拉取 |

### 5.2 可靠性要求

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 系统可用性 | 99.9%（交易时段） | 年度可用时间 |
| 数据完整性 | 99.99% | 不丢失已确认数据 |
| 故障恢复时间 | < 5分钟 | 自动重启 + 断点续传 |
| 断点续传 | 100%覆盖 | 所有采集任务支持断点续传 |
| 数据备份 | 每日全量 | PostgreSQL pg_dump |

### 5.3 安全性要求

- 数据库密码、SMTP密码通过环境变量注入，禁止硬编码
- `.env` 文件加入 `.gitignore`
- 配置文件中敏感字段使用 `${ENV_VAR}` 占位符
- 日志中禁止输出密码、Token 等敏感信息

### 5.4 可维护性要求

- 代码覆盖率: 核心业务逻辑 ≥ 95%，整体 ≥ 80%
- 日志规范: 结构化日志，5级分级
- 配置驱动: 所有参数可配置，无需改代码
- 模块化: 数据源适配器可独立替换

### 5.5 兼容性要求

| 平台 | 版本 | 说明 |
|------|------|------|
| macOS | 12+ (Monterey) | launchd 后台运行 |
| Ubuntu | 20.04+ | systemd 后台运行 |
| Python | 3.11+ | Conda `agent` 环境 |
| PostgreSQL | 15+ | 分区表支持 |

---

## 6. 验收标准

### 6.1 FR-001 双数据源适配器

- **Given** 系统配置了 AkShare 和 Baostock 两个数据源
- **When** 调用数据适配器获取5分钟K线
- **Then** 优先使用 Baostock 获取，返回正确的 DataFrame

- **Given** Baostock 连接失败
- **When** 调用数据适配器获取5分钟K线
- **Then** 自动切换到 AkShare，记录降级日志

### 6.2 FR-002 分钟级K线采集

- **Given** 数据库中无历史数据
- **When** 首次启动系统
- **Then** 从2020-01-02开始回溯5分钟K线，从最近5个交易日回溯1分钟K线

- **Given** 数据库中已有历史数据
- **When** 启动增量更新
- **Then** 仅采集最新缺失时段的数据

- **Given** 采集过程中进程异常退出
- **When** 系统自动重启
- **Then** 从上次断点位置继续采集

### 6.3 FR-003 日K线采集

- **Given** 数据库中无日线数据
- **When** 首次启动
- **Then** 从2016-01-01开始回溯日K线

- **Given** 日线数据中包含ST股票
- **When** 采集日线时
- **Then** isST字段正确标记

### 6.4 FR-004 五档盘口采集

- **Given** 配置了100支监控股票
- **When** 交易时段触发采集
- **Then** 在5分钟内完成100支股票的盘口数据采集

- **Given** 非交易时段
- **When** 盘口采集任务触发
- **Then** 跳过采集，等待下一交易日

### 6.5 FR-005 特化标记

- **Given** 某股票被标记为ST
- **When** 日线数据更新
- **Then** stock_marks 表中 is_st=True，st_type 正确

- **Given** 某股票同时在A股和港股上市
- **When** 港股数据更新
- **Then** stock_marks 表中 has_hk=True，hk_code 正确

### 6.6 FR-006 指数监控

- **Given** 交易时段（9:30-15:00）
- **When** 每分钟触发指数采集
- **Then** 上证指数和深证成指数据正确入库，延迟<5秒

- **Given** 东方财富API连续失败3次
- **When** 降级到AkShare
- **Then** 记录WARNING日志，数据仍正常入库

### 6.7 FR-007 数据完整性检查

- **Given** 数据库中缺少某交易日的分钟K线数据
- **When** 系统启动执行完整性检查
- **Then** 自动触发补全任务，补全缺失数据

### 6.8 FR-008 配置管理

- **Given** 配置文件中数据库密码使用 `${DB_PASSWORD}` 占位符
- **When** 系统启动加载配置
- **Then** 从环境变量读取实际密码，日志中不输出密码明文

### 6.9 FR-009 日志与告警

- **Given** 产生 CRITICAL 级别日志
- **When** 数据库连接断开
- **Then** 立即发送邮件通知，包含错误详情和时间戳

### 6.10 FR-010 后台运行

- **Given** 进程异常退出
- **When** launchd/systemd 检测到退出
- **Then** 自动重启进程，从断点位置继续采集

---

## 7. 环境与部署

### 7.1 开发环境

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | Conda `agent` 环境 |
| PostgreSQL | 15+ | 主数据存储 |
| Conda | 最新版 | 环境管理 |

### 7.2 核心依赖

| 包名 | 用途 | 说明 |
|------|------|------|
| akshare | AkShare数据源 | 实时行情+盘口+港股 |
| baostock | Baostock数据源 | 历史K线+ST标记 |
| sqlalchemy | ORM | 数据库操作 |
| psycopg2-binary | PostgreSQL驱动 | 批量写入 |
| alembic | 数据库迁移 | 版本管理 |
| loguru | 日志 | 5级日志+轮转 |
| pydantic | 配置验证 | 数据模型 |
| apscheduler | 任务调度 | 定时任务 |
| requests | HTTP请求 | 东方财富API |

### 7.3 运行环境

| 平台 | 后台方案 | 自启 | 异常重启 |
|------|---------|------|----------|
| macOS | launchd plist | RunAtLoad=true | KeepAlive=true |
| Ubuntu | systemd service | WantedBy=multi-user.target | Restart=always |

### 7.4 数据库环境

- PostgreSQL 15+ 实例
- 独立 schema: `stock_spider`
- 连接池: 最小5，最大10+20溢出
- 时区: Asia/Shanghai

---

## 8. 辅助文件

### 8.1 配置文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 主配置 | `config/config.json` | 运行参数 |
| 环境变量 | `config/.env` | 敏感信息（不入库） |
| 环境变量模板 | `config/.env.example` | 敏感信息模板 |

### 8.2 部署脚本

| 文件 | 路径 | 说明 |
|------|------|------|
| 启动脚本 | `scripts/start.sh` | Linux/Mac 启动 |
| macOS plist | `scripts/com.stock.spider.plist` | launchd 配置 |
| Ubuntu service | `scripts/stock-spider.service` | systemd 配置 |

### 8.3 数据库迁移

| 文件 | 路径 | 说明 |
|------|------|------|
| Alembic配置 | `alembic.ini` | 迁移配置 |
| 迁移脚本 | `alembic/versions/` | 版本化迁移 |

### 8.4 PoC 验证脚本

| 文件 | 路径 | 说明 |
|------|------|------|
| AkShare PoC | `poc_akshare_api.py` | AkShare 接口验证 |
| Baostock PoC | `poc_baostock.py` | Baostock 接口验证 |
| 东方财富 PoC | `poc_eastmoney.py` | 东方财富 API 验证 |

---

## 9. 待验证任务清单

以下任务需在开发前完成验证，确认技术可行性：

### VT-001: AkShare 1分钟K线实时采集验证
- **目标**: 验证交易时段 `stock_zh_a_hist_min_em(period=1)` 的数据延迟和完整性
- **验证项**: 数据延迟、字段完整性、频率限制实测
- **优先级**: 高
- **前置条件**: 交易时段
- **验证方法**: 连续10分钟采集单只股票1分钟K线，记录延迟和成功率

### VT-002: Baostock 5分钟K线历史批量拉取验证
- **目标**: 验证从2020-01-02开始批量拉取5分钟K线的可行性
- **验证项**: 单次返回量、断点续传、连接稳定性、全量拉取时间估算
- **优先级**: 高
- **前置条件**: 无
- **验证方法**: 拉取10只股票2020年全年5分钟K线，计算平均耗时

### VT-003: 东方财富API指数实时数据验证
- **目标**: 验证交易时段 `push2.eastmoney.com` API 的稳定性
- **验证项**: 响应时间、数据完整性、连续运行1小时稳定性
- **优先级**: 高
- **前置条件**: 交易时段
- **验证方法**: 连续1小时每60秒采集上证/深证指数

### VT-004: AkShare五档盘口批量采集验证
- **目标**: 验证 `stock_bid_ask_em()` 对100支股票的批量采集可行性
- **验证项**: 单只耗时、总耗时、频率限制、数据完整性
- **优先级**: 高
- **前置条件**: 交易时段
- **验证方法**: 连续采集100支股票盘口数据3轮，记录耗时和成功率

### VT-005: AkShare港股数据采集验证
- **目标**: 验证港股数据接口的可用性和数据质量
- **验证项**: A+H股关联、数据延迟、字段完整性
- **优先级**: 中
- **前置条件**: 无
- **验证方法**: 获取港股全量数据，与A股列表交叉比对

### VT-006: PostgreSQL分区表性能验证
- **目标**: 验证按月分区表在分钟级数据下的写入和查询性能
- **验证项**: 批量写入吞吐（目标≥10000条/秒）、查询响应时间、分区管理
- **优先级**: 中
- **前置条件**: PostgreSQL实例
- **验证方法**: 写入100万条模拟分钟K线数据，测试查询性能

### VT-007: 全量5分钟K线拉取时间估算
- **目标**: 估算5400+只股票从2020年至今的5分钟K线完整拉取所需时间
- **验证项**: 单只股票全年拉取耗时、限流等待时间、总时间估算
- **优先级**: 高
- **前置条件**: VT-002 完成
- **验证方法**: 基于 VT-002 的单只耗时，推算全量时间

### VT-008: 数据完整性检查策略验证
- **目标**: 验证启动时数据完整性检查的可行性方案
- **验证项**: 缺失数据识别效率、补全策略、与交易日历对齐
- **优先级**: 中
- **前置条件**: VT-002 + PostgreSQL实例
- **验证方法**: 模拟缺失数据场景，测试检测和补全流程

---

## 10. 附录

### 10.1 数据源 API 边界汇总

| 数据源 | 频率限制 | 连接方式 | 账号需求 | 数据延迟 |
|--------|---------|---------|---------|---------|
| AkShare | ~17次/分钟/IP | HTTP短连接 | 无 | 3-15秒 |
| Baostock | ~20次/秒 | TCP长连接 | 无（匿名登录） | 分钟线20:00后 |
| 东方财富 | ~5-10次/分钟 | HTTP短连接 | 无 | ~100ms |

### 10.2 关键技术决策记录

| 决策 | 选择 | 原因 | 依据 |
|------|------|------|------|
| 分钟级策略 | 1分钟+5分钟混合 | AkShare 1分钟仅5天，Baostock仅5分钟 | PoC验证 |
| 历史回溯起点 | 分钟数据2020-01-02 | Baostock实测最早2020年 | PoC验证 |
| 指数监控方案 | 东方财富REST API | 响应快(~96ms)、无需浏览器 | PoC验证 |
| 盘口采集范围 | 指定100支 | 全量5400+只需4.5小时/轮 | AkShare限制 |
| 浏览器自动化 | 不使用 | 东方财富有REST API | PoC验证 |
| 日线回溯起点 | 2016-01-01 | 用户需求 | 原始需求文档 |

### 10.3 风险清单

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 东方财富API变更/关闭 | 指数监控失效 | 中 | 降级到AkShare |
| AkShare接口变动 | 实时数据中断 | 中 | 锁定版本+降级策略 |
| Baostock服务不稳定 | 历史数据拉取延迟 | 低 | 断点续传+重试 |
| 5分钟K线全量拉取耗时过长 | 首次部署周期长 | 高 | 分批拉取+进度展示 |
| PostgreSQL存储空间不足 | 数据写入失败 | 中 | 监控磁盘+分区管理 |
| 反爬机制升级 | 数据采集受限 | 低 | 降级+代理池 |

---

**文档结束**
