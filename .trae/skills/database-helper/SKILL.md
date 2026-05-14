---
name: database-helper
description: Assists with database schema design, query optimization, migrations, and data modeling. Use when designing database schemas, writing complex SQL queries, optimizing slow queries, creating migrations, choosing appropriate indexes, or working with ORMs and database-specific features.
---

# Database Helper Skill

This skill helps with all aspects of database work including schema design, query writing, optimization, and migrations. Use this whenever you need to design data models, write complex queries, or improve database performance.

## Database Design Principles

### 1. **Normalization Levels**

| Normal Form | Rule | Purpose |
|-------------|------|---------|
| **1NF** | Atomic values only | No repeating groups |
| **2NF** | 1NF + No partial dependencies | Full functional dependency |
| **3NF** | 2NF + No transitive dependencies | Only key dependencies |
| **BCNF** | Every determinant is a candidate key | Stricter 3NF |

### 2. **When to Denormalize**
- Read-heavy workloads
- Complex aggregations needed frequently
- Performance > storage cost
- Reporting/analytics use cases

### 3. **Data Types Selection**

| Data Type | PostgreSQL | MySQL | Use Case |
|-----------|------------|-------|----------|
| **Primary Key** | `BIGSERIAL` / `UUID` | `BIGINT AUTO_INCREMENT` | Identity |
| **String (short)** | `VARCHAR(255)` | `VARCHAR(255)` | Names, emails |
| **String (long)** | `TEXT` | `TEXT` / `LONGTEXT` | Content |
| **Integer** | `INTEGER` / `BIGINT` | `INT` / `BIGINT` | Counts |
| **Decimal** | `NUMERIC(10,2)` | `DECIMAL(10,2)` | Money |
| **Boolean** | `BOOLEAN` | `TINYINT(1)` | Flags |
| **Date/Time** | `TIMESTAMPTZ` | `DATETIME` / `TIMESTAMP` | Events |
| **JSON** | `JSONB` | `JSON` | Flexible data |
| **Enum** | `CREATE TYPE` | `ENUM(...)` | Fixed options |

## Schema Design Patterns

### Basic Entity Table

```sql
-- PostgreSQL
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    uuid            UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending' NOT NULL,
    
    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at      TIMESTAMPTZ,  -- Soft delete
    
    -- Constraints
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_status_valid CHECK (status IN ('pending', 'active', 'inactive', 'banned'))
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### One-to-Many Relationship

```sql
-- Parent table
CREATE TABLE customers (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Child table with foreign key
CREATE TABLE orders (
    id              BIGSERIAL PRIMARY KEY,
    customer_id     BIGINT NOT NULL,
    order_number    VARCHAR(50) UNIQUE NOT NULL,
    total_amount    NUMERIC(12,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key with appropriate action
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON DELETE RESTRICT  -- Prevent deletion if orders exist
        ON UPDATE CASCADE
);

-- Index for the foreign key (critical for JOIN performance)
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

### Many-to-Many Relationship

```sql
-- Entity tables
CREATE TABLE products (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    parent_id   BIGINT REFERENCES categories(id),  -- Self-referencing for hierarchy
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Junction table
CREATE TABLE product_categories (
    product_id      BIGINT NOT NULL,
    category_id     BIGINT NOT NULL,
    is_primary      BOOLEAN DEFAULT FALSE,
    display_order   INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite primary key
    PRIMARY KEY (product_id, category_id),
    
    -- Foreign keys
    CONSTRAINT fk_pc_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_pc_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE CASCADE
);

-- Indexes for junction table
CREATE INDEX idx_pc_product_id ON product_categories(product_id);
CREATE INDEX idx_pc_category_id ON product_categories(category_id);
```

### Polymorphic Associations

```sql
-- Comments that can belong to different entities
CREATE TABLE comments (
    id              BIGSERIAL PRIMARY KEY,
    content         TEXT NOT NULL,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    
    -- Polymorphic reference
    commentable_type    VARCHAR(50) NOT NULL,  -- 'post', 'product', 'article'
    commentable_id      BIGINT NOT NULL,
    
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT comments_type_valid
        CHECK (commentable_type IN ('post', 'product', 'article'))
);

CREATE INDEX idx_comments_polymorphic 
    ON comments(commentable_type, commentable_id);
```

### Audit/History Table

```sql
-- Main table
CREATE TABLE accounts (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    balance     NUMERIC(15,2) DEFAULT 0,
    updated_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Audit table
CREATE TABLE account_history (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL,
    
    -- What changed
    field_name      VARCHAR(50) NOT NULL,
    old_value       TEXT,
    new_value       TEXT,
    
    -- Who/when/why
    changed_by      BIGINT REFERENCES users(id),
    changed_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    change_reason   TEXT,
    
    -- Request context
    ip_address      INET,
    user_agent      TEXT
);

CREATE INDEX idx_account_history_account ON account_history(account_id);
CREATE INDEX idx_account_history_changed_at ON account_history(changed_at DESC);

-- Trigger for automatic auditing
CREATE OR REPLACE FUNCTION audit_account_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.balance IS DISTINCT FROM NEW.balance THEN
        INSERT INTO account_history (account_id, field_name, old_value, new_value)
        VALUES (NEW.id, 'balance', OLD.balance::TEXT, NEW.balance::TEXT);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_accounts
    AFTER UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION audit_account_changes();
```

## Query Patterns

### Pagination

```sql
-- Offset-based (simple but slow for large offsets)
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 20 OFFSET 100;

-- Cursor-based / Keyset pagination (efficient)
SELECT * FROM products
WHERE created_at < '2025-01-15T10:30:00Z'
   OR (created_at = '2025-01-15T10:30:00Z' AND id < 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- With total count (use sparingly)
SELECT 
    *,
    COUNT(*) OVER() as total_count
FROM products
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

### Full-Text Search

```sql
-- PostgreSQL full-text search
ALTER TABLE products ADD COLUMN search_vector tsvector;

UPDATE products SET 
    search_vector = to_tsvector('english', 
        coalesce(name, '') || ' ' || 
        coalesce(description, '')
    );

CREATE INDEX idx_products_search ON products USING GIN(search_vector);

-- Search query
SELECT *, ts_rank(search_vector, query) as rank
FROM products, to_tsquery('english', 'laptop & gaming') query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 20;

-- Trigger to auto-update search vector
CREATE FUNCTION products_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        coalesce(NEW.name, '') || ' ' || 
        coalesce(NEW.description, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_products_search
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION products_search_trigger();
```

### Hierarchical Data (Recursive CTE)

```sql
-- Get all descendants of a category
WITH RECURSIVE category_tree AS (
    -- Base case: start with parent
    SELECT id, name, parent_id, 0 as level, ARRAY[id] as path
    FROM categories
    WHERE id = 1  -- Root category
    
    UNION ALL
    
    -- Recursive case: get children
    SELECT c.id, c.name, c.parent_id, ct.level + 1, ct.path || c.id
    FROM categories c
    INNER JOIN category_tree ct ON c.parent_id = ct.id
    WHERE NOT c.id = ANY(ct.path)  -- Prevent cycles
)
SELECT * FROM category_tree
ORDER BY path;

-- Get all ancestors of a category
WITH RECURSIVE category_ancestors AS (
    SELECT id, name, parent_id, 0 as level
    FROM categories
    WHERE id = 15  -- Starting category
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ca.level + 1
    FROM categories c
    INNER JOIN category_ancestors ca ON c.id = ca.parent_id
)
SELECT * FROM category_ancestors
ORDER BY level DESC;
```

### Aggregate with Grouping

```sql
-- Sales report with rollup
SELECT 
    COALESCE(region, 'TOTAL') as region,
    COALESCE(product_category, 'ALL CATEGORIES') as category,
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as order_count,
    SUM(amount) as total_sales,
    AVG(amount) as avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.id
WHERE order_date >= '2024-01-01'
GROUP BY ROLLUP(region, product_category), DATE_TRUNC('month', order_date)
ORDER BY region NULLS LAST, category NULLS LAST, month;

-- Window functions for running totals
SELECT 
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) as running_total,
    AVG(amount) OVER (
        ORDER BY order_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as seven_day_avg,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) as rn
FROM orders;
```

### UPSERT (Insert or Update)

```sql
-- PostgreSQL ON CONFLICT
INSERT INTO user_preferences (user_id, preference_key, preference_value)
VALUES (123, 'theme', 'dark')
ON CONFLICT (user_id, preference_key)
DO UPDATE SET 
    preference_value = EXCLUDED.preference_value,
    updated_at = CURRENT_TIMESTAMP;

-- MySQL INSERT ... ON DUPLICATE KEY
INSERT INTO user_preferences (user_id, preference_key, preference_value)
VALUES (123, 'theme', 'dark')
ON DUPLICATE KEY UPDATE
    preference_value = VALUES(preference_value),
    updated_at = CURRENT_TIMESTAMP;
```

## Index Strategies

### Index Types

```sql
-- B-Tree (default, most common)
CREATE INDEX idx_users_email ON users(email);

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- Composite index (order matters!)
CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at DESC);

-- Partial index (filter)
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';

-- Covering index (include columns)
CREATE INDEX idx_products_category_covering 
ON products(category_id) 
INCLUDE (name, price);

-- GIN for arrays and JSONB
CREATE INDEX idx_products_tags ON products USING GIN(tags);
CREATE INDEX idx_users_metadata ON users USING GIN(metadata jsonb_path_ops);

-- GiST for geometric/range data
CREATE INDEX idx_locations_coords ON locations USING GIST(coordinates);

-- BRIN for large, naturally ordered tables
CREATE INDEX idx_logs_timestamp ON logs USING BRIN(created_at);
```

### Index Selection Guidelines

| Query Pattern | Index Type | Example |
|---------------|------------|---------|
| Equality (`=`) | B-Tree | `WHERE email = 'x'` |
| Range (`<`, `>`, `BETWEEN`) | B-Tree | `WHERE created_at > '2024-01-01'` |
| Pattern (`LIKE 'abc%'`) | B-Tree | `WHERE name LIKE 'John%'` |
| Pattern (`LIKE '%abc%'`) | GIN + pg_trgm | Full-text search |
| Array contains | GIN | `WHERE tags @> ARRAY['tag1']` |
| JSONB queries | GIN | `WHERE data @> '{"key": "value"}'` |
| Geometry | GiST | `WHERE ST_Contains(area, point)` |
| Time-series data | BRIN | Large append-only tables |

### When NOT to Index

- Small tables (< 1000 rows)
- Columns with low cardinality (e.g., boolean, status)
- Frequently updated columns
- Columns rarely used in WHERE/JOIN/ORDER BY
- Wide indexes on write-heavy tables

## Query Optimization

### EXPLAIN ANALYZE

```sql
-- Get query execution plan with timing
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active'
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 10;

-- Key metrics to look for:
-- - Seq Scan on large tables (needs index?)
-- - Nested Loop with many rows (consider Hash/Merge Join)
-- - High "actual time" values
-- - Big difference between estimated and actual rows
```

### Common Optimization Patterns

```sql
-- ❌ SLOW: Function on indexed column
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';

-- ✅ FAST: Create functional index or use CITEXT
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
-- OR use case-insensitive type
ALTER TABLE users ALTER COLUMN email TYPE CITEXT;

-- ❌ SLOW: OR conditions
SELECT * FROM products WHERE category_id = 1 OR category_id = 2;

-- ✅ FAST: Use IN
SELECT * FROM products WHERE category_id IN (1, 2);

-- ❌ SLOW: SELECT * when not needed
SELECT * FROM users WHERE id = 123;

-- ✅ FAST: Select only needed columns
SELECT id, name, email FROM users WHERE id = 123;

-- ❌ SLOW: Subquery in SELECT
SELECT 
    u.*,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
FROM users u;

-- ✅ FAST: JOIN with aggregation
SELECT u.*, COALESCE(o.order_count, 0) as order_count
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) as order_count 
    FROM orders 
    GROUP BY user_id
) o ON o.user_id = u.id;

-- ❌ SLOW: NOT IN with subquery
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM banned_users);

-- ✅ FAST: LEFT JOIN with NULL check
SELECT u.* FROM users u
LEFT JOIN banned_users b ON b.user_id = u.id
WHERE b.user_id IS NULL;

-- ❌ SLOW: Large OFFSET
SELECT * FROM products ORDER BY created_at DESC LIMIT 20 OFFSET 10000;

-- ✅ FAST: Keyset pagination
SELECT * FROM products 
WHERE created_at < '2024-01-15T10:30:00Z'
ORDER BY created_at DESC 
LIMIT 20;
```

### N+1 Query Prevention

```python
# ❌ N+1 Problem
users = User.query.all()
for user in users:
    orders = Order.query.filter_by(user_id=user.id).all()  # N queries!
    print(f"{user.name}: {len(orders)} orders")

# ✅ Eager loading (SQLAlchemy)
users = User.query.options(joinedload(User.orders)).all()
for user in users:
    print(f"{user.name}: {len(user.orders)} orders")  # No extra queries

# ✅ Subquery loading
users = User.query.options(subqueryload(User.orders)).all()

# ✅ Single query with aggregation
results = db.session.query(
    User,
    func.count(Order.id).label('order_count')
).outerjoin(Order).group_by(User.id).all()
```

## Migrations

### Migration Structure

```python
# Alembic migration (Python)
"""Add user preferences table

Revision ID: a1b2c3d4e5f6
Revises: previous_revision_id
Create Date: 2025-01-15 10:30:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('preference_key', sa.String(100), nullable=False),
        sa.Column('preference_value', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], 
                                 ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'preference_key', 
                            name='uq_user_preferences')
    )
    
    op.create_index('idx_user_preferences_user_id', 
                    'user_preferences', ['user_id'])


def downgrade():
    op.drop_index('idx_user_preferences_user_id')
    op.drop_table('user_preferences')
```

### Safe Migration Patterns

```sql
-- Add column (safe - no lock)
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Add column with default (PostgreSQL 11+ safe)
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;

-- Add NOT NULL constraint (requires data migration)
-- Step 1: Add nullable column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Step 2: Backfill data
UPDATE users SET phone = '' WHERE phone IS NULL;

-- Step 3: Add constraint
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- Add index concurrently (no lock)
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);

-- Rename column (may break app if not coordinated)
-- Consider: add new column, migrate data, drop old column

-- Drop column (coordinate with app deployment)
ALTER TABLE users DROP COLUMN deprecated_field;
```

### Zero-Downtime Migration Pattern

```sql
-- Step 1: Add new column (nullable)
ALTER TABLE users ADD COLUMN new_field VARCHAR(255);

-- Step 2: Deploy app that writes to BOTH old and new columns
-- Step 3: Backfill data
UPDATE users SET new_field = old_field WHERE new_field IS NULL;

-- Step 4: Deploy app that reads from new column
-- Step 5: Add constraints to new column
ALTER TABLE users ALTER COLUMN new_field SET NOT NULL;

-- Step 6: Deploy app that only writes to new column
-- Step 7: Drop old column
ALTER TABLE users DROP COLUMN old_field;
```

## Connection Pooling

```python
# SQLAlchemy with connection pooling
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,           # Maintained connections
    max_overflow=20,        # Extra connections when pool exhausted
    pool_timeout=30,        # Seconds to wait for connection
    pool_recycle=1800,      # Recycle connections after 30 min
    pool_pre_ping=True,     # Verify connection before use
)

# Django settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'CONN_MAX_AGE': 600,  # Keep connections for 10 minutes
        'CONN_HEALTH_CHECKS': True,
    }
}
```

## Database Checklist

### Schema Design
- [ ] Appropriate data types used
- [ ] Primary keys defined
- [ ] Foreign keys with proper actions
- [ ] Constraints for data integrity
- [ ] Indexes for query patterns
- [ ] Soft delete if needed

### Performance
- [ ] EXPLAIN ANALYZE for slow queries
- [ ] Indexes for WHERE/JOIN/ORDER columns
- [ ] No N+1 query patterns
- [ ] Connection pooling configured
- [ ] Query timeout set

### Migrations
- [ ] Reversible migrations
- [ ] No data loss
- [ ] Zero-downtime compatible
- [ ] Tested in staging

## Output Format

When helping with database tasks, provide:

```
## Database Solution

### Schema Design
```sql
[SQL DDL statements]
```

### Query
```sql
[Optimized query]
```

### Indexes Recommended
[Index recommendations with rationale]

### Migration Steps
1. [Step 1]
2. [Step 2]

### Performance Notes
- [Consideration 1]
- [Consideration 2]
```

## Notes

- Always test queries with realistic data volumes
- Use EXPLAIN ANALYZE before and after optimization
- Consider read/write ratio when designing indexes
- Plan for data growth and scalability
- Backup before running migrations
- Monitor query performance in production

## DB_Inspector: 验收级数据一致性校验

### 核心理念

DB_Inspector 用于在 API 测试后验证 Postgres 数据库中的数据是否正确持久化、一致且符合预期。与普通查询的区别：

| 维度 | 普通查询 | DB_Inspector 校验 |
|------|---------|------------------|
| 目的 | 获取数据 | **断言**数据是否符合预期 |
| 触发时机 | 业务逻辑中 | API 操作**之后**自动触发 |
| 输出格式 | 数据集 | ✅/❌ + 差异详情 + 报告条目 |
| 关注点 | 查询性能 | 数据完整性、约束合规、状态流转 |

### 连接管理

```python
import psycopg
from contextlib import contextmanager
from typing import Any, Dict, List, Optional


class DBInspector:
    """DB_Inspector — 校验 Postgres 数据一致性"""

    def __init__(self, dsn: str = "postgresql://user:pass@localhost:5432/testdb"):
        self.dsn = dsn
        self._connection = None

    @contextmanager
    def connect(self):
        """上下文管理器：自动连接/关闭"""
        conn = psycopg.connect(self.dsn, autocommit=True)
        try:
            yield conn
        finally:
            conn.close()

    def execute_one(self, sql: str, params: tuple = None) -> Optional[Dict]:
        """执行查询，返回单行字典"""
        with self.connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchone()

    def execute_all(self, sql: str, params: tuple = None) -> List[Dict]:
        """执行查询，返回所有行"""
        with self.connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def count(self, table: str, where: str = "1=1", params: tuple = None) -> int:
        """快速计数"""
        row = self.execute_one(f"SELECT COUNT(*) AS cnt FROM {table} WHERE {where}", params)
        return row["cnt"] if row else 0
```

### 基础校验方法

```python
class DBInspector(DBInspector):
    # ... 继承上面的连接管理 ...

    def assert_exists(self, table: str, where: str, params: tuple = None,
                     label: str = "") -> Dict:
        """断言记录存在"""
        row = self.execute_one(f"SELECT * FROM {table} WHERE {where}", params)
        if not row:
            raise AssertionError(
                f"[{label or f'{table}.exists'}] "
                f"期望存在记录 WHERE {where}, 但未找到"
            )
        return row

    def assert_not_exists(self, table: str, where: str, params: tuple = None,
                          label: str = ""):
        """断言记录不存在"""
        cnt = self.count(table, where, params)
        if cnt > 0:
            raise AssertionError(
                f"[{label or f'{table}.not_exists'}] "
                f"期望无匹配记录 WHERE {where}, 实际找到 {cnt} 条"
            )

    def assert_count(self, table: str, expected: int,
                     where: str = "1=1", params: tuple = None,
                     label: str = ""):
        """断言记录数量"""
        actual = self.count(table, where, params)
        if actual != expected:
            raise AssertionError(
                f"[{label or f'{table}.count'}] "
                f"期望 {expected} 条, 实际 {actual} 条 (WHERE {where})"
            )

    def assert_equals(self, table: str, field: str, expected: Any,
                      where: str, params: tuple = None, label: str = ""):
        """断言字段值等于预期"""
        row = self.execute_one(f"SELECT {field} FROM {table} WHERE {where}", params)
        actual = row[field] if row else None
        if actual != expected:
            raise AssertionError(
                f"[{label or f'{table}.{field}'}] "
                f"期望 '{expected}', 实际 '{actual}' (WHERE {where})"
            )

    def assert_field_set(self, table: str, fields: Dict[str, Any],
                         where: str, params: tuple = None, label: str = ""):
        """批量断言多个字段值"""
        row = self.assert_exists(table, where, params, label)
        errors = []
        for field, expected in fields.items():
            if row.get(field) != expected:
                errors.append(f"  {field}: 期望={expected!r}, 实际={row.get(field)!r}")
        if errors:
            raise AssertionError(
                f"[{label or 'fields_match'}] 字段不匹配:\n" + "\n".join(errors)
            )
        return row
```

### 用户流程数据校验

```python
def verify_user_registration(db: DBInspector, user_data: dict):
    """注册后校验用户数据完整性"""

    # 1. 用户表有记录
    user = db.assert_exists("users",
        where="email = %s", params=(user_data["email"],),
        label="注册后用户存在")

    # 2. 字段值正确
    db.assert_field_set("users", {
        "name": user_data["name"],
        "status": "active",
        "deleted_at": None,
    }, where="id = %s", params=(user["id"],), label="用户字段完整")

    # 3. 密码已哈希（不是明文）
    password_hash = db.execute_one(
        "SELECT password_hash FROM users WHERE id = %s", (user["id"],)
    )["password_hash"]
    assert not password_hash == user_data["password"], "密码不应明文存储"

    # 4. 时间戳已设置
    db.assert_field_set("users", {
        "created_at": lambda v: v is not None,
        "updated_at": lambda v: v is not None,
    }, where="id = %s", params=(user["id"],), label="时间戳已填充")


def verify_user_deletion(db: DBInspector, user_id: int):
    """删除后校验软删除状态"""

    # 软删除：记录仍在但 deleted_at 不为空
    user = db.assert_exists("users",
        where="id = %s AND deleted_at IS NOT NULL",
        params=(user_id,), label="软删除标记已设置")

    # 关联数据清理（根据业务规则）
    db.assert_not_exists("sessions",
        where="user_id = %s", params=(user_id,),
        label="会话已清理")


def verify_search_result_persistence(db: DBInspector, query: str, result_ids: list):
    """搜索结果数据一致性校验"""

    for rid in result_ids:
        item = db.assert_exists("search_results",
            where="id = %s AND query = %s",
            params=(rid, query), label=f"搜索结果 {rid} 存在")

        # 分数字段合理
        score = item.get("score")
        assert isinstance(score, (int, float)) and score >= 0, \
            f"分数应为非负数, 实际 {score}"
```

### 状态机流转校验

```python
def verify_order_status_flow(db: DBInspector, order_id: int):
    """订单状态流转校验 — 确保状态只能按规则变化"""

    status_history = db.execute_all(
        """
        SELECT status, changed_at FROM order_status_log
        WHERE order_id = %s ORDER BY changed_at ASC
        """, (order_id,)
    )

    valid_transitions = {
        "pending": ["paid", "cancelled"],
        "paid": ["shipped", "refunded"],
        "shipped": ["delivered"],
        "delivered": [],
        "cancelled": [],
        "refunded": [],
    }

    prev_status = None
    for entry in status_history:
        curr_status = entry["status"]
        if prev_status:
            allowed = valid_transitions.get(prev_status, [])
            assert curr_status in allowed, (
                f"非法状态转换: {prev_status} → {curr_status}, "
                f"允许: {allowed}"
            )
        prev_status = curr_status
```

### 外键约束校验

```python
def verify_referential_integrity(db: DBInspector):
    """外键完整性检查 — 无孤儿记录"""

    checks = [
        ("orders.user_id", """
            SELECT o.id FROM orders o LEFT JOIN users u ON o.user_id = u.id
            WHERE u.id IS NULL AND o.deleted_at IS NULL"""),
        ("order_items.order_id", """
            SELECT oi.id FROM order_items oi LEFT JOIN orders o ON oi.order_id = o.id
            WHERE o.id IS NULL"""),
        ("comments.user_id", """
            SELECT c.id FROM comments c LEFT JOIN users u ON c.user_id = u.id
            WHERE u.id IS NULL"""),
    ]

    errors = []
    for name, orphan_sql in checks:
        orphans = db.execute_all(orphan_sql)
        if orphans:
            ids = [str(r["id"]) for r in orphans]
            errors.append(f"{name}: 孤儿记录 IDs=[{', '.join(ids[:10])}]")

    if errors:
        raise AssertionError(f"外键完整性违规:\n" + "\n".join(errors))
```

### 数据量与分布校验

```python
def verify_data_distribution(db: DBInspector):
    """数据分布合理性校验"""

    # 各状态比例合理
    status_dist = db.execute_all("""
        SELECT status, COUNT(*) AS cnt FROM users GROUP BY status ORDER BY cnt DESC
    """)
    total = sum(r["cnt"] for r in status_dist)

    print(f"\n用户状态分布 (总计 {total}):")
    for r in status_dist:
        pct = r["cnt"] / total * 100 if total > 0 else 0
        print(f"  {r['status']}: {r['cnt']} ({pct:.1f}%)")

    # 无异常大表
    large_tables = db.execute_all("""
        SELECT relname AS table_name, n_live_tup AS row_estimate
        FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 10
    """)
    print(f"\nTop 10 大表:")
    for t in large_tables:
        print(f"  {t['table_name']}: ~{t['row_estimate']} 行")
```

### 与 APITester 联动使用

```python
def run_api_then_verify(api: APITester, db: DBInspector):
    """API 请求 + DB 数据联动校验"""

    # Step 1: 通过 API 创建资源
    created = api.post("/articles", body={
        "title": "验收测试文章",
        "content": "这是一篇验收测试内容",
        "category": "tech",
    })
    article_id = created["id"]

    # Step 2: DB 校验数据已正确写入
    article = db.assert_exists("articles",
        where="id = %s", params=(article_id,),
        label="API 创建后文章存在于 DB")

    db.assert_field_set("articles", {
        "title": "验收测试文章",
        "content": "这是一篇验收测试内容",
        "category": "tech",
        "version": 1,
        "is_published": False,
    }, where="id = %s", params=(article_id,), label="文章字段完整")

    # Step 3: 通过 API 更新
    api.put(f"/articles/{article_id}", body={"title": "更新后的标题"})

    # Step 4: DB 校验更新生效
    db.assert_equals("articles", "title", "更新后的标题",
        where="id = %s", params=(article_id,),
        label="API 更新后 DB 同步")

    updated_row = db.execute_one(
        "SELECT version, updated_at FROM articles WHERE id = %s", (article_id,)
    )
    assert updated_row["version"] >= 1, "版本号应递增"

    # Step 5: 通过 API 删除
    api.delete(f"/articles/{article_id}")

    # Step 6: DB 校验删除生效（软删除或硬删除）
    db.assert_not_exists("articles",
        where="id = %s AND deleted_at IS NULL",
        params=(article_id,), label="API 删除后 DB 已移除")

    return {"article_id": article_id, "passed": True}
```
