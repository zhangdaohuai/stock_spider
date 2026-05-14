# Tasks

- [x] Task 1: 项目骨架初始化 — 创建 stock_crawler 模块目录结构、conda 环境配置、依赖管理
  - [x] SubTask 1.1: 创建 stock_crawler/ 包目录结构（adapters/、models/、scheduler/、storage/、monitor/、notification/、config/）
  - [x] SubTask 1.2: 创建 requirements.txt 或 pyproject.toml（akshare、baostock、sqlalchemy[asyncio]、asyncpg、loguru、pydantic、apscheduler、aiohttp）
  - [x] SubTask 1.3: 创建 config.json 模板（含 data_sources、schedule、database、notification、monitor、logging 配置段）
  - [x] SubTask 1.4: 创建 conda 环境检查入口

- [x] Task 2: 双数据源适配器 — 实现 AkShare 和 Baostock 统一适配器接口
  - [x] SubTask 2.1: 定义 BaseDataAdapter 抽象基类（get_minute_kline、get_daily_kline、get_realtime_quote、get_bid_ask）
  - [x] SubTask 2.2: 实现 AkShareAdapter（分钟K线 stock_zh_a_hist_min_em、五档盘口 stock_bid_ask_em、港股接口）
  - [x] SubTask 2.3: 实现 BaostockAdapter（分钟K线 query_history_k_data_plus、日线 isST 字段、登录/登出管理）
  - [x] SubTask 2.4: 实现 DataSourceFactory 工厂类（配置驱动切换、降级回退逻辑）

- [x] Task 3: API 边界与频率控制 — 实现各数据源的调用频率限制和账号轮换
  - [x] SubTask 3.1: 实现 RateLimiter 令牌桶限流器（AkShare ≥0.5s/次、Baostock ≥0.2s/次）
  - [x] SubTask 3.2: 实现多账号轮换管理器（JSON 配置驱动、达到限制自动切换）
  - [x] SubTask 3.3: 实现 Baostock 连接池管理（单连接 ≤5000 次查询后重登录）

- [x] Task 4: PostgreSQL 数据存储 — 实现分区表和 ORM 模型
  - [x] SubTask 4.1: 定义 SQLAlchemy 模型（minute_klines、bid_ask_snapshots、stock_marks、index_quotes）
  - [x] SubTask 4.2: 实现按月分区表自动创建（minute_klines 按 trade_time 月分区）
  - [x] SubTask 4.3: 实现数据写入层（批量 upsert、去重逻辑、data_source 标记）
  - [x] SubTask 4.4: 实现数据库迁移脚本（Alembic）

- [x] Task 5: 分钟K线采集引擎 — 实现全量回溯和增量更新逻辑
  - [x] SubTask 5.1: 实现全量回溯调度器（首次启动从 2016-01-01 开始、按股票+时间段分批采集）
  - [x] SubTask 5.2: 实现增量更新调度器（查询数据库最新时间点、仅采集缺失时段）
  - [x] SubTask 5.3: 实现 AkShare 1分钟 + Baostock 5分钟 互补采集逻辑
  - [x] SubTask 5.4: 实现采集断点续传（记录进度到数据库、异常恢复后继续）

- [x] Task 6: ST/退市/港股标记 — 实现股票特化标记采集
  - [x] SubTask 6.1: 实现 Baostock isST 字段采集（日线查询时附带）
  - [x] SubTask 6.2: 实现 AkShare 股票名称 ST 匹配（名称含 ST/*ST/退）
  - [x] SubTask 6.3: 实现港股数据采集（AkShare 港股接口、A+H 股关联标记）

- [x] Task 7: 五档盘口采集 — 实现交易时段实时盘口数据采集
  - [x] SubTask 7.1: 实现交易时段判断（9:30-11:30、13:00-15:00）
  - [x] SubTask 7.2: 实现 AkShare stock_bid_ask_em 定时采集
  - [x] SubTask 7.3: 实现盘口数据批量写入 PostgreSQL

- [x] Task 8: 实盘指数监控 — 实现每分钟上证/深证指数采集
  - [x] SubTask 8.1: 实现东方财富指数数据解析（zs000001、zs399001）
  - [x] SubTask 8.2: 实现每分钟定时调度（仅交易时段运行）
  - [x] SubTask 8.3: 实现指数数据存储和异常告警

- [x] Task 9: 日志与邮件通知 — 实现严格日志分级和 CRITICAL 邮件通知
  - [x] SubTask 9.1: 配置 loguru 五级日志（DEBUG/INFO/WARNING/ERROR/CRITICAL）
  - [x] SubTask 9.2: 实现邮件通知模块（SMTP 配置、CRITICAL 级别触发、含错误详情和时间戳）
  - [x] SubTask 9.3: 实现日志轮转和归档策略

- [x] Task 10: 后台运行与部署 — 实现 macOS/Ubuntu 无人值守长期运行
  - [x] SubTask 10.1: 创建 macOS launchd plist 配置（开机自启、异常重启）
  - [x] SubTask 10.2: 创建 Ubuntu systemd service 配置（开机自启、异常重启）
  - [x] SubTask 10.3: 实现主进程守护逻辑（信号处理、优雅退出、进度持久化）

# Checklist 验证修复任务

- [x] Fix 1: 将 AccountManager 集成到数据采集流程
- [x] Fix 2: 将全量回溯起始日期改为 2016-01-01
- [x] Fix 3: 将 IndexJob、BidAskJob、StMarkJob 注册到 SchedulerEngine
- [x] Fix 4: 生成 Alembic 初始迁移脚本
- [x] Fix 5: 为关键配置项添加必填校验

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 2, Task 3, Task 4]
- [Task 6] depends on [Task 2, Task 4]
- [Task 7] depends on [Task 2, Task 3, Task 4]
- [Task 8] depends on [Task 2, Task 4]
- [Task 9] depends on [Task 1]
- [Task 10] depends on [Task 5, Task 7, Task 8, Task 9]
