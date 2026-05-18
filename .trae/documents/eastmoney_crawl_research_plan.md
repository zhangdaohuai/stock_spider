# 东方财富网页递归爬取研究计划

## 一、任务目标

以海天味业（603288）为基础，递归研究东方财富网页上所有与股票相关的可抓取信息，形成完整报告并实现爬虫验证代码。

## 二、网页结构分析结果

东方财富的股票数据页面采用 **前端SPA + 后端REST API** 架构，网页HTML仅包含框架，实际数据全部通过AJAX请求JSON API获取。因此爬取策略为：**直接调用REST API获取结构化JSON数据**，而非解析HTML页面。

### 2.1 入口页面链接图谱

以 `https://quote.eastmoney.com/sh603288.html` 为入口，可递归发现以下子页面域：

```
quote.eastmoney.com          ← 行情主页（入口）
├── push2.eastmoney.com      ← 实时行情API
├── push2his.eastmoney.com   ← 历史K线/分时API
├── data.eastmoney.com       ← 数据中心（100+子页面）
│   ├── zjlx/               ← 资金流向
│   ├── stock/lhb/           ← 龙虎榜单
│   ├── rzrq/                ← 融资融券
│   ├── gpzy/                ← 股权质押
│   ├── dzjy/                ← 大宗交易
│   ├── bbsj/                ← 年报季报/业绩报表
│   ├── gdfx/                ← 股东分析
│   ├── dxf/                 ← 限售解禁
│   ├── notices/             ← 公告大全
│   ├── report/              ← 研究报告
│   ├── yjfp/                ← 分红送配
│   ├── stockcomment/        ← 千股千评
│   ├── jgdy/                ← 机构调研
│   ├── stockdata/           ← 数据全景图
│   ├── stockcalendar/       ← 个股日历
│   └── hsgt/                ← 沪深港通
├── emweb.securities.eastmoney.com  ← F10档案（SPA）
│   ├── cpbd                 ← 操盘必读
│   ├── gsgk                 ← 公司概况
│   ├── jyfx                 ← 经营分析
│   ├── hxtc                 ← 核心题材
│   ├── gdyj                 ← 股东研究
│   ├── gsds                 ← 公司大事
│   ├── gbjg                 ← 股本结构
│   ├── cwfx                 ← 财务分析
│   ├── fhrz                 ← 分红融资
│   ├── zbyz                 ← 资本运作
│   ├── thbj                 ← 行业对比
│   └── glgg                 ← 关联个股
└── guba.eastmoney.com       ← 股吧讨论
```

## 三、实施步骤

### 步骤1：创建递归链接发现爬虫

**文件**：`tests/functional_test_case/poc_eastmoney_link_discovery.py`

- 从海天味业行情页入口开始
- 递归爬取页面内所有 `eastmoney.com` 域名下的链接
- 过滤掉非股票相关的链接（广告、下载、登录等）
- 输出完整的链接树和分类结果
- **深度限制**：3层递归
- **域名限制**：仅 `*.eastmoney.com`

### 步骤2：创建API端点探测爬虫

**文件**：`tests/functional_test_case/poc_eastmoney_api_discovery.py`

- 对步骤1发现的每个页面，通过浏览器开发者工具模式（拦截XHR请求）识别其底层API
- 使用 Playwright 或 requests+正则 方式提取页面JS中的API端点
- 记录每个API的：URL、请求方法、参数、返回数据结构
- 以海天味业(603288)为参数，实际调用API验证数据可获取性

### 步骤3：实现各数据域的爬虫验证代码

按数据域拆分为独立脚本，每个脚本验证一类数据：

| 脚本文件 | 数据域 | API基础URL |
|----------|--------|------------|
| `poc_em_quote.py` | 实时行情+K线+分时+盘口 | `push2.eastmoney.com` / `push2his.eastmoney.com` |
| `poc_em_fund_flow.py` | 资金流向（个股/板块/大盘） | `push2.eastmoney.com` |
| `poc_em_lhb.py` | 龙虎榜单 | `data.eastmoney.com` |
| `poc_em_margin.py` | 融资融券 | `data.eastmoney.com` |
| `poc_em_pledge.py` | 股权质押 | `data.eastmoney.com` |
| `poc_em_block_trade.py` | 大宗交易 | `data.eastmoney.com` |
| `poc_em_finance.py` | 财务数据（三表+业绩） | `data.eastmoney.com` / `emweb.securities.eastmoney.com` |
| `poc_em_shareholder.py` | 股东分析+十大股东+机构持仓 | `data.eastmoney.com` |
| `poc_em_notice.py` | 公告大全+个股日历 | `data.eastmoney.com` |
| `poc_em_research.py` | 研报+盈利预测 | `data.eastmoney.com` |
| `poc_em_dividend.py` | 分红送配 | `data.eastmoney.com` |
| `poc_em_f10.py` | F10档案全量数据 | `emweb.securities.eastmoney.com` |
| `poc_em_hsgt.py` | 沪深港通 | `data.eastmoney.com` |

### 步骤4：运行所有爬虫验证脚本

- 逐个运行步骤3的脚本
- 记录每个API的：可用性、数据字段、数据量、响应时间
- 标记失败或受限的接口

### 步骤5：生成研究报告

**文件**：`docs/eastmoney_crawl_research_report.md`

报告结构：
1. 研究概述（目标、方法、范围）
2. 网页链接图谱（完整递归结果）
3. API端点清单（URL、参数、返回字段、可用性）
4. 可抓取实体清单（按类别：行情、财务、股东、公告等）
5. 数据字段详细映射
6. 限流与反爬策略分析
7. 结论与建议

## 四、技术方案

### 4.1 链接发现方案

使用 `requests` + `BeautifulSoup` 解析HTML提取链接，递归3层深度：

```python
# 伪代码
def discover_links(url, depth=3, visited=set()):
    if depth == 0 or url in visited:
        return
    visited.add(url)
    html = requests.get(url).text
    links = BeautifulSoup(html).find_all('a', href=True)
    for link in links:
        if is_eastmoney_stock_related(link):
            discover_links(link, depth-1, visited)
```

### 4.2 API发现方案

东方财富页面的JS代码中硬编码了API端点，两种策略：

**策略A（优先）**：直接使用已知的东方财富API文档和已验证的端点
- `push2.eastmoney.com/api/qt/stock/get` — 单只股票实时行情
- `push2.eastmoney.com/api/qt/clist/get` — 批量股票列表
- `push2his.eastmoney.com/api/qt/stock/kline/get` — K线历史
- `push2his.eastmoney.com/api/qt/stock/trends2/get` — 分时线
- `datacenter-web.eastmoney.com/api/data/v1/get` — 数据中心通用接口
- `emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/*` — F10财务分析

**策略B（补充）**：使用 Playwright 拦截XHR请求，自动发现未知API

### 4.3 限流策略

- 每次请求间隔 ≥ 1秒
- 使用 `requests.Session` 复用连接
- 设置合理的 User-Agent 和 Referer
- 单脚本运行时间控制在5分钟内

## 五、执行分工

| 步骤 | 负责成员 | 产出 |
|------|----------|------|
| 步骤1 | search agent | 链接发现爬虫 + 链接图谱 |
| 步骤2 | search agent | API端点清单 |
| 步骤3 | module-engineer × 3（并行） | 13个爬虫验证脚本 |
| 步骤4 | integration-test-engineer | 运行结果汇总 |
| 步骤5 | req-analyst | 研究报告文档 |

## 六、风险与约束

1. **IP封锁风险**：东方财富反爬严格，需严格控制请求频率（≥1秒/次）
2. **SPA页面**：F10档案等SPA页面HTML无数据，必须调用API
3. **登录限制**：部分数据（如自选股）需登录，不在本次研究范围
4. **数据准确性**：API返回的字段编码（如f43）需与实际含义对照验证
5. **接口稳定性**：东方财富API可能随时变更，需标注验证日期
