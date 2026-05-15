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
