# Tasks

## 事项一：建库与版本管理

- [x] Task 1: 初始化Alembic环境与JSON配置
  - [x] 1.1 创建 `config/db_config.json` 数据库连接配置模板(host/port/database/user/password_env/db_version/pool_min/pool_max)
  - [x] 1.2 创建 `config/import_config.json` 导入参数配置模板(batch_size/data_dir/log_dir/periods)
  - [x] 1.3 创建 `config/trade_calendar.json` 交易日历配置(覆盖2021-2023年，每年每月包含交易日日期列表)
  - [x] 1.4 创建最小化 `alembic.ini`（仅含 `script_location = migrations`，Alembic CLI必需）
  - [x] 1.5 创建 `migrations/env.py`（从config/db_config.json读取数据库URL，配置raw SQL模式，不使用target_metadata/autogenerate）
  - [x] 1.6 创建 `migrations/script.py.mako` 模板
  - [x] 1.7 创建 `migrations/versions/` 目录

- [x] Task 2: 创建初始Schema migration脚本
  - [x] 2.1 创建 `migrations/versions/001_initial_schema.py`，仅包含upgrade()函数（禁止downgrade）
  - [x] 2.2 upgrade()创建db_version表(version/description/applied_at)，并在upgrade()末尾插入初始版本记录('001', '初始Schema')
  - [x] 2.3 upgrade()创建stock_info表（含索引）
  - [x] 2.4 upgrade()创建kline_1m分区表（core_code主键+17个月分区+默认分区+索引），core_code=market+code+YYYYMMDDHHmm
  - [x] 2.5 upgrade()创建kline_5m分区表（core_code主键+19个月分区+默认分区+索引），core_code=market+code+YYYYMMDDHHmm
  - [x] 2.6 upgrade()创建import_progress表（含唯一约束）
  - [x] 2.7 upgrade()创建kline_monthly_stats月度统计表（period/month/code/market/row_count/expected_count/diff_pct/checked_at，唯一约束period+month+code+market）

- [x] Task 3: 创建数据库连接池和版本管理基础设施
  - [x] 3.1 创建 `src/` 根目录
  - [x] 3.2 创建 `src/stock_spider/` 顶级包及 `__init__.py`
  - [x] 3.3 创建 `src/stock_spider/data/` 包及 `__init__.py`
  - [x] 3.4 创建 `src/stock_spider/data/storage/` 包及 `__init__.py`
  - [x] 3.5 创建 `src/stock_spider/data/importer/` 包及 `__init__.py`
  - [x] 3.6 创建 `src/stock_spider/utils/` 包及 `__init__.py`
  - [x] 3.7 创建 `config/db_config.json` 数据库连接配置（如Task1未创建）
  - [x] 3.8 创建 `config/import_config.json` 导入参数配置（如Task1未创建）
  - [x] 3.9 实现 `src/stock_spider/data/storage/connection.py` — PostgreSQL连接池(从config/db_config.json读取配置，使用psycopg2.pool.SimpleConnectionPool)
  - [x] 3.10 实现 `src/stock_spider/data/storage/db_manager.py` — DatabaseManager类(ensure_schema/版本检查/自动升级/禁止降级)

- [x] Task 4: 创建数据库建设及升级方案文档
  - [x] 4.1 创建 `sql/database_upgrade_plan.md` — 完整的数据库建设及升级方案文档

- [x] Task 5: 执行初始migration建库
  - [x] 5.1 执行 `alembic upgrade head` 创建6张表(db_version/stock_info/kline_1m/kline_5m/import_progress/kline_monthly_stats)及分区
  - [x] 5.2 验证db_version表已插入初始版本记录('001')
  - [x] 5.3 验证kline_1m/kline_5m主键为(core_code, trade_time)复合主键
  - [x] 5.4 验证kline_monthly_stats表结构正确
  - [x] 5.5 验证表结构（\dt查看表列表，\d+查看分区）

## 事项二：基础工具lib实现

- [x] Task 6: 实现交易日历lib(独立于导入流程)
  - [x] 6.1 创建 `config/trade_calendar.json` 交易日历配置(覆盖2021-2023年，格式：{"2021":{"10":["2021-10-08",...],...},...})
  - [x] 6.2 实现 `src/stock_spider/utils/trade_calendar.py` — TradeCalendar类(get_trading_days_count/get_trading_days/is_trading_day/calc_expected_count)，从config/trade_calendar.json读取数据
  - [x] 6.3 TradeCalendar.calc_expected_count() 精确计算：1m=240×交易日天数, 5m=48×交易日天数
  - [x] 6.4 TradeCalendar 缺失回退：年月不在配置中时使用简化算法(工作日近似)并记录WARNING
  - [x] 6.5 编写单元测试 `tests/unit/test_trade_calendar.py`（覆盖交易日计算、expected_count计算、缺失回退）

- [x] Task 7: 实现核心编码生成工具和市场判断工具
  - [x] 7.1 实现 `src/stock_spider/utils/core_code.py` — generate_core_code(market, code, trade_time) -> str，生成market+code+YYYYMMDDHHmm(20位)
  - [x] 7.2 实现 `src/stock_spider/utils/market_util.py` — classify_stock(code, ktype=None) -> tuple[str|None, bool]
  - [x] 7.3 编写单元测试 `tests/unit/test_core_code.py`（覆盖1m/5m编码、唯一性、边界值）
  - [x] 7.4 编写单元测试 `tests/unit/test_market_util.py`

## 事项三：数据导入lib实现

- [x] Task 8: 实现ZIP文件流式读取器
  - [x] 8.1 实现 `src/stock_spider/data/importer/zip_reader.py` — ZipReader类(list_csv_files/read_csv_stream/get_file_count)
  - [x] 8.2 编写单元测试 `tests/unit/test_zip_reader.py`（使用内存zip fixture）

- [x] Task 9: 实现CSV多格式解析器
  - [x] 9.1 定义数据类 `src/stock_spider/data/importer/models.py` — Kline1mRecord/Kline5mRecord dataclass(含core_code字段)
  - [x] 9.2 实现 `src/stock_spider/data/importer/csv_parser.py` — CsvParser类(parse_1m_row/parse_5m_row/detect_encoding/parse_scientific)，解析时生成core_code
  - [x] 9.3 编写单元测试 `tests/unit/test_csv_parser.py`（覆盖1m/5m格式、科学计数法、中文表头、编码检测、core_code生成）

- [x] Task 10: 实现数据库批量写入器和进度追踪
  - [x] 10.1 实现 `src/stock_spider/data/importer/db_writer.py` — DbWriter类(write_1m_batch/write_5m_batch/flush，execute_values批量5000条，ON CONFLICT(core_code) DO NOTHING)
  - [x] 10.2 实现 `src/stock_spider/data/importer/progress_tracker.py` — ProgressTracker类(start_import/finish_import/fail_import/is_completed/get_pending_zips)
  - [x] 10.3 编写db_writer集成测试 `tests/integration/test_db_writer.py`（需PostgreSQL实例）

- [x] Task 11: 实现月度统计和导入报告
  - [x] 11.1 实现 `src/stock_spider/data/importer/monthly_stats.py` — MonthlyStats类(record_stats/get_stats/validate_monthly_stats)，使用TradeCalendar.calc_expected_count()计算精确expected_count
  - [x] 11.2 实现 `src/stock_spider/data/importer/import_report.py` — ImportReport类(generate_monthly_report/generate_summary_report)，生成单月/全量导入报告，输出到控制台(表格)和日志(JSON)

- [x] Task 12: 实现同花顺数据导入主控
  - [x] 12.1 实现 `src/stock_spider/data/importer/ths_importer.py` — ThsImporter类(import_period/import_month/import_zip/get_import_status)，导入完成后调用MonthlyStats.record_stats()和ImportReport.generate_monthly_report()
  - [x] 12.2 实现 `src/stock_spider/data/importer/__init__.py` — 导出ThsImporter公共接口

- [x] Task 13: 实现数据完整性校验器
  - [x] 13.1 实现 `src/stock_spider/data/importer/data_validator.py` — DataValidator类(validate_row_count/validate_ohlcv_consistency/validate_daily_count/validate_no_zero_volume/validate_partition_integrity/validate_monthly_stats)，使用TradeCalendar获取交易日列表和计算expected_count
  - [x] 13.2 编写单元测试 `tests/unit/test_data_validator.py`（使用mock数据库）

## 事项四：执行脚本(tools)

- [x] Task 14: 创建执行脚本
  - [x] 14.1 创建 `tools/import_ths_kline.py` — 导入主控脚本(argparse: --period/--month/--status)，导入完成后自动生成报告
  - [x] 14.2 创建 `tools/init_db.py` — 数据库初始化脚本(调用DatabaseManager.ensure_schema())
  - [x] 14.3 创建 `tools/check_status.py` — 导入状态查询脚本(支持--stats查询kline_monthly_stats)
  - [x] 14.4 创建 `tools/validate_import.py` — 导入后数据校验脚本(argparse: --period/--month/--all，调用DataValidator)

## 事项五：导入执行与验证

- [ ] Task 15: 执行单月导入验证(小规模)
  - [ ] 15.1 运行 `python tools/import_ths_kline.py --period 1m --month 202302` 导入单月1分钟线
  - [ ] 15.2 检查导入报告输出(控制台+日志)
  - [ ] 15.3 运行 `python tools/validate_import.py --period 1m --month 202302` 执行数据校验
  - [ ] 15.4 检查import_progress表确认status='success'
  - [ ] 15.5 检查kline_monthly_stats表已记录该月统计，expected_count使用TradeCalendar精确计算
  - [ ] 15.6 检查校验报告：行数一致、OHLCV一致性通过、每日条数正常、月度统计差异<5%

- [ ] Task 16: 执行全量1分钟线导入
  - [ ] 16.1 运行 `python tools/import_ths_kline.py --period 1m` 导入全部17个月1分钟线
  - [ ] 16.2 检查全量导入汇总报告
  - [ ] 16.3 运行 `python tools/validate_import.py --period 1m --all` 执行全量数据校验
  - [ ] 16.4 检查所有月份import_progress状态均为success
  - [ ] 16.5 检查kline_monthly_stats所有月份统计完整，expected_count基于交易日历精确计算
  - [ ] 16.6 检查校验报告：所有月份行数一致、OHLCV一致性通过、默认分区无数据

- [ ] Task 17: 执行全量5分钟线导入
  - [ ] 17.1 运行 `python tools/import_ths_kline.py --period 5m` 导入全部19个月5分钟线
  - [ ] 17.2 检查全量导入汇总报告
  - [ ] 17.3 运行 `python tools/validate_import.py --period 5m --all` 执行全量数据校验
  - [ ] 17.4 检查所有月份import_progress状态均为success
  - [ ] 17.5 检查kline_monthly_stats所有月份统计完整
  - [ ] 17.6 检查校验报告：所有月份行数一致、OHLCV一致性通过、默认分区无数据

- [ ] Task 18: 防重复导入验证
  - [ ] 18.1 对已导入的月份再次运行导入命令，验证import_progress跳过status='success'的zip
  - [ ] 18.2 对某月份手动将import_progress状态改为'failed'，重新运行导入，验证ON CONFLICT(core_code) DO NOTHING正确跳过已存在数据
  - [ ] 18.3 验证重复导入后数据库行数不变

# Task Dependencies
- Task 1 → Task 2 (需先配置Alembic环境)
- Task 2 → Task 5 (需先编写migration脚本)
- Task 3 → Task 5 (需先有连接池才能执行migration)
- Task 3 → Task 6, Task 7 (并行，需包结构)
- Task 6 → Task 11 (MonthlyStats需TradeCalendar计算expected_count)
- Task 6 → Task 13 (DataValidator需TradeCalendar获取交易日列表)
- Task 7 → Task 9 (需core_code生成函数)
- Task 7 + Task 8 + Task 9 → Task 10 (需解析器和读取器)
- Task 10 → Task 11 (需数据库写入器)
- Task 10 → Task 12 (需写入器和进度追踪)
- Task 6 + Task 11 + Task 12 → Task 13 (需月度统计、交易日历和主控)
- Task 12 → Task 14 (需主控类)
- Task 13 → Task 14.4 (需DataValidator)
- Task 14 → Task 15 (需执行脚本)
- Task 15 → Task 16 (单月验证通过后再全量导入)
- Task 16 → Task 17 (1分钟线导入完成后再导入5分钟线)
- Task 16 + Task 17 → Task 18 (全量导入完成后验证防重复)
- Task 4 可与 Task 2 并行（文档独立于代码）
