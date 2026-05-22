# pytdx / mootdx 分钟线数据能力与限制研究报告

> 研究日期: 2026-05-18
> 研究员: Res_Charlie (技术研究员)
> 状态: 已完成 PoC 验证

---

## 一、研究摘要

本研究深入调查了 pytdx 和 mootdx 两个 Python 库获取 A 股历史分钟线数据的能力与限制，并通过 PoC 脚本进行了实际验证。核心发现如下：

| 数据类型 | 在线服务器保留深度 | 翻页能否获取更早数据 | 数据重复问题 |
|---------|-------------------|-------------------|------------|
| 1分钟线 | **约5个月(约100个交易日)** | 能，通过 start 参数翻页 | 无重复，翻页数据连续 |
| 5分钟线 | **约13个月(约260个交易日)** | 能，通过 start 参数翻页 | 无重复，翻页数据连续 |
| 历史分时数据 | **约2个月(不稳定)** | 不适用(按日期查询) | 部分日期缺失 |

**关键结论**: pytdx 的 `get_security_bars` 配合翻页机制(start参数)可以获取在线服务器上存储的全部分钟线数据，1分钟线约5个月、5分钟线约13个月。超出此范围的历史数据需要依赖通达信本地数据文件或其他数据源。

---

## 二、pytdx 库详细分析

### 2.1 基本信息

- **GitHub**: https://github.com/rainx/pytdx (已归档，不再维护)
- **当前版本**: 1.72 (pip install pytdx)
- **许可证**: MIT
- **兼容性**: Python 2.7+ / 3.6+, Windows / macOS / Linux
- **依赖**: 纯 Python 实现，无 C 扩展
- **已知问题**: 与 tushare 内置的 pytdx 版本冲突，需重新安装

### 2.2 TdxHq_API (标准行情) 核心方法

| 方法 | 参数 | 说明 | 分钟线相关 |
|------|------|------|-----------|
| `connect(ip, port)` | IP, 端口 | 连接标准行情服务器 | 端口通常7709 |
| `disconnect()` | - | 断开连接 | - |
| `get_security_bars(category, market, code, start, count)` | K线类型, 市场, 代码, 起始位置, 数量 | **获取K线数据(核心方法)** | category=7/8为1分钟, 0为5分钟 |
| `get_index_bars(category, market, code, start, count)` | 同上 | 获取指数K线 | 同上 |
| `get_minute_time_data(market, code)` | 市场, 代码 | 获取当日分时图数据 | 仅当日 |
| `get_history_minute_time_data(market, code, date)` | 市场, 代码, 日期(YYYYMMDD) | **获取历史分时数据** | 按日查询，返回240条 |
| `get_security_quotes(market_code_list)` | [(市场,代码),...] | 获取实时行情 | - |
| `get_transaction_data(market, code, start, count)` | 市场, 代码, 起始, 数量 | 获取分笔成交 | - |
| `get_security_count(market)` | 市场 | 获取市场股票数量 | - |
| `get_security_list(market, start)` | 市场, 起始位置 | 获取股票列表 | - |
| `get_xdxr_info(market, code)` | 市场, 代码 | 获取除权除息信息 | - |
| `get_finance_info(market, code)` | 市场, 代码 | 获取财务信息 | - |
| `get_and_parse_block_info(block_file)` | 板块文件名 | 获取板块信息 | - |

### 2.3 category 参数映射 (K线类型)

| 值 | 含义 | 备注 |
|----|------|------|
| 0 | 5分钟K线 | 在线保留约13个月 |
| 1 | 15分钟K线 | - |
| 2 | 30分钟K线 | - |
| 3 | 1小时K线 | - |
| 4 | 日K线 | - |
| 5 | 周K线 | - |
| 6 | 月K线 | - |
| 7 | 1分钟K线 | 在线保留约5个月 |
| 8 | 1分钟K线 | 与7返回相同数据 |
| 9 | 日K线 | 与4相同 |
| 10 | 季K线 | - |
| 11 | 年K线 | - |

### 2.4 get_security_bars 关键参数详解

```python
api.get_security_bars(category, market, code, start, count)
```

- **category**: K线类型(见上表)
- **market**: 0=深圳, 1=上海
- **code**: 6位证券代码字符串
- **start**: 起始位置，0表示最新数据，递增表示往更早的数据翻页
- **count**: 单次请求数量，**最大值800**

**返回值**: `list[OrderedDict]`，每个元素包含:
- `datetime`: 时间字符串 (如 "2026-05-18 14:30")
- `open`, `close`, `high`, `low`: OHLC 价格
- `vol`: 成交量
- `amount`: 成交额
- `year`, `month`, `day`, `hour`, `minute`: 时间分量

**重要特性**:
- 返回数据按时间**倒序**排列(最新在前)
- start 参数支持翻页，每次增加800即可获取更早的数据
- 翻页数据**无重复**，各页之间时间连续

### 2.5 PoC 实测结果

#### 1分钟线 (category=7) 深度测试

| start | 获取条数 | 时间范围 |
|-------|---------|---------|
| 0 | 800 | 2026-05-18 14:30 ~ 2026-05-13 13:11 |
| 800 | 800 | 2026-05-13 13:10 ~ 2026-05-08 10:21 |
| ... | ... | ... |
| 22400 | 610 | 2025-12-22 13:10 ~ 2025-12-18 09:31 |

**总计**: 约23010条，时间跨度从 2025-12-18 到 2026-05-18，约**5个月(约100个交易日)**

#### 5分钟线 (category=0) 深度测试

| start | 获取条数 | 时间范围 |
|-------|---------|---------|
| 0 | 800 | 2026-05-18 14:30 ~ 2026-04-21 10:25 |
| ... | ... | ... |
| 23200 | 554 | 2024-05-17 13:10 ~ 2024-04-29 09:35 |

**总计**: 约23754条，时间跨度从 2024-04-29 到 2026-05-18，约**13个月(约260个交易日)**

#### get_history_minute_time_data 范围测试

| 距今天数 | 日期 | 结果 |
|---------|------|------|
| 30 | 20260418 | 无数据(周末) |
| 45 | 20260403 | 有数据(240条) |
| 60 | 20260319 | 有数据(240条) |
| 75 | 20260304 | 有数据(240条) |
| 90 | 20260217 | 无数据 |
| 150 | 20251219 | 有数据(240条) |
| 180 | 20251119 | 有数据(240条) |
| 200 | 20251030 | 有数据(240条) |
| 365 | 20250518 | 无数据 |

**结论**: `get_history_minute_time_data` 的可用性不稳定，部分交易日可能返回空数据。该接口按日期查询，每天返回240条(4小时 x 60分钟)。实际可用范围大约2个月，但存在间断。

### 2.6 连接池与断线重连

pytdx 支持以下稳定性机制:

1. **心跳包**: `TdxHq_API(heartbeat=True)` - 自动发送心跳包保持连接
2. **多线程安全**: `TdxHq_API(multithread=True)` - 线程安全模式
3. **连接池(试验性)**: `pytdx.pool` 模块提供 failover 支持
4. **自动选最优IP**: `select_best_ip()` 工具函数

### 2.7 已知 Bug 与限制

1. **tushare 冲突**: tushare 内置旧版 pytdx，导致 `'bool' object does not support the context manager protocol` 错误。需 `pip uninstall pytdx && pip install pytdx` 重新安装
2. **项目已归档**: GitHub 仓库已归档，不再接受 PR 和 issue
3. **服务器IP变动**: 内置的服务器列表部分已失效，需使用 `select_best_ip()` 动态获取
4. **单次请求上限800条**: 需要翻页获取更多数据
5. **非股票品种价格异常**: 可转债等品种返回价格为实际价格x10

---

## 三、mootdx 库详细分析

### 3.1 基本信息

- **GitHub**: https://github.com/mootdx/mootdx
- **当前版本**: 0.11.7 (最新 0.10.11, pip 安装版本可能更新)
- **许可证**: MIT
- **兼容性**: Python 3.5+, Windows / macOS / Linux
- **依赖**: pytdx >= 1.67
- **维护状态**: 较活跃，持续更新

### 3.2 Quotes 类 (在线行情) 核心方法

```python
from mootdx.quotes import Quotes
client = Quotes.factory(market='std', bestip=True, timeout=15)
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `quotes(symbol)` | 股票代码 | 获取实时行情 |
| `bars(symbol, frequency, offset)` | 代码, 周期, 数量 | **获取K线数据** |
| `index(symbol, frequency)` | 代码, 周期 | 获取指数K线 |
| `minute(symbol)` | 代码 | 获取分时数据 |
| `transaction(symbol, offset)` | 代码, 数量 | 获取分笔成交 |
| `close()` | - | 关闭连接 |

### 3.3 frequency 参数映射

| 值 | 含义 | 备注 |
|----|------|------|
| 0 | 5分钟线 | - |
| 1 | 15分钟线 | - |
| 2 | 30分钟线 | - |
| 3 | 1小时线 | - |
| 4 | 日线 | - |
| 5 | 周线 | - |
| 6 | 月线 | - |
| 7 | 1分钟线 | - |
| 8 | 1分钟线 | 与7相同 |
| 9 | 日线 | 与4相同 |
| 10 | 季线 | - |
| 11 | 年线 | - |

### 3.4 offset 参数与翻页机制

mootdx 的 `bars()` 方法中:
- **offset**: 控制返回的数据条数，不是翻页偏移量
- 底层仍调用 pytdx 的 `get_security_bars`，start=0, count=offset
- **不支持直接翻页**，如需获取更早数据，需直接使用 pytdx 的 start 参数

### 3.5 Reader 类 (本地数据读取)

```python
from mootdx.reader import Reader
reader = Reader.factory(market='std', tdxdir='C:/new_tdx')
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `daily(symbol)` | 代码 | 读取日线(.day) |
| `minute(symbol, suffix)` | 代码, 分钟类型 | 读取分钟线(.lc1/.lc5) |
| `fzline(symbol)` | 代码 | 读取分时线 |
| `block_new(name, symbol)` | 名称, 代码列表 | 管理自定义板块 |

**suffix 参数**: 1=1分钟, 5=5分钟, 15=15分钟, 30=30分钟, 60=60分钟

### 3.6 mootdx vs pytdx 对比

| 特性 | pytdx | mootdx |
|------|-------|--------|
| 底层实现 | 原生实现 | 封装 pytdx |
| API 易用性 | 较底层 | 更友好 |
| 翻页支持 | 直接支持(start参数) | 不直接支持 |
| 本地数据读取 | TdxMinBarReader | Reader.minute() |
| 自动选最优IP | select_best_ip() | bestip=True |
| 心跳包 | heartbeat=True | heartbeat=True |
| 维护状态 | 已归档 | 较活跃 |
| 除权处理 | 无 | to_adjust() |
| 缓存机制 | 无 | pandas_cache |
| 财务数据 | get_finance_info | Affair 模块 |

---

## 四、分钟线数据深度问题深度分析

### 4.1 在线服务器数据保留深度 (PoC 实测)

| 数据类型 | 在线保留深度 | 对应条数 | 翻页后总深度 |
|---------|------------|---------|------------|
| 1分钟线 | 约5个月 | ~23000条 | 与单次相同(翻页不增加深度) |
| 5分钟线 | 约13个月 | ~24000条 | 与单次相同(翻页不增加深度) |
| 历史分时 | 约2个月(不稳定) | 每天240条 | 不适用 |

**重要澄清**: 翻页(start参数)不是增加数据深度，而是**访问服务器上已有的全部数据**。单次请求最多800条，但服务器实际存储了更多数据，需要通过翻页来获取全部。

### 4.2 翻页机制详解

```
start=0:     获取最新的800条
start=800:   获取第801~1600条
start=1600:  获取第1601~2400条
...
```

- 数据按时间倒序排列(最新在前)
- 翻页数据**无重复**，各页时间连续
- 当返回数据不足800条时，表示已到达服务器存储的最早数据
- **不存在 offset>800 后数据重复的问题** (实测验证)

### 4.3 get_history_minute_time_data 的特殊性

该接口按日期查询历史分时数据，每天返回240条(9:30-11:30, 13:00-15:00)。

**实测发现**:
- 可用性不稳定，部分交易日返回空数据
- 可用范围约2个月，但存在间断
- 60天前的数据可能获取到，90天前的数据通常获取不到
- 150-200天前的数据偶尔能获取到(可能是服务器缓存差异)

### 4.4 通达信本地数据下载限制

| 数据类型 | 盘后下载限制 | 文件路径 | 文件格式 |
|---------|------------|---------|---------|
| 1分钟线 | 最近100天 | vipdoc/[sh\|sz]/minline/*.lc1 | 二进制 |
| 5分钟线 | 最近500天 | vipdoc/[sh\|sz]/fzline/*.lc5 | 二进制 |
| 日线 | 无明确限制 | vipdoc/[sh\|sz]/lday/*.day | 二进制 |

**注意**: 通达信盘中不支持下载分钟数据，需盘后下载。

---

## 五、替代方案分析

### 5.1 通达信本地数据导入方案

**原理**: 利用通达信客户端的"盘后数据下载"功能将分钟线数据保存到本地，再用 pytdx/mootdx 的 Reader 模块解析。

**优点**:
- 数据完整性好，与通达信官方一致
- 无频率限制
- 支持1分钟线(100天)和5分钟线(500天)

**缺点**:
- 需要 Windows 系统运行通达信客户端
- 盘中无法下载分钟数据
- 1分钟线仅100天，5分钟线仅500天
- 需要定期手动下载

**代码示例**:
```python
from pytdx.reader import TdxLCMinBarReader
reader = TdxLCMinBarReader()
df = reader.get_df("C:/new_tdx/vipdoc/sz/minline/sz000001.lc1")
```

### 5.2 通达信 VIP 服务器 (Level-2 行情)

**原理**: 开通通达信 Level-2 行情服务(付费)，获取更详细的行情数据。

**数据内容**:
- 十档买卖盘
- 逐笔成交
- 买卖队列
- 大单统计

**限制**:
- **不提供更深的分钟线历史数据**，分钟线深度与免费版相同
- 需要付费(通常通过券商开通)
- 数据量大，本地存储压力大

**结论**: VIP 服务器主要提供实时数据的精细化，**不能解决分钟线历史深度问题**。

### 5.3 通达信数据补充工具

**原理**: 使用第三方工具将 CSV 格式的历史分钟线数据写入通达信本地数据文件。

**工具**: 通达信1分钟/5分钟数据补充工具 (sigmagu.com)

**特点**:
- 历史数据可从2004年开始补充
- 需要提供 CSV 格式的源数据
- 数据导入耗时较长(1分钟数据每年约500MB)
- 导入后可通过 pytdx Reader 读取

**限制**:
- 需要先获取 CSV 格式的历史数据源
- 仅适用于 Windows 系统

### 5.4 其他基于 TDX 协议的开源项目

| 项目 | 地址 | 特点 |
|------|------|------|
| pytdx2 | https://github.com/liewhite/pytdx2 | pytdx 的 TypeScript/Python 重写版 |
| tdx-api | https://github.com/oficcejo/tdx-api | 提供 REST API 接口封装 |
| QUANTAXIS | https://github.com/yutiansut/QUANTAXIS | 完整量化平台，内置 pytdx 封装 |
| TdxQuant | 通达信官方 Python 插件 | 需要通达信客户端，支持1分钟线 |

### 5.5 其他数据源方案

| 数据源 | 分钟线深度 | 费用 | 备注 |
|--------|----------|------|------|
| Baostock | 5分钟线约5年 | 免费 | 1分钟线不支持 |
| AkShare | 取决于数据源 | 免费 | 部分接口有分钟线 |
| Tushare | 1分钟线需积分 | 积分制 | 1分钟线需5000积分 |
| 聚宽(JoinQuant) | 1分钟线 | 付费 | 数据质量好 |
| RiceQuant | 1分钟线 | 付费 | 专业量化平台 |
| Wind | 1分钟线 | 付费(昂贵) | 机构级数据 |

---

## 六、综合建议

### 6.1 针对本项目(基础实时数据爬虫)的建议

**场景**: A股分钟级全量数据采集

**推荐方案**: **pytdx + 翻页机制 + 定时采集**

1. **实时采集**: 使用 pytdx `get_security_bars(category=7)` 每日收盘后采集当天1分钟线
2. **历史回补**: 使用翻页机制(start参数)获取服务器上保留的约5个月历史1分钟线
3. **更深历史**: 如需超过5个月的1分钟线，需结合以下方案:
   - 方案A: 在 Windows 服务器上运行通达信客户端，定期下载本地数据
   - 方案B: 使用 Baostock 获取5分钟线(约5年深度)作为补充
   - 方案C: 使用 Tushare (需积分) 获取1分钟线

### 6.2 技术选型建议

| 需求 | 推荐方案 | 理由 |
|------|---------|------|
| 实时1分钟线 | pytdx get_security_bars(7) | 直接、高效、免费 |
| 历史1分钟线(5个月内) | pytdx 翻页获取 | 无重复、数据连续 |
| 历史1分钟线(超5个月) | 通达信本地数据 + Reader | 最可靠的历史数据源 |
| 5分钟线 | pytdx get_security_bars(0) | 保留约13个月 |
| 更友好API | mootdx | 封装更好，但翻页需回退 pytdx |

### 6.3 风险提示

1. **pytdx 已归档**: 不再维护，未来可能因通达信协议变更而失效
2. **服务器可用性**: 通达信行情服务器可能随时变更IP或端口
3. **频率限制**: 请求过于频繁可能被封IP，建议间隔0.3秒以上
4. **数据完整性**: 在线服务器的分钟线数据可能因停牌等原因存在缺失
5. **合规风险**: pytdx 基于逆向工程，使用需注意合规性

---

## 七、PoC 代码

PoC 验证脚本位于:
- [poc_tdx_minute.py](file:///Users/zhangdaohuai/Documents/work/agents/codes/stock_spider/poc_tdx_minute.py) - 完整验证脚本
- [poc_depth_test.py](file:///Users/zhangdaohuai/Documents/work/agents/codes/stock_spider/poc_depth_test.py) - 深度翻页测试脚本

**注意**: 这些 PoC 脚本仅用于技术研究验证，不应合入主代码库。

---

## 八、参考资源

1. pytdx 官方文档: https://pytdx-docs.readthedocs.io/zh-cn/latest/
2. pytdx GitHub: https://github.com/rainx/pytdx
3. mootdx GitHub: https://github.com/mootdx/mootdx
4. mootdx 文档: https://mootdx.readthedocs.io
5. 通达信数据目录结构: 雪球文章 (2024-01-25)
6. 通达信分钟数据补充工具: https://www.sigmagu.com/resource/48
