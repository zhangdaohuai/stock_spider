# 同花顺历史K线数据导入 Spec

## Why
项目已有同花顺导出的历史分钟K线zip数据(2021-2023, 约10.8GB)，需要将其导入PostgreSQL数据库，为后续实时采集提供历史数据基础。仅导入1分钟和5分钟K线，仅保留主板股票数据(含ST)。本次仅完成数据导入工作，不涉及其他功能。

## What Changes
- 新建 `src/stock_spider/data/importer/` 库模块，封装为可复用的lib，实现zip文件流式读取、CSV解析、数据库批量写入
- 新建 `src/stock_spider/utils/market_util.py`，实现股票代码到市场的判断
- 新建 `src/stock_spider/data/storage/connection.py`，实现PostgreSQL连接池
- 新建 `src/stock_spider/data/storage/db_manager.py`，实现DatabaseManager(版本检查、自动升级、禁止降级)
- 新建 `tools/` 目录，放置执行脚本(不属于主干功能)
- 新建 `migrations/` 目录，使用Alembic管理数据库Schema版本(仅upgrade，禁止downgrade)
- 新建 `sql/database_upgrade_plan.md`，数据库建设及升级完整方案文档
- 所有配置文件使用JSON格式，存放在 `config/` 目录
- 实现断点续传机制，支持中断后从上次位置继续导入
- 实现三层防重复导入机制(应用层zip跳过/core_code唯一索引/ON CONFLICT DO NOTHING)
- 实现导入后数据完整性校验(行数/OHLCV一致性/每日条数/零成交量/跨分区检查)
- 实现核心编码(core_code=market+code+YYYYMMDDHHmm)作为K线表主键，防止重复导入
- 新增kline_monthly_stats月度统计表，按月按股票记录行数，快速发现数据丢失
- 新增交易日历配置和计算lib，精确计算expected_count，确保数据完整性校验正确
- 实现导入报告生成(单月报告+全量汇总报告)
- 数据库Schema包含db_version表，系统启动时自动检查版本并升级

## Impact
- Affected specs: stock_crawler（共享PostgreSQL实例，新增kline_1m/kline_5m表）
- Affected code: 新增 `src/stock_spider/data/importer/` lib、`migrations/` 和 `tools/`，不影响现有代码

---

## ADDED Requirements

### Requirement: 配置管理规范(JSON)
系统 SHALL 所有配置文件使用JSON格式，存放在 `config/` 目录。禁止使用INI/YAML等其他格式。配置文件通过环境变量 `CONFIG_PATH` 指定路径。敏感信息(密码)使用 `.env` + `pydantic` 读取，不提交到代码仓库。

#### Scenario: 数据库连接配置
- **WHEN** 系统需要连接PostgreSQL
- **THEN** 从 `config/db_config.json` 读取连接参数(host/port/database/user/password)

#### Scenario: 导入参数配置
- **WHEN** 系统执行数据导入
- **THEN** 从 `config/import_config.json` 读取导入参数(batch_size/data_dir/log_dir等)

#### Scenario: Alembic数据库URL
- **WHEN** Alembic需要数据库连接
- **THEN** `migrations/env.py` 从 `config/db_config.json` 读取数据库URL，不硬编码在alembic.ini中

#### Scenario: 配置路径指定
- **WHEN** 需要指定配置文件路径
- **THEN** 通过环境变量 `CONFIG_PATH` 指定，默认使用 `config/` 目录

#### Scenario: 敏感信息保护
- **WHEN** 配置包含密码等敏感信息
- **THEN** 使用 `.env` 文件存储，通过 `pydantic` 读取，`.env` 不提交到代码仓库

### Requirement: 数据库Schema与版本升级规范
系统 SHALL 使用Alembic管理数据库Schema版本，只允许升级，绝对禁止降级。Schema包含db_version/kline_1m/kline_5m/stock_info/import_progress/kline_monthly_stats六张表。使用raw SQL migration（非autogenerate），因分区表需要自定义SQL。系统启动时通过DatabaseManager自动检查版本并执行升级。

#### Scenario: 初始建库
- **WHEN** 首次执行数据库初始化
- **THEN** 运行 `alembic upgrade head`，创建db_version/kline_1m/kline_5m/stock_info/import_progress/kline_monthly_stats六张表及分区，并在db_version表插入初始版本记录

#### Scenario: 版本升级
- **WHEN** Schema发生变更(如新增字段、新增分区)
- **THEN** 通过Alembic migration脚本升级，不直接修改表结构

#### Scenario: 禁止降级
- **WHEN** 配置版本低于数据库已应用版本
- **THEN** 系统报错终止，绝对不允许降级操作

#### Scenario: 系统启动自动升级
- **WHEN** 系统启动时
- **THEN** DatabaseManager自动读取config/db_config.json中的db_version，与数据库db_version表比对，如配置版本>数据库版本则自动执行alembic upgrade，如配置版本<=数据库版本则跳过

#### Scenario: 数据库版本表
- **WHEN** 执行初始migration
- **THEN** 创建db_version表(version/description/applied_at)，并在upgrade()末尾插入当前版本记录

#### Scenario: 1分钟K线表
- **WHEN** 执行初始migration
- **THEN** 创建kline_1m分区表，含17个月分区(202110~202302)+默认分区，主键(core_code)，core_code=market+code+YYYYMMDDHHmm(如"SH600519202302010930")，唯一索引uk_kline_1m_core防止重复导入

#### Scenario: 5分钟K线表
- **WHEN** 执行初始migration
- **THEN** 创建kline_5m分区表，含19个月分区(202108~202302)+默认分区，主键(core_code)，core_code=market+code+YYYYMMDDHHmm(如"SZ000858202302010935")，唯一索引uk_kline_5m_core防止重复导入

#### Scenario: 新增分区
- **WHEN** 需要导入超出当前分区范围的数据(如2023年3月之后)
- **THEN** 创建新的Alembic migration脚本添加分区，不修改已有migration

#### Scenario: migration不可变
- **WHEN** migration脚本已合入主分支
- **THEN** 不可修改该脚本，只能新增后续migration

#### Scenario: migration仅包含upgrade
- **WHEN** 创建新的migration脚本
- **THEN** 仅实现upgrade()函数，不实现downgrade()函数(禁止降级)

### Requirement: DatabaseManager(数据库版本管理与自动升级)
系统 SHALL 在 `src/stock_spider/data/storage/db_manager.py` 提供DatabaseManager类，负责数据库版本检查和自动升级。系统运行时首先运行此模块。

#### Scenario: 启动时版本检查
- **WHEN** 系统启动调用 `DatabaseManager.ensure_schema()`
- **THEN** 读取config/db_config.json的db_version字段，查询数据库db_version表最新版本，比对两者

#### Scenario: 自动升级
- **WHEN** 配置版本 > 数据库版本
- **THEN** 自动执行 `alembic upgrade head`，升级完成后验证db_version表记录

#### Scenario: 版本一致
- **WHEN** 配置版本 == 数据库版本
- **THEN** 跳过升级，记录INFO日志

#### Scenario: 禁止降级
- **WHEN** 配置版本 < 数据库版本
- **THEN** 抛出异常终止程序，记录CRITICAL日志，绝不执行降级

#### Scenario: 数据库不存在
- **WHEN** 首次运行，db_version表不存在
- **THEN** 自动执行 `alembic upgrade head` 创建完整Schema

### Requirement: 数据库建设及升级方案文档
系统 SHALL 在 `sql/database_upgrade_plan.md` 提供完整的数据库建设及升级方案文档，包含版本管理规范、升级流程、禁止降级约束、升级脚本编写规范等。

#### Scenario: 方案文档内容
- **WHEN** 开发者需要了解数据库升级流程
- **THEN** 文档包含：版本号规范、升级触发机制、自动升级流程、禁止降级约束、migration编写规范、版本比对逻辑、异常处理

### Requirement: ZIP文件流式读取器(lib)
系统 SHALL 在 `src/stock_spider/data/importer/zip_reader.py` 提供ZipReader类，从zip文件流式读取CSV内容，处理GBK文件名解码，不解压到磁盘。

#### Scenario: 列出zip内CSV文件
- **WHEN** 调用 `list_csv_files(zip_path)`
- **THEN** 返回zip内所有.csv文件名列表，文件名使用cp437→gbk回退解码

#### Scenario: 流式读取单个CSV
- **WHEN** 调用 `read_csv_stream(zip_path, filename)`
- **THEN** 返回迭代器，逐行yield原始字节行，不将整个文件加载到内存

#### Scenario: 统计CSV文件数
- **WHEN** 调用 `get_file_count(zip_path)`
- **THEN** 返回zip内.csv文件数量

### Requirement: CSV多格式解析器(lib)
系统 SHALL 在 `src/stock_spider/data/importer/csv_parser.py` 提供CsvParser类，解析1分钟和5分钟两种不同格式的CSV数据，统一输出标准数据类。

#### Scenario: 1分钟K线解析
- **WHEN** 输入1分钟K线的CSV行 `000001,2023-02-01 09:30:00,15.03,15.03,15.03,15.03,3601.0,5412300.0,15.03`
- **THEN** 输出Kline1mRecord(code="000001", trade_time=datetime, open=15.03, close=15.03, high=15.03, low=15.03, volume=3601, amount=5412300.00, avg_price=15.03)

#### Scenario: 5分钟K线解析
- **WHEN** 输入5分钟K线的CSV行 `000001,平安银行,5.0,2023-02-01 09:35:00,15.03,15.01,15.08,14.95,43954.0,6.59863E7,0.02`
- **THEN** 输出Kline5mRecord(code="000001", trade_time=datetime, open=15.03, close=15.01, high=15.08, low=14.95, volume=43954, amount=65986300.00, turnover=0.02)

#### Scenario: 科学计数法解析
- **WHEN** 遇到成交额字段值 `2.98901E7`
- **THEN** 使用Decimal解析为29890100.00，精度不丢失

#### Scenario: 编码自动检测
- **WHEN** 读取CSV原始字节
- **THEN** 按优先级尝试utf-8→gbk→gb18030→latin1解码

#### Scenario: 中文表头跳过
- **WHEN** CSV第一行包含中文表头（如 `"股票代码","分时时间",...`）
- **THEN** 自动识别并跳过，不作为数据行处理

### Requirement: 市场判断工具(lib)
系统 SHALL 在 `src/stock_spider/utils/market_util.py` 提供市场判断函数，根据股票代码判断所属市场，并过滤非主板标的。

#### Scenario: 主板股票识别
- **WHEN** 输入代码 `600519`
- **THEN** 返回 `("SH", True)` 表示上海主板

#### Scenario: 深圳主板识别
- **WHEN** 输入代码 `000858`
- **THEN** 返回 `("SZ", True)` 表示深圳主板

#### Scenario: 中小板识别
- **WHEN** 输入代码 `002001`
- **THEN** 返回 `("SZ", True)` 表示深圳中小板(归入主板)

#### Scenario: 创业板排除
- **WHEN** 输入代码 `300001`
- **THEN** 返回 `(None, False)` 表示创业板，排除

#### Scenario: 科创板排除
- **WHEN** 输入代码 `688001`
- **THEN** 返回 `(None, False)` 表示科创板，排除

#### Scenario: 指数排除
- **WHEN** 输入代码 `000001` 且ktype=10
- **THEN** 返回 `(None, False)` 表示指数，排除

### Requirement: 数据库批量写入器(lib)
系统 SHALL 在 `src/stock_spider/data/importer/db_writer.py` 提供DbWriter类，使用psycopg2.extras.execute_values批量写入K线数据到PostgreSQL。

#### Scenario: 批量写入1分钟线
- **WHEN** 调用 `write_1m_batch(records)`
- **THEN** 使用execute_values批量INSERT，每批5000条，ON CONFLICT DO NOTHING跳过重复

#### Scenario: 批量写入5分钟线
- **WHEN** 调用 `write_5m_batch(records)`
- **THEN** 同上逻辑写入kline_5m表

#### Scenario: 事务控制
- **WHEN** 单个zip文件处理完成
- **THEN** 提交当前事务；处理失败则回滚

### Requirement: 导入进度追踪(lib)
系统 SHALL 在 `src/stock_spider/data/importer/progress_tracker.py` 提供ProgressTracker类，记录每个zip文件的导入状态，支持断点续传。

#### Scenario: 记录导入开始
- **WHEN** 开始处理某个zip文件
- **THEN** 在import_progress表中插入记录，status='running'

#### Scenario: 记录导入完成
- **WHEN** zip文件处理完成
- **THEN** 更新status='success'，记录total_files/imported_files/total_rows

#### Scenario: 记录导入失败
- **WHEN** zip文件处理异常
- **THEN** 更新status='failed'，记录error_msg

#### Scenario: 断点续传
- **WHEN** 程序重启后开始导入
- **THEN** 查询import_progress，跳过status='success'的zip文件

### Requirement: 同花顺数据导入主控(lib)
系统 SHALL 在 `src/stock_spider/data/importer/ths_importer.py` 提供ThsImporter类，协调ZIP读取、CSV解析、数据库写入的完整流程。

#### Scenario: 导入1分钟线全部数据
- **WHEN** 调用 `import_period("1m")`
- **THEN** 扫描`stock_data/tdx_data/一分钟K线数据/`目录，按月顺序导入17个zip文件

#### Scenario: 导入5分钟线全部数据
- **WHEN** 调用 `import_period("5m")`
- **THEN** 扫描`stock_data/tdx_data/五分钟K线数据/`目录，按月顺序导入19个zip文件

#### Scenario: 单zip处理流程
- **WHEN** 处理单个zip文件
- **THEN** 执行：读取CSV列表 → 逐文件流式读取 → 解析 → 过滤非主板 → 批量写入 → 更新进度

#### Scenario: 数据过滤
- **WHEN** 解析CSV数据行
- **THEN** 仅保留主板股票(60xxxx/00xxxx/002xxx)，排除指数(ktype=10)、创业板(30xxxx)、科创板(68xxxx)、北交所(8xxxxx/4xxxxx)

#### Scenario: 异常数据跳过
- **WHEN** 遇到open/close/high/low为0或空、high<low、volume<0的行
- **THEN** 跳过该行，记录ERROR日志

### Requirement: 执行脚本(tools)
系统 SHALL 在 `tools/` 目录提供命令行执行脚本，调用lib完成数据导入。执行脚本不属于主干功能，仅调用lib模块，不包含业务逻辑。

#### Scenario: 执行1分钟线导入
- **WHEN** 运行 `python tools/import_ths_kline.py --period 1m`
- **THEN** 调用ThsImporter.import_period("1m")执行导入

#### Scenario: 执行5分钟线导入
- **WHEN** 运行 `python tools/import_ths_kline.py --period 5m`
- **THEN** 调用ThsImporter.import_period("5m")执行导入

#### Scenario: 执行单月导入
- **WHEN** 运行 `python tools/import_ths_kline.py --period 1m --month 202302`
- **THEN** 仅导入指定月份的zip文件

#### Scenario: 查看导入状态
- **WHEN** 运行 `python tools/import_ths_kline.py --status`
- **THEN** 查询import_progress表，显示各zip文件的导入状态

#### Scenario: 数据库初始化
- **WHEN** 运行 `python tools/init_db.py`
- **THEN** 执行Alembic upgrade head，创建数据库表结构

#### Scenario: 导入进度查询
- **WHEN** 运行 `python tools/check_status.py`
- **THEN** 查询import_progress表，显示各周期各月份的导入状态

### Requirement: 防重复导入机制
系统 SHALL 通过三层机制防止数据重复导入，确保多次运行导入程序不会产生重复数据。核心防重手段为core_code唯一索引。

#### Scenario: 第1层-应用层zip级别跳过
- **WHEN** 程序启动执行导入
- **THEN** 查询import_progress表，跳过status='success'的zip文件，仅处理pending/failed的zip

#### Scenario: 第2层-核心编码唯一索引
- **WHEN** 写入K线数据到kline_1m/kline_5m表
- **THEN** core_code(market+code+YYYYMMDDHHmm)作为主键和唯一索引，阻止相同股票+市场+时间的重复记录。1分钟线core_code格式：market(2位)+code(6位)+YYYYMMDDHHmm(12位)=20位，5分钟线core_code格式相同

#### Scenario: 第3层-ON CONFLICT DO NOTHING
- **WHEN** INSERT遇到core_code冲突(如zip中途失败后重新导入)
- **THEN** ON CONFLICT(core_code) DO NOTHING静默跳过重复行，不报错不回滚，继续写入后续数据

#### Scenario: 中途失败重入安全
- **WHEN** 某个zip文件导入中途失败(status='failed')后重新运行
- **THEN** 该zip重新导入时，已写入的CSV数据通过ON CONFLICT(core_code) DO NOTHING跳过，仅写入未完成的部分

### Requirement: 导入后数据完整性校验
系统 SHALL 在 `src/stock_spider/data/importer/data_validator.py` 提供DataValidator类，在数据导入完成后执行完整性校验，确保数据质量。

#### Scenario: 行数校验
- **WHEN** 调用 `validate_row_count(period, month)`
- **THEN** 查询数据库该月分区总行数，与import_progress记录的total_rows比对，差异超过1%则告警

#### Scenario: OHLCV一致性校验
- **WHEN** 调用 `validate_ohlcv_consistency(period, month)`
- **THEN** 检查 low<=open<=high 且 low<=close<=high 且 volume>=0，异常记录数超过0则报告ERROR

#### Scenario: 每日条数校验(1分钟线)
- **WHEN** 调用 `validate_daily_count(period='1m', month)`
- **THEN** 使用TradeCalendar获取该月交易日列表，检查每只股票每个交易日1分钟线应为240条(4小时×60分钟)，偏差超过5%则告警

#### Scenario: 每日条数校验(5分钟线)
- **WHEN** 调用 `validate_daily_count(period='5m', month)`
- **THEN** 使用TradeCalendar获取该月交易日列表，检查每只股票每个交易日5分钟线应为48条(4小时×12条/小时)，偏差超过5%则告警

#### Scenario: 零成交量检查
- **WHEN** 调用 `validate_no_zero_volume(period, month)`
- **THEN** 检查是否存在volume=0且amount>0的异常记录，存在则报告WARNING

#### Scenario: 跨分区数据检查
- **WHEN** 调用 `validate_partition_integrity(period, month)`
- **THEN** 检查默认分区(kline_1m_default/kline_5m_default)是否有数据，有数据则报告WARNING(说明有数据未落入正确月份分区)

### Requirement: 交易日历配置与计算(lib)
系统 SHALL 在 `src/stock_spider/utils/trade_calendar.py` 提供TradeCalendar类，从 `config/trade_calendar.json` 读取交易日历数据，精确计算每月交易日数，为月度统计expected_count提供准确依据。交易日历lib独立于导入流程，可被DataValidator和MonthlyStats调用。

#### Scenario: 交易日历配置格式
- **WHEN** 系统需要交易日历数据
- **THEN** 从 `config/trade_calendar.json` 读取，格式为 `{"2021": {"10": ["2021-10-08","2021-10-11",...], "11": [...]}, ...}`，每年每月包含该月所有交易日的日期列表

#### Scenario: 获取月交易日数
- **WHEN** 调用 `TradeCalendar.get_trading_days_count(year, month)`
- **THEN** 返回该月交易日天数(整数)，如2023年2月返回20

#### Scenario: 获取月交易日列表
- **WHEN** 调用 `TradeCalendar.get_trading_days(year, month)`
- **THEN** 返回该月所有交易日的date列表，如[datetime.date(2023,2,1), datetime.date(2023,2,2), ...]

#### Scenario: 判断是否交易日
- **WHEN** 调用 `TradeCalendar.is_trading_day(date)`
- **THEN** 返回True/False，判断指定日期是否为交易日

#### Scenario: 计算1分钟线expected_count
- **WHEN** 调用 `TradeCalendar.calc_expected_count(period='1m', year, month)`
- **THEN** 返回 240 × 交易日天数(每交易日240条1分钟线)

#### Scenario: 计算5分钟线expected_count
- **WHEN** 调用 `TradeCalendar.calc_expected_count(period='5m', year, month)`
- **THEN** 返回 48 × 交易日天数(每交易日48条5分钟线)

#### Scenario: 交易日历缺失处理
- **WHEN** 请求的年月不在config/trade_calendar.json中
- **THEN** 记录WARNING日志，回退使用简化算法(当月工作日-法定节假日近似值)，并在报告中标注"日历数据缺失，使用近似值"

#### Scenario: 交易日历数据来源
- **WHEN** 需要更新交易日历数据
- **THEN** 手动维护config/trade_calendar.json，数据来源于交易所官方公告。初始版本覆盖2021-2023年(与数据范围一致)

### Requirement: 核心编码(core_code)生成工具(lib)
系统 SHALL 在 `src/stock_spider/utils/core_code.py` 提供核心编码生成函数，将market+code+trade_time编码为唯一字符串，用于K线表主键和防重复导入。

#### Scenario: 1分钟线核心编码生成
- **WHEN** 调用 `generate_core_code(market="SH", code="600519", trade_time=datetime(2023,2,1,9,30))`
- **THEN** 返回 `"SH600519202302010930"` (market(2)+code(6)+YYYYMMDDHHmm(12)=20位)

#### Scenario: 5分钟线核心编码生成
- **WHEN** 调用 `generate_core_code(market="SZ", code="000858", trade_time=datetime(2023,2,1,9,35))`
- **THEN** 返回 `"SZ000858202302010935"` (格式相同，时间精确到分钟)

#### Scenario: 核心编码唯一性
- **WHEN** 相同股票相同时间生成core_code
- **THEN** 结果始终相同(确定性编码)，不同股票或不同时间产生不同core_code

### Requirement: 月度数据统计表
系统 SHALL 在数据库Schema中新增 `kline_monthly_stats` 表，按月记录每只股票的K线条数统计，用于快速发现数据丢失。

#### Scenario: 统计表结构
- **WHEN** 执行初始migration
- **THEN** 创建kline_monthly_stats表(period/month/code/market/row_count/expected_count/diff_pct/checked_at)，唯一约束(period, month, code, market)

#### Scenario: 导入后自动统计
- **WHEN** 某月zip文件导入完成(status更新为success前)
- **THEN** 按market+code分组统计该月各股票的K线条数，写入kline_monthly_stats表

#### Scenario: 数据丢失检测
- **WHEN** 调用 `validate_monthly_stats(period, month)`
- **THEN** 使用TradeCalendar.calc_expected_count()计算精确的expected_count(1m=240条/日×交易日天数, 5m=48条/日×交易日天数)，比对kline_monthly_stats.row_count与expected_count，diff_pct超过5%则告警

#### Scenario: 统计表查询
- **WHEN** 运行 `python tools/check_status.py --stats`
- **THEN** 查询kline_monthly_stats表，显示各月份各股票的行数统计和差异百分比

### Requirement: 导入报告生成
系统 SHALL 在数据导入完成后自动生成导入报告，汇总导入结果和数据质量。

#### Scenario: 单月导入报告
- **WHEN** 某月zip导入完成
- **THEN** 生成该月导入报告：导入总行数/成功文件数/失败文件数/跳过行数(非主板+异常数据)/耗时

#### Scenario: 全量导入报告
- **WHEN** 全量导入完成
- **THEN** 生成汇总报告：各月份导入状态/总行数/总耗时/数据校验结果/月度统计差异

#### Scenario: 报告输出格式
- **WHEN** 导入报告生成
- **THEN** 同时输出到控制台(表格形式)和日志文件(JSON格式)，报告内容包括：period/month/total_rows/imported_rows/skipped_rows/duration/validation_result

### Requirement: lib命名规范
系统 SHALL 遵循以下命名规范：

- 模块名: 小写下划线 (zip_reader, csv_parser, db_writer)
- 类名: 大驼峰 (ZipReader, CsvParser, DbWriter, ThsImporter)
- 函数名: 小写下划线 (parse_1m_row, write_1m_batch, import_period)
- 常量: 大写下划线 (BATCH_SIZE, DEFAULT_ENCODING)
- 数据类: 大驼峰+Record后缀 (Kline1mRecord, Kline5mRecord)

---

## MODIFIED Requirements
无

## REMOVED Requirements
无
