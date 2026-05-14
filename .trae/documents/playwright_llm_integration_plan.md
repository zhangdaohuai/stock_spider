# Smart Search 模块 - Playwright + 开源 LLM 集成计划

## 1. 项目现状分析

### 1.1 当前架构
- **搜索引擎**：支持 Tavily AI 和 SearXNG
- **核心功能**：多引擎适配器、意图识别、深度内容解析、来源可靠性评分、文件下载、数据库和缓存集成
- **依赖项**：pydantic、httpx、beautifulsoup4、loguru、sqlalchemy、redis、aiofiles

### 1.2 需要修改的部分
1. **搜索引擎**：移除 Tavily AI，添加 Playwright + 浏览器 + 开源 LLM 搜索引擎
2. **配置**：添加 Playwright 和开源 LLM 相关配置
3. **依赖**：添加 Playwright、开源 LLM 库等新依赖
4. **代码结构**：修改搜索引擎工厂和相关模块

## 2. 实现计划

### 2.1 步骤 1：更新配置文件

**文件**：`smart_search/config/settings.py`

**修改内容**：
- 移除 `TAVILY_API_KEY` 配置
- 添加 Playwright 相关配置
- 添加开源 LLM 相关配置（Hugging Face、本地模型等）
- 配置 Hugging Face API 密钥（可选，用于免费额度）

### 2.2 步骤 2：创建 Playwright 搜索引擎

**文件**：`smart_search/core/search_engines/playwright.py`

**实现内容**：
- 创建 `PlaywrightSearchEngine` 类，继承自 `SearchEngine` 基类
- 实现 `search` 方法，使用 Playwright 启动浏览器进行搜索
- 支持通过浏览器访问主流搜索引擎（Google、Bing、DuckDuckGo 等）
- 解析搜索结果，提取标题、URL、摘要等信息

### 2.3 步骤 3：创建开源 LLM 集成模块

**文件**：`smart_search/core/llm/`

**实现内容**：
- `base.py`：LLM 抽象基类
- `huggingface.py`：Hugging Face 开源模型实现
- `local.py`：本地部署的开源模型实现
- `factory.py`：LLM 工厂类，用于创建和管理 LLM 实例

### 2.4 步骤 4：修改搜索引擎工厂

**文件**：`smart_search/core/search_engines/factory.py`

**修改内容**：
- 移除 Tavily AI 相关代码
- 添加 Playwright 搜索引擎支持
- 更新默认搜索引擎为 Playwright

### 2.5 步骤 5：更新内容处理器

**文件**：`smart_search/core/processors/content_processor.py`

**修改内容**：
- 集成开源 LLM 进行内容总结
- 使用 LLM 对抓取的网页内容进行清洗和去噪
- 支持使用 LLM 生成更准确的摘要

### 2.6 步骤 6：更新查询处理器

**文件**：`smart_search/core/processors/query_processor.py`

**修改内容**：
- 使用开源 LLM 优化搜索查询
- 增强意图识别能力
- 支持更复杂的查询自动补全

### 2.7 步骤 7：更新空结果处理器

**文件**：`smart_search/core/processors/empty_result_processor.py`

**修改内容**：
- 使用开源 LLM 生成更智能的搜索建议
- 基于原始查询和上下文生成相关的搜索词

### 2.8 步骤 8：更新依赖项

**文件**：`requirements.txt`

**修改内容**：
- 添加 `playwright` 依赖
- 添加 `transformers` 依赖（Hugging Face 模型）
- 添加 `torch` 依赖（PyTorch，用于本地模型）
- 添加 `huggingface_hub` 依赖（Hugging Face API）

### 2.9 步骤 9：更新测试脚本

**文件**：`test_smart_search.py`

**修改内容**：
- 更新测试用例，使用 Playwright 搜索引擎
- 添加开源 LLM 相关测试

## 3. 技术实现细节

### 3.1 Playwright 浏览器集成
- 使用 Playwright 启动无头浏览器
- 支持通过浏览器访问主流搜索引擎
- 模拟用户搜索行为，避免被反爬
- 解析搜索结果页面，提取相关信息

### 3.2 开源 LLM 集成
- 支持 Hugging Face 开源模型（如 Mistral、LLaMA 等）
- 支持本地部署的开源模型
- 实现 LLM 工厂，根据配置选择合适的模型
- 使用 LLM 进行内容总结和查询优化
- 处理 LLM 调用的错误和重试

### 3.3 性能优化
- 浏览器实例复用
- LLM 调用缓存
- 并发处理搜索请求
- 合理的超时和错误处理
- 本地模型的量化和优化

## 4. 配置示例

### 4.1 开源 LLM 配置
```python
# LLM settings
LLM_PROVIDER = "huggingface"  # huggingface, local

# Hugging Face settings
HUGGINGFACE_API_KEY = "your_huggingface_api_key"  # 可选，用于免费额度
HUGGINGFACE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

# Local model settings
LOCAL_MODEL_PATH = "./models/mistral-7b-instruct-v0.2"
LOCAL_MODEL_DEVICE = "cpu"  # cpu, cuda
```

### 4.2 Playwright 配置
```python
# Playwright settings
PLAYWRIGHT_BROWSER = "chromium"  # chromium, firefox, webkit
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_TIMEOUT = 30000
```

## 5. 风险评估

### 5.1 潜在风险
- **反爬限制**：浏览器搜索可能会触发搜索引擎的反爬机制
- **性能问题**：浏览器启动和运行可能会消耗较多资源
- **LLM 性能**：开源 LLM 的性能可能不如商业模型
- **依赖管理**：Playwright 需要安装浏览器，可能增加部署复杂度
- **本地模型资源**：本地部署的 LLM 可能需要较多的内存和计算资源

### 5.2 风险缓解策略
- **代理池**：使用代理池避免 IP 被封
- **浏览器配置**：优化浏览器配置，减少资源消耗
- **LLM 缓存**：缓存 LLM 响应，减少重复计算
- **模型选择**：根据资源情况选择合适大小的模型
- **错误处理**：实现优雅的错误处理和降级策略

## 6. 预期结果

### 6.1 功能改进
- **更灵活的搜索**：通过浏览器可以访问更多搜索引擎
- **更智能的内容处理**：使用开源 LLM 进行内容总结和清洗
- **更准确的查询优化**：使用 LLM 理解用户意图
- **更好的空结果处理**：使用 LLM 生成相关搜索建议
- **完全免费**：所有组件均为开源免费

### 6.2 性能预期
- 基础搜索响应时间：5-15 秒（包含浏览器启动时间）
- 深度搜索响应时间：20-40 秒（包含浏览器抓取和 LLM 处理）
- 并发处理能力：支持 3-5 个并发请求（取决于硬件资源）

## 7. 后续步骤

1. 执行上述修改步骤
2. 安装新的依赖项
3. 配置 Playwright 和 LLM 相关设置
4. 运行测试脚本验证功能
5. 优化性能和错误处理
6. 文档更新和部署指南

## 8. 结论

通过集成 Playwright + 浏览器 + 开源 LLM 的方式，Smart Search 模块将变得更加灵活、智能且完全免费。移除所有付费依赖后，模块将不再受限于特定的 API 或服务，而是可以通过浏览器访问各种搜索引擎，同时利用开源 LLM 的能力提升内容处理和查询优化的质量。

这种架构变更将使 Smart Search 模块更适合处理复杂的搜索场景，特别是在需要深度内容解析和智能处理的情况下，同时保持完全免费的特性。