---
name: redis-development
description: Redis performance optimization and best practices. Use this skill when working with Redis data structures, Redis Query Engine (RQE), vector search with RedisVL, semantic caching with LangCache, or optimizing Redis performance.
license: MIT
metadata:
  author: redis
  version: "1.0.0"
---

# Redis Best Practices

Comprehensive performance optimization guide for Redis, including Redis Query Engine, vector search, and semantic caching. Contains 29 rules across 11 categories, prioritized by impact to guide automated optimization and code generation.

## When to Apply

Reference these guidelines when:
- Designing Redis data models and key structures
- Implementing caching, sessions, or real-time features
- Using Redis Query Engine (FT.CREATE, FT.SEARCH, FT.AGGREGATE)
- Building vector search or RAG applications with RedisVL
- Implementing semantic caching with LangCache
- Optimizing Redis performance and memory usage

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Data Structures & Keys | HIGH | `data-` |
| 2 | Memory & Expiration | HIGH | `ram-` |
| 3 | Connection & Performance | HIGH | `conn-` |
| 4 | JSON Documents | MEDIUM | `json-` |
| 5 | Redis Query Engine | HIGH | `rqe-` |
| 6 | Vector Search & RedisVL | HIGH | `vector-` |
| 7 | Semantic Caching | MEDIUM | `semantic-cache-` |
| 8 | Streams & Pub/Sub | MEDIUM | `stream-` |
| 9 | Clustering & Replication | MEDIUM | `cluster-` |
| 10 | Security | HIGH | `security-` |
| 11 | Observability | MEDIUM | `observe-` |

## Quick Reference

### 1. Data Structures & Keys (HIGH)

- `data-choose-structure` - Choose the Right Data Structure
- `data-key-naming` - Use Consistent Key Naming Conventions

### 2. Memory & Expiration (HIGH)

- `ram-limits` - Configure Memory Limits and Eviction Policies
- `ram-ttl` - Set TTL on Cache Keys

### 3. Connection & Performance (HIGH)

- `conn-blocking` - Avoid Slow Commands in Production
- `conn-pipelining` - Use Pipelining for Bulk Operations
- `conn-pooling` - Use Connection Pooling or Multiplexing
- `conn-timeouts` - Configure Connection Timeouts

### 4. JSON Documents (MEDIUM)

- `json-partial-updates` - Use JSON Paths for Partial Updates
- `json-vs-hash` - Choose JSON vs Hash Appropriately

### 5. Redis Query Engine (HIGH)

- `rqe-dialect` - Use DIALECT 2 for Query Syntax
- `rqe-field-types` - Choose the Correct Field Type
- `rqe-index-creation` - Index Only Fields You Query
- `rqe-index-management` - Manage Indexes for Zero-Downtime Updates
- `rqe-query-optimization` - Write Efficient Queries

### 6. Vector Search & RedisVL (HIGH)

- `vector-algorithm-choice` - Choose HNSW vs FLAT Based on Requirements
- `vector-hybrid-search` - Use Hybrid Search for Better Results
- `vector-index-creation` - Configure Vector Indexes Properly
- `vector-rag-pattern` - Implement RAG Pattern Correctly

### 7. Semantic Caching (MEDIUM)

- `semantic-cache-best-practices` - Configure Semantic Cache Properly
- `semantic-cache-langcache-usage` - Use LangCache for LLM Response Caching

### 8. Streams & Pub/Sub (MEDIUM)

- `stream-choosing-pattern` - Choose Streams vs Pub/Sub Appropriately

### 9. Clustering & Replication (MEDIUM)

- `cluster-hash-tags` - Use Hash Tags for Multi-Key Operations
- `cluster-read-replicas` - Use Read Replicas for Read-Heavy Workloads

### 10. Security (HIGH)

- `security-acls` - Use ACLs for Fine-Grained Access Control
- `security-auth` - Always Use Authentication in Production
- `security-network` - Secure Network Access

### 11. Observability (MEDIUM)

- `observe-commands` - Use Observability Commands for Debugging
- `observe-metrics` - Monitor Key Redis Metrics

## How to Use

Read individual rule files for detailed explanations and code examples:

```
rules/rqe-index-creation.md
rules/vector-rag-pattern.md
```

Each rule file contains:
- Brief explanation of why it matters
- Correct example(s) with explanation
- Either an "Incorrect" example (for anti-patterns that cause real harm) or "When to use / When NOT needed" guidance (for optional features)
- Additional context and references

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`

## Redis_Inspector: 验收级缓存校验

### 核心理念

Redis_Inspector 用于在 API 操作后验证 Redis 缓存是否正确填充、命中、失效。与普通 redis-cli 操作的区别：

| 维度 | 普通 redis-cli | Redis_Inspector 校验 |
|------|---------------|---------------------|
| 目的 | 手动查看数据 | **断言**缓存状态是否符合预期 |
| 触发时机 | 任意时刻 | API 操作**之后自动触发** |
| 输出格式 | 原始值 | ✅/❌ + TTL 检查 + 命中率分析 |
| 关注点 | 数据内容 | 缓存一致性、失效策略、穿透防护 |

### 连接管理

```python
import redis
from typing import Any, Optional


class RedisInspector:
    """Redis_Inspector — 校验 Redis 缓存状态"""

    def __init__(self, host: str = "localhost", port: int = 6379,
                 db: int = 0, password: Optional[str] = None):
        self.client = redis.Redis(
            host=host, port=port, db=db, password=password,
            decode_responses=True,
        )

    def ping(self) -> bool:
        """检查连接"""
        return self.client.ping()

    def get_key(self, key: str) -> Optional[str]:
        """获取 key 的值（String 类型）"""
        return self.client.get(key)

    def get_hash(self, key: str) -> dict:
        """获取 Hash 所有字段"""
        return self.client.hgetall(key)

    def get_ttl(self, key: str) -> int:
        """获取 key 的剩余 TTL (秒)，-1 表示永不过期，-2 表示不存在"""
        return self.client.ttl(key)

    def get_type(self, key: str) -> str:
        """获取 key 的类型"""
        return self.client.type(key)

    def scan_keys(self, pattern: str, count: int = 100) -> list:
        """安全地扫描匹配模式的 keys（避免 KEYS * 阻塞）"""
        cursor = 0
        keys = []
        while True:
            cursor, batch = self.client.scan(cursor, match=pattern, count=count)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys
```

### 基础校验方法

```python
class RedisInspector(RedisInspector):
    # ... 继承上面的连接管理 ...

    def assert_exists(self, key: str, label: str = ""):
        """断言 key 存在"""
        exists = self.client.exists(key)
        if not exists:
            raise AssertionError(
                f"[{label or f'key:{key}'}] 期望 key 存在，实际不存在"
            )

    def assert_not_exists(self, key: str, label: str = ""):
        """断言 key 不存在"""
        exists = self.client.exists(key)
        if exists:
            raise AssertionError(
                f"[{label or f'key:{key}'}] 期望 key 不存在，但存在"
            )

    def assert_value(self, key: str, expected: Any, label: str = ""):
        """断言 String 类型值等于预期"""
        actual = self.client.get(key)
        if actual != expected:
            raise AssertionError(
                f"[{label or f'key:{key}.value'}] "
                f"期望 '{expected}', 实际 '{actual}'"
            )

    def assert_hash_field(self, key: str, field: str, expected: Any,
                          label: str = ""):
        """断言 Hash 字段值等于预期"""
        actual = self.client.hget(key, field)
        if actual != expected:
            raise AssertionError(
                f"[{label or f'{key}.{field}'}] "
                f"期望 '{expected}', 实际 '{actual}'"
            )

    def assert_ttl_range(self, key: str, min_sec: int, max_sec: int,
                         label: str = ""):
        """断言 TTL 在合理范围内"""
        ttl = self.client.ttl(key)
        if ttl == -2:
            raise AssertionError(
                f"[{label or f'key:{key}.ttl'}] key 不存在"
            )
        if ttl < min_sec or ttl > max_sec:
            raise AssertionError(
                f"[{label or f'key:{key}.ttl'}] "
                f"TTL 应在 [{min_sec}, {max_sec}] 秒内, 实际 {ttl} 秒"
            )
        return ttl

    def assert_type(self, key: str, expected_type: str, label: str = ""):
        """断言 key 类型正确"""
        actual_type = self.client.type(key)
        if actual_type != expected_type:
            raise AssertionError(
                f"[{label or f'key:{key}.type'}] "
                f"期望类型 {expected_type}, 实际 {actual_type}"
            )
```

### 缓存写入验证

```python
def verify_cache_write(redis: RedisInspector, cache_key: str,
                       expected_value: dict, ttl_range: tuple = (300, 3600)):
    """API 写入后验证缓存已正确设置"""

    # 1. Key 存在且类型为 hash
    redis.assert_exists(cache_key, label="缓存 key 已创建")
    redis.assert_type(cache_key, "hash", label="缓存类型为 hash")

    # 2. 字段完整
    for field, value in expected_value.items():
        redis.assert_hash_field(cache_key, field, value,
                                label=f"字段 {field} 正确")

    # 3. TTL 合理（默认 5 分钟 ~ 1 小时）
    ttl = redis.assert_ttl_range(cache_key, ttl_range[0], ttl_range[1],
                                 label="TTL 在合理范围")
    print(f"  ✓ 缓存 {cache_key} TTL={ttl}s")

    return True


def verify_user_session_cache(redis: RedisInspector, user_id: int, token: str):
    """用户登录后验证 session 缓存"""

    session_key = f"sessions:user:{user_id}"
    redis.assert_exists(session_key, label="session 缓存已创建")

    session_data = redis.get_hash(session_key)
    assert session_data.get("token") == token, "token 不匹配"
    assert session_data.get("user_id") == str(user_id), "user_id 不匹配"

    # Session TTL 通常较短（如 30 分钟）
    redis.assert_ttl_range(session_key, 1700, 1900,
                           label="session TTL 约 30 分钟")


def verify_search_cache(redis: RedisInspector, query: str):
    """搜索结果缓存验证"""

    cache_key = f"search:result:{query}"
    redis.assert_exists(cache_key, label="搜索结果已缓存")

    result = redis.get_hash(cache_key)
    assert "results" in result, "缺少 results 字段"
    assert "query" in result, "缺少 query 字段"

    # 搜索缓存 TTL 较长（如 10 分钟 ~ 1 小时）
    redis.assert_ttl_range(cache_key, 600, 3600,
                           label="搜索结果 TTL 合理")
```

### 缓存失效验证

```python
def verify_cache_invalidation(redis: RedisInspector, cache_key_pattern: str):
    """API 更新/删除后验证缓存已失效"""

    keys = redis.scan_keys(cache_key_pattern)
    if keys:
        raise AssertionError(
            f"[缓存失效] 期望模式 '{cache_key_pattern}' 下无 key, "
            f"但仍有 {len(keys)} 个: {keys[:5]}"
        )
    print(f"  ✓ 缓存模式 {cache_key_pattern} 已全部失效")


def verify_partial_invalidation(redis: RedisInspector, base_key: str,
                                 invalidated_fields: list):
    """部分失效：Hash 中特定字段被删除或更新"""

    for field in invalidated_fields:
        value = redis.client.hget(base_key, field)
        if value is not None:
            raise AssertionError(
                f"[部分失效] 字段 {base_key}.{field} "
                f"期望已被清除, 实际仍存在: {value}"
            )
    print(f"  ✓ 字段 {invalidated_fields} 已从 {base_key} 清除")
```

### 缓存命中率分析

```python
def analyze_cache_effectiveness(redis: RedisInspector,
                                 prefix: str = "cache:"):
    """分析指定前缀下缓存的命中率相关指标"""

    all_keys = redis.scan_keys(prefix + "*")

    stats = {
        "total_keys": len(all_keys),
        "by_type": {},
        "ttl_distribution": {"no_expiry": 0, "<1min": 0, "1min-1h": 0, ">1h": 0},
        "memory_estimate": 0,
    }

    for key in all_keys:
        key_type = redis.get_type(key)
        stats["by_type"][key_type] = stats["by_type"].get(key_type, 0) + 1

        ttl = redis.get_ttl(key)
        if ttl == -1:
            stats["ttl_distribution"]["no_expiry"] += 1
        elif ttl < 60:
            stats["ttl_distribution"]["<1min"] += 1
        elif ttl < 3600:
            stats["ttl_distribution"]["1min-1h"] += 1
        else:
            stats["ttl_distribution"][">1h"] += 1

    print(f"\n=== 缓存效果分析 (前缀: {prefix}) ===")
    print(f"总 key 数: {stats['total_keys']}")
    print(f"\n按类型分布:")
    for t, cnt in sorted(stats["by_type"].items()):
        print(f"  {t}: {cnt}")
    print(f"\nTTL 分布:")
    for dist, cnt in stats["ttl_distribution"].items():
        print(f"  {dist}: {cnt}")

    return stats


def check_redis_stats(redis: RedisInspector):
    """检查 Redis 服务端统计信息"""

    info = redis.client.info()
    print(f"\n=== Redis 服务状态 ===")
    print(f"版本: {info['redis_version']}")
    print(f"连接数: {info['connected_clients']}")
    print(f"内存使用: {info['used_memory_human']}")
    print(f"命中率: {info.get('keyspace_hits', 0)} / "
          f"{info.get('keyspace_misses', 0)} "
          f"(命中率: {info.get('keyspace_hit_rate', 'N/A')})")

    db_info = info.get("db0", "")
    print(f"DB0 keys: {db_info}")

    return info
```

### 与 APITester / DB_Inspector 联动

```python
def run_full_acceptance_test(api: APITester, db: DBInspector,
                              redis: RedisInspector):
    """三重联动验收测试：API → DB → Redis"""

    report_lines = []

    # ========== 场景 1: 用户注册 ==========
    api.login("admin", "adminpass")

    created = api.post("/users", body={
        "email": "triple_test@example.com",
        "name": "Triple Test User",
    })

    # DB 校验
    user_id = created["id"]
    db.assert_exists("users", where="id = %s",
                     params=(user_id,), label="用户已入库")

    # Redis 校验 — 用户信息可能被缓存
    user_cache_key = f"user:{user_id}"
    try:
        redis.assert_exists(user_cache_key, label="用户信息已缓存")
        report_lines.append(("用户注册", "✅ API+DB+Cache 全通过"))
    except AssertionError:
        report_lines.append(("用户注册", "✅ API+DB 通过 (无缓存要求)"))

    # ========== 场景 2: 搜索请求 ==========
    search_result = api.get("/search?q=redis+cache")

    # DB 校验 — 搜索日志记录
    db.assert_count("search_logs", expected=1,
                    where="query LIKE %s", params=("%redis%",),
                    label="搜索日志已记录")

    # Redis 校验 — 搜索结果被缓存
    search_cache_key = f"search:result:redis+cache"
    redis.assert_exists(search_cache_key, label="搜索结果已缓存到 Redis")
    redis.assert_ttl_range(search_cache_key, 300, 3600,
                           label="搜索缓存 TTL 合理")

    report_lines.append(("搜索流程", "✅ API+DB+Cache 全通过"))

    # ========== 场景 3: 更新触发缓存失效 ==========
    api.put(f"/users/{user_id}", body={"name": "Updated Name"})

    # DB 校验
    db.assert_equals("users", "name", "Updated Name",
                     where="id = %s", params=(user_id,),
                     label="DB 中名称已更新")

    # Redis 校验 — 缓存应失效或更新
    cached_name = redis.client.hget(user_cache_key, "name")
    if cached_name and cached_name != "Updated Name":
        raise AssertionError(
            f"缓存未同步更新: DB='Updated Name', Cache='{cached_name}'"
        )
    report_lines.append(("更新同步", "✅ DB→Cache 一致"))

    # ========== 场景 4: 删除清理所有存储 ==========
    api.delete(f"/users/{user_id}", expected_status=204)

    db.assert_not_exists("users",
                         where="id = %s AND deleted_at IS NULL",
                         params=(user_id,), label="DB 已软删除")

    redis.assert_not_exists(user_cache_key, label="Redis 缓存已清理")
    report_lines.append(("删除清理", "✅ DB+Cache 全部清理"))

    return report_lines
```
