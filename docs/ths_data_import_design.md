# 同花顺历史K线数据导入 — Python设计方案

> **设计日期**：2026-05-18
> **数据来源**：`stock_data/tdx_data/` 下的zip压缩文件
> **目标数据库**：PostgreSQL (schema见 `sql/ths_kline_schema.sql`)
> **本次范围**：仅完成数据导入，三大事项：建库(含版本升级)、数据导入lib、tools执行脚本

---

## 一、数据源分析总结

### 1.1 文件结构

```
stock_data/tdx_data/
├── 一分钟K线数据/     # 17个月(202110~202302), 7057MB, ~11687只/月
└── 五分钟K线数据/     # 19个月(202108~202302), 3807MB
```

### 1.2 CSV字段差异

| 周期 | 字段 | 编码 | 特殊处理 |
|------|------|------|---------|
| 1分钟 | code,tdate,open,close,high,low,cjl,cje,cjjj | 早期utf-8仅表头, 后期gbk | 无name/ktype/fq/hsl |
| 5分钟 | code,name,ktype,[fq,]tdate,open,close,high,low,cjl,cje,hsl | 同上 | 早期含fq字段, 后期不含 |

### 1.3 关键难点

1. **文件名GBK编码**：macOS的unzip无法正确处理，需Python zipfile模块解码
2. **CSV编码不一致**：早期zip的CSV表头是utf-8(仅2行)，后期是gbk(含数据)
3. **科学计数法**：成交额使用`2.98901E7`格式
4. **数据量巨大**：1分钟线约4.08亿条，需批量写入
5. **字段不统一**：1分钟线无name/ktype/fq/hsl，5分钟线含这些字段
6. **市场判断**：CSV中无市场字段，需从代码推断(6开头=SH, 0/3开头=SZ)

---

## 二、项目结构

```
stock_spider/                          # 项目根目录
├── src/                               # 代码根目录
│   └── stock_spider/                  # 顶级包
│       ├── __init__.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── importer/              # 数据导入lib模块
│       │   │   ├── __init__.py        # 导出ThsImporter公共接口
│       │   │   ├── zip_reader.py      # ZIP文件读取器(GBK解码)
│       │   │   ├── csv_parser.py      # CSV解析器(多编码/多格式)
│       │   │   ├── models.py          # 数据类(Kline1mRecord/Kline5mRecord)
│       │   │   ├── db_writer.py       # 数据库批量写入器
│       │   │   ├── progress_tracker.py # 导入进度追踪
│       │   │   └── ths_importer.py    # 同花顺数据导入主控
│       │   └── storage/
│       │       ├── __init__.py
│       │       ├── connection.py      # 数据库连接池
│       │       └── db_manager.py      # 数据库版本管理与自动升级
│       └── utils/
│           ├── __init__.py
│           └── market_util.py         # 市场判断工具
├── tools/                             # 执行脚本(不属于主干功能)
│   ├── import_ths_kline.py            # 导入主控脚本
│   ├── init_db.py                     # 数据库初始化脚本
│   └── check_status.py               # 导入状态查询脚本
├── migrations/                        # Alembic迁移脚本
│   ├── env.py                         # Alembic环境配置
│   ├── script.py.mako                 # 迁移脚本模板
│   └── versions/                      # 迁移版本目录
│       └── 001_initial_schema.py      # 初始Schema(4张表+分区)
├── config/                            # 配置文件目录(全部JSON格式)
│   ├── db_config.json                 # 数据库连接配置
│   └── import_config.json             # 导入参数配置
├── tests/                             # 测试目录
│   ├── unit/                          # 单元测试
│   └── integration/                   # 集成测试
├── docs/
│   └── ths_data_import_design.md  # 本设计文档
├── sql/                            # SQL目录(与docs平行)
│   ├── ths_kline_schema.sql       # Schema设计参考
│   └── database_upgrade_plan.md   # 数据库建设及升级完整方案
└── stock_data/                        # 数据源目录(不入库)
    └── tdx_data/
```

---

## 三、核心类设计

### 3.1 ZipReader — ZIP文件读取器

```
职责: 从zip文件流式读取CSV内容，处理GBK文件名解码
方法:
  - list_csv_files(zip_path) -> list[str]       # 列出zip内所有CSV文件
  - read_csv_stream(zip_path, filename) -> iter  # 流式读取单个CSV
  - get_file_count(zip_path) -> int              # 统计CSV文件数
注意: 不解压到磁盘，直接从zip流中读取
```

### 3.2 CsvParser — CSV解析器

```
职责: 解析不同格式的CSV数据，统一输出标准格式
方法:
  - parse_1m_row(raw_line) -> Kline1mRecord      # 解析1分钟K线行
  - parse_5m_row(raw_line) -> Kline5mRecord      # 解析5分钟K线行
  - detect_encoding(raw_bytes) -> str             # 自动检测编码
  - parse_scientific(value_str) -> Decimal        # 解析科学计数法
注意:
  - 1分钟线: 9个字段(code,tdate,open,close,high,low,cjl,cje,cjjj)
  - 5分钟线: 11-12个字段(含name,ktype,[fq],hsl)
  - 第一行可能是中文表头(需跳过)
  - 成交额可能是科学计数法
```

### 3.3 DbWriter — 数据库批量写入器

```
职责: 批量写入K线数据到PostgreSQL
方法:
  - write_1m_batch(records: list[Kline1mRecord]) -> int   # 批量写1分钟线
  - write_5m_batch(records: list[Kline5mRecord]) -> int   # 批量写5分钟线
  - write_stock_info(records: list[StockInfo]) -> int      # 写股票信息
  - flush() -> int                                          # 刷新缓冲区
配置:
  - batch_size: 5000 (每批写入条数)
  - 使用psycopg2.extras.execute_values批量写入
  - ON CONFLICT DO NOTHING (跳过重复数据)
```

### 3.4 ProgressTracker — 导入进度追踪

```
职责: 记录每个zip文件的导入状态，支持断点续传
方法:
  - start_import(period, zip_file) -> None       # 记录导入开始
  - finish_import(period, zip_file, stats) -> None  # 记录导入完成
  - fail_import(period, zip_file, error) -> None    # 记录导入失败
  - is_completed(period, zip_file) -> bool        # 检查是否已完成
  - get_pending_zips(period) -> list[str]         # 获取待处理zip列表
```

### 3.5 ThsImporter — 同花顺数据导入主控

```
职责: 协调ZIP读取、CSV解析、数据库写入的完整流程
方法:
  - import_period(period: str) -> ImportResult    # 导入某个周期的所有月份数据
  - import_month(period: str, month: str) -> ImportResult  # 导入单月数据
  - import_zip(zip_path: str) -> ImportResult     # 导入单个zip文件
  - get_import_status() -> list[ImportProgress]   # 查询导入进度
流程:
  1. 扫描目录获取所有zip文件
  2. 查询import_progress跳过已完成的zip
  3. 逐zip处理: 读取CSV -> 解析 -> 批量写入
  4. 更新import_progress状态
  5. 处理下一个zip
```

---

## 四、核心算法

### 4.1 市场判断

```
输入: code(6位字符串)
规则:
  - 6开头 → SH(上海)
  - 0开头 → SZ(深圳)
  - 002开头 → SZ(深圳, 中小板)
  - 3开头 → SZ(深圳, 创业板, 排除)
  - 68开头 → SH(科创板, 排除)
  - 8/4开头 → BJ(北交所, 排除)
输出: (market, is_main_board) — market为SH/SZ或None, is_main_board为True/False
```

### 4.2 编码检测

```
输入: raw_bytes(前4096字节)
算法:
  1. 尝试utf-8解码 → 成功则返回utf-8
  2. 尝试gbk解码 → 成功则返回gbk
  3. 尝试gb18030解码 → 成功则返回gb18030
  4. 兜底返回latin1
注意: 早期zip的CSV第一行是中文表头(utf-8), 第二行开始是数据
      后期zip整文件都是gbk编码
```

### 4.3 科学计数法解析

```
输入: value_str(如 "2.98901E7" 或 "5412300.0")
算法:
  1. 如果包含 'E' 或 'e' → 使用Decimal(value_str)解析
  2. 否则 → 直接float(value_str)
  3. 转为NUMERIC(18,2)写入数据库
```

### 4.4 数据过滤

```
规则:
  - 仅保留主板股票: code以 60xxxx(SH) / 00xxxx(SZ) / 002xxx(SZ) 开头
  - 排除指数: ktype=10 或 code=000001/399001等
  - 排除空数据行: open/close/high/low全为0或空
```

---

## 五、数据库版本管理(Alembic)

### 5.1 设计原则

| 原则 | 说明 |
|------|------|
| 唯一入口 | 所有Schema变更必须通过Alembic migration执行 |
| 禁止直改 | 禁止直接修改数据库表结构 |
| 不可变历史 | migration脚本一旦合入主分支，不可修改，只能新增 |
| 禁止降级 | 只允许升级，绝对禁止降级。migration仅包含upgrade()，不实现downgrade() |
| 原始SQL | 使用raw SQL migration(非autogenerate)，因分区表需要自定义SQL |
| 自动升级 | 系统启动时DatabaseManager自动检查版本并升级 |
| 版本比对 | config/db_config.json的db_version与数据库db_version表比对 |

### 5.2 DatabaseManager — 数据库版本管理与自动升级

```
职责: 系统启动时自动检查数据库版本并执行升级，禁止降级
位置: src/stock_spider/data/storage/db_manager.py
方法:
  - ensure_schema() -> None                       # 主入口：检查版本并自动升级
  - _get_config_version() -> str                   # 读取config/db_config.json的db_version
  - _get_db_version() -> str | None                # 查询数据库db_version表最新版本
  - _run_upgrade() -> None                         # 执行alembic upgrade head
  - _verify_version(expected: str) -> bool         # 验证升级后版本是否正确

流程:
  1. 读取config/db_config.json的db_version字段
  2. 查询数据库db_version表最新版本(如表不存在则视为首次运行)
  3. 比对版本:
     - 配置版本 > 数据库版本 → 执行alembic upgrade head
     - 配置版本 == 数据库版本 → 跳过，记录INFO日志
     - 配置版本 < 数据库版本 → 抛出异常终止(禁止降级)
  4. 升级完成后验证db_version表记录
```

### 5.3 初始Migration内容

初始migration (`001_initial_schema.py`) 将创建以下5张表：
- `db_version` — 数据库版本记录表(系统启动时首先检查)
- `stock_info` — 股票基本信息表
- `kline_1m` — 1分钟K线分区表(17个月分区+默认分区)
- `kline_5m` — 5分钟K线分区表(19个月分区+默认分区)
- `import_progress` — 导入进度追踪表

upgrade()末尾在db_version表插入初始版本记录：
```sql
INSERT INTO db_version (version, description) VALUES ('001', '初始Schema');
```

### 5.4 版本升级场景

| 场景 | 操作 | 示例 |
|------|------|------|
| 新增分区 | 创建新migration添加分区 | `002_add_kline_1m_202303_partition.py` |
| 新增字段 | 创建新migration ALTER TABLE | `003_add_kline_1m_signal_column.py` |
| 新增表 | 创建新migration CREATE TABLE | `004_add_kline_daily_table.py` |
| 修改字段 | 创建新migration ALTER COLUMN | `005_modify_amount_precision.py` |

**版本比对规则**：
- 系统启动时，DatabaseManager读取 `config/db_config.json` 的 `db_version` 字段
- 与数据库 `db_version` 表最新版本比对
- `db_version` 字段值 = 当前代码期望的最低数据库版本
- 如配置版本 > 数据库版本 → 自动执行 `alembic upgrade head`
- 如配置版本 == 数据库版本 → 跳过升级
- 如配置版本 < 数据库版本 → **抛出异常终止**（禁止降级）

**升级操作流程**：
1. 修改 `config/db_config.json` 的 `db_version` 为新版本号(如 "002")
2. 创建新的migration脚本(如 `002_add_partition.py`)
3. 系统启动时自动检测版本差异并执行升级
4. 升级成功后db_version表自动记录新版本

### 5.5 Alembic配置

所有配置使用JSON格式，Alembic的数据库URL从 `config/db_config.json` 读取：

```json
// config/db_config.json 示例
{
    "host": "localhost",
    "port": 5432,
    "database": "stock_spider",
    "user": "postgres",
    "password_env": "DB_PASSWORD",
    "db_version": "001",
    "pool_min": 2,
    "pool_max": 10
}
```

```json
// config/import_config.json 示例
{
    "batch_size": 5000,
    "data_dir": "stock_data/tdx_data",
    "log_dir": "logs",
    "periods": {
        "1m": "一分钟K线数据",
        "5m": "五分钟K线数据"
    }
}
```

`migrations/env.py` 配置要点：
- 从 `config/db_config.json` 读取数据库连接参数，拼接为SQLAlchemy URL
- 密码从环境变量读取（`password_env`字段指定环境变量名），不硬编码
- 使用 `op.execute()` 执行raw SQL（支持分区表等PostgreSQL特性）
- 不使用 `target_metadata`（不依赖SQLAlchemy模型autogenerate）
- 保留最小化 `alembic.ini`（仅含 `script_location = migrations`，Alembic CLI必需）

---

## 六、执行脚本(tools)

### 6.1 设计原则

- 执行脚本放在 `tools/` 目录，不属于主干功能
- 仅调用lib模块完成具体工作，不包含业务逻辑
- 使用 `argparse` 提供命令行接口
- 脚本可通过 `python tools/xxx.py` 直接运行

### 6.2 脚本清单

| 脚本 | 功能 | 调用 |
|------|------|------|
| `tools/import_ths_kline.py` | 导入主控脚本 | 调用 `ThsImporter.import_period()` |
| `tools/init_db.py` | 数据库初始化 | 执行 `alembic upgrade head` |
| `tools/check_status.py` | 导入状态查询 | 调用 `ThsImporter.get_import_status()` |

### 6.3 命令行参数设计

```bash
# 导入1分钟线全部数据
python tools/import_ths_kline.py --period 1m

# 导入5分钟线全部数据
python tools/import_ths_kline.py --period 5m

# 导入单月数据
python tools/import_ths_kline.py --period 1m --month 202302

# 查看导入状态
python tools/import_ths_kline.py --status

# 初始化数据库
python tools/init_db.py

# 查询导入进度
python tools/check_status.py
```

---

## 七、性能优化策略

### 7.1 写入优化

| 策略 | 说明 | 预期提升 |
|------|------|---------|
| 批量写入 | execute_values, 每批5000条 | 10x vs 逐条INSERT |
| 事务块 | 每个zip一个事务 | 减少提交开销 |
| ON CONFLICT DO NOTHING | 跳过重复, 避免报错 | 避免回滚 |
| 导入前删索引 | 导入完再重建 | 2-3x |
| UNLOGGED TABLE | 导入阶段禁用WAL | 2x(导入完成后转LOGGED) |

### 7.2 内存优化

| 策略 | 说明 |
|------|------|
| 流式读取 | 不解压到磁盘, 从zip流直接读取 |
| 逐文件处理 | 每个CSV文件独立处理, 不累积 |
| 批量提交 | 每5000条提交一次, 释放内存 |
| 分月导入 | 按月分批, 避免一次性处理全部 |

### 7.3 并发优化

| 策略 | 说明 |
|------|------|
| 单线程写入 | PostgreSQL单连接写入, 避免锁竞争 |
| 顺序导入 | 1m → 5m, 避免IO竞争 |

---

## 八、数据验证规则

### 8.1 导入时验证

| 规则 | 处理 |
|------|------|
| 交易时间不在09:30-11:30/13:00-15:00 | 记录WARNING, 仍导入 |
| open/close/high/low为0或空 | 跳过该行, 记录ERROR |
| high < low | 跳过该行, 记录ERROR |
| volume < 0 | 跳过该行, 记录ERROR |
| code不在主板范围 | 跳过(非主板) |
| 重复数据(code+market+trade_time) | ON CONFLICT DO NOTHING |

### 8.2 导入后验证

| 规则 | SQL |
|------|-----|
| 每日1分钟线应为240条 | `GROUP BY code, date HAVING COUNT != 240` |
| 成交量/成交额不应为0 | `WHERE volume = 0 OR amount = 0` |
| 无跨日数据 | `WHERE DATE(trade_time) != 交易日` |

---

## 九、风险与注意事项

### 9.1 数据风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 1分钟线数据量4.08亿条 | 导入耗时可能超过24小时 | 分月导入, 断点续传 |
| 科学计数法精度丢失 | 成交额可能不精确 | 使用Decimal类型 |
| 早期数据含指数 | 指数数据混入股票表 | 过滤ktype=10 |
| 文件名含特殊字符 | 解码失败 | cp437→gbk回退机制 |

### 9.2 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 磁盘空间不足(预估72GB) | 导入失败 | 提前检查磁盘空间 |
| PostgreSQL连接超时 | 大事务中断 | 设置statement_timeout=0 |
| 内存溢出 | 进程崩溃 | 流式处理+批量提交 |
| 编码解析错误 | 数据丢失 | 多编码回退+错误日志 |

---

## 十、lib命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | 小写下划线 | zip_reader, csv_parser, db_writer |
| 类名 | 大驼峰 | ZipReader, CsvParser, DbWriter, ThsImporter |
| 函数名 | 小写下划线 | parse_1m_row, write_1m_batch, import_period |
| 常量 | 大写下划线 | BATCH_SIZE, DEFAULT_ENCODING |
| 数据类 | 大驼峰+Record后缀 | Kline1mRecord, Kline5mRecord |
