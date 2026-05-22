# 功能验证测试用例 — 使用与验证指南

## 1. 概述

本目录下的验证脚本（PoC）用于在正式开发前，对三大数据源的 API 能力和边界进行实际验证。所有验证结果将作为 PRD 和架构设计的事实依据。

### 数据源覆盖

| 数据源 | 验证脚本 | 底层协议 | 需要登录 |
|--------|----------|----------|----------|
| 东方财富（直接API） | `poc_eastmoney.py` | HTTP REST | 否 |
| Baostock | `poc_baostock.py` / `poc_baostock_extra.py` | 自有TCP协议 | 是（匿名） |
| AkShare | `poc_akshare_api.py` / `poc_akshare_quick.py` | HTTP REST（底层调东方财富） | 否 |

---

## 2. 环境准备

### 2.1 Conda 环境

所有脚本必须在 `agent` conda 环境下运行：

```bash
conda activate agent
```

### 2.2 依赖包

| 包名 | 用途 | 安装命令 |
|------|------|----------|
| `akshare` | AkShare 数据源 | `pip install akshare` |
| `baostock` | Baostock 数据源 | `pip install baostock` |
| `requests` | 东方财富直接HTTP请求 | `pip install requests` |
| `pandas` | 数据处理 | `pip install pandas` |

### 2.3 代理问题（重要）

系统环境变量可能设置了 HTTP 代理（如 `http_proxy=http://127.0.0.1:7890`），而东方财富 API 不支持代理访问。运行脚本前**必须清除代理**：

**方式一：运行时清除（推荐）**

所有脚本已在代码开头自动清除代理环境变量，直接运行即可。

**方式二：命令行清除**

```bash
http_proxy= https_proxy= ALL_PROXY= conda run -n agent python tests/functional_test_case/poc_eastmoney.py
```

### 2.4 运行目录

所有脚本需在项目根目录下运行：

```bash
cd /path/to/stock_spider
```

---

## 3. 脚本详细说明

### 3.1 东方财富直接API验证 — `poc_eastmoney.py`

**目的**：验证东方财富网公开 REST API 的可用性、数据完整性和响应速度，不依赖任何第三方库。

**运行命令**：

```bash
conda run -n agent python tests/functional_test_case/poc_eastmoney.py
```

**测试项一览**：

| 编号 | 测试项 | API端点 | 验证目标 |
|------|--------|---------|----------|
| 1 | 上证指数实时行情 | `push2.eastmoney.com/api/qt/stock/get` | secid=1.000001 实时数据字段完整性 |
| 2 | 深证成指实时行情 | `push2.eastmoney.com/api/qt/stock/get` | secid=0.399001 实时数据字段完整性 |
| 3 | 指数列表 | `push2.eastmoney.com/api/qt/clist/get` | 批量获取指数列表 |
| 4 | 日线K线历史 | `push2his.eastmoney.com/api/qt/stock/kline/get` | klt=101 日线数据 |
| 5 | 5分钟K线 | `push2his.eastmoney.com/api/qt/stock/kline/get` | klt=5 分钟线数据 |
| 6 | 分时线数据 | `push2his.eastmoney.com/api/qt/stock/trends2/get` | 当日分时数据 |
| 7 | 响应时间评估 | `push2.eastmoney.com/api/qt/stock/get` | 连续5次请求测速 |

**关键参数说明**：

- `secid` 格式：`{市场编码}.{代码}`，沪市=1，深市=0
  - 上证指数：`1.000001`
  - 深证成指：`0.399001`
  - 个股示例：`0.000001`（平安银行）
- `klt` K线周期：`101`=日线，`5`=5分钟，`1`=1分钟
- `fqt` 复权：`1`=前复权，`2`=后复权，`0`=不复权

**预期输出示例**：

```
============================================================
测试1: 上证指数实时行情
============================================================
状态码: 200
{
  "rc": 0,
  "data": {
    "f43": 4177.92,    # 最新价
    "f57": "000001",   # 代码
    "f58": "上证指数",  # 名称
    "f170": -1.52      # 涨跌幅%
  }
}
...
测试7: 响应时间评估 (连续5次请求)
  第1次: 0.251s, 状态码: 200
  ...
平均响应时间: 0.222s, 最快: 0.190s, 最慢: 0.251s
```

---

### 3.2 Baostock核心接口验证 — `poc_baostock.py`

**目的**：验证 Baostock 核心接口的能力边界，包括登录、股票列表、K线数据、分钟线回溯、频率限制等。

**运行命令**：

```bash
conda run -n agent python tests/functional_test_case/poc_baostock.py
```

**测试项一览**：

| 编号 | 测试项 | API方法 | 验证目标 |
|------|--------|---------|----------|
| 1 | 登录测试 | `bs.login()` | 匿名登录是否成功 |
| 2 | 全量股票列表 | `bs.query_all_stock()` | 沪深北股票数量统计 |
| 3 | 日线K线数据 | `bs.query_history_k_data_plus()` | frequency="d" 日线 |
| 4 | 5分钟K线数据 | `bs.query_history_k_data_plus()` | frequency="5" 分钟线 |
| 5 | 分钟线回溯(2016) | `bs.query_history_k_data_plus()` | 2016年分钟线是否可用 |
| 6 | 分钟线回溯(2019) | `bs.query_history_k_data_plus()` | 2019年分钟线是否可用 |
| 7 | isST字段 | `bs.query_history_k_data_plus()` | ST标识字段是否可用 |
| 8 | 指数分钟线 | `bs.query_history_k_data_plus()` | 指数是否支持分钟线 |
| 9 | 实时行情接口 | `bs.query_current_data` | 该接口是否存在 |
| 10 | API方法列表 | `dir(bs)` | 列出所有公开方法 |
| 11 | 港股数据 | `bs.query_history_k_data_plus()` | 港股代码是否支持 |
| 12 | 频率限制 | 连续10次请求 | 是否有限流 |

**关键参数说明**：

- 股票代码格式：`{市场}.{代码}`
  - 沪市：`sh.600000`（浦发银行）
  - 深市：`sz.000001`（平安银行）
  - 指数：`sh.000001`（上证指数）
- `frequency`：`"d"`=日线，`"5"`=5分钟，`"15"`=15分钟，`"30"`=30分钟，`"60"`=60分钟
- `adjustflag`：`"1"`=后复权，`"2"`=前复权，`"3"`=不复权

**预期输出示例**：

```
1. 登录测试
  error_code: 0
  error_msg: success

2. 获取全量股票列表 (query_all_stock)
  总记录数: 5352
  沪市(sh): 2263, 深市(sz): 2840, 北交所(bj): 249

4. 5分钟K线数据测试
  记录数: 48

5. 分钟线最早数据回溯测试 (2016年)
  2016年分钟线数据不可用!

12. 调用频率限制测试 (连续10次快速请求)
  10次请求耗时: 1.21秒
  成功: 10, 失败: 0
```

---

### 3.3 Baostock补充验证 — `poc_baostock_extra.py`

**目的**：补充验证 Baostock 分钟线回溯边界、证券基本资料、行业分类、ST标识、ETF数据等。

**运行命令**：

```bash
conda run -n agent python tests/functional_test_case/poc_baostock_extra.py
```

**测试项一览**：

| 测试项 | API方法 | 验证目标 |
|--------|---------|----------|
| 分钟线回溯边界 | `query_history_k_data_plus()` | 逐年(2019-2022)分钟线最早可用日期 |
| 证券基本资料 | `query_stock_basic()` | IPO日期、退市日期、状态等字段 |
| 行业分类 | `query_stock_industry()` | 证监会行业分类 |
| ST股票isST字段 | `query_history_k_data_plus()` | ST股票的isST字段值 |
| ETF数据 | `query_history_k_data_plus()` | ETF基金代码是否支持 |

**预期输出示例**：

```
分钟线数据回溯边界测试
  2019年1月: 0条记录
  2020年1月: 768条记录
    最早: 2020-01-02 20200102093500000
  2021年1月: 960条记录
    最早: 2021-01-04 20210104093500000

证券基本资料测试 (query_stock_basic)
  字段: ['code', 'code_name', 'ipoDate', 'outDate', 'type', 'status']

行业分类测试 (query_stock_industry)
  字段: ['updateDate', 'code', 'code_name', 'industry', 'industryClassification']
```

---

### 3.4 AkShare完整验证 — `poc_akshare_api.py`

**目的**：验证 AkShare 封装接口的完整能力，包括股票列表、实时行情、分钟K线、日线、五档盘口、ST/退市股、港股等。

**运行命令**：

```bash
conda run -n agent python tests/functional_test_case/poc_akshare_api.py
```

> ⚠️ **注意**：此脚本包含11个测试项，每个间隔3秒，总耗时约1-2分钟。由于底层调用东方财富API，频繁请求可能触发IP封锁。

**测试项一览**：

| 编号 | 测试项 | AkShare方法 | 验证目标 |
|------|--------|-------------|----------|
| 1 | A股全量股票列表 | `stock_info_a_code_name()` | 股票总数和字段 |
| 2 | 沪深京A股实时行情 | `stock_zh_a_spot_em()` | 全量实时行情 |
| 3 | 分钟K线(近期) | `stock_zh_a_hist_min_em()` | 1分钟线近期数据 |
| 4 | 分钟K线(2016回溯) | `stock_zh_a_hist_min_em()` | 1分钟线历史回溯 |
| 5 | 日线历史(2016回溯) | `stock_zh_a_hist()` | 日线历史数据 |
| 6 | 五档盘口 | `stock_bid_ask_em()` | 单只股票盘口数据 |
| 7 | ST风险警示板 | `stock_zh_a_st_em()` | ST股票列表 |
| 8 | 退市股票 | `stock_zh_a_stop_em()` | 退市股票列表 |
| 9 | 港股实时行情 | `stock_hk_spot_em()` | 港股实时数据 |
| 10 | 港股分钟数据 | `stock_hk_hist_min_em()` | 港股5分钟线 |
| 11 | 分钟数据最大条数 | `stock_zh_a_hist_min_em()` | 单次请求最大数据量 |

**关键参数说明**：

- `symbol`：6位纯数字代码，如 `"000001"`
- `period`：`"1"`=1分钟，`"5"`=5分钟，`"15"`=15分钟，`"daily"`=日线
- `adjust`：`"qfq"`=前复权，`"hfq"`=后复权，`""`=不复权

---

### 3.5 AkShare关键接口快速验证 — `poc_akshare_quick.py`

**目的**：精简版验证脚本，仅测试5个核心接口，每个间隔5秒，降低触发IP封锁的风险。适合日常快速验证。

**运行命令**：

```bash
conda run -n agent python tests/functional_test_case/poc_akshare_quick.py
```

**测试项一览**：

| 编号 | 测试项 | AkShare方法 |
|------|--------|-------------|
| 1 | 沪深京A股实时行情 | `stock_zh_a_spot_em()` |
| 2 | 分钟K线(近期) | `stock_zh_a_hist_min_em()` |
| 3 | 日线历史数据 | `stock_zh_a_hist()` |
| 4 | ST风险警示板 | `stock_zh_a_st_em()` |
| 5 | 五档盘口数据 | `stock_bid_ask_em()` |

---

## 4. 已验证的关键结论

以下结论基于实际运行结果，作为 PRD 和架构设计的事实依据。

### 4.1 东方财富直接API

| 结论 | 详情 |
|------|------|
| ✅ 指数实时行情可用 | 上证/深证指数实时数据完整，含最新价、涨跌幅、成交量等 |
| ✅ 指数分钟K线可用 | 5分钟K线可获取约1536条历史数据 |
| ✅ 分时线可用 | 当日241条分时数据 |
| ✅ 日线历史完整 | 8639条日线数据，可追溯至上市首日 |
| ✅ 响应速度快 | 平均0.222s/次 |
| ⚠️ 反爬机制严格 | 短时间频繁请求会触发IP封锁（连接被远程关闭），封锁时间>10分钟 |

### 4.2 Baostock

| 结论 | 详情 |
|------|------|
| ✅ 匿名登录可用 | 无需注册，直接 `bs.login()` |
| ✅ 全量股票列表 | 沪深北共5352只 |
| ✅ 日线数据完整 | 含18个字段（开高低收、成交量、换手率、PE、PB等） |
| ✅ 5分钟K线可用 | 每日48条5分钟数据 |
| ✅ 无频率限制 | 连续10次请求1.21秒，全部成功 |
| ✅ 证券基本资料 | 含IPO日期、状态 |
| ✅ 行业分类 | 证监会行业分类可用 |
| ❌ 分钟线最早2020年 | 2019年及之前无分钟线数据，最早2020-01-02 |
| ❌ 指数不支持分钟线 | 指数代码查询分钟线返回空数据 |
| ❌ 不支持港股 | 港股代码格式不兼容 |
| ❌ 不支持ETF | ETF代码查询返回空数据 |
| ❌ 无实时行情接口 | `query_current_data` 方法不存在 |

### 4.3 AkShare

| 结论 | 详情 |
|------|------|
| ✅ 股票列表可用 | 5515只A股，耗时约10s |
| ✅ 日线历史完整 | 可回溯至2016年 |
| ✅ 五档盘口可用 | 36行数据，含5档买卖价和量 |
| ⚠️ 分钟线仅近期 | 1分钟线仅能获取最近5个交易日 |
| ⚠️ 受东方财富反爬限制 | 底层调用东方财富API，同样受IP封锁影响 |

---

## 5. 故障排查

### 5.1 `RemoteDisconnected` / `Connection aborted`

**现象**：所有东方财富相关请求返回 `('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))`

**原因**：IP 被东方财富反爬机制封锁

**解决方案**：

1. 等待30分钟至数小时后重试
2. 切换网络（如切换WiFi/使用手机热点）
3. 使用代理（需确保代理可用）：
   ```bash
   conda run -n agent python tests/functional_test_case/poc_eastmoney.py
   # 修改脚本，在请求中添加 proxies 参数
   ```

### 5.2 `ProxyError` / 代理连接失败

**现象**：`Unable to connect to proxy` 或 `Connection refused` 到 `127.0.0.1:7890`

**原因**：系统环境变量设置了代理，但代理服务未运行

**解决方案**：

1. 脚本已内置代理清除逻辑，确保在 `import akshare` 之前执行
2. 或命令行手动清除：
   ```bash
   http_proxy= https_proxy= ALL_PROXY= conda run -n agent python <脚本路径>
   ```

### 5.3 Baostock 登录失败

**现象**：`error_code` 不为 `"0"`

**原因**：网络问题或 Baostock 服务器维护

**解决方案**：

1. 检查网络连接
2. 访问 [Baostock官网](http://baostock.com/) 查看服务状态
3. 稍后重试

### 5.4 AkShare 返回空DataFrame

**现象**：接口调用成功但返回0行数据

**原因**：

1. 非交易时段（盘后调用分钟线接口）
2. 日期范围超出数据可用范围（如1分钟线仅5天）
3. 股票代码不存在

**解决方案**：

1. 在交易时段（9:30-15:00）运行
2. 调整日期参数到最近5个交易日内
3. 确认股票代码正确

---

## 6. 推荐运行顺序

首次验证建议按以下顺序执行，避免触发IP封锁：

```
步骤1: poc_baostock.py          (无IP封锁风险，约30秒)
步骤2: poc_baostock_extra.py    (无IP封锁风险，约20秒)
步骤3: poc_eastmoney.py         (7个测试，约15秒)
步骤4: 等待5分钟
步骤5: poc_akshare_quick.py     (5个测试，间隔5秒，约45秒)
步骤6: poc_akshare_api.py       (11个测试，间隔3秒，约2分钟，仅当需要完整验证时运行)
```

---

## 7. 东方财富API字段速查

### 7.1 实时行情字段映射

| 字段代码 | 含义 | 字段代码 | 含义 |
|----------|------|----------|------|
| f43 | 最新价 | f44 | 最高价 |
| f45 | 最低价 | f46 | 今开 |
| f47 | 成交量（手） | f48 | 成交额 |
| f50 | 量比 | f57 | 代码 |
| f58 | 名称 | f60 | 昨收 |
| f107 | 市场编码 | f168 | 换手率 |
| f169 | 涨跌额 | f170 | 涨跌幅 |
| f171 | 振幅 | f116 | 总市值 |
| f117 | 流通市值 | f152 | 市场类型 |

### 7.2 secid 编码规则

| 市场 | 编码前缀 | 示例 |
|------|----------|------|
| 沪市 | 1 | `1.600000`（浦发银行）、`1.000001`（上证指数） |
| 深市 | 0 | `0.000001`（平安银行）、`0.399001`（深证成指） |
| 北交所 | 0 | `0.830799` |
| 港股 | 116 | `116.00700`（腾讯控股） |

### 7.3 K线周期参数 (klt)

| 值 | 含义 | 值 | 含义 |
|----|------|----|------|
| 1 | 1分钟 | 5 | 5分钟 |
| 15 | 15分钟 | 30 | 30分钟 |
| 60 | 60分钟 | 101 | 日线 |
| 102 | 周线 | 103 | 月线 |

---

## 8. 浏览器爬取验证脚本（DrissionPage / Playwright）

### 8.1 环境准备

#### 安装DrissionPage

```bash
pip install DrissionPage
```

当前已安装版本：DrissionPage 4.1.1.2

#### 安装Playwright（XHR拦截脚本需要）

```bash
pip install playwright
playwright install chromium
```

当前已安装版本：Playwright 1.52.0

#### 代理问题

浏览器爬取脚本**不需要**清除代理环境变量，因为浏览器会自动处理网络连接。但如果系统代理导致浏览器无法访问东方财富，可临时关闭代理。

### 8.2 DrissionPage基础验证 — `poc_drissionpage_basic.py`

**目的**：验证DrissionPage能否正常启动浏览器、访问东方财富页面并提取数据。

**运行命令**：

```bash
python tests/functional_test_case/poc_drissionpage_basic.py
```

**测试项一览**：

| 编号 | 测试项 | 验证目标 |
|------|--------|---------|
| 1 | 安装验证 | DrissionPage版本号、核心模块导入 |
| 2 | 无头启动 | Chrome无头模式启动 |
| 3 | 页面访问 | 访问东方财富行情页 |
| 4 | 元素提取 | 股票名称、价格等基本元素 |
| 5 | 表格提取 | 页面中的数据表格 |

**预期输出**：

```
验证结果汇总
  安装验证: 通过
  无头启动: 通过
  页面访问: 通过
  元素提取: 通过
  表格提取: 通过
  总计: 5/5 项通过
```

### 8.3 行情页浏览器爬取 — `poc_em_browser_quote.py`

**目的**：使用DrissionPage浏览器模式爬取行情主页数据，替代被IP封锁的push2 API。

**运行命令**：

```bash
python tests/functional_test_case/poc_em_browser_quote.py
```

**测试项一览**：

| 编号 | 测试项 | 说明 |
|------|--------|------|
| 0 | 页面结构探索 | 统计Canvas/SVG/Table/IFrame数量 |
| 1 | 实时行情 | 提取股票名称、价格、涨跌幅 |
| 2 | K线数据 | 检测K线渲染方式（Canvas/表格） |
| 3 | 分时线 | 检测分时线渲染方式 |
| 4 | 五档盘口 | 提取买卖五档数据 |
| 5 | 资金流向 | 提取主力/大单/中单/小单净流入 |

**关键发现**：
- K线和分时线使用Canvas绘制，无法直接从DOM提取
- 资金流向数据可通过JS从表格提取
- 实时行情在交易时段可从DOM提取，盘后显示"-"

### 8.4 数据中心浏览器爬取 — `poc_em_browser_datacenter.py`

**目的**：使用DrissionPage浏览器模式爬取数据中心9个模块的表格数据。

**运行命令**：

```bash
python tests/functional_test_case/poc_em_browser_datacenter.py
```

**测试项一览**：

| 编号 | 模块 | URL | 表格列数 |
|------|------|-----|---------|
| 1 | 龙虎榜 | data.eastmoney.com/stock/lhb/ | 4列 |
| 2 | 融资融券 | data.eastmoney.com/rzrq/ | 21列 |
| 3 | 大宗交易 | data.eastmoney.com/dzjy/ | 10列 |
| 4 | 股权质押 | data.eastmoney.com/gpzy/ | 8列 |
| 5 | 股东分析 | data.eastmoney.com/gdfx/ | 16列 |
| 6 | 业绩报表 | data.eastmoney.com/bbsj/ | 18列 |
| 7 | 分红送配 | data.eastmoney.com/yjfp/ | 21列 |
| 8 | 沪深港通 | data.eastmoney.com/hsgt/ | 22列 |
| 9 | 研究报告 | data.eastmoney.com/report/ | 17列 |

**关键特性**：
- 每个模块自动提取表头和前3行数据
- 支持搜索筛选（输入股票代码"603288"）
- 自动检测翻页组件
- 模块间间隔3秒避免请求过快

**注意**：此脚本运行时间较长（约3-5分钟），因为需要依次访问9个页面。

### 8.5 F10档案浏览器爬取 — `poc_em_browser_f10.py`

**目的**：使用DrissionPage浏览器模式爬取F10档案页面，解决部分API返回非JSON的问题。

**运行命令**：

```bash
python tests/functional_test_case/poc_em_browser_f10.py
```

**测试项一览**：

| 编号 | 标签 | API状态 | 浏览器模式 |
|------|------|---------|-----------|
| 1 | 公司概况 | ✅ API可用 | ✅ 浏览器可提取 |
| 2 | 经营分析 | ✅ API可用 | ✅ 浏览器可提取 |
| 3 | 核心题材 | ❌ API非JSON | ✅ 浏览器可提取 |
| 4 | 股本结构 | ❌ API非JSON | ✅ 浏览器可提取 |
| 5 | 公司大事 | ❌ API非JSON | ⚠️ 部分可提取 |
| 6 | 财务分析 | ✅ API可用 | ✅ 浏览器可提取 |
| 7 | 资本运作 | ✅ API可用 | ✅ 浏览器可提取 |
| 8 | 关联个股 | ❌ API非JSON | ✅ 浏览器可提取 |
| 9 | 股东研究 | ⚠️ API空数据 | ✅ 浏览器可提取 |

**关键发现**：
- 之前API失败的4个接口中，3个可通过浏览器模式成功提取
- 股本结构数据完整：包含股份流通受限表、流通股份分布情况表
- 融资融券个股级数据可通过F10页面获取（51行历史数据）

### 8.6 XHR请求拦截 — `poc_em_xhr_intercept.py`

**目的**：使用Playwright拦截浏览器XHR请求，发现隐藏的API端点。

**运行命令**：

```bash
python tests/functional_test_case/poc_em_xhr_intercept.py
```

**测试项一览**：

| 编号 | 场景 | 拦截域名 | 结果 |
|------|------|---------|------|
| 1 | 龙虎榜 | datacenter-web.eastmoney.com | 0个请求（页面URL已变更） |
| 2 | 行情页 | push2/push2his.eastmoney.com | 20个请求 |
| 3 | F10档案 | emweb.securities.eastmoney.com | 217个请求 |

**行情页发现的API端点**：

| 端点路径 | 请求次数 | 说明 |
|---------|---------|------|
| /api/qt/stock/get | 6 | 实时行情 |
| /api/qt/stock/kline/get | 1 | K线数据 |
| /api/qt/stock/trends2/sse | 2 | 分时线 |
| /api/qt/stock/details/get | 1 | 盘口明细 |
| /api/qt/stock/fflow/kline/get | 1 | 资金流向 |
| /api/qt/clist/get | 1 | 股票列表 |
| /api/qt/slist/get | 3 | 排行列表 |
| /api/qt/pkyd/get | 2 | 盘口异动 |
| /api/qt/kamt/get | 1 | 沪深港通资金 |
| /api/qt/ulist/get | 1 | 涨停列表 |

**注意**：此脚本运行时间较长（约2-3分钟），需要启动Playwright浏览器。

### 8.7 故障排查（浏览器爬取）

#### Chrome启动失败

**现象**：`ChromiumPage` 创建失败或超时

**解决方案**：
1. 确保系统已安装Chrome或Chromium浏览器
2. 检查Chrome版本是否与DrissionPage兼容
3. 尝试不使用无头模式：去掉 `co.headless()` 调用

#### 页面加载超时

**现象**：`page.get()` 长时间无响应

**解决方案**：
1. 增加等待时间：`time.sleep(5)` 后再提取数据
2. 检查网络连接
3. 尝试使用 `page.wait.doc_loaded(timeout=30)`

#### 元素定位失败

**现象**：`page.ele()` 返回None或抛出异常

**解决方案**：
1. 使用多种选择器策略：CSS、XPath、文本定位
2. 增加等待时间让动态内容加载完成
3. 使用 `page.wait.eles_loaded()` 等待元素出现

#### DrissionPage v4.x API变更

| v3.x用法 | v4.x用法 |
|---------|---------|
| `co.set_headless(True)` | `co.headless()` |
| `page.wait.ele_loaded()` | `page.wait.doc_loaded()` |
| `page.wait(timeout=10)` | `page.wait.doc_loaded(timeout=10)` |

---

## 9. 推荐运行顺序（含浏览器爬取）

```
步骤1: poc_drissionpage_basic.py           (基础验证，约30秒)
步骤2: poc_baostock.py                     (无IP封锁风险，约30秒)
步骤3: poc_em_browser_datacenter.py        (数据中心9模块，约3-5分钟)
步骤4: poc_em_browser_f10.py               (F10档案9标签，约3-5分钟)
步骤5: 等待5分钟
步骤6: poc_em_browser_quote.py             (行情主页，约2分钟)
步骤7: poc_em_xhr_intercept.py             (XHR拦截，约2-3分钟)
步骤8: poc_eastmoney.py                    (API验证，约15秒)
步骤9: poc_akshare_quick.py                (AkShare快速验证，约45秒)
```

---

## 10. 同花顺数据源验证脚本

### 10.1 环境准备

#### 安装依赖

```bash
pip install thsdk pywencai 'mootdx[all]' pytdx
```

#### 创建mootdx配置目录

```bash
mkdir -p ~/.mootdx
```

### 10.2 JSONP API端点探测 — `poc_ths_jsonp_api.py`

**目的**：全量探测同花顺d.10jqka.com.cn的JSONP API端点可用性。

**运行命令**：

```bash
python tests/functional_test_case/poc_ths_jsonp_api.py
```

**测试项一览**：

| 编号 | 测试项 | 验证目标 |
|------|--------|---------|
| 1 | 分钟线(1/5/15/30/60分钟) | 各周期分钟线按年获取 |
| 2 | 实时行情 | 个股实时价格数据 |
| 3 | 个股详情 | 个股基本面信息 |
| 4 | 行情排行 | 全A股涨跌排行 |
| 5 | 概念/行业板块 | 板块列表和排名 |
| 6 | 问财接口 | 自然语言查询 |
| 7 | 资金流向/大单追踪 | 资金数据 |
| 8 | 分时数据(v6) | v6版API分时线 |
| 9 | K线(日/周/月) | 标准K线数据 |
| 10 | 龙虎榜 | 龙虎榜数据 |

**关键发现**：
- v2 API period code与社区流传映射不同：30=5分钟, 40=30分钟, 50=60分钟
- v6 API period=60 可获取1分钟线
- 实时行情和日K线稳定可用
- 问财、龙虎榜、大单追踪等接口需认证

### 10.3 分钟线深度验证 — `poc_ths_minute_line.py`

**目的**：深度验证同花顺分钟线数据格式、历史覆盖范围、反爬策略。

**运行命令**：

```bash
python tests/functional_test_case/poc_ths_minute_line.py
```

**测试项一览**：

| 编号 | 测试项 | 验证目标 |
|------|--------|---------|
| 1 | 分钟线历史覆盖 | 2020-2026年各周期数据可用性 |
| 2 | 数据格式解析 | CSV字段解析和含义 |
| 3 | 多股票对比 | 不同股票分钟线差异 |
| 4 | 实时行情 | 实时行情数据提取 |
| 5 | 反爬策略检测 | Referer/UA/高频/问财/qd接口 |
| 6 | v6版API | v6版端点可用性 |

### 10.4 Period Code诊断 — `poc_ths_period_diagnosis.py`

**目的**：暴力测试v2/v6 API所有period code，确定正确的映射关系。

**运行命令**：

```bash
python tests/functional_test_case/poc_ths_period_diagnosis.py
```

**关键输出**：

```
v2 API有效period code:
  00/01/02: 日K线(243条)
  10/11/12: 周K线(53条)
  20/21/22: 月K线(12条)
  30: 5分钟线(5664条) - 不稳定
  40/41/42: 30分钟线(1944条)
  50/51/52: 60分钟线(972条)
  70/71/72: 日K线datetime(243条)
  80/81/82: 年K线(1条)
  90/91/92: 季K线(4条)

v6 API:
  period=01: 日K线(total=5919)
  period=60: 1分钟线(total=11207)
```

**注意**：此脚本运行时间较长（约3-5分钟），因为需要测试100个period code。

### 10.5 v6 API历史范围验证 — `poc_ths_v6_history.py`

**目的**：验证v6 API 1分钟线的按年获取能力和历史范围。

**运行命令**：

```bash
python tests/functional_test_case/poc_ths_v6_history.py
```

**关键发现**：

| API | Period | 数据类型 | 2020 | 2024 | 2025 | 2026 |
|-----|--------|---------|------|------|------|------|
| v6 | 60 | 1分钟线 | ❌ | ❌ | ❌ | ✅(11207条) |
| v2 | 40 | 30分钟线 | - | ✅ | ✅ | ✅ |
| v2 | 50 | 60分钟线 | - | ✅ | ✅ | ✅ |

### 10.6 THSDK验证 — `poc_thsdk.py`

**目的**：验证THSDK（同花顺C库Python封装）的安装和功能。

**运行命令**：

```bash
python tests/functional_test_case/poc_thsdk.py
```

**测试项一览**：

| 编号 | 测试项 | 游客模式结果 |
|------|--------|------------|
| 1 | 安装验证 | ✅ v1.7.18 |
| 2 | 连接验证 | ✅ 游客模式可用 |
| 3 | 分钟K线 | ❌ "not data" |
| 4 | 日内分时 | ⚠️ 部分成功 |
| 5 | 历史分时快照 | ❌ "not data" |
| 6 | 实时行情 | ❌ 无quote属性 |

**注意**：游客模式限制严重，分钟线数据需正式账号。

### 10.7 pywencai验证 — `poc_pywencai.py`

**目的**：验证pywencai（同花顺问财）的自然语言选股功能。

**运行命令**：

```bash
python tests/functional_test_case/poc_pywencai.py
```

**测试项一览**：

| 编号 | 测试项 | 结果 |
|------|--------|------|
| 1 | 安装验证 | ✅ v0.13.1 |
| 2 | 基础查询(市盈率/个股/涨幅) | ✅ 全部成功 |
| 3 | Cookie认证需求 | ✅ 无Cookie可用 |
| 4 | 条件选股(涨停/换手/破净/ROE) | ✅ 全部成功 |

**注意**：pywencai不支持分钟线数据，仅用于选股和基本面数据。

### 10.8 mootdx分钟线验证 — `poc_mootdx_minute.py`

**目的**：验证mootdx（通达信协议）获取分钟线数据的能力。

**运行命令**：

```bash
python tests/functional_test_case/poc_mootdx_minute.py
```

**测试项一览**：

| 编号 | 测试项 | 结果 | 历史深度 |
|------|--------|------|---------|
| 1 | 1分钟线 | ✅ | 仅5天 |
| 2 | 5分钟线 | ✅ | 约1个月 |
| 3 | 15/30/60分钟线 | ✅ | 更深 |
| 4 | 历史分时 | ❌ | API参数错误 |
| 5 | 1分钟线历史深度 | ✅ | offset>800后数据重复 |
| 6 | 多股票对比 | ✅ | 3只均成功 |

### 10.9 pytdx分钟线验证 — `poc_pytdx_minute.py`

**目的**：验证pytdx获取分钟线数据的能力（原始pytdx库）。

**运行命令**：

```bash
python tests/functional_test_case/poc_pytdx_minute.py
```

**注意**：pytdx原始服务器地址可能已失效，建议优先使用mootdx。

### 10.10 故障排查（同花顺）

#### THSDK "not data"错误

**现象**：所有分钟K线返回"not data"

**原因**：游客模式权限不足

**解决方案**：
1. 使用正式同花顺账号：`THS({'username': 'xxx', 'password': 'xxx'})`
2. 在交易时段（9:30-15:00）运行

#### pywencai Node.js警告

**现象**：`DeprecationWarning: The 'punycode' module is deprecated`

**原因**：pywencai依赖Node.js执行JS，Node.js版本过新

**解决方案**：忽略此警告，不影响功能

#### mootdx PermissionError

**现象**：`PermissionError: [Errno 1] Operation not permitted: '/Users/xxx/.mootdx'`

**解决方案**：
```bash
mkdir -p ~/.mootdx
```

#### 同花顺API 404错误

**现象**：部分period code或年份返回404

**原因**：
1. period code不正确（参考10.4节诊断结果）
2. 该年份无数据（如v6 1分钟线仅当年可用）
3. API不稳定（如v2 period=30）

---

## 11. 推荐运行顺序（含同花顺）

```
步骤1: poc_ths_jsonp_api.py               (JSONP API探测，约2分钟)
步骤2: poc_ths_period_diagnosis.py         (Period Code诊断，约3-5分钟)
步骤3: poc_ths_v6_history.py               (v6历史范围，约1分钟)
步骤4: poc_ths_minute_line.py              (分钟线深度验证，约2分钟)
步骤5: poc_thsdk.py                        (THSDK验证，约30秒)
步骤6: poc_pywencai.py                     (问财验证，约1分钟)
步骤7: poc_mootdx_minute.py                (mootdx分钟线，约30秒)
```
