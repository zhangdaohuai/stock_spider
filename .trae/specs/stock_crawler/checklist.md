# A股实时数据爬虫 - 验证清单

## 数据源适配器
- [x] AkShare 适配器能正确获取分钟K线数据（stock_zh_a_hist_min_em）
- [x] AkShare 适配器能正确获取五档盘口数据（stock_bid_ask_em）
- [x] AkShare 适配器能正确获取港股数据
- [x] Baostock 适配器能正确获取5分钟K线数据（query_history_k_data_plus）
- [x] Baostock 适配器能正确获取 isST 标记字段
- [x] Baostock 适配器登录/登出管理正常
- [x] 数据源降级回退逻辑正常（主源失败自动切换备源）

## API 边界与频率控制
- [x] AkShare 调用间隔 ≥ 0.5 秒
- [x] Baostock 调用间隔 ≥ 0.2 秒
- [x] 多账号轮换正常工作（达到限制自动切换）
- [x] Baostock 单连接 ≤ 5000 次查询后自动重登录
- [x] 所有账号耗尽时等待冷却并记录 WARNING 日志

## 分钟K线数据采集
- [x] 首次启动从 2016-01-01 全量回溯
- [x] 增量更新仅采集缺失时段数据
- [x] AkShare 1分钟粒度数据正确存储
- [x] Baostock 5分钟粒度数据正确存储
- [x] 断点续传功能正常（异常恢复后继续采集）

## ST/退市/港股标记
- [x] Baostock isST 字段正确采集和存储
- [x] AkShare 股票名称 ST 匹配正常
- [x] 退市风险标记（名称含"退"字）正确识别
- [x] 港股数据采集和 A+H 股关联标记正常

## 五档盘口数据
- [x] 交易时段判断正确（9:30-11:30、13:00-15:00）
- [x] 五档盘口数据字段完整（bid1-5_price/volume、ask1-5_price/volume）
- [x] 盘口数据批量写入 PostgreSQL 正常

## 实盘指数监控
- [x] 上证指数（000001）每分钟采集正常
- [x] 深证指数（399001）每分钟采集正常
- [x] 非交易时段停止采集
- [x] 指数数据存储正确

## PostgreSQL 数据存储
- [x] 分钟K线表按月分区正确创建
- [x] 数据批量 upsert 去重逻辑正常
- [x] data_source 字段正确标记数据来源
- [x] Alembic 迁移脚本可正常执行

## JSON 配置文件
- [x] config.json 包含所有必要配置段（data_sources、schedule、database、notification、monitor、logging）
- [x] 配置文件加载和验证正常
- [x] 配置项缺失时有明确错误提示

## 日志与邮件通知
- [x] loguru 五级日志输出正确（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- [x] CRITICAL 级别日志触发邮件通知
- [x] 邮件包含错误详情和时间戳
- [x] 日志轮转和归档正常

## 后台运行与部署
- [x] macOS launchd plist 配置正确（开机自启、异常重启）
- [x] Ubuntu systemd service 配置正确（开机自启、异常重启）
- [x] 主进程信号处理正常（SIGTERM 优雅退出）
- [x] 进程异常退出后自动恢复并继续采集

## Conda 环境
- [x] 系统启动时检测 conda 环境（agent）
- [x] 非 agent 环境拒绝启动并给出提示
