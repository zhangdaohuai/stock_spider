# smart_search 模块 - 产品需求文档

## Overview
- **Summary**: 开发一个名为 `smart_search` 的 Python 模块，作为 LangGraph 架构中的核心 Tool，集成第三方搜索服务（Tavily/SearXNG），在互联网上检索行业动态及特定公司文件（PDF/Excel），并返回经过清洗、去噪、具备元数据标记的精炼结果集。
- **Purpose**: 为 LangGraph 架构提供高效、可靠的外部信息检索能力，支持行业动态和公司文件的获取与处理。
- **Target Users**: LangGraph 架构中的 Agent 系统，需要外部信息检索能力的应用场景。

## Goals
- 实现多引擎搜索适配器，支持 Tavily AI 和 SearXNG
- 提供意图识别与 Query 自动补全功能
- 实现深度内容解析，包括网页抓取和 Markdown 转换
- 对搜索结果进行来源可靠性评分
- 返回结构化的 JSON 格式结果
- 处理异常情况并保证性能要求
- 支持文件下载到本地指定目录
- 集成 PostgreSQL 数据库和 Redis 缓存

## Non-Goals (Out of Scope)
- 不实现自定义搜索引擎
- 不处理文件内容的深度分析（仅下载和基本元数据提取）
- 不提供用户界面
- 不处理复杂的自然语言查询理解（仅基础布尔逻辑）

## Background & Context
- 该模块作为 LangGraph 架构的核心 Tool，需要与其他组件无缝集成
- 依赖外部搜索服务（Tavily AI 和 SearXNG）提供搜索能力
- 需要处理不同类型的文件（PDF、Excel 等）和网页内容
- 需要保证搜索结果的可靠性和时效性

## Functional Requirements
- **FR-1**: 多引擎适配器 - 支持同时或切换使用 Tavily AI 和 SearXNG
- **FR-2**: 意图识别与 Query 自动补全 - 针对 finance 主题自动优化查询
- **FR-3**: 深度内容解析 - 在 advanced 模式下抓取网页内容并转换为 Markdown
- **FR-4**: 来源可靠性评分 - 对搜索结果进行自动打分（0-1.0）
- **FR-5**: 结构化输出 - 返回符合指定格式的 JSON 数组
- **FR-6**: 文件下载 - 下载上市公司公告到本地指定目录
- **FR-7**: 数据库集成 - 使用 PostgreSQL 存储数据
- **FR-8**: 缓存集成 - 使用 Redis 进行缓存

## Non-Functional Requirements
- **NFR-1**: 性能要求 - 基础搜索响应需在 1 分钟内，深度搜索响应需在 3 分钟内
- **NFR-2**: 并发处理 - 网页抓取阶段支持 asyncio 并发请求
- **NFR-3**: 反爬处理 - 集成代理池和 User-Agent 随机切换
- **NFR-4**: 异常处理 - 处理超时、网络错误等异常情况，关键性错误通过邮件告知
- **NFR-5**: 空结果兜底 - 无结果时返回建议的搜索词
- **NFR-6**: 数据源管理 - 全网检索确定数据源，单独建表维护

## Constraints
- **Technical**: Python 3.10+，依赖 pydantic、httpx、beautifulsoup4、loguru 等库
- **Business**: 需要配置 TAVILY_API_KEY、SEARXNG_URL、PROXY_URL 等环境变量
- **Dependencies**: 依赖外部搜索服务（Tavily AI、SearXNG）、Crawl4AI 或 Jina Reader API

## Assumptions
- 外部搜索服务（Tavily AI、SearXNG）可用且配置正确
- 代理池配置正确且可用
- PostgreSQL 数据库和 Redis 服务已启动且可访问
- 本地文件系统有足够空间存储下载的文件

## Acceptance Criteria

### AC-1: 多引擎搜索
- **Given**: 配置了 Tavily AI 和 SearXNG
- **When**: 执行搜索查询
- **Then**: 系统应根据配置使用相应的搜索引擎
- **Verification**: `programmatic`
- **Notes**: 支持通过配置文件切换引擎

### AC-2: Query 自动优化
- **Given**: topic='finance'，query="宁德时代 财报"，file_type=['pdf']
- **When**: 执行搜索
- **Then**: 系统应自动优化查询为："宁德时代" (annual report OR 财务报告) filetype:pdf
- **Verification**: `programmatic`

### AC-3: 深度内容解析
- **Given**: depth='advanced'，搜索结果包含网页链接
- **When**: 执行搜索
- **Then**: 系统应抓取网页内容并转换为 Markdown，剔除广告、样式、JS 代码
- **Verification**: `programmatic`
- **Notes**: 对于 PDF/Excel 链接，仅返回下载 URL 及文件名

### AC-4: 来源可靠性评分
- **Given**: 搜索结果包含不同来源的链接
- **When**: 执行搜索
- **Then**: 系统应对每个结果进行评分，官方源 1.0，主流财经媒体 0.8，社交平台 0.4，失效/低质量域名直接过滤
- **Verification**: `programmatic`

### AC-5: 结构化输出
- **Given**: 执行搜索
- **When**: 搜索完成
- **Then**: 系统应返回符合指定格式的 JSON 数组，包含 title、url、source_type、publish_date、snippet、full_content、file_meta、reliability_score、trace_id 字段
- **Verification**: `programmatic`

### AC-6: 文件下载
- **Given**: 搜索结果包含上市公司公告链接
- **When**: 执行搜索
- **Then**: 系统应下载所有格式的公告到本地指定目录
- **Verification**: `programmatic`

### AC-7: 数据库和缓存集成
- **Given**: PostgreSQL 和 Redis 服务已配置
- **When**: 执行搜索
- **Then**: 系统应使用 PostgreSQL 存储数据，使用 Redis 进行缓存
- **Verification**: `programmatic`

### AC-8: 性能要求
- **Given**: 执行基础搜索（depth='basic'）
- **When**: 发起搜索请求
- **Then**: 响应应在 3s 内完成
- **Verification**: `programmatic`

### AC-9: 深度搜索性能
- **Given**: 执行深度搜索（depth='advanced'）
- **When**: 发起搜索请求
- **Then**: 响应应在 15s 内完成
- **Verification**: `programmatic`

### AC-10: 并发处理
- **Given**: 深度搜索模式下有多个网页需要抓取
- **When**: 执行搜索
- **Then**: 系统应使用 asyncio 并发请求，不得串行执行
- **Verification**: `programmatic`

### AC-11: 反爬处理
- **Given**: 配置了代理池和 User-Agent 随机切换
- **When**: 执行搜索和网页抓取
- **Then**: 系统应使用代理池和随机 User-Agent
- **Verification**: `programmatic`

### AC-12: 空结果兜底
- **Given**: 搜索无结果
- **When**: 执行搜索
- **Then**: 系统应返回建议的搜索词
- **Verification**: `programmatic`

### AC-13: 数据源管理
- **Given**: 执行全网搜索
- **When**: 搜索完成
- **Then**: 系统应确定数据源并将其存储到单独的表中进行维护
- **Verification**: `programmatic`

### AC-14: 异常分级和邮件通知
- **Given**: 系统发生关键性错误
- **When**: 错误发生
- **Then**: 系统应通过邮件通知相关人员
- **Verification**: `programmatic`

## Open Questions
- [ ] 本地文件下载的具体目录结构如何设计？
- [ ] PostgreSQL 数据库的具体表结构如何设计？
- [ ] 如何处理不同类型文件的下载和存储？
- [ ] 代理池的具体实现方式是什么？