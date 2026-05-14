---
name: python-testing-patterns
description: "Implement comprehensive testing strategies with pytest, fixtures, mocking, and test-driven development. Use when writing Python tests, setting up test suites, or implementing testing best practices."
risk: safe
source: community
date_added: "2026-02-27"
---

# Python Testing Patterns

Comprehensive guide to implementing robust testing strategies in Python using pytest, fixtures, mocking, parameterization, and test-driven development practices.

## Use this skill when

- Writing unit tests for Python code
- Setting up test suites and test infrastructure
- Implementing test-driven development (TDD)
- Creating integration tests for APIs and services
- Mocking external dependencies and services
- Testing async code and concurrent operations
- Setting up continuous testing in CI/CD
- Implementing property-based testing
- Testing database operations
- Debugging failing tests

## Do not use this skill when

- The task is unrelated to python testing patterns
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## 1. Test Project Structure

```
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # 共享 fixtures
│   ├── test_core.py         # 单元测试
│   ├── unit/                # 单元测试目录
│   │   ├── __init__.py
│   │   └── test_service.py
│   ├── integration/         # 集成测试目录
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── e2e/                 # 端到端测试目录
│       ├── __init__.py
│       └── test_workflow.py
└── pyproject.toml
```

## 2. pytest 配置

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-ra",                       # 显示所有测试结果摘要
    "--strict-markers",          # 未知标记报错
    "--strict-config",           # 配置问题报错
    "--cov=myproject",           # 覆盖率
    "--cov-report=term-missing", # 显示缺失行
    "--cov-fail-under=80",       # 最低覆盖率
]
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:third_party.*",
]

[tool.coverage.run]
branch = true
source = ["src/myproject"]
omit = [
    "*/__main__.py",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "@abstractmethod",
]
fail_under = 80
show_missing = true
```

## 3. Fixtures 模式

### 基础 Fixture

```python
# tests/conftest.py
import pytest
from myproject.db import Database

@pytest.fixture
def db():
    """提供测试数据库"""
    database = Database(":memory:")
    database.init()
    yield database
    database.close()

@pytest.fixture
def sample_data(db):
    """填充测试数据"""
    db.insert({"name": "test"})
    return db
```

### Fixture 作用域

```python
# session 级别：整个测试会话只创建一次
@pytest.fixture(scope="session")
def app():
    application = create_app()
    yield application

# module 级别：每个模块创建一次
@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)

# function 级别（默认）：每个测试函数创建一次
@pytest.fixture
def clean_db(db):
    db.truncate()
    return db
```

### Fixture 依赖组合

```python
@pytest.fixture
def authenticated_client(client, db):
    user = db.create_user("testuser", "password")
    token = create_token(user)
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

## 4. Mock 模式

### unittest.mock 基础

```python
from unittest.mock import Mock, patch, MagicMock

# Mock 对象
mock_service = Mock()
mock_service.get_data.return_value = {"key": "value"}

# patch 装饰器：替换模块中的对象
@patch("myproject.service.external_api.fetch")
def test_with_mock(mock_fetch):
    mock_fetch.return_value = {"status": "ok"}
    result = my_function()
    assert result == {"status": "ok"}

# patch 上下文管理器
def test_with_context():
    with patch("myproject.service.external_api.fetch") as mock_fetch:
        mock_fetch.return_value = {"status": "ok"}
        result = my_function()
    # patch 在 with 块结束后自动恢复
```

### Mock 验证

```python
def test_mock_called():
    mock_service = Mock()
    mock_service.process("input_data")

    mock_service.process.assert_called_once_with("input_data")
    mock_service.process.assert_called_once()

def test_mock_called_multiple():
    mock_service = Mock()
    mock_service.send("msg1")
    mock_service.send("msg2")

    assert mock_service.send.call_count == 2
    mock_service.send.assert_any_call("msg1")
```

### Async Mock

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_mock():
    mock_repo = AsyncMock()
    mock_repo.get_user.return_value = {"id": 1, "name": "test"}

    result = await mock_repo.get_user(1)
    assert result["name"] == "test"
    mock_repo.get_user.assert_awaited_once_with(1)
```

### Property Mock

```python
def test_property_mock():
    mock_obj = Mock()
    type(mock_obj).status = PropertyMock(return_value="active")

    assert mock_obj.status == "active"
```

### pytest-mock (推荐)

pytest-mock 提供 `mocker` fixture，比 `@patch` 更简洁，自动清理无需手动恢复。

```bash
# 安装
uv add --group test pytest-mock
```

```python
# mocker.patch 替代 @patch 装饰器
def test_with_mocker(mocker):
    mock_api = mocker.patch("myproject.service.external_api.fetch")
    mock_api.return_value = {"status": "ok"}

    result = my_function()
    assert result == {"status": "ok"}
    mock_api.assert_called_once()

# mocker.patch.object 替代 patch.object
def test_patch_object(mocker):
    mock_method = mocker.patch.object(MyService, "process")
    mock_method.return_value = "processed"

    service = MyService()
    result = service.process("input")
    assert result == "processed"

# mocker.patch 多个对象
def test_patch_multiple(mocker):
    mock_fetch = mocker.patch("myproject.service.fetch")
    mock_save = mocker.patch("myproject.service.save")
    mock_fetch.return_value = {"data": "test"}
    mock_save.return_value = True

    result = process_and_save()
    assert result is True
    mock_fetch.assert_called_once()
    mock_save.assert_called_once()

# mocker.spy 监听真实调用（不替换实现）
def test_with_spy(mocker):
    spy = mocker.spy(MyService, "process")

    service = MyService()
    result = service.process("input")
    assert result is not None
    spy.assert_called_once_with("input")

# mocker.stub 创建轻量存根
def test_with_stub(mocker):
    stub = mocker.stub(name="callback")
    stub("arg1", "arg2")

    stub.assert_called_once_with("arg1", "arg2")
```

**何时用 mocker vs @patch：**

| 场景 | 推荐 | 理由 |
|------|------|------|
| 单个 mock | `mocker.patch` | 自动清理，无需装饰器 |
| 多个 mock | `mocker.patch` | 避免 `@patch` 嵌套装饰器 |
| 需要保留真实实现 | `mocker.spy` | 监听但不替换 |
| 测试类中所有方法 | `@patch` 装饰器 | 类级别更清晰 |

## 5. 参数化测试

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("", 0),
    ("test", 4),
])
def test_string_length(input, expected):
    assert len(input) == expected

# 命名参数化
@pytest.mark.parametrize("value,expected", [
    pytest.param(0, "zero", id="zero-case"),
    pytest.param(1, "one", id="one-case"),
    pytest.param(-1, "negative", id="negative-case"),
])
def test_classify(value, expected):
    assert classify(value) == expected

# 多维参数化
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    assert x * y == x * y
```

## 6. 异常测试

```python
import pytest
from myproject.core import divide

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

def test_divide_by_zero_message():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(1, 0)

def test_custom_exception():
    with pytest.raises(ValidationError) as exc_info:
        validate_input("")
    assert "empty" in str(exc_info.value)
```

## 7. 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data()
    assert result is not None

# 异步 fixture
@pytest.fixture
async def async_db():
    db = await AsyncDatabase.connect("sqlite+aiosqlite:///:memory:")
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_with_async_fixture(async_db):
    result = await async_db.query("SELECT 1")
    assert result is not None
```

## 8. 属性测试 (Hypothesis)

```python
from hypothesis import given, strategies as st, settings, HealthCheck

@given(st.text())
def test_reverse_is_reversible(s):
    assert reverse_string(reverse_string(s)) == s

@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    assert add(a, b) == add(b, a)

# 自定义策略
user_strategy = st.builds(
    User,
    name=st.text(min_size=1, max_size=50),
    age=st.integers(min_value=0, max_value=150),
    email=st.from_regex(r"[a-z]+@[a-z]+\.[a-z]+"),
)

@given(user_strategy)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_user_serialization(user):
    data = user.to_dict()
    restored = User.from_dict(data)
    assert restored == user
```

## 9. Markers 标记

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.integration
def test_api_call():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature():
    pass

@pytest.mark.xfail(reason="Known bug #123")
def test_known_bug():
    pass
```

## 10. 运行测试

```bash
# 运行全部测试
uv run pytest

# 详细输出
uv run pytest -v

# 运行指定文件
uv run pytest tests/test_core.py

# 运行指定测试函数
uv run pytest tests/test_core.py::test_function_name

# 按名称模式匹配
uv run pytest -k "test_parse"

# 按标记运行
uv run pytest -m "not slow"
uv run pytest -m "integration"

# 首次失败即停
uv run pytest -x

# 只运行上次失败的
uv run pytest --lf

# 先运行上次失败的，再运行其余
uv run pytest --ff

# 并行运行（需 pytest-xdist）
uv run pytest -n auto
```

## 11. 覆盖率

### 分级覆盖率策略

不同代码重要程度不同，应采用分级覆盖率要求：

| 代码类别 | 覆盖率要求 | 优先级 | 示例 |
|---------|-----------|--------|------|
| **安全关键路径** | 100% | 🔴 CRITICAL | 认证/授权、输入验证、SSRF 防护 |
| **核心业务逻辑** | 80-90% | 🟡 HIGH | 订单处理、支付流程、数据转换 |
| **工具/辅助函数** | 70-80% | 🟢 MEDIUM | 格式化、日志、通用工具 |
| **整体项目** | ≥80% | 🟡 HIGH | 全项目平均 |

```toml
# pyproject.toml — 整体覆盖率门槛
[tool.coverage.report]
fail_under = 80
show_missing = true

# 安全关键模块单独配置更高门槛
# 在 CI 中可针对特定模块设置：
# uv run pytest --cov=myproject.auth --cov-fail-under=100
# uv run pytest --cov=myproject --cov-fail-under=80
```

```yaml
# CI 分级覆盖率检查
- name: Test security-critical (100%)
  run: uv run pytest tests/unit/test_auth.py tests/unit/test_validation.py --cov=myproject.auth --cov=myproject.validation --cov-fail-under=100

- name: Test core logic (80%)
  run: uv run pytest tests/unit/test_services.py --cov=myproject.services --cov-fail-under=80

- name: Test overall (80%)
  run: uv run pytest --cov=myproject --cov-fail-under=80
```

### 覆盖率排除项

```toml
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "@abstractmethod",
    "pass",                    # 空方法/占位符
]
```

### 覆盖率命令

```bash
# 运行并生成覆盖率
uv run pytest --cov=myproject

# 分支覆盖率（推荐开启）
uv run pytest --cov=myproject --cov-branch

# HTML 报告
uv run pytest --cov=myproject --cov-report=html
open htmlcov/index.html

# 只看报告（不运行测试）
uv run coverage report
uv run coverage html

# 指定模块单独检查覆盖率
uv run pytest --cov=myproject.auth --cov-fail-under=100
```

## 12. CI 集成

```yaml
# GitHub Actions
- name: Run tests
  run: |
    uv sync --group test
    uv run pytest --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
```

## 13. Makefile 集成

```makefile
.PHONY: test test-cov test-fast

test:
	uv run pytest

test-cov:
	uv run pytest --cov-report=html
	open htmlcov/index.html

test-fast:
	uv run pytest -x -q --no-cov
```

## 14. 测试结构化写法

### AAA 模式 (Arrange-Act-Assert)

```python
def test_user_creation():
    # Arrange — 准备测试数据和环境
    user_data = {"name": "Alice", "email": "alice@example.com"}
    service = UserService(db=test_db)

    # Act — 执行被测试的操作
    user = service.create(user_data)

    # Assert — 验证结果
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert test_db.query(User).count() == 1
```

### Given-When-Then 模式

```python
def test_password_reset():
    # Given — 已有用户和重置令牌
    user = create_user(email="user@test.com")
    token = generate_reset_token(user)

    # When — 用户使用令牌重置密码
    result = reset_password(token, new_password="NewPass123!")

    # Then — 密码更新成功，旧密码失效
    assert result.success is True
    assert authenticate("user@test.com", "NewPass123!") is not None
    assert authenticate("user@test.com", "OldPass456!") is None
```

## 15. 测试反模式清单

### ❌ 反模式：测试实现细节

```python
# ❌ 错误：测试私有方法和内部状态
def test_private_method():
    service = MyService()
    assert service._internal_counter == 5  # 耦合内部实现

# ✅ 正确：测试公开行为
def test_public_behavior():
    service = MyService()
    result = service.process("input")
    assert result.status == "completed"
```

### ❌ 反模式：Mock 一切

```python
# ❌ 错误：过度 mock 导致测试失去意义
@patch("module.ClassA")
@patch("module.ClassB")
@patch("module.ClassC")
@patch("module.ClassD")
def test_with_too_many_mocks(mock_d, mock_c, mock_b, mock_a):
    # 如果所有依赖都被 mock，你测试的是什么？
    pass

# ✅ 正确：只 mock 外部边界，内部逻辑用真实对象
def test_with_minimal_mock(mocker):
    # 只 mock 外部 API 调用
    mocker.patch("module.external_api.call")
    # 内部服务用真实实例
    service = MyService(real_repo=InMemoryRepo())
    result = service.process("input")
    assert result.status == "completed"
```

### ❌ 反模式：测试之间有依赖

```python
# ❌ 错误：测试依赖执行顺序
class TestUserFlow:
    def test_step1_create(self):
        self.user_id = create_user()  # 存到 self 上

    def test_step2_update(self):
        update_user(self.user_id)  # 依赖 step1 的结果

# ✅ 正确：每个测试独立，通过 fixture 准备数据
def test_update_user(db_with_user):
    result = update_user(db_with_user.user_id, name="New")
    assert result.name == "New"

def test_delete_user(db_with_user):
    result = delete_user(db_with_user.user_id)
    assert result.success is True
```

### ❌ 反模式：模糊的断言

```python
# ❌ 错误：断言太宽泛
def test_api_response():
    response = call_api()
    assert response is not None  # 几乎不会失败
    assert isinstance(response, dict)  # 没验证具体值

# ✅ 正确：精确断言
def test_api_response():
    response = call_api()
    assert response["status"] == 200
    assert response["data"]["name"] == "expected_name"
    assert len(response["data"]["items"]) == 3
```

### ❌ 反模式：忽略异常路径

```python
# ❌ 错误：只测试 happy path
def test_divide():
    assert divide(10, 2) == 5

# ✅ 正确：同时测试 happy path 和错误路径
def test_divide_happy():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(10, 0)

def test_divide_negative():
    assert divide(-10, 2) == -5
```

### ❌ 反模式：硬编码测试数据

```python
# ❌ 错误：魔法值散落各处
def test_calculation():
    result = calculate(42, 17, 3.14)
    assert result == 131.88

# ✅ 正确：命名常量 + 参数化
EXPECTED_RESULT = 131.88

def test_calculation():
    result = calculate(base=42, multiplier=17, factor=3.14)
    assert result == EXPECTED_RESULT

@pytest.mark.parametrize("base,multiplier,factor,expected", [
    (42, 17, 3.14, 131.88),
    (0, 10, 2.0, 0.0),
    (-1, 5, 1.0, -5.0),
])
def test_calculation_parametrized(base, multiplier, factor, expected):
    assert calculate(base, multiplier, factor) == expected
```

### ❌ 反模式：不验证 Mock 调用

```python
# ❌ 错误：mock 了但不验证
def test_with_mock(mocker):
    mock_save = mocker.patch("module.save")
    process_data("input")
    # 没验证 save 是否被调用、参数是否正确

# ✅ 正确：验证 mock 调用
def test_with_mock(mocker):
    mock_save = mocker.patch("module.save")
    process_data("input")
    mock_save.assert_called_once_with({"processed": "input"})
```

### ❌ 反模式：测试代码重复

```python
# ❌ 错误：每个测试重复 setup
def test_create_user():
    db = Database(":memory:")
    db.init()
    service = UserService(db)
    result = service.create("Alice")
    assert result.name == "Alice"

def test_update_user():
    db = Database(":memory:")
    db.init()
    service = UserService(db)
    service.create("Alice")
    result = service.update("Alice", name="Bob")
    assert result.name == "Bob"

# ✅ 正确：提取 fixture 消除重复
@pytest.fixture
def user_service():
    db = Database(":memory:")
    db.init()
    return UserService(db)

def test_create_user(user_service):
    result = user_service.create("Alice")
    assert result.name == "Alice"

def test_update_user(user_service):
    user_service.create("Alice")
    result = user_service.update("Alice", name="Bob")
    assert result.name == "Bob"
```

## 16. 常见测试模式

```python
from httpx import AsyncClient, ASGITransport
from myproject.main import app

@pytest.mark.asyncio
async def test_create_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/users", json={"name": "test"})
        assert response.status_code == 201
```

### 测试数据库操作

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()

def test_create_user(db_session):
    user = User(name="test")
    db_session.add(user)
    db_session.commit()

    result = db_session.query(User).first()
    assert result.name == "test"
```

### 测试外部 API 调用

```python
@patch("myproject.service.requests.get")
def test_fetch_data(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    mock_get.return_value.status_code = 200

    result = fetch_data("http://api.example.com")
    assert result == {"data": "test"}
    mock_get.assert_called_once_with("http://api.example.com")
```

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.

## Limitations

- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
