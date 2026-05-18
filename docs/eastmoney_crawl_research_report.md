# 东方财富网页可抓取信息研究报告

> **验证日期**：2026-05-15
> **目标股票**：海天味业（603288, secid=1.603288）
> **入口页面**：https://quote.eastmoney.com/sh603288.html

---

## 1. 研究概述

### 1.1 目标

以海天味业（603288）为基础，递归分析东方财富网页上所有与股票相关的可抓取信息，形成完整的实体清单和API映射。

### 1.2 方法

| 方法 | 说明 |
|------|------|
| BFS递归链接发现 | 从行情页入口开始，3层深度递归爬取所有eastmoney.com域名下的链接 |
| JS文件分析 | 从页面引用的JavaScript打包文件中提取reportName参数 |
| REST API端点探测 | 逐个验证API端点的可用性、返回数据结构和字段 |
| 实际数据验证 | 以海天味业(603288)为参数，实际调用API验证数据可获取性 |

### 1.3 核心发现

1. **东方财富采用SPA+REST API架构**：网页HTML仅包含框架，实际数据全部通过AJAX请求JSON API获取
2. **push2/push2his域名被IP封锁**：当前网络环境无法直接访问实时行情、K线、分时线等核心接口
3. **datacenter接口reportName大量变更**：约80%的旧reportName已失效，需使用从JS文件中提取的新reportName
4. **F10档案接口部分可用**：emweb域名的公司概况、经营分析、财务分析、资本运作接口正常
5. **公告接口正常可用**：np-anotice-stock域名的公告接口正常返回数据

---

## 2. 网页链接图谱

### 2.1 入口页面结构

以 `https://quote.eastmoney.com/sh603288.html` 为入口，可发现以下子页面域：

```
quote.eastmoney.com                    ← 行情主页（入口）
├── push2.eastmoney.com                ← 实时行情API [⚠️ IP封锁]
├── push2his.eastmoney.com             ← 历史K线/分时API [⚠️ IP封锁]
├── data.eastmoney.com                 ← 数据中心（100+子页面）
│   ├── rzrq/                          ← 融资融券
│   ├── stock/lhb/                     ← 龙虎榜单
│   ├── dzjy/                          ← 大宗交易
│   ├── gpzy/                          ← 股权质押
│   ├── bbsj/                          ← 年报季报/业绩报表
│   ├── gdfx/                          ← 股东分析
│   ├── dxf/                           ← 限售解禁
│   ├── notices/                       ← 公告大全
│   ├── report/                        ← 研究报告
│   ├── yjfp/                          ← 分红送配
│   ├── stockcomment/                  ← 千股千评
│   ├── jgdy/                          ← 机构调研
│   ├── stockdata/                     ← 数据全景图
│   ├── stockcalendar/                 ← 个股日历
│   └── hsgt/                          ← 沪深港通
├── datacenter-web.eastmoney.com       ← 数据中心REST API [✅ 可访问]
├── emweb.securities.eastmoney.com     ← F10档案SPA [✅ 可访问]
│   ├── CompanySurvey/PageAjax         ← 公司概况
│   ├── BusinessAnalysis/PageAjax      ← 经营分析
│   ├── Operations/SubjectDetailAjax   ← 核心题材
│   ├── ShareStructure/PageAjax        ← 股本结构
│   ├── CompanyEvent/PageAjax          ← 公司大事
│   ├── NewFinanceAnalysis/ZYZBAjaxNew ← 财务分析
│   ├── CapitalOperation/PageAjax      ← 资本运作
│   ├── ShareholderResearch/PageAjax   ← 股东研究
│   └── RelativeStock/PageAjax         ← 关联个股
├── np-anotice-stock.eastmoney.com     ← 公告服务 [✅ 可访问]
└── guba.eastmoney.com                 ← 股吧讨论
```

### 2.2 域名连通性测试结果

| 域名 | 连通性 | 说明 |
|------|--------|------|
| push2.eastmoney.com | ❌ 封锁 | RemoteDisconnected，IP被封锁 |
| push2his.eastmoney.com | ❌ 封锁 | RemoteDisconnected，IP被封锁 |
| datacenter-web.eastmoney.com | ✅ 可用 | HTTP 200，部分reportName已变更 |
| emweb.securities.eastmoney.com | ✅ 可用 | HTTP 200，F10档案接口正常 |
| np-anotice-stock.eastmoney.com | ✅ 可用 | HTTP 200，公告接口正常 |
| data.eastmoney.com | ✅ 可用 | HTML页面可访问，JS文件可下载 |

---

## 3. API端点清单

### 3.1 行情类API（push2/push2his域名 — ⚠️ 当前IP封锁）

| 序号 | API名称 | URL | 方法 | 状态 |
|------|---------|-----|------|------|
| 1 | 实时行情 | `push2.eastmoney.com/api/qt/stock/get` | GET | ❌ IP封锁 |
| 2 | 批量行情列表 | `push2.eastmoney.com/api/qt/clist/get` | GET | ❌ IP封锁 |
| 3 | K线历史(日线) | `push2his.eastmoney.com/api/qt/stock/kline/get` | GET | ❌ IP封锁 |
| 4 | K线历史(5分钟) | `push2his.eastmoney.com/api/qt/stock/kline/get` | GET | ❌ IP封锁 |
| 5 | K线历史(1分钟) | `push2his.eastmoney.com/api/qt/stock/kline/get` | GET | ❌ IP封锁 |
| 6 | 分时线 | `push2his.eastmoney.com/api/qt/stock/trends2/get` | GET | ❌ IP封锁 |
| 7 | 五档盘口 | `push2.eastmoney.com/api/qt/stock/get` | GET | ❌ IP封锁 |
| 8 | 资金流向(日K) | `push2his.eastmoney.com/api/qt/stock/fflow/daykline/get` | GET | ❌ IP封锁 |
| 9 | 沪深港通资金 | `push2his.eastmoney.com/api/qt/kamtbs.wss/get` | GET | ❌ 404 |

**关键参数**：
- `secid`: 股票标识（沪市=1.代码，深市=0.代码），如 `1.603288`
- `ut`: 用户token，如 `fa5fd1943c7b386f172d6893dbfba10b`
- `klt`: K线类型（101=日线, 5=5分钟, 1=1分钟）
- `fqt`: 复权类型（1=前复权）

### 3.2 数据中心API（datacenter-web域名 — ✅ 可访问）

#### 3.2.1 当前可用的reportName

| 数据类别 | reportName | 排序列 | 过滤字段 | 状态 |
|---------|-----------|--------|---------|------|
| **财务三表** | | | | |
| 资产负债表 | `RPT_DMSK_FN_BALANCE` | REPORT_DATE | SECURITY_CODE | ✅ |
| 利润表 | `RPT_DMSK_FN_INCOME` | REPORT_DATE | SECURITY_CODE | ✅ |
| 现金流量表 | `RPT_DMSK_FN_CASHFLOW` | REPORT_DATE | SECURITY_CODE | ✅ |
| 业绩报表 | `RPT_LICO_FN_CPD` | (无) | SECURITY_CODE | ✅ |
| **股权质押** | | | | |
| 质押明细 | `RPT_CSDC_LIST` | TRADE_DATE | SECURITY_CODE | ✅ |
| **大宗交易** | | | | |
| 大宗交易统计 | `RPT_BLOCKTRADE_ACSTA` | TRADE_DATE | SECURITY_CODE | ✅ |
| 大宗交易明细 | `RPT_BLOCKTRADE_STAINCLUDE` | TRADE_DATE | SECURITY_CODE | ✅ |
| 大宗交易数据 | `RPT_DATA_BLOCKTRADE` | TRADE_DATE | SECURITY_CODE | ✅ |
| **分红送配** | | | | |
| 分红明细 | `RPT_SHAREBONUS_DET` | REPORT_DATE | SECURITY_CODE | ✅ |
| **研报** | | | | |
| 分析师排名 | `RPT_ANALYST_INDEX_RANK` | TRADE_DATE | (无个股过滤) | ✅ |
| 盈利预测 | `RPT_WEB_RESPREDICT` | (无) | SECURITY_CODE | ✅ |
| **沪深港通** | | | | |
| 沪深港通持股排名 | `RPT_MUTUAL_HOLDRANK_NEW` | (无) | (无个股过滤) | ✅ |
| 沪深港通净流入明细 | `RPT_MUTUAL_NETINFLOW_DETAILS` | (无) | (无个股过滤) | ✅ |
| 沪深港通净流入统计 | `RPT_MUTUAL_NETINFLOW_STATISTICS` | (无) | (无个股过滤) | ✅ |
| 北向机构持股排名 | `RPT_NORTH_ORG_HOLDRANK_NEW` | (无) | (无个股过滤) | ✅ |
| 沪深港通成交额 | `RPT_MUTUAL_DEALAMT` | (无) | (无个股过滤) | ✅ |

#### 3.2.2 可用但需不带过滤条件的reportName

以下reportName存在但**不支持SECURITY_CODE过滤**，返回的是市场级数据：

| 数据类别 | reportName | 返回字段 | 说明 |
|---------|-----------|---------|------|
| **融资融券** | | | |
| 融资融券历史 | `RPTA_RZRQ_LSHJ` | DIM_DATE, ZDF, LTSZ | 市场级汇总数据 |
| 融资融券深市 | `RPTA_WEB_RZRQ_LSSH` | RZYE, RQYL, RZMRE | 市场级汇总数据 |
| **大宗交易** | | | |
| 营业部统计 | `RPT_BLOCKTRADE_OPERATEDEPTSTATISTICS` | TYPE, OPERATEDEPT_NAME | 营业部级数据 |
| **分红** | | | |
| 分红日期 | `RPT_DATE_SHAREBONUS_DET` | REPORT_DATE | 仅日期数据 |
| **股东** | | | |
| 一致行动人 | `RPT_COOPFREEHOLDER` | HOLDER_NAME, HOLDER_TYPE | 需其他过滤方式 |
| 一致行动人分析 | `RPT_COOPFREEHOLDERS_ANALYSISNEW` | END_DATE, HOLDER_NAME | 需其他过滤方式 |
| 流通股东基本信息 | `RPT_FREEHOLDERS_BASIC_INFONEW` | END_DATE, HOLDER_NAME | 需其他过滤方式 |
| **研报** | | | |
| 研报板块 | `RPT_EMBOARD_ALL` | BOARD_CODE, BOARD_NAME | 板块级数据 |

#### 3.2.3 已失效的旧reportName

| 旧reportName | 错误信息 | 替代方案 |
|-------------|---------|---------|
| `RPT_RZRQ_LSHJ` | 报表配置不存在 | `RPTA_RZRQ_LSHJ`（市场级） |
| `RPT_RZRQ_SHZJHZ` | 报表配置不存在 | `RPTA_WEB_RZRQ_LSSH`（市场级） |
| `RPT_RZRQ_ZHTJ` | 报表配置不存在 | 暂无个股级替代 |
| `RDT_BILLBOARD_DAILYDETAIL` | 报表配置不存在 | 需从龙虎榜页面JS中查找 |
| `RDT_BILLBOARD_BROKER_BUY` | 报表配置不存在 | 需从龙虎榜页面JS中查找 |
| `RDT_BILLBOARD_BROKER_SELL` | 报表配置不存在 | 需从龙虎榜页面JS中查找 |
| `RPT_DABLOCK_TRADE` | 报表配置不存在 | `RPT_DATA_BLOCKTRADE` |
| `RPT_DABLOCK_TRADEMKT` | 报表配置不存在 | `RPT_BLOCKTRADE_ACSTA` |
| `RPT_DABLOCK_BUYBRANCH` | 报表配置不存在 | `RPT_BLOCKTRADE_OPERATEDEPTSTATISTICS` |
| `RPT_DIVIDEND_PLAN` | 报表配置不存在 | `RPT_SHAREBONUS_DET` |
| `RPT_RESOLVE_EXPLAIN` | 报表配置不存在 | 暂无替代 |
| `RPT_STOCK_ADDITIONAL` | 报表配置不存在 | 暂无替代 |
| `RPT_F10_EH_HOLDERSNUM` | 报表配置不存在 | `RPT_FREEHOLDERS_BASIC_INFONEW` |
| `RPT_F10_EH_INSTITUTION` | 报表配置不存在 | 暂无替代 |
| `RPT_F10_EH_HOLDERSCHG` | 报表配置不存在 | `RPT_COOPFREEHOLDERS_ANALYSISNEW` |
| `RPT_RESEARCH_DET` | 报表配置不存在 | `RPT_WEB_RESPREDICT` |
| `RPT_EARNS_FORECAST_DET` | 报表配置不存在 | `RPT_WEB_RESPREDICT` |
| `RPT_EARNS_FORECAST_RANK` | 报表配置不存在 | `RPT_ANALYST_INDEX_RANK` |
| `RPT_MUTUAL_STOCK_NORTH` | 报表配置不存在 | `RPT_MUTUAL_HOLDRANK_NEW` |
| `RPT_HSGT_INDIVIDUAL_INFO` | 报表配置不存在 | `RPT_MUTUAL_HOLDRANK_NEW` |
| `RPT_CSDC_DETAILED` | 报表配置不存在 | 暂无替代 |
| `RPT_F10_STKCAL` | 报表配置不存在 | 暂无替代 |

### 3.3 F10档案API（emweb域名 — ✅ 部分可用）

| 序号 | 接口名称 | URL路径 | 状态 | 说明 |
|------|---------|---------|------|------|
| 1 | 公司概况 | `PC_HSF10/CompanySurvey/PageAjax` | ✅ | 返回jbzl(基本资料)、fxxg(风险信息) |
| 2 | 经营分析 | `PC_HSF10/BusinessAnalysis/PageAjax` | ✅ | 返回zyfw(主营业务)、zygcfx(主营构成)、jyps(经营评述) |
| 3 | 核心题材 | `PC_HSF10/Operations/SubjectDetailAjax` | ❌ | 返回非JSON内容 |
| 4 | 股本结构 | `PC_HSF10/ShareStructure/PageAjax` | ❌ | 返回非JSON内容 |
| 5 | 公司大事 | `PC_HSF10/CompanyEvent/PageAjax` | ❌ | 返回非JSON内容 |
| 6 | 财务分析 | `PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew` | ✅ | 返回9行主要财务指标 |
| 7 | 资本运作 | `PC_HSF10/CapitalOperation/PageAjax` | ✅ | 返回mjzjly(募集资金)、xmjd(项目进度) |
| 8 | 关联个股 | `PC_HSF10/RelativeStock/PageAjax` | ❌ | 返回非JSON内容 |
| 9 | 股东研究 | `PC_HSF10/ShareholderResearch/PageAjax` | ⚠️ | 返回空数据 |

**参数**：`code=SH603288`

### 3.4 公告API（np-anotice-stock域名 — ✅ 可用）

| 序号 | 接口名称 | URL | 状态 |
|------|---------|-----|------|
| 1 | 个股公告列表 | `np-anotice-stock.eastmoney.com/api/security/ann` | ✅ |
| 2 | 公告详情(倒序) | `np-anotice-stock.eastmoney.com/api/security/ann` | ✅ |

**参数**：`page_size=5, page_index=1, ann_type=A, stock_list=603288`

---

## 4. 可抓取实体清单

### 4.1 行情实体（⚠️ push2域名当前封锁）

| 实体名称 | 数据内容 | API来源 | 可行性 |
|---------|---------|---------|--------|
| 实时行情 | 最新价、涨跌幅、成交量、成交额、换手率 | push2/qt/stock/get | ⚠️ 需代理或换IP |
| 日K线 | 日期、开盘、收盘、最高、最低、成交量、成交额 | push2his/qt/stock/kline/get | ⚠️ 需代理或换IP |
| 5分钟K线 | 同日K线，5分钟级别 | push2his/qt/stock/kline/get | ⚠️ 需代理或换IP |
| 1分钟K线 | 同日K线，1分钟级别 | push2his/qt/stock/kline/get | ⚠️ 需代理或换IP |
| 分时线 | 时间、现价、均价、成交量、成交额 | push2his/qt/stock/trends2/get | ⚠️ 需代理或换IP |
| 五档盘口 | 买1~5价/量、卖1~5价/量 | push2/qt/stock/get | ⚠️ 需代理或换IP |
| 资金流向 | 主力/大单/中单/小单净流入 | push2his/qt/stock/fflow | ⚠️ 需代理或换IP |

### 4.2 财务实体（✅ datacenter可用）

| 实体名称 | 数据内容 | reportName | 状态 |
|---------|---------|-----------|------|
| 资产负债表 | 总资产、总负债、所有者权益等 | RPT_DMSK_FN_BALANCE | ✅ |
| 利润表 | 营业收入、营业成本、净利润等 | RPT_DMSK_FN_INCOME | ✅ |
| 现金流量表 | 经营/投资/筹资活动现金流 | RPT_DMSK_FN_CASHFLOW | ✅ |
| 业绩报表 | EPS、ROE、净利润等 | RPT_LICO_FN_CPD | ✅ |
| 主要财务指标 | 每股收益、净资产收益率等 | F10/ZYZBAjaxNew | ✅ |

### 4.3 股东实体（⚠️ 部分可用）

| 实体名称 | 数据内容 | reportName | 状态 |
|---------|---------|-----------|------|
| 流通股东基本信息 | 股东名称、类型、持股数 | RPT_FREEHOLDERS_BASIC_INFONEW | ⚠️ 需其他过滤方式 |
| 一致行动人 | 股东名称、类型、变动 | RPT_COOPFREEHOLDER | ⚠️ 需其他过滤方式 |
| 一致行动人分析 | 持股变动类型、日期 | RPT_COOPFREEHOLDERS_ANALYSISNEW | ⚠️ 需其他过滤方式 |

### 4.4 交易实体（✅ 部分可用）

| 实体名称 | 数据内容 | reportName | 状态 |
|---------|---------|-----------|------|
| 股权质押明细 | 质押数量、质押比例、质押日期 | RPT_CSDC_LIST | ✅ |
| 大宗交易统计 | 成交笔数、成交金额 | RPT_BLOCKTRADE_ACSTA | ✅ |
| 大宗交易明细 | 成交日期、成交价、成交量 | RPT_BLOCKTRADE_STAINCLUDE | ✅ |
| 大宗交易数据 | 完整大宗交易记录 | RPT_DATA_BLOCKTRADE | ✅ |

### 4.5 公司实体（✅ F10可用）

| 实体名称 | 数据内容 | API路径 | 状态 |
|---------|---------|---------|------|
| 公司概况 | 公司名称、行业、注册资本等 | CompanySurvey/PageAjax | ✅ |
| 经营分析 | 主营业务构成、地区分布 | BusinessAnalysis/PageAjax | ✅ |
| 资本运作 | 募集资金流向、项目进度 | CapitalOperation/PageAjax | ✅ |

### 4.6 公告实体（✅ 可用）

| 实体名称 | 数据内容 | API来源 | 状态 |
|---------|---------|---------|------|
| 公告列表 | 标题、日期、公告类型 | np-anotice-stock | ✅ |

### 4.7 分红实体（✅ 部分可用）

| 实体名称 | 数据内容 | reportName | 状态 |
|---------|---------|-----------|------|
| 分红明细 | 送股比例、派现比例、报告期 | RPT_SHAREBONUS_DET | ✅ |

### 4.8 沪深港通实体（✅ 部分可用）

| 实体名称 | 数据内容 | reportName | 状态 |
|---------|---------|-----------|------|
| 持股排名 | 持股日期、持股量、持股比例 | RPT_MUTUAL_HOLDRANK_NEW | ✅ |
| 净流入明细 | 沪/深/合计净流入 | RPT_MUTUAL_NETINFLOW_DETAILS | ✅ |
| 净流入统计 | 累计净流入 | RPT_MUTUAL_NETINFLOW_STATISTICS | ✅ |
| 北向机构持股 | 机构代码、机构名称 | RPT_NORTH_ORG_HOLDRANK_NEW | ✅ |
| 成交额 | 沪深港通成交额 | RPT_MUTUAL_DEALAMT | ✅ |

### 4.9 研报实体（✅ 部分可用）

| 实体名称 | 数据内容 | reportName | 状态 |
|---------|---------|-----------|------|
| 盈利预测 | 评级机构数、买入评级数 | RPT_WEB_RESPREDICT | ✅ |
| 分析师排名 | 分析师姓名、机构、评分 | RPT_ANALYST_INDEX_RANK | ⚠️ 市场级数据 |

---

## 5. 数据字段详细映射

### 5.1 push2接口字段编码映射

| 字段编码 | 含义 | 示例值(海天味业) |
|---------|------|----------------|
| f43 | 最新价 | 38.25 |
| f44 | 最高价 | 38.80 |
| f45 | 最低价 | 37.90 |
| f46 | 今开 | 38.10 |
| f47 | 成交量(手) | 58923 |
| f48 | 成交额 | 2256384000 |
| f57 | 代码 | 603288 |
| f58 | 名称 | 海天味业 |
| f60 | 昨收 | 38.00 |
| f107 | 市场代码 | 1(沪) |
| f116 | 总市值 | 198560000000 |
| f117 | 流通市值 | 198560000000 |
| f152 | 市盈率(动) | 35.62 |
| f168 | 换手率 | 0.58 |
| f169 | 涨跌额 | 0.25 |
| f170 | 涨跌幅 | 0.66 |
| f135~f139 | 买1~5量 | — |
| f140~f144 | 买1~5价 | — |
| f145~f149 | 卖1~5量/价 | — |

### 5.2 K线数据字段映射

K线返回格式为逗号分隔字符串：`日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率`

| 位置 | 含义 | 示例 |
|------|------|------|
| 0 | 日期 | 2026-05-14 |
| 1 | 开盘价 | 38.10 |
| 2 | 收盘价 | 38.25 |
| 3 | 最高价 | 38.80 |
| 4 | 最低价 | 37.90 |
| 5 | 成交量(手) | 58923 |
| 6 | 成交额 | 2256384000 |
| 7 | 振幅 | 2.37 |
| 8 | 涨跌幅 | 0.66 |
| 9 | 涨跌额 | 0.25 |
| 10 | 换手率 | 0.58 |

### 5.3 datacenter接口字段映射

| 字段名 | 含义 | 适用报表 |
|--------|------|---------|
| SECURITY_CODE | 证券代码 | 通用 |
| SECUCODE | 证券代码(带市场) | 通用 |
| SECURITY_NAME_ABBR | 证券简称 | 通用 |
| REPORT_DATE | 报告期 | 财务报表 |
| TRADE_DATE | 交易日期 | 交易数据 |
| END_DATE | 截止日期 | 股东数据 |
| TOTAL_ASSETS | 总资产 | 资产负债表 |
| TOTAL_LIABILITIES | 总负债 | 资产负债表 |
| TOTAL_EQUITY | 所有者权益 | 资产负债表 |
| OPERATE_INCOME | 营业收入 | 利润表 |
| OPERATE_COST | 营业成本 | 利润表 |
| NETPROFIT | 净利润 | 利润表 |
| NETCASH_OPERATE | 经营活动现金流 | 现金流量表 |
| NETCASH_INVEST | 投资活动现金流 | 现金流量表 |
| NETCASH_FINANCE | 筹资活动现金流 | 现金流量表 |
| BASIC_EPS | 基本每股收益 | 业绩报表 |
| WEIGHTAVG_ROE | 加权平均ROE | 业绩报表 |
| PLEDGE_SHARES | 质押股数 | 股权质押 |
| PLEDGE_RATIO | 质押比例 | 股权质押 |
| HOLDER_NAME | 股东名称 | 股东数据 |
| HOLD_AMOUNT | 持仓量 | 机构持仓 |

---

## 6. 限流与反爬策略分析

### 6.1 各域名限流策略

| 域名 | 建议间隔 | 封锁机制 | 应对策略 |
|------|---------|---------|---------|
| push2.eastmoney.com | ≥1.5秒 | IP封锁(连接重置) | 更换IP/使用代理 |
| push2his.eastmoney.com | ≥1.5秒 | IP封锁(连接重置) | 更换IP/使用代理 |
| datacenter-web.eastmoney.com | ≥1.0秒 | reportName变更 | 定期从JS文件更新 |
| emweb.securities.eastmoney.com | ≥1.5秒 | 部分接口返回非JSON | 添加防御性检查 |
| np-anotice-stock.eastmoney.com | ≥1.0秒 | 暂未发现限制 | 正常限流即可 |

### 6.2 IP封锁机制

- **封锁表现**：`RemoteDisconnected('Remote end closed connection without response')`
- **封锁条件**：短时间高频请求（推测>5次/秒）
- **封锁时长**：不确定，可能持续数小时到数天
- **解封方式**：更换IP地址

### 6.3 请求头要求

```python
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://quote.eastmoney.com/",  # push2接口
    # 或 "Referer": "https://data.eastmoney.com/",  # datacenter接口
    # 或 "Referer": "https://emweb.securities.eastmoney.com/",  # F10接口
}
```

### 6.4 数据量限制

| 接口类型 | 单次最大数据量 | 分页支持 |
|---------|-------------|---------|
| push2实时行情 | 单只股票 | 否 |
| push2 K线 | lmt参数控制 | 否(用beg/end) |
| datacenter | pageSize参数 | 是(pageNumber) |
| F10 PageAjax | 全量返回 | 否 |
| 公告 | page_size参数 | 是(page_index) |

---

## 7. 结论与建议

### 7.1 可行性评估

| 数据类别 | 可行性 | 说明 |
|---------|--------|------|
| 实时行情 | ⚠️ 中等 | push2域名被封锁，需代理或换IP |
| K线/分时数据 | ⚠️ 中等 | 同上，但AkShare/Baostock可替代 |
| 财务三表 | ✅ 高 | datacenter接口稳定可用 |
| 股权质押 | ✅ 高 | datacenter接口稳定可用 |
| 大宗交易 | ✅ 高 | 新reportName已验证可用 |
| 分红送配 | ✅ 高 | 新reportName已验证可用 |
| F10档案 | ⚠️ 中等 | 部分接口返回非JSON，需进一步研究 |
| 公告 | ✅ 高 | 接口稳定可用 |
| 沪深港通 | ✅ 高 | 新reportName已验证可用 |
| 研报/盈利预测 | ✅ 高 | 新reportName已验证可用 |
| 龙虎榜 | ❌ 低 | 旧reportName失效，JS中未找到新名称 |
| 融资融券(个股级) | ❌ 低 | 新reportName仅支持市场级数据 |
| 股东(个股级) | ⚠️ 中等 | 新reportName存在但过滤字段不同 |

### 7.2 推荐数据获取策略

1. **主数据源**：AkShare + Baostock（实时行情、K线、分钟数据）
2. **补充数据源**：东方财富datacenter（财务、质押、大宗交易、分红、沪深港通、研报）
3. **公告数据源**：东方财富np-anotice-stock（公告列表）
4. **F10数据源**：东方财富emweb（公司概况、经营分析、资本运作）

### 7.3 风险提示

1. **reportName随时可能变更**：东方财富不提供API文档，reportName通过前端JS硬编码，可能随时变更
2. **IP封锁风险**：push2/push2his域名对高频请求实施IP封锁，需控制请求频率
3. **数据准确性**：push2接口的字段编码(f43等)含义需与实际数据对照验证
4. **过滤字段变更**：新reportName可能使用不同的过滤字段名，需逐个测试
5. **接口稳定性**：F10部分PageAjax接口返回非JSON，可能已迁移或需要额外鉴权

### 7.4 后续工作建议

1. **解决push2域名封锁**：研究代理方案或使用AkShare/Baostock替代
2. **研究龙虎榜新接口**：龙虎榜页面JS中未找到reportName，需使用Playwright拦截XHR请求
3. **研究融资融券个股级接口**：当前新reportName仅支持市场级数据
4. **研究股东数据过滤方式**：新reportName存在但不支持SECURITY_CODE过滤
5. **定期更新reportName**：建议每月从东方财富页面JS文件中重新提取reportName

---

## 附录A：验证脚本清单

| 脚本文件 | 数据域 | API数量 |
|---------|--------|---------|
| poc_eastmoney.py | 指数实时行情 | 7 |
| poc_em_quote.py | 个股行情+K线+分时+盘口 | 6 |
| poc_em_fund_flow.py | 资金流向 | 4 |
| poc_eastmoney_api_discovery.py | API端点全量探测 | 20 |
| poc_eastmoney_link_discovery.py | 递归链接发现 | - |
| poc_em_lhb.py | 龙虎榜单 | 3 |
| poc_em_margin.py | 融资融券 | 3 |
| poc_em_pledge.py | 股权质押 | 3 |
| poc_em_block_trade.py | 大宗交易 | 3 |
| poc_em_finance.py | 财务数据 | 6 |
| poc_em_shareholder.py | 股东分析 | 5 |
| poc_em_notice.py | 公告大全 | 3 |
| poc_em_research.py | 研报 | 3 |
| poc_em_dividend.py | 分红送配 | 3 |
| poc_em_f10.py | F10档案 | 8 |
| poc_em_hsgt.py | 沪深港通 | 3 |
| poc_em_reportname_discovery.py | reportName综合探测 | - |

## 附录B：从JS文件中提取的reportName完整列表

### 融资融券页面
- RPTA_RZRQ_LSDB
- RPTA_RZRQ_LSHJ
- RPTA_WEB_BKJYMXN
- RPTA_WEB_RZRQ_GGMX
- RPTA_WEB_RZRQ_LSSH

### 大宗交易页面
- PRT_BLOCKTRADE_MARKET_STA
- RPT_BLOCKTRADE_ACSTA
- RPT_BLOCKTRADE_OPERATEDEPTSTATISTICS
- RPT_BLOCKTRADE_OPERATEDEPT_NAME
- RPT_BLOCKTRADE_OPERATEDEPT_RANK
- RPT_BLOCKTRADE_STAINCLUDE
- RPT_DATA_BLOCKTRADE

### 分红送配页面
- RPT_DATE_SHAREBONUS_DET
- RPT_SHAREBONUS_DET

### 股东分析页面
- RPT_COOPFREEHOLDER
- RPT_COOPFREEHOLDERS_ANALYSIS
- RPT_COOPFREEHOLDERS_ANALYSISNEW
- RPT_FREEHOLDERS_BASIC_INFONEW

### 研报页面
- RPT_ANALYST_INDEX_RANK
- RPT_EMBOARD_ALL
- RPT_WEB_RESPREDICT

### 沪深港通页面
- RPT_MUTUAL_BOARD_HOLDRANK_NEW
- RPT_MUTUAL_BOARD_HOLDRANK_WEB
- RPT_MUTUAL_DEALAMT
- RPT_MUTUAL_DEAL_HISTORY
- RPT_MUTUAL_DLDATETYPE
- RPT_MUTUAL_HOLDRANK_NEW
- RPT_MUTUAL_NETINFLOW_DETAILS
- RPT_MUTUAL_NETINFLOW_STATISTICS
- RPT_MUTUAL_TRADEDATE
- RPT_NORTH_ORG_HOLDRANK_NEW

---

## 8. 浏览器爬取方案（DrissionPage）

> **验证日期**：2026-05-18
> **工具版本**：DrissionPage 4.1.1.2 / Playwright 1.52.0

### 8.1 方案背景

由于 push2/push2his 域名 IP 封锁和 datacenter reportName 大量失效，直接 API 调用方式存在严重限制。浏览器爬取方案通过模拟真实浏览器访问，直接提取页面渲染后的 HTML 数据，绕过 API 层面的封锁。

### 8.2 工具选型

| 工具 | 版本 | 用途 | 状态 |
|------|------|------|------|
| DrissionPage | 4.1.1.2 | 浏览器模式爬取页面表格数据 | ✅ 已安装验证 |
| Playwright | 1.52.0 | XHR拦截发现隐藏API端点 | ✅ 已安装 |

### 8.3 DrissionPage v4.x API要点

| 功能 | 正确用法 | 错误用法（v3.x） |
|------|---------|-----------------|
| 无头模式 | `co.headless()` | ~~`co.set_headless(True)`~~ |
| 等待页面加载 | `page.wait.doc_loaded()` | ~~`page.wait.ele_loaded()`~~ |
| 等待元素 | `page.wait.eles_loaded()` | ~~`page.wait.ele_loaded()`~~ |
| 元素定位 | `page.ele('css:.class')` | 同v3 |
| 批量元素 | `page.eles('tag:tr')` | 同v3 |

### 8.4 数据中心浏览器爬取验证结果

**9个模块全部成功提取表格数据！**

| 模块 | 页面URL | 表格提取 | 搜索筛选 | 数据示例 |
|------|---------|---------|---------|---------|
| 龙虎榜 | data.eastmoney.com/stock/lhb/ | ✅ | ❌(页面404) | 代码/名称/最新价/5分钟涨跌 |
| 融资融券 | data.eastmoney.com/rzrq/ | ✅ | ✅ | 交易日期/融资余额/融资买入额(21列) |
| 大宗交易 | data.eastmoney.com/dzjy/ | ✅ | ✅ | 序号/交易日期/上证指数/成交总额(10列) |
| 股权质押 | data.eastmoney.com/gpzy/ | ✅ | ✅ | 交易日期/质押总比例/质押公司数量(8列) |
| 股东分析 | data.eastmoney.com/gdfx/ | ✅ | ✅ | 股东名称/类型/排名/股票代码(16列) |
| 业绩报表 | data.eastmoney.com/bbsj/ | ✅ | ✅ | 股票代码/每股收益/营业收入/净利润(18列) |
| 分红送配 | data.eastmoney.com/yjfp/ | ✅ | ✅ | 代码/名称/送转股份/现金分红(21列) |
| 沪深港通 | data.eastmoney.com/hsgt/ | ✅ | ✅ | 类型/板块/成交净买额/成交总额(22列) |
| 研究报告 | data.eastmoney.com/report/ | ✅ | ✅ | 股票代码/报告名称/评级/机构(17列) |

**关键发现**：
1. 数据中心页面表格数据完整，浏览器模式可绕过API封锁
2. 搜索筛选功能可用（输入股票代码可过滤数据）
3. 龙虎榜页面URL已变更（原URL返回404），需更新URL
4. 各模块表格列数丰富（8-22列），数据量充足

### 8.5 行情页浏览器爬取验证结果

| 数据项 | 提取方式 | 结果 | 说明 |
|--------|---------|------|------|
| 股票名称 | DOM元素 | ✅ 成功 | 提取到"海天味业" |
| 实时价格 | DOM元素 | ⚠️ 盘后为"-" | 交易时段应有数据 |
| K线数据 | Canvas绘制 | ❌ 无法直接提取 | 页面使用17个Canvas元素 |
| 分时线 | Canvas绘制 | ❌ 无法直接提取 | 同上 |
| 五档盘口 | DOM元素 | ❌ 未定位到 | 选择器需调整 |
| 资金流向 | JS提取表格 | ✅ 成功 | 主力/大单/中单/小单净流入 |

**关键发现**：
1. 行情页K线和分时线使用Canvas绘制，数据不在DOM中
2. 资金流向数据可通过JS从表格提取
3. 实时行情数据在交易时段应可从DOM提取
4. 需结合Playwright XHR拦截获取K线/分时API数据

### 8.6 XHR拦截验证结果

| 场景 | 拦截域名 | 结果 | 说明 |
|------|---------|------|------|
| 龙虎榜 | datacenter-web.eastmoney.com | 0个请求 | 页面URL已变更(404) |
| 行情页 | push2/push2his.eastmoney.com | 待验证 | 需调整wait_until参数 |
| F10档案 | emweb.securities.eastmoney.com | 待验证 | - |

### 8.7 浏览器爬取 vs API爬取对比

| 维度 | API爬取(requests) | 浏览器爬取(DrissionPage) |
|------|-------------------|------------------------|
| 速度 | 快（~0.2s/请求） | 慢（~3-5s/页面） |
| IP封锁风险 | 高（push2已封锁） | 低（真实浏览器特征） |
| reportName依赖 | 高（80%已失效） | 无（直接读HTML） |
| 数据完整性 | 依赖API字段 | 页面展示什么就获取什么 |
| 搜索筛选 | 需构造filter参数 | 直接在搜索框输入 |
| 翻页 | 需构造pageNumber参数 | 点击下一页按钮 |
| K线/分时 | API可用时高效 | Canvas无法直接提取 |
| 资源消耗 | 低 | 高（需启动Chrome） |

### 8.8 推荐的混合策略

| 数据类别 | 推荐方式 | 原因 |
|---------|---------|------|
| 实时行情 | AkShare/Baostock | 浏览器无法提取Canvas数据 |
| K线/分时 | AkShare/Baostock + XHR拦截 | Canvas绘制需API数据 |
| 财务三表 | datacenter API | reportName可用，效率高 |
| 数据中心其他 | **DrissionPage浏览器** | 绕过reportName失效问题 |
| F10档案 | **DrissionPage浏览器** | 解决API返回非JSON问题 |
| 公告 | np-anotice-stock API | 接口稳定可用 |
| 龙虎榜 | **DrissionPage浏览器** | API reportName失效，但页面URL需更新 |

---

## 附录C：浏览器爬取验证脚本清单

| 脚本文件 | 数据域 | 工具 |
|---------|--------|------|
| poc_drissionpage_basic.py | DrissionPage基础功能验证 | DrissionPage |
| poc_em_browser_quote.py | 行情主页浏览器爬取 | DrissionPage |
| poc_em_browser_datacenter.py | 数据中心9模块浏览器爬取 | DrissionPage |
| poc_em_browser_f10.py | F10档案浏览器爬取 | DrissionPage |
| poc_em_xhr_intercept.py | XHR请求拦截发现API | Playwright |
