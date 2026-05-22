# 数据库建设及升级方案

## 1. 概述

本文档定义同花顺K线数据导入系统的数据库建设及升级方案。

核心原则：

- 使用 Alembic 管理 Schema 版本，只允许升级，绝对禁止降级
- 系统启动时通过 DatabaseManager 自动检查版本并执行升级
- 所有 Schema 变更必须通过 migration 脚本执行，禁止直接修改数据库
- migration 脚本一旦合入主分支，不可修改，只能新增

## 2. 版本号规范

### 2.1 版本号格式

三位数字字符串，如 `"001"`、`"002"`、`"003"`。

### 2.2 版本号规则

- 版本号递增，不可跳过（不允许从 001 直接跳到 003）
- 版本号不可复用（已使用的版本号不可再次使用）

### 2.3 版本号存储位置

版本号存储在两处，系统启动时进行比对：

| 存储位置 | 字段 | 说明 |
|---------|------|------|
| 配置文件 `config/db_config.json` | `db_version` | 当前代码期望的最低数据库版本 |
| 数据库 `db_version` 表 | `version` | 数据库实际已应用的版本 |

### 2.4 版本一致性约束

两者必须满足以下关系之一：

- 配置版本 == 数据库版本 -- 版本一致，跳过升级
- 配置版本 > 数据库版本 -- 允许升级，执行 alembic upgrade head
- 配置版本 < 数据库版本 -- 禁止降级，抛出异常终止

## 3. 数据库表结构

系统共包含 6 张表，详细定义参考 `sql/ths_kline_schema.sql`。

### 3.1 db_version -- 数据库版本记录表

系统启动时首先检查此表，用于与配置文件版本比对。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| version | VARCHAR(20) | PRIMARY KEY | 版本号（如 001/002/003） |
| description | VARCHAR(200) | NOT NULL | 版本描述（如"初始Schema"） |
| applied_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 版本应用时间 |

### 3.2 stock_info -- 股票基本信息表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| code | VARCHAR(6) | PRIMARY KEY (联合) | 证券代码（6位） |
| name | VARCHAR(20) | NOT NULL | 证券名称 |
| market | VARCHAR(2) | PRIMARY KEY (联合) | 市场：SH=上海，SZ=深圳 |
| stock_type | SMALLINT | NOT NULL DEFAULT 1 | 类型：1=股票，10=指数，2=基金 |
| list_date | DATE | | 上市日期 |
| delist_date | DATE | | 退市日期（NULL 表示未退市） |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

索引：

- `idx_stock_info_type` ON (stock_type)
- `idx_stock_info_name` ON (name)

### 3.3 kline_1m -- 1分钟K线表（分区表）

估算数据量：约 4.08 亿条，按月分区。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| core_code | VARCHAR(20) | PRIMARY KEY | 核心编码：market(2)+code(6)+YYYYMMDDHHmm(12)=20位 |
| trade_time | TIMESTAMP | NOT NULL | 交易时间（精确到分钟） |
| code | VARCHAR(6) | NOT NULL | 证券代码 |
| market | VARCHAR(2) | NOT NULL | 市场：SH/SZ |
| open | NUMERIC(10,3) | | 开盘价 |
| close | NUMERIC(10,3) | | 收盘价 |
| high | NUMERIC(10,3) | | 最高价 |
| low | NUMERIC(10,3) | | 最低价 |
| volume | BIGINT | | 成交量（手） |
| amount | NUMERIC(18,2) | | 成交额（元） |
| avg_price | NUMERIC(10,3) | | 成交均价 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

分区策略：PARTITION BY RANGE (trade_time)，初始分区 202110~202302（17个月分区 + 1个默认分区）。

索引：

- `idx_kline_1m_time` ON (trade_time)
- `idx_kline_1m_code_time` ON (code, trade_time)

### 3.4 kline_5m -- 5分钟K线表（分区表）

估算数据量：约 9120 万条，按月分区。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| core_code | VARCHAR(20) | PRIMARY KEY | 核心编码：market(2)+code(6)+YYYYMMDDHHmm(12)=20位 |
| trade_time | TIMESTAMP | NOT NULL | 交易时间 |
| code | VARCHAR(6) | NOT NULL | 证券代码 |
| market | VARCHAR(2) | NOT NULL | 市场：SH/SZ |
| open | NUMERIC(10,3) | | 开盘价 |
| close | NUMERIC(10,3) | | 收盘价 |
| high | NUMERIC(10,3) | | 最高价 |
| low | NUMERIC(10,3) | | 最低价 |
| volume | BIGINT | | 成交量（手） |
| amount | NUMERIC(18,2) | | 成交额（元） |
| turnover | NUMERIC(8,4) | | 换手率（%） |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

分区策略：PARTITION BY RANGE (trade_time)，初始分区 202108~202302（19个月分区 + 1个默认分区）。

索引：

- `idx_kline_5m_time` ON (trade_time)
- `idx_kline_5m_code_time` ON (code, trade_time)

### 3.5 import_progress -- 数据导入进度追踪表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PRIMARY KEY | 自增主键 |
| period | VARCHAR(4) | NOT NULL, UNIQUE (联合) | 周期：1m/5m |
| zip_file | VARCHAR(50) | NOT NULL, UNIQUE (联合) | ZIP 文件名 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 状态：pending/running/success/failed |
| total_files | INTEGER | DEFAULT 0 | 总文件数 |
| imported_files | INTEGER | DEFAULT 0 | 已导入文件数 |
| total_rows | BIGINT | DEFAULT 0 | 总行数 |
| error_msg | TEXT | | 错误信息 |
| started_at | TIMESTAMP | | 开始时间 |
| finished_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

### 3.6 kline_monthly_stats -- 月度数据统计表

按月按股票记录K线条数，用于快速检测数据丢失。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PRIMARY KEY | 自增主键 |
| period | VARCHAR(4) | NOT NULL, UNIQUE (联合) | 周期：1m/5m |
| month | VARCHAR(6) | NOT NULL, UNIQUE (联合) | 月份（如 202302） |
| code | VARCHAR(6) | NOT NULL, UNIQUE (联合) | 证券代码 |
| market | VARCHAR(2) | NOT NULL, UNIQUE (联合) | 市场：SH/SZ |
| row_count | INTEGER | NOT NULL DEFAULT 0 | 实际记录数 |
| expected_count | INTEGER | NOT NULL DEFAULT 0 | 预期记录数（1m=240条/日 x 交易日数，5m=48条/日 x 交易日数） |
| diff_pct | NUMERIC(8,4) | NOT NULL DEFAULT 0 | 差异百分比 = (row_count - expected_count) / expected_count * 100 |
| checked_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 统计时间 |

索引：

- `idx_kline_monthly_stats_month` ON (period, month)
- `idx_kline_monthly_stats_diff` ON (period, diff_pct) WHERE ABS(diff_pct) > 5

## 4. 升级触发机制

系统启动时，由 `DatabaseManager.ensure_schema()` 自动检查并触发升级。

### 4.1 触发条件

| 条件 | 操作 |
|------|------|
| db_version 表不存在 | 执行 `alembic upgrade head`（首次建库） |
| 配置版本 > 数据库版本 | 执行 `alembic upgrade head` |
| 配置版本 == 数据库版本 | 跳过升级，记录 INFO 日志 |
| 配置版本 < 数据库版本 | 抛出异常终止（禁止降级） |

### 4.2 DatabaseManager 方法说明

| 方法 | 说明 |
|------|------|
| `ensure_schema()` | 主入口：检查版本并自动升级 |
| `_get_config_version() -> str` | 读取 config/db_config.json 的 db_version |
| `_get_db_version() -> str \| None` | 查询数据库 db_version 表最新版本 |
| `_run_upgrade() -> None` | 执行 alembic upgrade head |
| `_verify_version(expected: str) -> bool` | 验证升级后版本是否正确 |

## 5. 自动升级流程

```
步骤1: 读取配置版本
  |
  v
  读取 config/db_config.json 的 db_version 字段
  获取配置版本 config_version
  |
  v
步骤2: 检查 db_version 表是否存在
  |
  +---> 表不存在 (首次建库)
  |       |
  |       v
  |     执行 alembic upgrade head
  |       |
  |       v
  |     跳转到步骤6
  |
  v
步骤3: 获取数据库当前版本
  |
  v
  查询 db_version 表最新版本
  获取数据库版本 db_version
  |
  v
步骤4: 版本比对
  |
  +---> config_version > db_version
  |       |
  |       v
  |     步骤5: 执行升级
  |
  +---> config_version == db_version
  |       |
  |       v
  |     跳过升级，记录 INFO 日志
  |       |
  |       v
  |     流程结束
  |
  +---> config_version < db_version
          |
          v
        抛出异常终止（禁止降级）
          |
          v
        流程结束（异常退出）
  |
  v
步骤5: 执行升级
  |
  v
  执行 alembic upgrade head
  |
  v
步骤6: 验证升级结果
  |
  v
  查询 db_version 表最新版本
  比对是否与 config_version 一致
  |
  +---> 一致
  |       |
  |       v
  |     记录 INFO 日志："数据库升级成功，当前版本: {config_version}"
  |       |
  |       v
  |     流程结束
  |
  +---> 不一致
          |
          v
        记录 CRITICAL 日志
        抛出异常终止
          |
          v
        流程结束（异常退出）
```

## 6. 禁止降级约束

### 6.1 原因

降级可能导致数据丢失，具体场景包括：

- 删除列：已写入的列数据将丢失
- 删除分区：分区内的所有数据将丢失
- 缩小字段精度：超出精度的数据将被截断
- 删除表：整表数据将丢失

### 6.2 实现方式

**Migration 脚本层面**：

- 每个 migration 脚本仅实现 `upgrade()` 函数
- `downgrade()` 函数体为 `raise NotImplementedError("禁止降级")`
- Alembic 历史记录不支持回退

**运行时层面**：

- `DatabaseManager` 检测到配置版本 < 数据库版本时，抛出异常终止程序
- 异常类型：`SchemaDowngradeForbiddenError`
- 异常信息包含配置版本和数据库版本，便于排查

## 7. Migration 编写规范

### 7.1 命名规范

格式：`{revision}_{description}.py`

示例：

- `001_initial_schema.py` -- 初始 Schema
- `002_add_kline_monthly_stats.py` -- 新增月度统计表
- `003_add_kline_1m_partition_202303.py` -- 新增 1 分钟线分区

### 7.2 脚本结构

```python
"""revision = '001'
revises = None
create_date = '2026-05-18'
"""

from alembic import op


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS db_version (
            version      VARCHAR(20)   PRIMARY KEY,
            description  VARCHAR(200)  NOT NULL,
            applied_at   TIMESTAMP     NOT NULL DEFAULT NOW()
        );
    """)
    # ... 其他DDL语句 ...

    # 在 db_version 表插入版本记录
    op.execute("""
        INSERT INTO db_version (version, description)
        VALUES ('001', '初始Schema');
    """)


def downgrade() -> None:
    raise NotImplementedError("禁止降级")
```

### 7.3 编写规则

| 规则 | 说明 |
|------|------|
| 仅实现 upgrade() | 每个 migration 只包含 upgrade 逻辑 |
| downgrade() 禁止实现 | 函数体固定为 `raise NotImplementedError("禁止降级")` |
| 插入版本记录 | 每个 migration 执行成功后在 db_version 表插入版本记录 |
| 使用 raw SQL | 使用 `op.execute()` 执行原始 SQL，不使用 autogenerate |
| 不可修改已合入脚本 | migration 脚本一旦合入主分支，不可修改，只能新增 |
| 不可跳过版本号 | 版本号必须连续递增 |

## 8. 新增分区规范

### 8.1 触发条件

当需要导入超出当前分区范围的数据时（如 2023 年 3 月之后的数据），需要创建新的分区。

### 8.2 操作步骤

1. 创建新的 Alembic migration 脚本（如 `003_add_kline_1m_partition_202303.py`）
2. 在 upgrade() 中使用 `op.execute()` 执行分区创建 SQL
3. 修改 `config/db_config.json` 的 `db_version` 为新版本号
4. 系统启动时自动检测版本差异并执行升级

### 8.3 示例 SQL

1 分钟线新增分区：

```sql
-- 新增 2023 年 3 月分区
CREATE TABLE kline_1m_202303 PARTITION OF kline_1m
    FOR VALUES FROM ('2023-03-01') TO ('2023-04-01');

-- 新增 2023 年 4 月分区
CREATE TABLE kline_1m_202304 PARTITION OF kline_1m
    FOR VALUES FROM ('2023-04-01') TO ('2023-05-01');
```

5 分钟线新增分区：

```sql
-- 新增 2023 年 3 月分区
CREATE TABLE kline_5m_202303 PARTITION OF kline_5m
    FOR VALUES FROM ('2023-03-01') TO ('2023-04-01');
```

### 8.4 注意事项

- 分区范围必须连续，不可重叠
- 新增分区前确认默认分区（default partition）中没有落入新分区范围的数据
- 如果默认分区中已有数据，需先使用 `ALTER TABLE ... DETACH PARTITION` 分离默认分区，迁移数据后再重新附加
- 每个分区创建后应执行 `ANALYZE` 更新统计信息

## 9. 异常处理

### 9.1 升级失败

| 项目 | 说明 |
|------|------|
| 日志级别 | CRITICAL |
| 处理方式 | 记录 CRITICAL 日志，抛出异常终止程序 |
| 日志内容 | 包含失败的具体 migration 版本号、错误原因 |
| 恢复方式 | 修复 migration 脚本或数据库状态后重新启动 |

### 9.2 数据库连接失败

| 项目 | 说明 |
|------|------|
| 日志级别 | ERROR |
| 处理方式 | 记录 ERROR 日志，重试 3 次后终止 |
| 重试间隔 | 指数退避：1s、2s、4s |
| 日志内容 | 包含连接参数（不含密码）、错误原因 |
| 恢复方式 | 确认数据库服务状态后重新启动 |

### 9.3 版本比对异常

| 项目 | 说明 |
|------|------|
| 日志级别 | ERROR |
| 处理方式 | 记录 ERROR 日志，终止程序 |
| 触发场景 | 配置版本 < 数据库版本（禁止降级） |
| 日志内容 | 包含配置版本号、数据库版本号 |
| 恢复方式 | 更新配置文件版本号或排查数据库版本来源 |

## 10. 版本历史

| 版本号 | 描述 | 涉及表 |
|--------|------|--------|
| 001 | 初始 Schema | db_version, stock_info, kline_1m（17个月分区+默认分区）, kline_5m（19个月分区+默认分区）, import_progress, kline_monthly_stats |
