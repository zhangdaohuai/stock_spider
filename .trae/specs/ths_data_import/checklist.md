## 事项一：建库与版本管理

- [ ] config/db_config.json 数据库连接配置创建完成(host/port/database/user/password_env/db_version/pool_min/pool_max)
- [ ] config/import_config.json 导入参数配置创建完成(batch_size/data_dir/log_dir/periods)
- [ ] config/trade_calendar.json 交易日历配置创建完成(覆盖2021-2023年，每年每月包含交易日日期列表)
- [ ] alembic.ini 仅含最小化配置(script_location = migrations)
- [ ] migrations/env.py 从config/db_config.json读取数据库URL，配置raw SQL模式，不使用target_metadata/autogenerate
- [ ] migrations/versions/001_initial_schema.py 仅包含upgrade()函数，不包含downgrade()（禁止降级）
- [ ] upgrade()创建db_version表(version/description/applied_at)
- [ ] upgrade()创建stock_info表（含索引idx_stock_info_type/idx_stock_info_name）
- [ ] upgrade()创建kline_1m分区表（core_code主键+17个月分区+默认分区+索引），core_code=market+code+YYYYMMDDHHmm
- [ ] upgrade()创建kline_5m分区表（core_code主键+19个月分区+默认分区+索引），core_code=market+code+YYYYMMDDHHmm
- [ ] upgrade()创建import_progress表（含uk_import_progress唯一约束）
- [ ] upgrade()创建kline_monthly_stats表（period/month/code/market/row_count/expected_count/diff_pct/checked_at，唯一约束period+month+code+market）
- [ ] upgrade()末尾在db_version表插入初始版本记录('001', '初始Schema')
- [ ] src/ 根目录及stock_spider包结构创建完成(data/storage, data/importer, utils)
- [ ] config/db_config.json 数据库连接配置模板创建完成
- [ ] src/stock_spider/data/storage/connection.py PostgreSQL连接池实现完成(从config/db_config.json读取配置，SimpleConnectionPool)
- [ ] src/stock_spider/data/storage/db_manager.py DatabaseManager实现完成(ensure_schema/版本检查/自动升级/禁止降级)
- [ ] DatabaseManager.ensure_schema() 能读取config/db_config.json的db_version并与数据库db_version表比对
- [ ] DatabaseManager 配置版本>数据库版本时自动执行alembic upgrade
- [ ] DatabaseManager 配置版本<=数据库版本时跳过升级
- [ ] DatabaseManager 配置版本<数据库版本时抛出异常终止（禁止降级）
- [ ] DatabaseManager 数据库不存在时(db_version表不存在)自动执行alembic upgrade head
- [ ] sql/database_upgrade_plan.md 数据库建设及升级完整方案文档创建完成
- [ ] 执行 `alembic upgrade head` 成功创建6张表(db_version/stock_info/kline_1m/kline_5m/import_progress/kline_monthly_stats)及分区
- [ ] 验证db_version表已插入初始版本记录('001')
- [ ] 验证kline_1m/kline_5m主键为core_code字段
- [ ] 验证kline_monthly_stats表结构正确
- [ ] 验证表结构正确（\dt查看表列表，\d+查看分区）

## 事项二：基础工具lib实现

- [ ] config/trade_calendar.json 交易日历配置覆盖2021-2023年，格式正确({"2021":{"10":["2021-10-08",...],...},...})
- [ ] src/stock_spider/utils/trade_calendar.py TradeCalendar类实现完成(get_trading_days_count/get_trading_days/is_trading_day/calc_expected_count)
- [ ] TradeCalendar 从config/trade_calendar.json读取交易日历数据
- [ ] TradeCalendar.get_trading_days_count(year, month) 返回该月交易日天数
- [ ] TradeCalendar.get_trading_days(year, month) 返回该月交易日date列表
- [ ] TradeCalendar.is_trading_day(date) 判断指定日期是否为交易日
- [ ] TradeCalendar.calc_expected_count('1m', year, month) 返回 240 × 交易日天数
- [ ] TradeCalendar.calc_expected_count('5m', year, month) 返回 48 × 交易日天数
- [ ] TradeCalendar 缺失回退：年月不在配置中时使用简化算法(工作日近似)并记录WARNING
- [ ] TradeCalendar 单元测试通过(覆盖交易日计算、expected_count计算、缺失回退)
- [ ] src/stock_spider/utils/core_code.py generate_core_code(market, code, trade_time)正确生成20位核心编码(market(2)+code(6)+YYYYMMDDHHmm(12))
- [ ] core_code生成确定性：相同输入始终产生相同输出
- [ ] core_code生成唯一性：不同股票或不同时间产生不同core_code
- [ ] core_code 单元测试通过(覆盖1m/5m编码、唯一性、边界值)
- [ ] src/stock_spider/utils/market_util.py 正确判断主板/排除非主板(60xxxx→SH, 00xxxx/002xxx→SZ, 其余排除)
- [ ] market_util 单元测试通过

## 事项三：数据导入lib实现

- [ ] src/stock_spider/data/importer/zip_reader.py 能从zip流式读取CSV，GBK文件名正确解码
- [ ] ZipReader 单元测试通过(使用内存zip fixture)
- [ ] src/stock_spider/data/importer/models.py Kline1mRecord/Kline5mRecord数据类定义完成(含core_code字段)
- [ ] src/stock_spider/data/importer/csv_parser.py 能解析1分钟线9字段CSV(code,tdate,open,close,high,low,cjl,cje,cjjj)
- [ ] CsvParser 解析时自动调用generate_core_code()生成core_code
- [ ] CsvParser 能解析5分钟线11-12字段CSV(含name,ktype,[fq],hsl)
- [ ] CsvParser 能正确解析科学计数法(2.98901E7→29890100.00)
- [ ] CsvParser 能自动检测编码(utf-8/gbk/gb18030/latin1)
- [ ] CsvParser 能跳过中文表头行
- [ ] CsvParser 单元测试通过(覆盖两种格式、科学计数法、中文表头、编码检测、core_code生成)
- [ ] src/stock_spider/data/importer/db_writer.py 使用execute_values批量写入，每批5000条
- [ ] DbWriter 使用ON CONFLICT(core_code) DO NOTHING跳过重复数据
- [ ] src/stock_spider/data/importer/progress_tracker.py 能记录/查询/更新import_progress表
- [ ] ProgressTracker 断点续传：跳过status=success的zip文件
- [ ] src/stock_spider/data/importer/monthly_stats.py MonthlyStats实现完成(record_stats/get_stats/validate_monthly_stats)
- [ ] MonthlyStats.record_stats() 使用TradeCalendar.calc_expected_count()计算精确expected_count
- [ ] MonthlyStats.validate_monthly_stats() 比对row_count与expected_count，diff_pct>5%告警
- [ ] src/stock_spider/data/importer/import_report.py ImportReport实现完成(generate_monthly_report/generate_summary_report)
- [ ] ImportReport 单月报告包含：导入总行数/成功文件数/失败文件数/跳过行数/耗时
- [ ] ImportReport 全量汇总报告包含：各月份导入状态/总行数/总耗时/数据校验结果/月度统计差异
- [ ] ImportReport 输出到控制台(表格形式)和日志文件(JSON格式)
- [ ] src/stock_spider/data/importer/ths_importer.py 能协调ZipReader+CsvParser+DbWriter+ProgressTracker+MonthlyStats+ImportReport完成完整导入流程
- [ ] ThsImporter 导入完成后自动调用MonthlyStats.record_stats()记录月度统计
- [ ] ThsImporter 导入完成后自动调用ImportReport.generate_monthly_report()生成报告
- [ ] ThsImporter 仅保留主板股票数据，排除指数/创业板/科创板/北交所
- [ ] ThsImporter 遇到异常数据(open=0/high<low等)跳过并记录ERROR日志
- [ ] src/stock_spider/data/importer/__init__.py 导出ThsImporter公共接口
- [ ] src/stock_spider/data/importer/data_validator.py DataValidator实现完成(6项校验方法)
- [ ] DataValidator.validate_row_count() 行数校验：数据库行数与import_progress.total_rows比对，差异>1%告警
- [ ] DataValidator.validate_ohlcv_consistency() OHLCV一致性：low<=open<=high, low<=close<=high, volume>=0
- [ ] DataValidator.validate_daily_count() 使用TradeCalendar获取交易日列表，1m=240条/日, 5m=48条/日，偏差>5%告警
- [ ] DataValidator.validate_no_zero_volume() 零成交量检查：volume=0且amount>0为异常
- [ ] DataValidator.validate_partition_integrity() 跨分区检查：默认分区有数据则告警
- [ ] DataValidator.validate_monthly_stats() 使用TradeCalendar.calc_expected_count()计算精确expected_count，diff_pct>5%告警
- [ ] DataValidator 单元测试通过

## 事项四：执行脚本(tools)

- [ ] tools/import_ths_kline.py 支持--period/--month/--status参数，调用ThsImporter，导入完成后自动生成报告
- [ ] tools/init_db.py 调用DatabaseManager.ensure_schema()初始化数据库
- [ ] tools/check_status.py 查询import_progress表显示导入状态，支持--stats查询kline_monthly_stats
- [ ] tools/validate_import.py 支持--period/--month/--all参数，调用DataValidator执行校验
- [ ] 执行脚本不包含业务逻辑，仅调用lib模块

## 核心编码(core_code)防重复机制

- [ ] core_code格式：market(2位)+code(6位)+YYYYMMDDHHmm(12位)=20位
- [ ] kline_1m主键为core_code，唯一索引uk_kline_1m_core
- [ ] kline_5m主键为core_code，唯一索引uk_kline_5m_core
- [ ] 第1层-应用层：import_progress表追踪zip级别状态，跳过status='success'的zip
- [ ] 第2层-核心编码：core_code唯一索引阻止相同股票+市场+时间的重复记录
- [ ] 第3层-写入层：DbWriter使用ON CONFLICT(core_code) DO NOTHING静默跳过重复INSERT
- [ ] 中途失败重入安全：zip失败后重新导入，已写入数据通过ON CONFLICT(core_code) DO NOTHING跳过

## 交易日历与数据完整性

- [ ] config/trade_calendar.json 覆盖2021-2023年，数据来源于交易所官方公告
- [ ] TradeCalendar独立于导入流程，可被DataValidator和MonthlyStats调用
- [ ] MonthlyStats使用TradeCalendar.calc_expected_count()计算精确expected_count
- [ ] DataValidator使用TradeCalendar获取交易日列表进行每日条数校验
- [ ] DataValidator使用TradeCalendar.calc_expected_count()进行月度统计校验
- [ ] 交易日历缺失时回退使用简化算法(工作日近似)并记录WARNING

## 月度统计与数据丢失检测

- [ ] kline_monthly_stats表按月按股票记录行数(period/month/code/market/row_count)
- [ ] expected_count使用TradeCalendar精确计算(1m=240×交易日天数, 5m=48×交易日天数)
- [ ] diff_pct=(row_count-expected_count)/expected_count*100，超过5%告警
- [ ] 导入完成后自动统计写入kline_monthly_stats
- [ ] tools/check_status.py --stats 可查询月度统计

## 导入报告

- [ ] 单月导入报告：导入总行数/成功文件数/失败文件数/跳过行数/耗时
- [ ] 全量汇总报告：各月份导入状态/总行数/总耗时/数据校验结果/月度统计差异
- [ ] 报告输出到控制台(表格形式)
- [ ] 报告输出到日志文件(JSON格式)

## 导入执行与验证

- [ ] 单月1分钟线导入成功(202302)，import_progress状态为success
- [ ] 单月数据校验通过：行数一致、OHLCV一致性通过、每日条数正常
- [ ] 单月kline_monthly_stats统计记录完整，expected_count基于交易日历精确计算
- [ ] 全量1分钟线导入成功(17个月)，所有月份import_progress状态为success
- [ ] 全量1分钟线校验通过：行数一致、OHLCV一致性通过、默认分区无数据
- [ ] 全量1分钟线kline_monthly_stats所有月份统计完整
- [ ] 全量5分钟线导入成功(19个月)，所有月份import_progress状态为success
- [ ] 全量5分钟线校验通过：行数一致、OHLCV一致性通过、默认分区无数据
- [ ] 全量5分钟线kline_monthly_stats所有月份统计完整
- [ ] 防重复导入验证：重复运行导入命令，数据库行数不变
- [ ] 防重复导入验证：手动设为failed后重新导入，ON CONFLICT(core_code) DO NOTHING正确跳过已存在数据

## 命名规范

- [ ] 所有lib模块遵循命名规范(模块:小写下划线, 类:大驼峰, 函数:小写下划线, 常量:大写下划线, 数据类:大驼峰+Record后缀)
- [ ] migration脚本命名遵循 {revision}_{description}.py 规范

## 配置规范

- [ ] 所有配置文件使用JSON格式，禁止INI/YAML等其他格式
- [ ] config/db_config.json 包含完整的数据库连接参数和db_version字段
- [ ] config/import_config.json 包含完整的导入参数
- [ ] config/trade_calendar.json 包含2021-2023年交易日历数据
- [ ] 敏感信息(密码)通过环境变量读取，不硬编码在JSON配置中
- [ ] alembic.ini仅含最小化配置，数据库URL从config/db_config.json读取

## 版本管理规范

- [ ] db_version表记录已应用的Schema版本
- [ ] config/db_config.json中的db_version字段与数据库db_version表比对
- [ ] 系统启动时DatabaseManager自动检查版本并升级
- [ ] 只允许升级，绝对禁止降级
- [ ] migration脚本仅包含upgrade()函数，不包含downgrade()函数
- [ ] 每个migration执行成功后在db_version表插入版本记录
- [ ] migration脚本一旦合入主分支，不可修改，只能新增
- [ ] sql/database_upgrade_plan.md 包含完整的数据库建设及升级方案
