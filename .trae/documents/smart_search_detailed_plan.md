# Smart Search 详细改进计划

## 1. 问题分析与现状评估

### 1.1 现有系统架构

**当前系统组件**：
- `SmartSearch` 主类：协调搜索流程
- `PlaywrightSearchEngine`：基于浏览器的搜索引擎
- `FinanceSearchEngine`：基于 HTTP 请求的财经网站搜索
- `LLM` 集成：智谱 AI、DeepSeek、Kimi
- 各种处理器：内容处理、查询处理、空结果处理

### 1.2 问题详细分析

| 问题类型 | 具体表现 | 影响程度 | 根本原因 |
|---------|---------|---------|--------|
| 网络访问 | 新浪财经返回 301 错误，雪球返回 502 错误 | 高 | 网站反爬措施、网络限制 |
| 反爬识别 | Google 搜索触发 reCAPTCHA 验证码 | 高 | 浏览器指纹识别、请求模式异常 |
| 数据获取 | 无法获取有效的财务报告信息 | 高 | 网站结构变化、反爬限制 |
| 存储功能 | 缺少完整的数据存储实现 | 中 | 存储模块未完全实现 |
| 错误处理 | 异常处理不完善，缺乏容错机制 | 中 | 错误处理逻辑简单 |

## 2. 技术架构设计

### 2.1 整体架构

```mermaid
flowchart TD
    Client[客户端] --> SmartSearch[SmartSearch 主类]
    SmartSearch --> SearchEngineFactory[搜索引擎工厂]
    SearchEngineFactory --> PlaywrightEngine[Playwright 搜索引擎]
    SearchEngineFactory --> FinanceEngine[Finance 搜索引擎]
    
    PlaywrightEngine --> CrawlerManager[爬虫管理器]
    CrawlerManager --> EastMoneyCrawler[东方财富网爬虫]
    CrawlerManager --> SinaCrawler[新浪财经爬虫]
    CrawlerManager --> XueQiuCrawler[雪球爬虫]
    CrawlerManager --> TongHuaShunCrawler[同花顺爬虫]
    
    FinanceEngine --> HttpCrawler[HTTP 爬虫]
    
    SmartSearch --> Processors[处理器链]
    Processors --> QueryProcessor[查询处理器]
    Processors --> ContentProcessor[内容处理器]
    Processors --> ReliabilityProcessor[可靠性处理器]
    Processors --> FileDownloader[文件下载器]
    
    SmartSearch --> Storage[存储系统]
    Storage --> DBStorage[数据库存储]
    Storage --> FileStorage[文件存储]
    Storage --> CacheStorage[缓存存储]
    
    SmartSearch --> LLMManager[LLM 管理器]
    LLMManager --> ZhipuLLM[智谱 AI]
    LLMManager --> DeepSeekLLM[DeepSeek]
    LLMManager --> KimiLLM[Kimi]
```

### 2.2 核心组件设计

#### 2.2.1 爬虫系统

| 组件 | 职责 | 技术实现 | 文件路径 |
|-----|-----|---------|--------|
| 爬虫管理器 | 管理多个网站爬虫，协调爬取任务 | 异步任务调度 | `smart_search/core/crawlers/manager.py` |
| 基础爬虫 | 提供通用的爬虫功能 | Playwright 浏览器自动化 | `smart_search/core/crawlers/base.py` |
| 东方财富网爬虫 | 爬取东方财富网的公司信息和财报 | Playwright + CSS 选择器 | `smart_search/core/crawlers/eastmoney.py` |
| 新浪财经爬虫 | 爬取新浪财经的新闻和数据 | Playwright + CSS 选择器 | `smart_search/core/crawlers/sina.py` |
| 雪球爬虫 | 爬取雪球的用户讨论和分析 | Playwright + CSS 选择器 | `smart_search/core/crawlers/xueqiu.py` |
| 同花顺爬虫 | 爬取同花顺的财务数据和指标 | Playwright + CSS 选择器 | `smart_search/core/crawlers/10jqka.py` |

#### 2.2.2 存储系统

| 组件 | 职责 | 技术实现 | 文件路径 |
|-----|-----|---------|--------|
| 存储管理器 | 管理不同类型的存储 | 工厂模式 | `smart_search/core/storage/manager.py` |
| 数据库存储 | 存储结构化财务数据 | PostgreSQL + SQLAlchemy | `smart_search/core/storage/db_storage.py` |
| 文件存储 | 存储下载的文档 | 本地文件系统 | `smart_search/core/storage/file_storage.py` |
| 缓存存储 | 缓存搜索结果 | Redis | `smart_search/core/storage/cache_storage.py` |

#### 2.2.3 处理器系统

| 组件 | 职责 | 技术实现 | 文件路径 |
|-----|-----|---------|--------|
| 查询处理器 | 优化搜索查询 | LLM 集成 | `smart_search/core/processors/query_processor.py` |
| 内容处理器 | 处理和总结搜索结果 | LLM 集成 | `smart_search/core/processors/content_processor.py` |
| 可靠性处理器 | 评估搜索结果可靠性 | 规则引擎 | `smart_search/core/processors/reliability_processor.py` |
| 文件下载器 | 下载和存储文档 | 异步 HTTP 请求 | `smart_search/core/processors/file_downloader.py` |
| 空结果处理器 | 生成搜索建议 | LLM 集成 | `smart_search/core/processors/empty_result_processor.py` |

#### 2.2.4 LLM 系统

| 组件 | 职责 | 技术实现 | 文件路径 |
|-----|-----|---------|--------|
| LLM 管理器 | 管理多个 LLM 提供商 | 工厂模式 + 桶策略 | `smart_search/core/llm/manager.py` |
| 智谱 AI | 提供 LLM 功能 | HTTP API | `smart_search/core/llm/zhipu.py` |
| DeepSeek | 提供 LLM 功能 | HTTP API | `smart_search/core/llm/deepseek.py` |
| Kimi | 提供 LLM 功能 | HTTP API | `smart_search/core/llm/kimi.py` |

## 3. 详细实现计划

### 3.1 爬虫系统实现

#### 3.1.1 基础爬虫 (`base.py`)

**核心功能**：
- 浏览器初始化与管理
- 反爬策略实现
- 通用页面交互
- 基础数据提取

**技术实现**：
```python
class BaseCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    async def init_browser(self):
        # 实现浏览器初始化，包括反爬配置
    
    async def navigate(self, url):
        # 实现页面导航，包括智能等待
    
    async def extract_data(self, selector):
        # 实现数据提取
    
    async def close(self):
        # 实现资源清理
```

#### 3.1.2 东方财富网爬虫 (`eastmoney.py`)

**目标 URL**：`https://so.eastmoney.com/web/s?keyword={公司名称} 财报`

**数据提取**：
- 财报列表：`.result-list li`
- 标题：`h3 a`
- 链接：`h3 a[href]`
- 摘要：`.result-info`
- 日期：`.result-date`

**文档识别**：
- PDF 链接：包含 `.pdf` 的链接
- Excel 链接：包含 `.xlsx` 或 `.xls` 的链接

#### 3.1.3 新浪财经爬虫 (`sina.py`)

**目标 URL**：`https://search.sina.com.cn/?q={公司名称} 财报&c=news`

**数据提取**：
- 新闻列表：`.box-result-list li`
- 标题：`.box-result h2 a`
- 链接：`.box-result h2 a[href]`
- 摘要：`.box-result p`
- 日期：`.box-result .fgray_time`

#### 3.1.4 雪球爬虫 (`xueqiu.py`)

**目标 URL**：`https://xueqiu.com/search?q={公司名称} 财报`

**数据提取**：
- 帖子列表：`.list_items li`
- 标题：`.title a`
- 链接：`.title a[href]`
- 摘要：`.text`
- 作者：`.user-info .name`
- 日期：`.user-info .time`

#### 3.1.5 同花顺爬虫 (`10jqka.py`)

**目标 URL**：`http://so.10jqka.com.cn/s?q={公司名称} 财报`

**数据提取**：
- 资讯列表：`.search-result-list li`
- 标题：`.tit a`
- 链接：`.tit a[href]`
- 摘要：`.des`
- 日期：`.time`

### 3.2 存储系统实现

#### 3.2.1 数据库存储 (`db_storage.py`)

**表结构设计**：

**`company` 表**
| 字段名 | 数据类型 | 描述 |
|-------|---------|------|
| `id` | `SERIAL` | 公司 ID |
| `name` | `VARCHAR(255)` | 公司名称 |
| `code` | `VARCHAR(20)` | 股票代码 |
| `industry` | `VARCHAR(100)` | 所属行业 |
| `created_at` | `TIMESTAMP` | 创建时间 |
| `updated_at` | `TIMESTAMP` | 更新时间 |

**`financial_report` 表**
| 字段名 | 数据类型 | 描述 |
|-------|---------|------|
| `id` | `SERIAL` | 报告 ID |
| `company_id` | `INTEGER` | 公司 ID |
| `year` | `INTEGER` | 报告年份 |
| `report_type` | `VARCHAR(50)` | 报告类型（年报、季报等） |
| `revenue` | `DECIMAL(20,2)` | 营业收入 |
| `net_profit` | `DECIMAL(20,2)` | 净利润 |
| `total_assets` | `DECIMAL(20,2)` | 总资产 |
| `total_liabilities` | `DECIMAL(20,2)` | 总负债 |
| `发布_date` | `DATE` | 发布日期 |
| `created_at` | `TIMESTAMP` | 创建时间 |
| `updated_at` | `TIMESTAMP` | 更新时间 |

**`document` 表**
| 字段名 | 数据类型 | 描述 |
|-------|---------|------|
| `id` | `SERIAL` | 文档 ID |
| `company_id` | `INTEGER` | 公司 ID |
| `title` | `VARCHAR(255)` | 文档标题 |
| `url` | `VARCHAR(500)` | 原始 URL |
| `file_path` | `VARCHAR(500)` | 存储路径 |
| `file_type` | `VARCHAR(50)` | 文件类型 |
| `size` | `INTEGER` | 文件大小 |
| `download_date` | `TIMESTAMP` | 下载日期 |
| `created_at` | `TIMESTAMP` | 创建时间 |

#### 3.2.2 文件存储 (`file_storage.py`)

**存储结构**：
```
storage/
├── documents/
│   ├── {company_name}/
│   │   ├── {year}/
│   │   │   ├── annual_report.pdf
│   │   │   ├── quarterly_report_1.pdf
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── cache/
    └── ...
```

**核心功能**：
- 文档下载
- 文件存储
- 路径管理
- 重复检测

### 3.3 处理器系统实现

#### 3.3.1 查询处理器 (`query_processor.py`)

**核心功能**：
- 查询意图识别
- 查询优化
- 多语言支持

**实现逻辑**：
```python
async def optimize_query(query, topic):
    # 1. 识别查询意图
    # 2. 根据意图优化查询
    # 3. 调用 LLM 进一步优化
    # 4. 返回优化后的查询
```

#### 3.3.2 内容处理器 (`content_processor.py`)

**核心功能**：
- 内容爬取
- 内容解析
- 内容总结

**实现逻辑**：
```python
async def process_content(results, depth):
    # 1. 对每个结果进行深度爬取
    # 2. 解析页面内容
    # 3. 调用 LLM 生成摘要
    # 4. 返回处理后的结果
```

#### 3.3.3 文件下载器 (`file_downloader.py`)

**核心功能**：
- 文档识别
- 文档下载
- 文档存储

**实现逻辑**：
```python
async def download_files(results):
    # 1. 识别结果中的文档链接
    # 2. 下载文档
    # 3. 存储到指定位置
    # 4. 更新结果中的文件信息
    # 5. 返回更新后的结果
```

### 3.4 LLM 系统实现

#### 3.4.1 LLM 管理器 (`manager.py`)

**核心功能**：
- LLM 实例管理
- 桶策略实现
- 故障切换

**实现逻辑**：
```python
def get_llm(provider):
    # 1. 获取指定提供商的 LLM 实例
    # 2. 实现桶策略，选择可用的 API 密钥
    # 3. 处理故障切换
    # 4. 返回 LLM 实例
```

#### 3.4.2 智谱 AI 实现 (`zhipu.py`)

**核心功能**：
- API 调用
- 桶策略支持
- 错误处理

**实现逻辑**：
```python
async def generate(prompt, **kwargs):
    # 1. 选择可用的 API 密钥
    # 2. 构建请求
    # 3. 调用 API
    # 4. 处理响应
    # 5. 返回生成的文本
```

## 4. 数据流与处理流程

### 4.1 搜索流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant SmartSearch as SmartSearch
    participant QueryProcessor as 查询处理器
    participant SearchEngine as 搜索引擎
    participant Crawler as 爬虫
    participant ContentProcessor as 内容处理器
    participant FileDownloader as 文件下载器
    participant Storage as 存储系统
    
    Client->>SmartSearch: 发起搜索请求
    SmartSearch->>QueryProcessor: 处理查询
    QueryProcessor-->>SmartSearch: 返回优化后的查询
    SmartSearch->>SearchEngine: 执行搜索
    SearchEngine->>Crawler: 爬取数据
    Crawler-->>SearchEngine: 返回搜索结果
    SearchEngine-->>SmartSearch: 返回原始结果
    SmartSearch->>ContentProcessor: 处理内容
    ContentProcessor-->>SmartSearch: 返回处理后的结果
    SmartSearch->>FileDownloader: 下载文档
    FileDownloader-->>SmartSearch: 返回带文件信息的结果
    SmartSearch->>Storage: 存储数据
    Storage-->>SmartSearch: 确认存储完成
    SmartSearch-->>Client: 返回最终结果
```

### 4.2 数据存储流程

```mermaid
sequenceDiagram
    participant SmartSearch as SmartSearch
    participant DBStorage as 数据库存储
    participant FileStorage as 文件存储
    participant CacheStorage as 缓存存储
    
    SmartSearch->>DBStorage: 存储公司信息
    DBStorage-->>SmartSearch: 公司 ID
    SmartSearch->>DBStorage: 存储财务数据
    SmartSearch->>FileStorage: 存储文档
    FileStorage-->>SmartSearch: 存储路径
    SmartSearch->>DBStorage: 存储文档信息
    SmartSearch->>CacheStorage: 缓存搜索结果
    CacheStorage-->>SmartSearch: 缓存确认
```

## 5. 技术选型与配置

### 5.1 核心技术栈

| 技术 | 版本 | 用途 | 配置文件 |
|-----|-----|-----|--------|
| Python | 3.9+ | 主要开发语言 | - |
| Playwright | 1.40.0 | 浏览器自动化 | `smart_search/config/crawler.py` |
| PostgreSQL | 15.0+ | 数据库存储 | `smart_search/config/database.py` |
| Redis | 7.0+ | 缓存存储 | `smart_search/config/redis.py` |
| SQLAlchemy | 2.0.23 | ORM | `smart_search/config/database.py` |
| httpx | 0.25.2 | HTTP 客户端 | - |
| BeautifulSoup4 | 4.12.2 | HTML 解析 | - |
| loguru | 0.7.2 | 日志管理 | - |

### 5.2 配置文件设计

#### `smart_search/config/crawler.py`
```python
class CrawlerConfig:
    # Playwright 配置
    PLAYWRIGHT_HEADLESS = True
    PLAYWRIGHT_TIMEOUT = 60000
    
    # 反爬配置
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...",
        # 更多用户代理
    ]
    
    # 请求间隔
    MIN_REQUEST_INTERVAL = 2
    MAX_REQUEST_INTERVAL = 5
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 3
```

#### `smart_search/config/storage.py`
```python
class StorageConfig:
    # 文档存储路径
    DOCUMENT_STORAGE_PATH = "./storage/documents"
    
    # 缓存存储路径
    CACHE_STORAGE_PATH = "./storage/cache"
    
    # 数据库配置
    DATABASE_URL = "postgresql://user:password@localhost:5432/smart_search"
    
    # Redis 配置
    REDIS_URL = "redis://localhost:6379/0"
    
    # 缓存过期时间（秒）
    CACHE_EXPIRY = 86400
```

## 6. 测试计划

### 6.1 单元测试

| 测试用例 | 测试目标 | 预期结果 |
|---------|---------|--------|
| 基础爬虫初始化 | 测试浏览器初始化 | 成功启动浏览器 |
| 东方财富网爬虫 | 测试爬取公司财报 | 成功获取财报列表 |
| 新浪财经爬虫 | 测试爬取新闻 | 成功获取新闻列表 |
| 雪球爬虫 | 测试爬取讨论 | 成功获取讨论列表 |
| 同花顺爬虫 | 测试爬取财务数据 | 成功获取财务数据 |
| 数据库存储 | 测试数据存储 | 成功存储到数据库 |
| 文件下载器 | 测试文档下载 | 成功下载并存储文档 |
| LLM 集成 | 测试 LLM 调用 | 成功生成文本 |

### 6.2 集成测试

| 测试用例 | 测试目标 | 预期结果 |
|---------|---------|--------|
| 完整搜索流程 | 测试整个搜索流程 | 成功完成从搜索到存储的全流程 |
| 多网站并行搜索 | 测试多网站同时爬取 | 成功获取多个网站的结果 |
| 文档下载与存储 | 测试文档下载和存储 | 成功下载文档并存储到指定位置 |
| 数据存储完整性 | 测试数据存储完整性 | 所有数据正确存储到数据库 |

### 6.3 端到端测试

| 测试用例 | 测试目标 | 预期结果 |
|---------|---------|--------|
| 海天味业财报搜索 | 测试搜索海天味业财报 | 成功获取 2023 年财报 |
| 多公司搜索 | 测试搜索多个公司 | 成功获取多个公司的信息 |
| 性能测试 | 测试系统性能 | 在合理时间内完成搜索 |
| 稳定性测试 | 测试系统稳定性 | 连续运行无错误 |

## 7. 部署与运维

### 7.1 依赖安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install

# 初始化数据库
python -m smart_search.utils.init_db

# 创建存储目录
mkdir -p storage/documents storage/cache
```

### 7.2 配置管理

**环境变量**：
- `DATABASE_URL`：数据库连接 URL
- `REDIS_URL`：Redis 连接 URL
- `ZHIPU_API_KEYS`：智谱 AI API 密钥
- `DEEPSEEK_API_KEY`：DeepSeek API 密钥
- `KIMI_API_KEY`：Kimi API 密钥

### 7.3 监控与日志

**日志配置**：
- 控制台日志：INFO 级别
- 文件日志：DEBUG 级别
- 错误日志：单独存储

**监控指标**：
- 搜索成功率
- 平均搜索时间
- 文档下载成功率
- API 调用次数
- 错误率

## 8. 风险与应对策略

| 风险 | 影响 | 应对策略 |
|-----|-----|--------|
| 网站反爬措施 | 爬取失败 | 实现反爬策略，包括随机用户代理、请求间隔、浏览器指纹伪装 |
| API 调用限制 | LLM 服务不可用 | 实现桶策略，多 API 密钥轮询，故障切换 |
| 数据质量问题 | 数据不准确 | 多源数据交叉验证，建立数据质量评估机制 |
| 存储容量问题 | 存储空间不足 | 实现数据清理策略，定期清理过期数据 |
| 性能问题 | 搜索速度慢 | 优化并发处理，实现缓存机制，使用异步编程 |
| 网络不稳定 | 爬取失败 | 实现重试机制，设置合理的超时时间 |

## 9. 扩展性设计

### 9.1 新数据源集成

**扩展点**：
- 新增爬虫类继承 `BaseCrawler`
- 在爬虫管理器中注册新爬虫
- 配置新爬虫的 URL 和选择器

### 9.2 新 LLM 集成

**扩展点**：
- 新增 LLM 类继承 `LLM` 基类
- 在 LLM 管理器中注册新 LLM
- 配置新 LLM 的 API 密钥和参数

### 9.3 新存储后端

**扩展点**：
- 新增存储类继承 `Storage` 基类
- 在存储管理器中注册新存储
- 配置新存储的参数

## 10. 结论

本详细计划提供了 Smart Search 系统的完整改进方案，包括：

1. **详细的技术架构设计**：从爬虫系统到存储系统的完整架构
2. **具体的实现细节**：每个组件的核心功能和实现逻辑
3. **详细的数据流和处理流程**：系统如何处理搜索请求和存储数据
4. **技术选型和配置**：详细的技术栈和配置参数
5. **全面的测试计划**：从单元测试到端到端测试
6. **部署与运维方案**：系统部署和监控策略
7. **风险与应对策略**：可能的风险和解决方案
8. **扩展性设计**：系统如何扩展以支持新功能

该计划已细化到架构师可以直接开始详细设计的程度，提供了完整的技术指导和实现路径。