# 通达信(TDX)历史分钟数据获取研究报告

> **验证日期**：2026-05-18
> **验证环境**：macOS / conda agent / Python 3.12 / mootdx 0.11.4
> **测试股票**：贵州茅台(600519)、五粮液(000858)、海天味业(603288)、平安银行(000001)

---

## 一、核心结论

### ⭐ 重大发现：通达信历史分时数据可回溯至2010年！

| 接口 | 数据类型 | 历史深度 | 每日条数 | 字段 | 推荐度 |
|------|---------|---------|---------|------|--------|
| **minutes(symbol, date)** | 历史分时 | **2010年至今** ✅ | 240条/日 | price, vol | ⭐⭐⭐⭐⭐ |
| **bars(freq=8)** | 1分钟K线 | **仅5天** | 最多800条 | OHLCV | ⭐⭐⭐ |
| **bars(freq=0)** | 5分钟K线 | **约1个月** | 最多800条 | OHLCV | ⭐⭐ |
| **bars(freq=1/2/3)** | 15/30/60分钟K线 | 约2-10个月 | 最多800条 | OHLCV | ⭐⭐ |

### 推荐方案

```
┌──────────────────────────────────────────────────────────────┐
│  历史分钟线获取方案(通达信)                                     │
│                                                                │
│  1分钟线(2010-至今):                                           │
│    → minutes(symbol, date) 逐日获取                           │
│    → 每日240条, 字段: price, vol                              │
│    → 需补算: open/high/low/close (从price序列计算)             │
│                                                                │
│  5分钟线(近期约1个月):                                         │
│    → bars(freq=0) 获取近期5分钟K线                            │
│    → 字段完整: OHLCV                                          │
│                                                                │
│  1分钟线(近期5天):                                             │
│    → bars(freq=8) 获取近期1分钟K线                            │
│    → 字段完整: OHLCV                                          │
│    → 用于验证和补充 minutes() 数据                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、通达信服务器架构

### 2.1 服务器体系

| 服务器类型 | 端口 | 用途 | 状态 |
|-----------|------|------|------|
| 标准行情服务器 | 7709 | A股/指数/基金行情 | ✅ 可用 |
| 扩展行情服务器 | 7727 | 期货/港股/期权 | ❌ 已失效(mootdx警告) |

### 2.2 连接方式

```python
from mootdx.quotes import Quotes

# 标准行情(推荐)
client = Quotes.factory(market="std")

# 扩展行情(已失效)
# client = Quotes.factory(market="ext")
```

### 2.3 连接验证结果

| 项目 | 结果 |
|------|------|
| 标准行情连接 | ✅ 成功 |
| 扩展行情连接 | ⚠️ 可连接但bars返回"市场参数错误" |
| 并发限制 | 无明确限制，建议间隔0.5秒以上 |

---

## 三、分钟K线接口(bars)详细分析

### 3.1 frequency参数映射（已验证）

| freq | 数据类型 | 单次最大条数 | 在线历史深度 | 验证结果 |
|------|---------|------------|------------|---------|
| 0 | 5分钟K线 | 800 | 约1个月 | ✅ |
| 1 | 15分钟K线 | 800 | 约2.5个月 | ✅ |
| 2 | 30分钟K线 | 800 | 约5个月 | ✅ |
| 3 | 60分钟K线 | 800 | 约10个月 | ✅ |
| 4 | 日K线 | 800 | 多年 | ✅ |
| 5 | 周K线 | 800 | 多年 | ✅ |
| 6 | 月K线 | 800 | 多年 | ✅ |
| **7** | **1分钟K线** | 800 | **约5天** | ✅ |
| **8** | **1分钟K线(备选)** | 800 | **约5天** | ✅ |
| 9 | 日K线(备选) | 800 | 多年 | ✅ |
| 10 | 季K线 | 800 | 多年 | ✅ |
| 11 | 年K线 | 800 | 多年 | ✅ |

### 3.2 1分钟K线深度实测

```
offset=0:     2026-05-18 14:51 ~ 15:00 (10条)
offset=100:   2026-05-18 13:11 ~ 15:00 (110条)
offset=200:   2026-05-18 10:01 ~ 15:00 (210条)
offset=400:   2026-05-15 10:41 ~ 15:00 (410条)
offset=600:   2026-05-14 11:21 ~ 15:00 (610条)
offset=800:   2026-05-13 13:41 ~ 15:00 (800条) ← 最大有效offset
offset=1000:  2026-05-13 13:41 ~ 15:00 (800条) ⚠️ 重复！
```

**关键限制**：offset超过800后数据重复，无法翻页获取更早数据。

### 3.3 5分钟K线深度实测

```
offset=0:     2026-05-18 14:15 ~ 15:00 (10条)
offset=800:   2026-04-21 10:55 ~ 15:00 (800条) ← 最大有效
offset=1600:  2026-04-21 10:55 ~ 15:00 (800条) ⚠️ 重复！
```

### 3.4 K线数据字段（已验证）

```
字段: open, close, high, low, vol, amount, year, month, day, hour, minute, datetime, volume
类型: float64, float64, float64, float64, float64, float64, int64, int64, int64, int64, int64, str, float64
```

**注意**：`vol`和`volume`字段相同，`amount`为成交额。14:59的K线数据可能出现异常值（如vol=5.877e-39）。

---

## 四、历史分时接口(minutes)详细分析 ⭐

### 4.1 接口说明

```python
# 当日分时
df = client.minute(symbol="600519")

# 历史分时(关键接口!)
df = client.minutes(symbol="600519", date="20200115")
```

### 4.2 历史深度验证结果

| 年份 | 可用月数 | 测试月数 | 验证结果 |
|------|---------|---------|---------|
| 2010 | 12 | 12 | ✅ 全部可用 |
| 2011 | 12 | 12 | ✅ 全部可用 |
| 2012 | 12 | 12 | ✅ 全部可用 |
| 2020 | 12 | 12 | ✅ 全部可用 |
| 2021 | 11 | 12 | ✅ (1个月15日为周末) |
| 2022 | 12 | 12 | ✅ 全部可用 |
| 2023 | 12 | 12 | ✅ 全部可用 |
| 2024 | 12 | 12 | ✅ 全部可用 |
| 2025 | 12 | 12 | ✅ 全部可用 |
| 2026 | 4 | 5 | ✅ (5月数据截止18日) |

**最早可获取日期**: 2010年1月5日（贵州茅台上市日为2001年，但服务器最早保留到2010年）

### 4.3 分时数据字段（已验证）

```
字段: price, vol, volume
类型: float64, int64, int64
每日条数: 240条(4小时×60分钟)
```

### 4.4 分时数据与1分钟K线的区别

| 对比项 | minutes() 分时 | bars(freq=8) 1分钟K线 |
|--------|---------------|---------------------|
| 历史深度 | **2010年至今** | 仅5天 |
| 字段 | price, vol | open, high, low, close, vol, amount |
| 每日条数 | 240 | 240 |
| 数据粒度 | 每分钟成交价 | 每分钟OHLCV |
| 获取方式 | 逐日查询 | 批量offset |
| 开高低收 | ❌ 仅有price | ✅ 完整OHLCV |

### 4.5 从分时数据补算1分钟K线

```python
# 从minutes()的price序列计算1分钟OHLCV
# 每日240条分时数据，每条代表1分钟
# price字段即为该分钟的成交价
# 但分时数据只有price，没有open/high/low/close

# 补算方法:
# 由于分时数据每条代表1分钟的快照价格
# 实际上该价格就是该分钟的收盘价
# open/high/low需要从更细粒度的tick数据计算(不可得)
# 
# 替代方案: 用前后分钟的价格近似计算
# open = 前一分钟price(或当前price)
# high = max(当前price, 前一分钟price)
# low = min(当前price, 前一分钟price)
# close = 当前price
```

**⚠️ 重要说明**：分时数据的`price`字段是该分钟的最后一笔成交价（即收盘价），无法精确还原开高低。如需精确OHLCV，需结合其他数据源。

---

## 五、通达信本地数据方案

### 5.1 通达信客户端数据文件

| 文件扩展名 | 数据类型 | 说明 |
|-----------|---------|------|
| .day | 日K线 | 二进制格式 |
| .lc1 | 1分钟线 | 二进制格式 |
| .lc5 | 5分钟线 | 二进制格式 |
| .min | 分时数据 | 二进制格式 |

### 5.2 盘后数据下载

通达信客户端支持"盘后数据下载"功能：
- 可下载1分钟线/5分钟线历史数据
- 下载范围：取决于客户端版本和服务器
- 下载后存储在本地二进制文件中

### 5.3 Python读取本地数据

```python
# 使用 pytdx 读取通达信本地数据文件
# 文件路径(Mac): ~/Library/Application Support/tdx/
# 文件路径(Windows): C:\new_tdx\vipdoc\
```

**评估**：本地数据方案依赖通达信客户端安装和手动下载，不适合自动化爬虫场景。

---

## 六、反爬与限制分析

### 6.1 通达信协议特点

| 特点 | 说明 |
|------|------|
| 协议类型 | TCP二进制协议(非HTTP) |
| 认证 | 无需账号/密码 |
| 频率限制 | 无明确限制 |
| IP封锁 | 极少发生 |
| 数据量限制 | 单次最多800条K线 |

### 6.2 注意事项

1. **offset翻页限制**：K线接口offset超过800后数据重复，无法获取更早数据
2. **连接断开**：长时间不活动可能导致连接断开，需要重连
3. **数据异常**：14:59的K线可能出现异常值(vol接近0)
4. **扩展行情失效**：7727端口扩展行情接口已失效
5. **分时字段有限**：minutes()仅返回price和vol，无OHLCV

---

## 七、验证脚本清单

| 脚本 | 功能 | 运行命令 |
|------|------|---------|
| `poc_tdx_minute_depth.py` | 分钟K线深度全量验证 | `python tests/functional_test_case/poc_tdx_minute_depth.py` |
| `poc_tdx_history_minute.py` | 历史分时数据深度验证 | `python tests/functional_test_case/poc_tdx_history_minute.py` |
| `poc_tdx_history_precise.py` | 历史分时精确验证(含交易日校验) | `python tests/functional_test_case/poc_tdx_history_precise.py` |
| `poc_mootdx_minute.py` | mootdx基础功能验证 | `python tests/functional_test_case/poc_mootdx_minute.py` |
| `poc_pytdx_minute.py` | pytdx基础功能验证 | `python tests/functional_test_case/poc_pytdx_minute.py` |

---

## 八、与项目需求的匹配分析

### 8.1 项目需求回顾

- 1分钟线 + 5分钟线混合方案
- 历史数据从2020-01-02开始
- 仅关注沪深主板A股

### 8.2 通达信方案匹配度

| 需求 | 通达信方案 | 匹配度 |
|------|-----------|--------|
| 1分钟线历史(2020+) | minutes()逐日获取, 2010年至今 | ⭐⭐⭐⭐⭐ |
| 5分钟线历史 | bars(freq=0)仅1个月 | ⭐⭐ |
| 1分钟线OHLCV | bars(freq=8)仅5天; minutes()仅price | ⭐⭐⭐ |
| 主板股票支持 | 60xxxx/00xxxx/002xxx | ⭐⭐⭐⭐⭐ |
| 免费无账号 | 无需账号 | ⭐⭐⭐⭐⭐ |

### 8.3 推荐组合方案

```
tdx-api(Docker) + BaoStock + 同花顺v6 API

1分钟线历史(2020-至今):
  → tdx-api /api/kline?type=minute1 (OHLCV完整, 约5个月深度)
  → tdx-api /api/minute?date=YYYYMMDD (逐日分时, 2010年至今, 仅price+vol)
  → 组合: kline获取近期5个月OHLCV, minute补全更早的price数据

5分钟线历史(2020-至今):
  → tdx-api /api/kline?type=minute5 (OHLCV完整, 约2年深度)
  → BaoStock补全更早的5分钟线

1分钟线近期(5个月):
  → tdx-api /api/kline?type=minute1 完整OHLCV
  → 比mootdx直接调用的5天深度大幅提升!

1分钟线当年:
  → 同花顺v6 API period=60
  → 完整OHLCV, 但仅当年3月至今
```

---

## 九、tdx-api 开源项目研究

### 9.1 项目概述

| 项目 | 说明 |
|------|------|
| 仓库 | https://github.com/oficcejo/tdx-api |
| 原作者 | [injoyai/tdx](https://github.com/injoyai/tdx) |
| 语言 | Go 1.22 |
| 部署 | Docker (推荐) |
| 接口数 | 32个RESTful API |
| 许可证 | MIT |

### 9.2 核心优势

1. **1分钟K线深度大幅提升**：`/api/kline?type=minute1` 返回23520条(约5个月)，远超mootdx直接调用的800条(5天)
2. **5分钟K线深度约2年**：`/api/kline?type=minute5` 返回23952条(约499个交易日)
3. **完整OHLCV字段**：K线接口返回open/high/low/close/volume/amount，无需从price近似计算
4. **RESTful API**：HTTP接口，任何语言均可调用，无需直接操作TCP协议
5. **Docker一键部署**：`docker-compose up -d` 即可启动
6. **前复权支持**：日/周/月K线支持同花顺前复权数据
7. **交易日查询**：内置交易日历接口

### 9.3 关键API验证结果

| API | 功能 | 验证结果 | 数据深度 |
|-----|------|---------|---------|
| `/api/health` | 健康检查 | ✅ | - |
| `/api/quote` | 五档行情 | ✅ 4只股票 | 实时 |
| `/api/kline?type=minute1` | 1分钟K线 | ✅ 23520条 | 2025-12-16 ~ 2026-05-18 |
| `/api/kline?type=minute5` | 5分钟K线 | ✅ 23952条 | 2024-04-23 ~ 2026-05-18 |
| `/api/kline?type=minute15` | 15分钟K线 | ✅ 7984条 | 2024-04-23 ~ 2026-05-18 |
| `/api/kline?type=minute30` | 30分钟K线 | ✅ 3992条 | 2024-04-23 ~ 2026-05-18 |
| `/api/kline?type=hour` | 60分钟K线 | ✅ 1996条 | 2024-04-23 ~ 2026-05-18 |
| `/api/kline?type=day` | 日K线 | ✅ 5919条 | 2001-08-27 ~ 2026-05-15 |
| `/api/kline?type=week` | 周K线 | ✅ 1264条 | 2001-08-31 ~ 2026-05-15 |
| `/api/kline?type=month` | 月K线 | ✅ 297条 | 2001-08-31 ~ 2026-05-15 |
| `/api/minute` | 历史分时 | ✅ 240条/日 | 2010年至今(逐日) |
| `/api/trade` | 当日分时成交 | ✅ 1800条 | 当日 |
| `/api/trade-history` | 历史分时成交 | ✅ | 逐日,最多2000条/次 |
| `/api/minute-trade-all` | 全天分时成交 | ✅ 4550条 | 逐日 |
| `/api/codes` | 股票列表 | ✅ 5522只 | 全市场 |
| `/api/search` | 搜索股票 | ✅ | 模糊搜索 |
| `/api/index` | 指数数据 | ✅ | 上证/深证/沪深300 |
| `/api/workday` | 交易日查询 | ✅ | 含前后交易日 |
| `/api/workday/range` | 交易日范围 | ✅ 8天/半月 | 日期范围 |
| `/api/batch-quote` | 批量行情 | ✅ | 多只股票 |
| `/api/stock-info` | 综合信息 | ✅ | 行情+K线+分时 |
| `/api/etf` | ETF列表 | ✅ | 全市场ETF |
| `/api/income` | 收益分析 | ✅ | 区间收益率 |
| `/api/market-count` | 市场统计 | ✅ | 50661只证券 |
| `/api/kline-all` | 全量K线 | ❌ 返回空 | 需先执行pull-kline任务 |
| `/api/kline-all/tdx` | TDX源K线 | ❌ 返回空 | 同上 |
| `/api/kline-all/ths` | THS源K线 | ❌ 返回空 | 同上 |
| `/api/trade-history/full` | 上市以来成交 | ❌ 返回空 | 可能需长时间等待 |
| `/api/tasks/pull-kline` | K线入库任务 | ✅ | tables参数需用"minute"而非"minute1" |

### 9.4 关键发现：1分钟K线深度对比

| 方案 | 1分钟K线深度 | 字段 | 获取方式 |
|------|------------|------|---------|
| **tdx-api /api/kline** | **5个月(98天×240=23520条)** | **完整OHLCV** | HTTP GET |
| mootdx bars(freq=8) | 5天(800条) | 完整OHLCV | TCP直连 |
| tdx-api /api/minute | 2010年至今 | 仅price+vol | HTTP GET逐日 |
| mootdx minutes() | 2010年至今 | 仅price+vol | TCP直连逐日 |

**tdx-api的/api/kline接口通过Go实现的分页拼接机制，将单次800条的限制突破为23520条！**

### 9.5 Go源码关键实现

```go
// client.go 中的关键方法

// GetMinute 获取分时数据(实际调用GetHistoryMinute)
func (this *Client) GetMinute(code string) (*protocol.MinuteResp, error) {
    return this.GetHistoryMinute(time.Now().Format("20060102"), code)
}

// GetHistoryMinute 获取历史分时数据
func (this *Client) GetHistoryMinute(date, code string) (*protocol.MinuteResp, error) {
    // 单次请求即可获取240条(全天)
}

// GetHistoryMinuteTrade 获取历史分时交易
// 历史数据只能查到20000609
func (this *Client) GetHistoryMinuteTrade(date, code string, start, count uint16) (*protocol.TradeResp, error) {
    // 单次最多2000条, 通过分页拼接获取全天
}

// GetKlineXXXAll 系列方法通过分页拼接获取全量K线
// 每次请求800条, 通过多次请求拼接突破单次限制
```

### 9.6 数据单位说明

| 字段 | 单位 | 换算 |
|------|------|------|
| 价格(Open/High/Low/Close) | 厘 | 实际价格 = 返回值 / 1000 |
| 成交量(Volume) | 手 | 实际股数 = 返回值 × 100 |
| 成交额(Amount) | 厘 | 实际金额 = 返回值 / 1000 |

### 9.7 部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/oficcejo/tdx-api.git
cd tdx-api

# 2. Docker构建并启动
docker-compose up -d --build

# 3. 验证服务
curl http://localhost:8080/api/health

# 4. 测试1分钟K线
curl "http://localhost:8080/api/kline?code=600519&type=minute1"
```

### 9.8 已知问题

| 问题 | 说明 | 解决方案 |
|------|------|---------|
| kline-all返回空 | 需先执行pull-kline任务入库 | 使用/api/kline替代(直接从TDX服务器获取) |
| trade-history/full返回空 | 可能需要长时间等待 | 使用/api/trade-history逐日获取 |
| pull-kline的tables参数 | 不支持"minute1"，需用"minute" | 参考API文档的tables列表 |
| workday/range返回空workdays | count字段正确但List为空 | 使用count字段即可 |
| 市场统计数字偏大 | 包含指数/基金/债券等 | 使用/api/codes过滤股票 |
| Docker代理问题 | 构建时可能遇到代理错误 | 设置build-arg http_proxy="" |

---

## 十、验证脚本清单

| 脚本 | 功能 | 运行命令 |
|------|------|---------|
| `poc_tdx_minute_depth.py` | 分钟K线深度全量验证(mootdx) | `python tests/functional_test_case/poc_tdx_minute_depth.py` |
| `poc_tdx_history_minute.py` | 历史分时数据深度验证(mootdx) | `python tests/functional_test_case/poc_tdx_history_minute.py` |
| `poc_tdx_history_precise.py` | 历史分时精确验证(含交易日校验) | `python tests/functional_test_case/poc_tdx_history_precise.py` |
| `poc_tdx_api_full.py` | tdx-api全量API验证(24项) | `python tests/functional_test_case/poc_tdx_api_full.py` |
| `poc_tdx_api_deep.py` | tdx-api关键接口深度验证(8项) | `python tests/functional_test_case/poc_tdx_api_deep.py` |
| `poc_mootdx_minute.py` | mootdx基础功能验证 | `python tests/functional_test_case/poc_mootdx_minute.py` |
| `poc_pytdx_minute.py` | pytdx基础功能验证 | `python tests/functional_test_case/poc_pytdx_minute.py` |

---

## 十一、风险与注意事项

### 11.1 数据质量风险

1. **分时数据无OHLCV**：minutes()仅返回price和vol，需近似计算开高低
2. **K线数据异常值**：14:59的K线vol可能接近0
3. **offset翻页失效**：超过800后数据重复，无法获取更早K线
4. **非交易日返回空**：minutes()在非交易日返回None，需配合交易日历

### 11.2 技术风险

1. **扩展行情失效**：7727端口接口已失效，未来标准行情也可能变更
2. **连接不稳定**：长时间不活动可能断开，需实现重连机制
3. **mootdx维护状态**：pytdx已归档，mootdx更新不频繁

### 11.3 法律风险

- 通达信协议为逆向工程产物，非官方公开API
- 商业使用可能违反通达信服务条款
- 建议仅用于个人研究
