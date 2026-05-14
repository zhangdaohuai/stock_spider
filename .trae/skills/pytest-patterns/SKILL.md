---
name: pytest-patterns
description: >-
  Python backend testing patterns with pytest for FastAPI applications. Use when writing
  Python tests: unit tests for services and repositories, integration tests for API
  endpoints with httpx.AsyncClient, fixture creation, factory setup with factory_boy,
  async testing with pytest-asyncio, mocking strategies, and parametrized tests.
  Covers test organization (tests/unit, tests/integration), conftest hierarchy, and
  coverage requirements. Does NOT cover frontend tests (use react-testing-patterns)
  or E2E browser tests (use e2e-testing).
license: MIT
compatibility: 'Python 3.12+, pytest 8+, pytest-asyncio, httpx, factory_boy'
metadata:
  author: platform-team
  version: '1.0.0'
  sdlc-phase: testing
allowed-tools: Read Edit Write Bash(pytest:*) Bash(python:*)
context: fork
---

# Pytest Patterns

## When to Use

Activate this skill when:
- Writing unit tests for service or repository classes
- Writing integration tests for FastAPI endpoints with httpx.AsyncClient
- Creating or refactoring pytest fixtures and conftest files
- Setting up factory_boy factories for test data
- Testing async code with pytest-asyncio
- Mocking external services (HTTP APIs, email, queues)
- Adding parametrized tests for input variations
- Auditing or improving test coverage

Do NOT use this skill for:
- Frontend React component or hook tests (use `react-testing-patterns`)
- E2E browser tests with Playwright (use `e2e-testing`)
- TDD red-green-refactor workflow enforcement (use `tdd-workflow`)
- Writing application code (use `python-backend-expert`)

## Instructions

### Test Organization

```
tests/
├── conftest.py              # Root conftest: DB session, async client, auth helpers
├── unit/
│   ├── conftest.py          # Unit-specific fixtures (mocked repos, services)
│   ├── services/
│   │   ├── test_user_service.py
│   │   └── test_order_service.py
│   └── repositories/
│       └── test_user_repository.py
├── integration/
│   ├── conftest.py          # Integration-specific fixtures (test DB, seeding)
│   ├── test_users_api.py
│   └── test_orders_api.py
└── factories/
    ├── __init__.py
    ├── user_factory.py
    └── order_factory.py
```

**Naming conventions:**
- Test files: `test_<module>.py`
- Test classes: `Test<Feature>` (group related tests, no `__init__`)
- Test functions: `test_<action>_<expected_outcome>` or `test_<scenario>`
- Fixtures: descriptive noun (`db_session`, `authenticated_client`, `sample_user`)

**Marker conventions:**
```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (no DB, no network)",
    "integration: Integration tests (real DB, real HTTP)",
    "slow: Tests that take > 1 second",
]
asyncio_mode = "auto"
```

Run subsets: `pytest -m unit`, `pytest -m integration`, `pytest -m "not slow"`.

### Fixture Architecture

#### Conftest Hierarchy

Fixtures cascade: root `conftest.py` provides shared fixtures; subdirectory conftest files add layer-specific fixtures.

**Root conftest (tests/conftest.py):**
```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.database import get_db

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

#### Fixture Scopes

| Scope | Use For | Example |
|-------|---------|---------|
| `function` (default) | Isolated per-test data | `db_session`, `sample_user` |
| `class` | Shared across test class | `service_instance` |
| `module` | Shared across test file | `seeded_database` |
| `session` | Shared across entire run | `engine`, `anyio_backend` |

**Rules:**
- Default to `function` scope for data isolation
- Use `session` scope only for expensive, stateless resources (engine, event loop)
- Never use `session` scope for mutable data -- tests will interfere with each other
- Fixtures that yield must clean up (rollback, delete, close)

#### Auth Fixtures

```python
@pytest.fixture
def auth_headers():
    """Return authorization headers for a standard test user."""
    token = create_test_token(user_id=1, role="member")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def authenticated_client(client, auth_headers):
    """AsyncClient pre-configured with auth headers."""
    client.headers.update(auth_headers)
    return client

@pytest.fixture
def admin_headers():
    """Return authorization headers for an admin user."""
    token = create_test_token(user_id=99, role="admin")
    return {"Authorization": f"Bearer {token}"}
```

### Factory Pattern

Use `factory_boy` for consistent, overridable test data.

```python
import factory
from app.models import User, Order

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    email = factory.LazyAttribute(lambda o: f"user{o.id}@example.com")
    display_name = factory.Faker("name")
    role = "member"
    is_active = True

class OrderFactory(factory.Factory):
    class Meta:
        model = Order

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.LazyAttribute(lambda o: UserFactory().id)
    total_cents = factory.Faker("random_int", min=100, max=100000)
    status = "pending"
```

**Usage in tests:**
```python
def test_user_defaults():
    user = UserFactory()
    assert user.is_active is True
    assert user.role == "member"

def test_user_override():
    admin = UserFactory(role="admin", display_name="Admin User")
    assert admin.role == "admin"

def test_user_batch():
    users = UserFactory.build_batch(5)
    assert len(users) == 5
```

**SQLAlchemy integration** (for integration tests that persist to DB):
```python
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = None  # Set per-test via conftest

    # ... fields same as above
```

Set session in conftest:
```python
@pytest.fixture(autouse=True)
def set_factory_session(db_session):
    UserFactory._meta.sqlalchemy_session = db_session
    OrderFactory._meta.sqlalchemy_session = db_session
```

### API Integration Tests

Test FastAPI endpoints with `httpx.AsyncClient` against the real app, but with a test database.

```python
import pytest
from httpx import AsyncClient

class TestUsersAPI:
    """Integration tests for /api/v1/users endpoints."""

    async def test_create_user_success(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post("/api/v1/users", json={
            "email": "new@example.com",
            "display_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "id" in data

    async def test_create_user_duplicate_email(self, authenticated_client, sample_user):
        response = await authenticated_client.post("/api/v1/users", json={
            "email": sample_user.email,
            "display_name": "Duplicate",
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_list_users_pagination(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/users?limit=10&cursor=0")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "next_cursor" in data

    async def test_get_user_not_found(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/users/99999")
        assert response.status_code == 404

    async def test_unauthenticated_request(self, client):
        response = await client.get("/api/v1/users")
        assert response.status_code == 401
```

**Key patterns:**
- Use `authenticated_client` for protected endpoints, plain `client` for auth testing
- Assert status code first, then response body
- Test error paths: 404, 409, 422, 401, 403
- Test pagination parameters
- Never assert on exact timestamps or auto-generated IDs (use `"id" in data`)

### Async Tests

With `asyncio_mode = "auto"` in pyproject.toml, all `async def test_*` functions run automatically.

```python
async def test_async_service_call(db_session):
    service = UserService(db_session)
    user = await service.create_user(email="test@example.com", display_name="Test")
    assert user.id is not None

async def test_concurrent_operations(db_session):
    service = UserService(db_session)
    import asyncio
    results = await asyncio.gather(
        service.get_user(1),
        service.get_user(2),
        service.get_user(3),
    )
    assert len(results) == 3
```

**Common pitfalls:**
- Do NOT mix `sync` and `async` fixtures carelessly -- an async fixture can only be used by async tests
- Always use `pytest-asyncio` (not `anyio` directly) for consistency
- If a test hangs, check for un-awaited coroutines or missing `async` keywords

### Mocking Strategy

**Mock external services -- YES:**
```python
from unittest.mock import AsyncMock, patch

async def test_send_notification(db_session):
    with patch("app.services.notification.EmailClient") as mock_email:
        mock_email.return_value.send = AsyncMock(return_value=True)
        service = NotificationService(db_session)
        result = await service.notify_user(user_id=1, message="Hello")
        assert result is True
        mock_email.return_value.send.assert_called_once()
```

**Mock the database -- NO:**
```python
# BAD: Mocking the database hides real query issues
async def test_user_service(mock_db):
    mock_db.execute.return_value = MockResult([user_dict])  # Don't do this

# GOOD: Use a real test database (SQLite or PostgreSQL in Docker)
async def test_user_service(db_session):
    service = UserService(db_session)
    user = await service.create_user(email="test@example.com", display_name="Test")
    fetched = await service.get_user(user.id)
    assert fetched.email == "test@example.com"
```

**What to mock:**
| Mock | Do Not Mock |
|------|-------------|
| HTTP APIs (use `respx` or `unittest.mock`) | Database queries |
| Email/SMS services | SQLAlchemy sessions |
| File storage (S3, GCS) | Repository methods (in integration tests) |
| Message queues (Redis, RabbitMQ) | Pydantic validation |
| Time/datetime (`freezegun`) | FastAPI dependency injection |
| Random/UUID generation | ORM relationships |

**`respx` for HTTP mocking:**
```python
import respx
from httpx import Response

@respx.mock
async def test_external_api_call():
    respx.get("https://api.example.com/data").mock(
        return_value=Response(200, json={"key": "value"})
    )
    service = ExternalDataService()
    result = await service.fetch_data()
    assert result["key"] == "value"
```

### Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple input/output combinations:

```python
@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("user@sub.domain.com", True),
    ("user+tag@example.com", True),
    ("", False),
    ("not-an-email", False),
    ("@missing-local.com", False),
    ("user@", False),
])
def test_email_validation(email, is_valid):
    if is_valid:
        assert validate_email(email) is True
    else:
        with pytest.raises(ValidationError):
            validate_email(email)
```

**Parametrize with IDs for readable output:**
```python
@pytest.mark.parametrize("status,expected_code", [
    pytest.param("active", 200, id="active-user-ok"),
    pytest.param("suspended", 403, id="suspended-user-forbidden"),
    pytest.param("deleted", 404, id="deleted-user-not-found"),
])
async def test_user_access_by_status(authenticated_client, status, expected_code):
    ...
```

**Parametrize multiple fixtures:**
```python
@pytest.mark.parametrize("role,can_delete", [
    ("admin", True),
    ("member", False),
    ("viewer", False),
])
async def test_delete_permission(client, role, can_delete):
    headers = {"Authorization": f"Bearer {create_test_token(role=role)}"}
    response = await client.delete("/api/v1/users/1", headers=headers)
    if can_delete:
        assert response.status_code == 204
    else:
        assert response.status_code == 403
```

### Coverage Requirements

**Minimum thresholds:**
- Overall: 80% line coverage
- Service layer: 90% (critical business logic)
- Repository layer: 70% (straightforward CRUD)
- Routes: 80% (all success + primary error paths)

**pyproject.toml configuration:**
```toml
[tool.coverage.run]
source = ["app"]
omit = ["app/migrations/*", "app/main.py", "app/__init__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ ==",
    "@overload",
]
```

**Running coverage:**
```bash
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

Use `scripts/check-test-coverage.sh` to automate coverage checks with report output.

### Test Anti-Patterns

**1. Testing implementation details:**
```python
# BAD: Tests internal method calls
def test_service_calls_repo(mock_repo):
    service.create_user(data)
    mock_repo.insert.assert_called_once_with(...)

# GOOD: Tests observable behavior
async def test_create_user(db_session):
    service = UserService(db_session)
    user = await service.create_user(email="a@b.com", display_name="A")
    fetched = await service.get_user(user.id)
    assert fetched is not None
```

**2. Shared mutable state between tests:**
```python
# BAD: Module-level mutable data
users = []

def test_add_user():
    users.append(User(id=1))  # Leaks to other tests

# GOOD: Use fixtures with function scope
@pytest.fixture
def users():
    return [UserFactory()]
```

**3. Overly broad assertions:**
```python
# BAD
assert response.status_code == 200  # Only checks status

# GOOD
assert response.status_code == 200
data = response.json()
assert data["email"] == "test@example.com"
assert data["role"] == "member"
```

**4. Missing error path tests:**
Every endpoint should have tests for at least: success, not found, validation error, and unauthorized.

## API_Tester: 验收级 API 全链路测试

### 核心理念

API_Tester 是独立于 pytest 框架的验收测试模式，用于模拟真实用户请求、验证端到端数据流。与单元/集成测试的区别：

| 维度 | 单元/集成测试 | API_Tester 验收测试 |
|------|-------------|-------------------|
| 运行方式 | `pytest` 框架内 | 独立脚本或 `requests`/`httpx` 直接调用 |
| 目标 | 函数/类级别 | 端到端用户流程 |
| Mock 策略 | mock 外部依赖 | 不 mock（或仅 mock 跨系统边界） |
| 数据校验 | assert 断言 | API 响应 + DB 数据 + 缓存状态 三重校验 |
| 输出格式 | pytest 报告 | 结构化 Test_Report.md |

### HTTP 请求模式

```python
import httpx
from typing import Optional
import json

class APITester:
    """API_Tester — 模拟 HTTP 请求并验证响应"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30)
        self.token: Optional[str] = None

    def login(self, username: str, password: str) -> dict:
        """登录获取 token"""
        resp = self.client.post(f"{self.base_url}/auth/login", json={
            "username": username,
            "password": password,
        })
        self._assert_status(resp, 200, "登录失败")
        data = resp.json()
        self.token = data.get("access_token")
        return data

    def get(self, path: str, expected_status: int = 200) -> dict:
        """GET 请求"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = self.client.get(f"{self.base_url}{path}", headers=headers)
        self._assert_status(resp, expected_status, f"GET {path}")
        return resp.json()

    def post(self, path: str, body: dict, expected_status: int = 201) -> dict:
        """POST 请求"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        } if self.token else {"Content-Type": "application/json"}
        resp = self.client.post(f"{self.base_url}{path}", json=body, headers=headers)
        self._assert_status(resp, expected_status, f"POST {path}")
        return resp.json()

    def put(self, path: str, body: dict, expected_status: int = 200) -> dict:
        """PUT 请求"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = self.client.put(f"{self.base_url}{path}", json=body, headers=headers)
        self._assert_status(resp, expected_status, f"PUT {path}")
        return resp.json()

    def delete(self, path: str, expected_status: int = 204) -> None:
        """DELETE 请求"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = self.client.delete(f"{self.base_url}{path}", headers=headers)
        self._assert_status(resp, expected_status, f"DELETE {path}")

    @staticmethod
    def _assert_status(resp: httpx.Response, expected: int, context: str):
        """断言 HTTP 状态码"""
        if resp.status_code != expected:
            raise AssertionError(
                f"[{context}] 期望 {expected}, 实际 {resp.status_code}\n"
                f"响应体: {resp.text[:500]}"
            )
```

### 用户流程编排

```python
def run_user_registration_flow(api: APITester):
    """完整用户注册流程测试"""
    results = []

    # Step 1: 注册新用户
    user_data = api.post("/users", body={
        "email": "acceptance_test@example.com",
        "password": "SecurePass123!",
        "name": "Acceptance Test User",
    })
    results.append(("POST /users 注册", True, user_data))

    # Step 2: 登录获取 token
    login_data = api.login("acceptance_test@example.com", "SecurePass123!")
    results.append(("POST /auth/login 登录", True, login_data))

    # Step 3: 查询个人信息
    profile = api.get("/users/me")
    results.append(("GET /users/me 个人信息", True, profile))
    assert profile["email"] == "acceptance_test@example.com"

    # Step 4: 更新信息
    updated = api.put("/users/me", body={"name": "Updated Name"})
    results.append(("PUT /users/me 更新", True, updated))

    # Step 5: 删除用户
    api.delete("/users/me", expected_status=204)
    results.append(("DELETE /users/me 删除", True, {}))

    return results


def run_search_flow(api: APITester, query: str):
    """搜索流程测试"""
    api.login("testuser", "testpass")

    # Step 1: 执行搜索
    search_result = api.get(f"/search?q={query}")
    assert "results" in search_result
    assert isinstance(search_result["results"], list)

    # Step 2: 分页验证
    page2 = api.get(f"/search?q={query}&page=2&size=10")
    assert page2.get("page") == 2

    # Step 3: 排序验证
    sorted_result = api.get(f"/search?q={query}&sort=relevance&order=desc")
    items = sorted_result["results"]
    for i in range(len(items) - 1):
        assert items[i]["score"] >= items[i + 1]["score"]

    return search_result
```

### 错误场景覆盖

```python
def test_error_scenarios(api: APITester):
    """错误路径全覆盖"""

    # 未认证访问
    try:
        api.client.get(f"{api.base_url}/users/me")
        raise AssertionError("未认证请求应返回 401")
    except httpx.HTTPStatusError as e:
        assert e.response.status_code == 401

    # 无效输入
    resp = api.client.post(f"{api.base_url}/users", json={
        "email": "invalid-email",
        "password": "short",
    })
    assert resp.status_code == 422

    # 资源不存在
    api.login("testuser", "testpass")
    try:
        api.get("/users/99999999", expected_status=404)
    except AssertionError as e:
        assert "404" in str(e)

    # 权限不足
    try:
        api.get("/admin/dashboard", expected_status=403)
    except AssertionError as e:
        assert "403" in str(e)

    # 重复创建
    api.post("/items", body={"name": "unique-item"})
    try:
        api.post("/items", body={"name": "unique-item"}, expected_status=409)
    except AssertionError as e:
        assert "409" in str(e)
```

### 异步 API 测试 (httpx.AsyncClient)

```python
import asyncio
import httpx

async def run_async_acceptance_tests():
    """异步版本 API_Tester"""
    async with httpx.AsyncClient(timeout=30) as client:
        base = "http://localhost:8000"

        # 并发执行多个请求
        tasks = [
            client.get(f"{base}/health"),
            client.get(f"{base}/metrics"),
            client.get(f"{base}/version"),
        ]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            assert r.status_code == 200

        # WebSocket 测试
        async with client.websocket_connect(f"{base}/ws/events") as ws:
            await ws.send_json({"type": "subscribe", "channel": "updates"})
            msg = await ws.receive_json()
            assert msg["type"] == "subscribed"


if __name__ == "__main__":
    asyncio.run(run_async_acceptance_tests())
```

### 测试结果收集器

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

@dataclass
class TestCaseResult:
    """单条测试用例结果"""
    name: str
    passed: bool
    expected: str
    actual: str
    details: str = ""
    duration_ms: float = 0.0

@dataclass
class AcceptanceTestReport:
    """验收测试报告"""
    test_suite: str
    environment: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime = None
    results: List[TestCaseResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, expected: str,
             actual: str, details: str = ""):
        self.results.append(TestCaseResult(
            name=name, passed=passed,
            expected=expected, actual=actual, details=details
        ))

    def summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A",
        }

    def to_markdown(self) -> str:
        s = self.summary()
        lines = [
            f"# 验收测试报告\n",
            f"- **测试套件**: {self.test_suite}",
            f"- **环境**: {self.environment}",
            f"- **时间**: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 结果总览\n",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总计 | {s['total']} |",
            f"| 通过 ✅ | {s['passed']} |",
            f"| 失败 ❌ | {s['failed']} |",
            f"| 通过率 | {s['rate']} |\n",
            f"\n## 用例详情\n",
            f"| 用例 | 结果 | 预期 | 实际 | 备注 |",
            f"|------|------|------|------|------|",
        ]
        for r in self.results:
            status = "✅" if r.passed else "❌"
            lines.append(
                f"| {r.name} | {status} | {r.expected} | "
                f"{r.actual} | {r.details} |"
            )
        return "\n".join(lines)
```

### 运行入口

```python
def main():
    """验收测试主入口"""
    report = AcceptanceTestReport(
        test_suite="Smart Search API Acceptance Tests",
        environment="staging",
    )

    api = APITester(base_url="http://localhost:8000")

    try:
        # 运行各流程
        run_user_registration_flow(api)
        report.add("用户注册全流程", True, "全部步骤通过", "通过")

        run_search_flow(api, "python fastapi")
        report.add("搜索流程", True, "结果返回+分页+排序正常", "通过")

        test_error_scenarios(api)
        report.add("错误场景覆盖", True, "401/422/404/403/409 全部正确", "通过")

    except Exception as e:
        report.add("异常捕获", False, "无异常", str(e), traceback.format_exc())

    finally:
        report.finished_at = datetime.utcnow()

        # 输出 Markdown 报告
        md_content = report.to_markdown()
        print(md_content)

        # 写入文件
        with open("Test_Report.md", "w", encoding="utf-8") as f:
            f.write(md_content)


if __name__ == "__main__":
    import traceback
    from datetime import datetime
    main()
```

## Examples

See `references/conftest-template.py` for production conftest setup.
See `references/factory-template.py` for factory_boy patterns.
See `references/api-test-template.py` for API integration test patterns.
See `references/service-test-template.py` for service unit test patterns.
See `references/integration-test-template.py` for full integration test patterns.
