以下是为 **基础实时数据爬虫（A股分钟级全量数据）** 制定的 **Python 代码军规**，作为项目开发与执行的核心规则，必须严格遵守。

---

# Python 代码军规（Code Rules of Engagement）

## 一、项目结构军规

1. **使用包内模块化结构**  
   所有源代码必须放在以项目命名的顶级包内（如 `stock_spider/`），禁止在根目录直接放置 `.py` 文件（除 `setup.py`、`pyproject.toml` 等工程文件外）。

2. **强制目录结构**  
   ```
   stock_spider/               # 顶级包
   ├── __init__.py
   ├── main.py                  # 程序入口
   ├── core/                    # 核心调度、主循环
   ├── data/                    # 数据层（所有接口、存储）
   │   ├── fetcher/             # AkShare / Baostock 封装
   │   ├── storage/             # PostgreSQL 操作
   │   └── models/              # 数据模型定义
   ├── utils/                   # 工具层（日志、告警、限流、配置）
   ├── monitor/                 # 实时监控（指数刷新等）
   └── exceptions.py            # 自定义异常
   ```

3. **测试目录** `tests/` 必须与顶级包同级，且内部结构与源代码一致。

---

## 二、编码风格军规（基于 PEP 8，强制）

1. **缩进**：4 个空格，禁止使用 Tab。
2. **行长度**：最大 79 字符（文档字符串/注释最大 72）。
3. **空行**：  
   - 顶层函数/类之间 **2 个空行**  
   - 类内方法之间 **1 个空行**
4. **导入**：  
   - 每个导入独占一行  
   - 顺序：标准库 → 第三方库 → 本地模块，组间空一行  
   - **禁止** `from module import *`  
   - 禁止相对导入（必须使用绝对导入，如 `from stock_spider.utils.logger import get_logger`）

5. **命名约定**  
   | 类型 | 示例 | 规则 |
   |------|------|------|
   | 变量/函数 | `user_name`, `fetch_data` | 小写 + 下划线 |
   | 类 | `DataFetcher`, `RateLimiter` | 大驼峰 |
   | 常量 | `MAX_RETRY`, `API_TIMEOUT` | 大写 + 下划线 |
   | 私有（模块内/类内） | `_internal_cache` | 单下划线前缀 |
   | 受保护（子类可用） | `_protected_method` | 单下划线 |
   | 魔术方法 | `__init__`, `__enter__` | 双下划线 |

---

## 三、类型注解军规

1. **所有公共函数、方法必须提供完整的类型注解**（参数类型、返回类型）。
2. **变量注解**：在复杂逻辑或宽作用域变量处建议添加注解。
3. 使用 `mypy --strict` 进行类型检查，**零容忍**（CI 中必须通过）。
4. 禁止使用 `Any` 除非与第三方库交互无法避免，此时需用 `# type: ignore` 并注释原因。

```python
# ✅ 正确
def batch_save(records: list[dict[str, object]]) -> int:
    ...

# ❌ 错误
def batch_save(records):
    ...
```

---

## 四、错误与异常军规

1. **捕获具体异常**：禁止使用裸露的 `except:` 或 `except Exception:`（除非在顶层日志记录后再次抛出）。
2. **自定义异常**：所有业务异常必须继承自 `stock_spider.exceptions.SpiderException`。
3. **异常链**：重新抛出时使用 `raise SpiderException(...) from original_exc`。
4. **资源清理**：必须使用 `with` 语句管理文件、网络连接、数据库会话等。
5. **函数内不吞异常**：除非明确处理，否则向上层抛出。

---

## 五、日志与告警军规

1. **禁止使用 `print()`** 输出任何运行时信息，全部使用 `logging`。
2. **日志分级**：
   - `DEBUG`：开发调试细节（默认关闭）
   - `INFO`：关键步骤（启动、数据更新完成、配置加载）
   - `WARNING`：可恢复错误（重试成功、接口限流）
   - `ERROR`：功能受损但程序继续（某股票获取失败）
   - `CRITICAL`：程序即将退出（数据库崩溃、严重配置错误）
3. **日志格式**：`"%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"`
4. **严重错误（CRITICAL）必须触发邮件告警**：使用异步非阻塞方式发送（不阻塞主循环）。
5. **日志轮转**：使用 `RotatingFileHandler`，单文件上限 100MB，保留 10 个备份。

---

## 六、配置与账号管理军规

1. **所有可变配置（数据库连接、API 密钥、账号、限流参数）必须存放在 JSON 配置文件中**，禁止硬编码。
2. 配置文件放在 `config/` 目录，使用环境变量 `CONFIG_PATH` 指定路径。
3. **多账号支持**：  
   - 每个数据源（AkShare / Baostock）配置一个账号列表。  
   - 账号轮换策略：按负载或故障自动切换。
4. 敏感信息（密码、token）**禁止提交到代码仓库**，使用 `.env` + `pydantic` 读取。

---

## 七、数据接口调用军规

1. **调用前必须研究并明确接口边界**：频率限制、单次最大数据量、并发限制等。
2. **实现限流装饰器**：对 AkShare / Baostock 的每次调用施加符合文档的限制（例如每秒最多 5 次）。
3. **重试机制**：网络错误或临时限流使用指数退避（最多 5 次），超出则记录 ERROR 并切换账号。
4. **数据完整性检查**：每个 DataFrame 必须验证关键字段（如 `code`, `close` 等），缺失则丢弃并告警。

---

## 八、数据库军规（PostgreSQL）

1. **连接池**：必须使用 `psycopg2.pool.SimpleConnectionPool` 或 `SQLAlchemy` 连接池。
2. **批量写入**：使用 `psycopg2.extras.execute_values` 单次提交 ≥1000 条，禁止逐条插入。
3. **表结构版本管理**：使用 `Alembic` 管理迁移脚本。
4. **索引**：对查询字段（`code`, `datetime`）建立复合索引。
5. **事务**：大批量写入使用事务块，失败时整体回滚。

---

## 九、实时监控军规

1. **指数刷新**：`monitor/` 模块必须每 60 秒（±1 秒）刷新上证/深证指数，时间漂移需补偿。
2. **独立线程**：监控任务与数据采集任务需运行在独立线程，避免互相阻塞。
3. **告警阈值**：指数刷新连续失败 3 次触发 WARNING，5 次触发 ERROR 并邮件通知。

---

## 十、性能与资源军规

1. **HTTP 会话复用**：使用 `requests.Session`，并在应用生命周期内保持。
2. **异步/并发**：I/O 密集型任务（爬虫、数据库写入）使用 `ThreadPoolExecutor`（上限 5 线程）；CPU 密集型使用 `ProcessPoolExecutor`。
3. **内存控制**：历史数据回溯必须分块处理（例如每月一批），禁止一次性加载所有年份数据到内存。
4. **避免循环导入**：使用延迟导入（`import` 写在函数内）或重构模块依赖。

---

## 十一、测试军规

1. **测试框架**：统一使用 `pytest` + `pytest-cov`。
2. **覆盖率目标**：核心业务逻辑（`data/`, `monitor/`） ≥ 95%，整体 ≥ 80%。
3. **测试分类**：单元测试（`tests/unit/`）、集成测试（`tests/integration/`，需 Docker 数据库）。
4. **Mock 外部依赖**：对 AkShare、Baostock、数据库的连接必须使用 `unittest.mock` 模拟。
5. **每个 PR/提交必须运行完整测试套件**，失败不可合并。

---

## 十二、工程化与交付军规

1. **环境管理**：强制使用 `conda` 且环境名固定为 `agent`（`conda activate agent`）。
2. **依赖导出**：`conda env export > environment.yml` 并提交到仓库。
3. **代码检查工具**：`pre-commit` 必须配置以下 hooks：
   - `black`（自动格式化）
   - `isort`（排序导入）
   - `flake8`（代码检查）
   - `mypy`（类型检查）
4. **后台运行**：提供 `scripts/start.sh`（Linux/Mac）支持 `nohup` 或 `systemd` 方式启动，且具备自动重启能力。
5. **文档**：每个模块必须包含 `README.md`，且函数 docstring 覆盖率达到 100%。

---

## 十三、严重违规后果

任何违反上述军规的代码 **不得合入主分支**。CI 流水线中任一检查（类型、格式、测试、覆盖率）失败则阻断合并。

> 本军规即日起生效，所有贡献者必须遵守。未尽事宜参考 [PEP 8](https://pep8.org/) 与 [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)。
> 