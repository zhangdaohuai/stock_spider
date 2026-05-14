---
name: modern-python
description: Configures Python projects with modern tooling (uv, ruff, ty). Use when creating projects, writing standalone scripts, or migrating from pip/Poetry/mypy/black.
risk: unknown
source: community
date_added: "2026-02-27"
---

# Modern Python

Guide for modern Python tooling and best practices, based on [trailofbits/cookiecutter-python](https://github.com/trailofbits/cookiecutter-python).

## When to Use This Skill

- Creating a new Python project or package
- Setting up `pyproject.toml` configuration
- Configuring development tools (linting, formatting, testing)
- Writing Python scripts with external dependencies
- Migrating from legacy tools (when user requests it)

## When NOT to Use This Skill

- **User wants to keep legacy tooling**: Respect existing workflows if explicitly requested
- **Python < 3.11 required**: These tools target modern Python
- **Non-Python projects**: Mixed codebases where Python isn't primary

## Anti-Patterns to Avoid

| Avoid | Use Instead |
|-------|-------------|
| `[tool.ty]` python-version | `[tool.ty.environment]` python-version |
| `uv pip install` | `uv add` and `uv sync` |
| Editing pyproject.toml manually to add deps | `uv add <pkg>` / `uv remove <pkg>` |
| `hatchling` build backend | `uv_build` (simpler, sufficient for most cases) |
| Poetry | uv (faster, simpler, better ecosystem integration) |
| requirements.txt | PEP 723 for scripts, pyproject.toml for projects |
| mypy / pyright | ty (faster, from Astral team) |
| `[project.optional-dependencies]` for dev tools | `[dependency-groups]` (PEP 735) |
| Manual virtualenv activation (`source .venv/bin/activate`) | `uv run <cmd>` |
| pre-commit | prek (faster, no Python runtime needed) |

**Key principles:**

- Always use `uv add` and `uv remove` to manage dependencies
- Never manually activate or manage virtual environments—use `uv run` for all commands
- Use `[dependency-groups]` for dev/test/docs dependencies, not `[project.optional-dependencies]`

## Decision Tree

```
What are you doing?
│
├─ Single-file script with dependencies?
│   └─ Use PEP 723 inline metadata (./references/pep723-scripts.md)
│
├─ New multi-file project (not distributed)?
│   └─ Minimal uv setup (see Quick Start below)
│
├─ New reusable package/library?
│   └─ Full project setup (see Full Setup below)
│
└─ Migrating existing project?
    └─ See Migration Guide below
```

## Tool Overview

| Tool | Purpose | Replaces |
|------|---------|----------|
| **uv** | Package/dependency management | pip, virtualenv, pip-tools, pipx, pyenv |
| **ruff** | Linting AND formatting | flake8, black, isort, pyupgrade, pydocstyle |
| **ty** | Type checking | mypy, pyright (faster alternative) |
| **pytest** | Testing with coverage | unittest |
| **prek** | Pre-commit hooks | pre-commit (faster, Rust-native) |

### Security Tools

| Tool | Purpose | When It Runs |
|------|---------|--------------|
| **shellcheck** | Shell script linting | pre-commit |
| **detect-secrets** | Secret detection | pre-commit |
| **actionlint** | Workflow syntax validation | pre-commit, CI |
| **zizmor** | Workflow security audit | pre-commit, CI |
| **pip-audit** | Dependency vulnerability scanning | CI, manual |
| **Dependabot** | Automated dependency updates | scheduled |

## Quick Start: Minimal Project

For simple multi-file projects not intended for distribution:

```bash
# Create project with uv
uv init myproject
cd myproject

# Add dependencies
uv add requests rich

# Add dev dependencies
uv add --group dev pytest ruff ty

# Run code
uv run python src/myproject/main.py

# Run tools
uv run pytest
uv run ruff check .
```

## Full Project Setup

If starting from scratch, ask the user if they prefer to use the Trail of Bits cookiecutter template to bootstrap a complete project with already preconfigured tooling.

```bash
uvx cookiecutter gh:trailofbits/cookiecutter-python
```

### 1. Create Project Structure

```bash
uv init --package myproject
cd myproject
```

This creates:

```
myproject/
├── pyproject.toml
├── README.md
├── src/
│   └── myproject/
│       └── __init__.py
└── .python-version
```

### 2. Configure pyproject.toml

Key sections:

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = [{include-group = "lint"}, {include-group = "test"}, {include-group = "audit"}]
lint = ["ruff", "ty"]
test = ["pytest", "pytest-cov"]
audit = ["pip-audit"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D", "COM812", "ISC001"]

[tool.pytest.ini_options]
addopts = ["--cov=myproject", "--cov-fail-under=80"]

[tool.ty.terminal]
error-on-warning = true

[tool.ty.environment]
python-version = "3.11"

[tool.ty.rules]
possibly-unresolved-reference = "error"
unused-ignore-comment = "warn"
```

### 3. Install Dependencies

```bash
# Install all dependency groups
uv sync --all-groups

# Or install specific groups
uv sync --group dev
```

### 4. Add Makefile

```makefile
.PHONY: dev lint format test build

dev:
	uv sync --all-groups

lint:
	uv run ruff format --check && uv run ruff check && uv run ty check src/

format:
	uv run ruff format .

test:
	uv run pytest

build:
	uv build
```

## Ruff Linter 配置详解

### 规则分类

| 代码 | 分类 | 描述 |
|------|------|------|
| `E`, `W` | pycodestyle | 风格错误和警告 |
| `F` | Pyflakes | 逻辑错误 |
| `I` | isort | 导入排序 |
| `N` | pep8-naming | 命名约定 |
| `D` | pydocstyle | 文档字符串约定 |
| `UP` | pyupgrade | Python 升级建议 |
| `B` | flake8-bugbear | Bug 检测 |
| `S` | flake8-bandit | 安全问题 |
| `A` | flake8-builtins | 内置名称遮蔽 |
| `C4` | flake8-comprehensions | 推导式改进 |
| `DTZ` | flake8-datetimez | 时区感知日期 |
| `T10` | flake8-debugger | 调试器语句 |
| `T20` | flake8-print | print 语句 |
| `PT` | flake8-pytest-style | Pytest 风格 |
| `SIM` | flake8-simplify | 简化建议 |
| `TID` | flake8-tidy-imports | 导入卫生 |
| `ARG` | flake8-unused-arguments | 未使用参数 |
| `ERA` | eradicate | 注释掉的代码 |
| `PL` | Pylint | Pylint 规则 |
| `RUF` | Ruff-specific | Ruff 自有规则 |
| `ANN` | flake8-annotations | 类型注解检查 |

### 推荐忽略

```toml
[tool.ruff.lint]
ignore = [
    "D",        # 文档字符串（选择性启用）
    "COM812",   # 缺少尾逗号（与格式化冲突）
    "ISC001",   # 单行隐式字符串拼接（与格式化冲突）
    "ANN401",   # 动态类型 Any
    "TD002",    # 缺少 TODO 作者
    "TD003",    # 缺少 TODO 链接
    "FIX002",   # 行包含 TODO
]
```

### 按文件忽略

```toml
[tool.ruff.lint.per-file-ignores]
# 测试文件
"tests/**/*.py" = [
    "S101",     # assert 使用
    "PLR2004",  # 魔法值
    "ANN",      # 类型注解
    "D",        # 文档字符串
]
# 脚本
"scripts/**/*.py" = [
    "T20",      # print 语句
    "INP001",   # 隐式命名空间包
]
# __init__.py
"__init__.py" = [
    "F401",     # 未使用导入（re-exports）
]
# 迁移文件
"**/migrations/*.py" = [
    "ALL",      # 忽略全部
]
```

### 导入排序 (isort)

```toml
[tool.ruff.lint.isort]
force-single-line = false
known-first-party = ["myproject"]
required-imports = ["from __future__ import annotations"]
section-order = [
    "future",
    "standard-library",
    "third-party",
    "first-party",
    "local-folder",
]
```

### 格式化配置

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
docstring-code-format = true
docstring-code-line-length = 80
```

## 运行 Ruff

```bash
# Lint 检查
uv run ruff check .
uv run ruff check --fix .               # 自动修复
uv run ruff check --fix --unsafe-fixes . # 包括不安全修复

# 格式化
uv run ruff format .
uv run ruff format --check .            # 仅检查
uv run ruff format --diff .             # 显示差异

# 代码现代化
uv run ruff check --select=UP --fix .   # 自动升级语法
uv run ruff check --select=UP .         # 仅预览
```

## 类型检查 (ty)

```bash
# 添加 ty 到开发依赖
uv add --group dev ty

# 运行类型检查
uv run ty check src/
```

## Migration Guide

### From requirements.txt + pip

**For standalone scripts**: Convert to PEP 723 inline metadata

**For projects**:

```bash
uv init --bare
uv add requests rich  # 逐个添加依赖
uv sync
```

Then:
1. Delete `requirements.txt`, `requirements-dev.txt`
2. Delete virtual environment (`venv/`, `.venv/`)
3. Add `uv.lock` to version control

### From flake8 + black + isort

1. Remove flake8, black, isort via `uv remove`
2. Delete `.flake8`, `[tool.black]`, `[tool.isort]` configs
3. Add ruff: `uv add --group dev ruff`
4. Add ruff configuration (see above)
5. Run `uv run ruff check --fix .` to apply fixes
6. Run `uv run ruff format .` to format

### From mypy / pyright

1. Remove mypy/pyright via `uv remove`
2. Delete `mypy.ini`, `pyrightconfig.json`, or `[tool.mypy]`/`[tool.pyright]` sections
3. Add ty: `uv add --group dev ty`
4. Run `uv run ty check src/`

## Quick Reference: uv Commands

| Command | Description |
|---------|-------------|
| `uv init` | Create new project |
| `uv init --package` | Create distributable package |
| `uv add <pkg>` | Add dependency |
| `uv add --group dev <pkg>` | Add to dependency group |
| `uv remove <pkg>` | Remove dependency |
| `uv sync` | Install dependencies |
| `uv sync --all-groups` | Install all dependency groups |
| `uv run <cmd>` | Run command in venv |
| `uv run --with <pkg> <cmd>` | Run with temporary dependency |
| `uv build` | Build package |
| `uv publish` | Publish to PyPI |

## Quick Reference: Dependency Groups

```toml
[dependency-groups]
dev = ["ruff", "ty"]
test = ["pytest", "pytest-cov", "hypothesis"]
docs = ["sphinx", "myst-parser"]
```

Install with: `uv sync --group dev --group test`

## Best Practices Checklist

- [ ] Use `src/` layout for packages
- [ ] Set `requires-python = ">=3.11"`
- [ ] Configure ruff with `select = ["ALL"]` and explicit ignores
- [ ] Use ty for type checking
- [ ] Enforce test coverage minimum (80%+)
- [ ] Use dependency groups instead of extras for dev tools
- [ ] Add `uv.lock` to version control
- [ ] Use PEP 723 for standalone scripts

## Read Next

- [ruff-config.md](./references/ruff-config.md) - Ruff linting/formatting configuration
- [testing.md](./references/testing.md) - pytest and coverage setup
- [pep723-scripts.md](./references/pep723-scripts.md) - PEP 723 inline script metadata
- [security-setup.md](./references/security-setup.md) - Security hooks and dependency scanning

## Limitations

- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
