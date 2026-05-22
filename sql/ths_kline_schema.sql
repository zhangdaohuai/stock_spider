-- ============================================================
-- 同花顺历史K线数据 PostgreSQL 数据库设计方案
-- 数据来源: stock_data/tdx_data/ 下的zip压缩文件
-- 设计日期: 2026-05-18
-- 版本管理: 通过db_version表与配置文件版本比对，自动升级
-- 重要约束: 只允许升级，绝对禁止降级
-- ============================================================

-- 一、数据源分析
-- --------------------------------------------------------
-- 1分钟K线: 17个月(202110~202302), 7057MB, ~11687只/月
--   字段: code, tdate, open, close, high, low, cjl, cje, cjjj
--   编码: 早期utf-8(仅表头), 后期gbk(含数据)
--
-- 5分钟K线: 19个月(202108~202302), 3807MB
--   字段: code, name, ktype, [fq,] tdate, open, close, high, low, cjl, cje, hsl
--   编码: 同上
--   注意: 早期zip含fq(复权)字段, 后期不含
--
-- 文件名格式: {code}_{name}_{ktype}_{source}(www.waizaowang.com).csv
-- ktype值: 1=股票, 10=指数, 5/15/30/60=K线周期
--
-- 关键发现:
--   - 1分钟线无name/ktype/fq/hsl字段(字段最少)
--   - 5分钟线含name/ktype/hsl, 早期还含fq
--   - cjl=成交量(手), cje=成交额(元), cjjj=成交均价, hsl=换手率
--   - 成交额使用科学计数法(如2.98901E7)
--   - 数据包含指数(000001=上证指数)和股票

-- ============================================================
-- 二、数据库设计(6张表)
-- ============================================================

-- 2.1 数据库版本表(系统启动时首先检查此表)
-- --------------------------------------------------------
-- 用于与config/db_config.json中的db_version字段比对
-- 系统启动时自动检查并升级，只允许升级，绝对禁止降级
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS db_version (
    version      VARCHAR(20)   PRIMARY KEY,
    description  VARCHAR(200)  NOT NULL,
    applied_at   TIMESTAMP     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  db_version IS '数据库Schema版本记录(与配置版本比对，自动升级)';
COMMENT ON COLUMN db_version.version IS '版本号(如001/002/003，与config/db_config.json的db_version对应)';
COMMENT ON COLUMN db_version.description IS '版本描述(如"初始Schema")';
COMMENT ON COLUMN db_version.applied_at IS '版本应用时间';

-- 2.2 股票基本信息表
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_info (
    code        VARCHAR(6)   NOT NULL,
    name        VARCHAR(20)  NOT NULL,
    market      VARCHAR(2)   NOT NULL,
    stock_type  SMALLINT     NOT NULL DEFAULT 1,
    list_date   DATE,
    delist_date DATE,
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_stock_info PRIMARY KEY (code, market)
);

COMMENT ON TABLE  stock_info IS '股票/指数基本信息';
COMMENT ON COLUMN stock_info.code IS '证券代码(6位)';
COMMENT ON COLUMN stock_info.name IS '证券名称';
COMMENT ON COLUMN stock_info.market IS '市场: SH=上海, SZ=深圳';
COMMENT ON COLUMN stock_info.stock_type IS '类型: 1=股票, 10=指数, 2=基金';
COMMENT ON COLUMN stock_info.list_date IS '上市日期';
COMMENT ON COLUMN stock_info.delist_date IS '退市日期(NULL表示未退市)';

CREATE INDEX idx_stock_info_type ON stock_info (stock_type);
CREATE INDEX idx_stock_info_name ON stock_info (name);

-- 2.3 1分钟K线表(核心表, 数据量最大)
-- --------------------------------------------------------
-- 估算: 17个月 × 5000只 × 20天 × 240条 = 约4.08亿条
-- 使用分区表按月分区, 提升查询和写入性能
-- core_code: market(2)+code(6)+YYYYMMDDHHmm(12)=20位，唯一索引防重入
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS kline_1m (
    core_code   VARCHAR(20)  NOT NULL,
    trade_time  TIMESTAMP    NOT NULL,
    code        VARCHAR(6)   NOT NULL,
    market      VARCHAR(2)   NOT NULL,
    open        NUMERIC(10,3),
    close       NUMERIC(10,3),
    high        NUMERIC(10,3),
    low         NUMERIC(10,3),
    volume      BIGINT,
    amount      NUMERIC(18,2),
    avg_price   NUMERIC(10,3),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_kline_1m PRIMARY KEY (core_code)
) PARTITION BY RANGE (trade_time);

COMMENT ON TABLE  kline_1m IS '1分钟K线数据(分区表)';
COMMENT ON COLUMN kline_1m.core_code IS '核心编码: market(2)+code(6)+YYYYMMDDHHmm(12)=20位，唯一索引防重入';
COMMENT ON COLUMN kline_1m.trade_time IS '交易时间(精确到分钟)';
COMMENT ON COLUMN kline_1m.code IS '证券代码';
COMMENT ON COLUMN kline_1m.market IS '市场: SH/SZ';
COMMENT ON COLUMN kline_1m.open IS '开盘价';
COMMENT ON COLUMN kline_1m.close IS '收盘价';
COMMENT ON COLUMN kline_1m.high IS '最高价';
COMMENT ON COLUMN kline_1m.low IS '最低价';
COMMENT ON COLUMN kline_1m.volume IS '成交量(手)';
COMMENT ON COLUMN kline_1m.amount IS '成交额(元)';
COMMENT ON COLUMN kline_1m.avg_price IS '成交均价';

-- 创建月分区(2021-10 ~ 2023-02)
CREATE TABLE kline_1m_202110 PARTITION OF kline_1m
    FOR VALUES FROM ('2021-10-01') TO ('2021-11-01');
CREATE TABLE kline_1m_202111 PARTITION OF kline_1m
    FOR VALUES FROM ('2021-11-01') TO ('2021-12-01');
CREATE TABLE kline_1m_202112 PARTITION OF kline_1m
    FOR VALUES FROM ('2021-12-01') TO ('2022-01-01');
CREATE TABLE kline_1m_202201 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-01-01') TO ('2022-02-01');
CREATE TABLE kline_1m_202202 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-02-01') TO ('2022-03-01');
CREATE TABLE kline_1m_202203 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-03-01') TO ('2022-04-01');
CREATE TABLE kline_1m_202204 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-04-01') TO ('2022-05-01');
CREATE TABLE kline_1m_202205 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-05-01') TO ('2022-06-01');
CREATE TABLE kline_1m_202206 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-06-01') TO ('2022-07-01');
CREATE TABLE kline_1m_202207 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-07-01') TO ('2022-08-01');
CREATE TABLE kline_1m_202208 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-08-01') TO ('2022-09-01');
CREATE TABLE kline_1m_202209 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-09-01') TO ('2022-10-01');
CREATE TABLE kline_1m_202210 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-10-01') TO ('2022-11-01');
CREATE TABLE kline_1m_202211 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-11-01') TO ('2022-12-01');
CREATE TABLE kline_1m_202212 PARTITION OF kline_1m
    FOR VALUES FROM ('2022-12-01') TO ('2023-01-01');
CREATE TABLE kline_1m_202301 PARTITION OF kline_1m
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE kline_1m_202302 PARTITION OF kline_1m
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');

-- 默认分区(容纳超出范围的数据)
CREATE TABLE kline_1m_default PARTITION OF kline_1m DEFAULT;

-- 分区索引
CREATE INDEX idx_kline_1m_time ON kline_1m (trade_time);
CREATE INDEX idx_kline_1m_code_time ON kline_1m (code, trade_time);

-- 2.4 5分钟K线表
-- --------------------------------------------------------
-- 估算: 19个月 × 5000只 × 20天 × 48条 = 约9120万条
-- core_code: market(2)+code(6)+YYYYMMDDHHmm(12)=20位，唯一索引防重入
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS kline_5m (
    core_code   VARCHAR(20)  NOT NULL,
    trade_time  TIMESTAMP    NOT NULL,
    code        VARCHAR(6)   NOT NULL,
    market      VARCHAR(2)   NOT NULL,
    open        NUMERIC(10,3),
    close       NUMERIC(10,3),
    high        NUMERIC(10,3),
    low         NUMERIC(10,3),
    volume      BIGINT,
    amount      NUMERIC(18,2),
    turnover    NUMERIC(8,4),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_kline_5m PRIMARY KEY (core_code)
) PARTITION BY RANGE (trade_time);

COMMENT ON TABLE  kline_5m IS '5分钟K线数据(分区表)';
COMMENT ON COLUMN kline_5m.core_code IS '核心编码: market(2)+code(6)+YYYYMMDDHHmm(12)=20位，唯一索引防重入';
COMMENT ON COLUMN kline_5m.turnover IS '换手率(%)';

CREATE TABLE kline_5m_202108 PARTITION OF kline_5m
    FOR VALUES FROM ('2021-08-01') TO ('2021-09-01');
CREATE TABLE kline_5m_202109 PARTITION OF kline_5m
    FOR VALUES FROM ('2021-09-01') TO ('2021-10-01');
CREATE TABLE kline_5m_202110 PARTITION OF kline_5m
    FOR VALUES FROM ('2021-10-01') TO ('2021-11-01');
CREATE TABLE kline_5m_202111 PARTITION OF kline_5m
    FOR VALUES FROM ('2021-11-01') TO ('2021-12-01');
CREATE TABLE kline_5m_202112 PARTITION OF kline_5m
    FOR VALUES FROM ('2021-12-01') TO ('2022-01-01');
CREATE TABLE kline_5m_202201 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-01-01') TO ('2022-02-01');
CREATE TABLE kline_5m_202202 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-02-01') TO ('2022-03-01');
CREATE TABLE kline_5m_202203 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-03-01') TO ('2022-04-01');
CREATE TABLE kline_5m_202204 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-04-01') TO ('2022-05-01');
CREATE TABLE kline_5m_202205 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-05-01') TO ('2022-06-01');
CREATE TABLE kline_5m_202206 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-06-01') TO ('2022-07-01');
CREATE TABLE kline_5m_202207 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-07-01') TO ('2022-08-01');
CREATE TABLE kline_5m_202208 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-08-01') TO ('2022-09-01');
CREATE TABLE kline_5m_202209 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-09-01') TO ('2022-10-01');
CREATE TABLE kline_5m_202210 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-10-01') TO ('2022-11-01');
CREATE TABLE kline_5m_202211 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-11-01') TO ('2022-12-01');
CREATE TABLE kline_5m_202212 PARTITION OF kline_5m
    FOR VALUES FROM ('2022-12-01') TO ('2023-01-01');
CREATE TABLE kline_5m_202301 PARTITION OF kline_5m
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
CREATE TABLE kline_5m_202302 PARTITION OF kline_5m
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
CREATE TABLE kline_5m_default PARTITION OF kline_5m DEFAULT;

CREATE INDEX idx_kline_5m_time ON kline_5m (trade_time);
CREATE INDEX idx_kline_5m_code_time ON kline_5m (code, trade_time);

-- 2.5 数据导入进度追踪表
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_progress (
    id              SERIAL       PRIMARY KEY,
    period          VARCHAR(4)   NOT NULL,
    zip_file        VARCHAR(50)  NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
    total_files     INTEGER      DEFAULT 0,
    imported_files  INTEGER      DEFAULT 0,
    total_rows      BIGINT       DEFAULT 0,
    error_msg       TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uk_import_progress UNIQUE (period, zip_file)
);

COMMENT ON TABLE  import_progress IS '数据导入进度追踪';
COMMENT ON COLUMN import_progress.period IS '周期: 1m/5m';
COMMENT ON COLUMN import_progress.status IS '状态: pending/running/success/failed';

-- 2.6 月度数据统计表(快速发现数据丢失)
-- --------------------------------------------------------
-- 按月按股票记录K线条数，用于快速检测数据丢失
-- 导入完成后自动统计写入，expected_count根据交易日数计算
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS kline_monthly_stats (
    id              SERIAL       PRIMARY KEY,
    period          VARCHAR(4)   NOT NULL,
    month           VARCHAR(6)   NOT NULL,
    code            VARCHAR(6)   NOT NULL,
    market          VARCHAR(2)   NOT NULL,
    row_count       INTEGER      NOT NULL DEFAULT 0,
    expected_count  INTEGER      NOT NULL DEFAULT 0,
    diff_pct        NUMERIC(8,4) NOT NULL DEFAULT 0,
    checked_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uk_kline_monthly_stats UNIQUE (period, month, code, market)
);

COMMENT ON TABLE  kline_monthly_stats IS '月度K线数据统计(按月按股票记录行数，快速发现数据丢失)';
COMMENT ON COLUMN kline_monthly_stats.period IS '周期: 1m/5m';
COMMENT ON COLUMN kline_monthly_stats.month IS '月份(如202302)';
COMMENT ON COLUMN kline_monthly_stats.code IS '证券代码';
COMMENT ON COLUMN kline_monthly_stats.market IS '市场: SH/SZ';
COMMENT ON COLUMN kline_monthly_stats.row_count IS '实际记录数';
COMMENT ON COLUMN kline_monthly_stats.expected_count IS '预期记录数(1m=240条/日×交易日数, 5m=48条/日×交易日数)';
COMMENT ON COLUMN kline_monthly_stats.diff_pct IS '差异百分比=(row_count-expected_count)/expected_count*100';
COMMENT ON COLUMN kline_monthly_stats.checked_at IS '统计时间';

CREATE INDEX idx_kline_monthly_stats_month ON kline_monthly_stats (period, month);
CREATE INDEX idx_kline_monthly_stats_diff ON kline_monthly_stats (period, diff_pct) WHERE ABS(diff_pct) > 5;

-- ============================================================
-- 三、常用查询示例
-- ============================================================

-- 查询当前数据库版本
-- SELECT * FROM db_version ORDER BY applied_at DESC LIMIT 1;

-- 查询某只股票某日1分钟K线
-- SELECT * FROM kline_1m
-- WHERE code = '000001' AND market = 'SZ'
--   AND trade_time >= '2023-02-01 09:30:00'
--   AND trade_time <  '2023-02-01 15:01:00'
-- ORDER BY trade_time;

-- 查询某只股票某月5分钟K线
-- SELECT * FROM kline_5m
-- WHERE code = '600519' AND market = 'SH'
--   AND trade_time >= '2023-01-01'
--   AND trade_time <  '2023-02-01'
-- ORDER BY trade_time;

-- ============================================================
-- 四、数据量估算与性能建议
-- ============================================================
--
-- 表名              估算行数      磁盘占用(估算)  分区数
-- ----------------  ----------  -------------  ------
-- db_version        ~10         <1MB           -
-- kline_1m          ~4.08亿     ~65GB          17+1
-- kline_5m          ~9120万     ~13GB          19+1
-- stock_info        ~12000      <1MB           -
-- import_progress   ~100        <1MB           -
-- kline_monthly_stats ~200万    <100MB         -
--
-- 性能建议:
-- 1. 使用COPY命令批量导入(比INSERT快10倍以上)
-- 2. 导入前删除索引, 导入后重建
-- 3. 设置maintenance_work_mem = '1GB' 加速索引创建
-- 4. 设置work_mem = '256MB' 加速查询排序
-- 5. 考虑对kline_1m使用UNLOGGED TABLE(导入阶段)
--    导入完成后再转为LOGGED TABLE
-- 6. 定期VACUUM ANALYZE各分区

-- ============================================================
-- 五、版本升级规范
-- ============================================================
--
-- 核心约束: 只允许升级，绝对禁止降级
--
-- 1. db_version表记录已应用的版本，与config/db_config.json的db_version比对
-- 2. 系统启动时自动检查版本，如配置版本>数据库版本则自动升级
-- 3. 如配置版本<数据库版本则报错终止(禁止降级)
-- 4. 所有Schema变更必须通过migration脚本执行，禁止直接修改数据库
-- 5. migration脚本命名: v{NNN}_{description}.py (如v001_initial_schema.py)
-- 6. 每个migration仅包含upgrade()函数，不实现downgrade()
-- 7. migration脚本一旦合入主分支，不可修改，只能新增
-- 8. 每个migration执行成功后，在db_version表插入一条记录
