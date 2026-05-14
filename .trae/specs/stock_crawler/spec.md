# A股实时数据爬虫 Spec

## Why
项目需要分钟级 A 股全量数据采集能力，支持历史回溯至 2016 年、ST/退市风险标记、五档买卖盘口、港股数据，并实现无人值守长期自动运行。

## What Changes
- 新建 `stock_crawler` Python 模块，作为独立数据采集引擎
- 集成 AkShare（实时行情 + 五档盘口 + 港股）和 Baostock（历史K线 + ST标记）双数据源
- 实现 PostgreSQL 分钟级数据存储，含自动建表和分区策略
- 实现 JSON 配置驱动的多账号轮换机制
- 实现无人值守后台运行（macOS launchd / Ubuntu systemd）
- 实现严格日志分级 + 严重错误邮件通知
- 实现实时实盘信息监控（每分钟刷新上证/深证指数）

## Impact
- Affected specs: smart_search（共享 PostgreSQL 实例，新增独立 schema）
- Affected code: 新增 `stock_crawler/` 模块，不影响现有代码

---

## ADDED Requirements

### Requirement: 双数据源适配器
系统 SHALL 提供 AkShare 和 Baostock 双数据源适配器，统一接口抽象，支持配置切换和降级回退。

#### Scenario: 正常数据获取
- **WHEN** 调用数据适配器获取分钟K线
- **THEN** 优先使用 Baostock 获取历史数据，AkShare 获取实时数据

#### Scenario: 数据源降级
- **WHEN** 主数据源请求失败或触发频率限制
- **THEN** 自动切换到备用数据源，记录降级事件日志

### Requirement: 分钟级K线数据采集
系统 SHALL 支持采集 A 股全量分钟级K线数据（1分钟/5分钟），字段包含：时间、开盘价、最高价、最低价、收盘价、成交量、成交额、涨跌幅、振幅、换手率。

#### Scenario: 首次全量回溯
- **WHEN** 首次启动且数据库中无历史数据
- **THEN** 从 2016-01-01 开始回溯所有 A 股分钟K线数据

#### Scenario: 增量更新
- **WHEN** 数据库中已有历史数据
- **THEN** 仅采集最新缺失时段的数据，避免重复请求

#### Scenario: 数据粒度
- **WHEN** 采集实时数据
- **THEN** AkShare 提供 1 分钟粒度，Baostock 提供 5 分钟粒度，两者互补存储

### Requirement: ST/退市风险标记
系统 SHALL 对 ST、*ST、退市风险股票进行标记，在数据采集时自动识别并存储标记信息。

#### Scenario: ST 标记识别
- **WHEN** 采集日K线数据时
- **THEN** 通过 Baostock 的 `isST` 字段获取结构化 ST 标记，同时通过 AkShare 股票名称匹配补充验证

#### Scenario: 退市风险标记
- **WHEN** 股票名称包含"退"字或交易所公告退市
- **THEN** 在数据库中标记 `delist_risk=True`

### Requirement: 港股数据支持
系统 SHALL 支持同时有 A 股和港股的上市公司港股行情数据采集。

#### Scenario: 港股数据采集
- **WHEN** 配置中启用港股数据采集
- **THEN** 通过 AkShare 的港股接口获取对应港股行情数据

### Requirement: 五档买卖盘口数据
系统 SHALL 支持采集 A 股实时五档买卖盘口数据。

#### Scenario: 五档盘口采集
- **WHEN** 交易时段内（9:30-15:00）定时触发
- **THEN** 通过 AkShare `stock_bid_ask_em` 接口获取买卖五档价格和委托量

### Requirement: 多账号轮换
系统 SHALL 支持 JSON 配置文件管理多个数据源账号，自动轮换使用以避免频率限制。

#### Scenario: 账号轮换
- **WHEN** 当前账号达到调用频率上限
- **THEN** 自动切换到下一个可用账号，记录切换事件

#### Scenario: 账号耗尽
- **WHEN** 所有账号均达到频率限制
- **THEN** 等待最短冷却时间后重试，发送 WARNING 级别日志

### Requirement: API 边界管理
系统 SHALL 遵守各数据源的 API 调用边界，包含频率限制、调用次数、数据范围。

#### Scenario: AkShare 频率控制
- **WHEN** 调用 AkShare 接口
- **THEN** 遵守以下限制：
  - 无需账号/Token，免费使用
  - 建议单接口调用间隔 ≥ 0.5 秒
  - 批量获取建议间隔 ≥ 1 秒
  - 无明确日调用次数上限，但高频请求可能被限流

#### Scenario: Baostock 频率控制
- **WHEN** 调用 Baostock 接口
- **THEN** 遵守以下限制：
  - 需先 `bs.login()` 登录，使用完毕后 `bs.logout()`
  - 无需注册账号，匿名登录即可
  - 建议单次查询间隔 ≥ 0.2 秒
  - 单次连接建议不超过 5000 次查询后重新登录
  - 分钟数据单次最多返回 8000 条记录

### Requirement: PostgreSQL 数据存储
系统 SHALL 将所有采集数据存入 PostgreSQL，采用分区表策略优化查询性能。

#### Scenario: 分钟K线表设计
- **WHEN** 存储分钟K线数据
- **THEN** 使用按月分区表，字段包含：stock_code, trade_time, open, high, low, close, volume, amount, change_pct, amplitude, turnover, frequency, data_source

#### Scenario: 五档盘口表设计
- **WHEN** 存储五档盘口数据
- **THEN** 字段包含：stock_code, snapshot_time, bid1-bid5_price, bid1-bid5_volume, ask1-ask5_price, ask1-ask5_volume, limit_up, limit_down, inner_vol, outer_vol

#### Scenario: ST标记表设计
- **WHEN** 存储ST/退市风险标记
- **THEN** 字段包含：stock_code, stock_name, is_st, delist_risk, has_hk, mark_date, data_source

### Requirement: JSON 配置文件
系统 SHALL 使用 JSON 格式配置文件管理所有运行参数。

#### Scenario: 配置文件结构
- **WHEN** 系统启动
- **THEN** 读取 `config.json`，包含以下配置段：
  - `data_sources`: 数据源连接参数和账号列表
  - `schedule`: 采集调度策略（分钟级/日级/实时）
  - `database`: PostgreSQL 连接参数
  - `notification`: 邮件通知配置
  - `monitor`: 实盘监控配置
  - `logging`: 日志级别和输出配置

### Requirement: Conda 环境运行
系统 SHALL 在 Conda 的 `agent` 环境中开发和运行。

#### Scenario: 环境检查
- **WHEN** 系统启动
- **THEN** 检测当前是否在 `agent` conda 环境中运行，否则拒绝启动并提示

### Requirement: 无界面后台运行
系统 SHALL 支持在 macOS 和 Ubuntu 上无界面后台运行，无人值守长期自动运行。

#### Scenario: macOS 后台运行
- **WHEN** 在 macOS 上部署
- **THEN** 通过 launchd plist 配置实现开机自启和异常自动重启

#### Scenario: Ubuntu 后台运行
- **WHEN** 在 Ubuntu 上部署
- **THEN** 通过 systemd service 配置实现开机自启和异常自动重启

#### Scenario: 异常自动恢复
- **WHEN** 进程异常退出
- **THEN** 系统自动重启，从上次中断位置继续采集

### Requirement: 日志分级与邮件通知
系统 SHALL 实现严格日志分级（DEBUG/INFO/WARNING/ERROR/CRITICAL），严重错误通过邮件及时通知。

#### Scenario: 日志分级
- **WHEN** 系统运行中产生日志
- **THEN** 按级别输出：
  - DEBUG: 详细调试信息（仅开发环境）
  - INFO: 正常采集进度、数据统计
  - WARNING: 频率限制触发、账号切换、数据缺失
  - ERROR: 单次采集失败、网络超时、数据库写入失败
  - CRITICAL: 数据源不可用、数据库连接断开、进程异常

#### Scenario: 邮件通知
- **WHEN** 产生 CRITICAL 级别日志
- **THEN** 立即发送邮件通知到配置的收件人列表，包含错误详情和时间戳

### Requirement: 实时实盘信息监控
系统 SHALL 每分钟刷新上证指数和深证指数的实时行情。

#### Scenario: 指数监控
- **WHEN** 交易时段内（9:30-15:00）
- **THEN** 每分钟采集上证指数（000001）和深证指数（399001）的实时数据
- **THEN** 数据来源：东方财富 `https://quote.eastmoney.com/zs000001.html` 和 `https://quote.eastmoney.com/zs399001.html`

#### Scenario: 非交易时段
- **WHEN** 非交易时段
- **THEN** 停止指数采集，等待下一交易日开盘

---

## MODIFIED Requirements
无（全新模块）

## REMOVED Requirements
无
