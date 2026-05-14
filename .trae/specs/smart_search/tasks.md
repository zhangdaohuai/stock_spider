# smart_search 模块 - 实现计划（分解和优先级任务列表）

## [ ] 任务 1: 项目初始化和依赖管理
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 创建项目目录结构
  - 初始化 Python 包
  - 配置依赖项（pydantic、httpx、beautifulsoup4、loguru 等）
  - 设置环境变量配置文件
- **Acceptance Criteria Addressed**: AC-1, AC-7
- **Test Requirements**:
  - `programmatic` TR-1.1: 项目目录结构正确创建
  - `programmatic` TR-1.2: 依赖项正确安装
  - `programmatic` TR-1.3: 环境变量配置文件正确设置
- **Notes**: 使用 poetry 或 requirements.txt 管理依赖

## [ ] 任务 2: 多引擎适配器实现
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 实现策略模式设计的搜索引擎适配器
  - 集成 Tavily AI 搜索服务
  - 集成 SearXNG 搜索服务
  - 实现配置文件驱动的引擎切换
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: 能够成功使用 Tavily AI 进行搜索
  - `programmatic` TR-2.2: 能够成功使用 SearXNG 进行搜索
  - `programmatic` TR-2.3: 能够通过配置文件切换搜索引擎
- **Notes**: 使用 httpx 进行 HTTP 请求

## [ ] 任务 3: 意图识别与 Query 自动补全
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 实现意图识别逻辑
  - 针对 finance 主题的 Query 自动优化
  - 实现文件类型过滤的查询构建
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 当 topic='finance' 时，能够自动优化查询
  - `programmatic` TR-3.2: 能够根据 file_type 参数构建正确的查询
- **Notes**: 实现简单的规则引擎进行查询优化

## [ ] 任务 4: 深度内容解析模块
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 集成 Crawl4AI 或 Jina Reader API
  - 实现网页内容抓取
  - 实现 HTML 到 Markdown 的转换
  - 实现广告、样式、JS 代码的剔除
  - 实现 PDF/Excel 链接的特殊处理
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 能够成功抓取网页内容
  - `programmatic` TR-4.2: 能够将 HTML 转换为 Markdown
  - `programmatic` TR-4.3: 转换后的 Markdown 中不包含广告、样式、JS 代码
  - `programmatic` TR-4.4: 对于 PDF/Excel 链接，仅返回下载 URL 及文件名
- **Notes**: 使用 asyncio 实现并发抓取

## [ ] 任务 5: 来源可靠性评分模块
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 实现来源类型识别
  - 实现可靠性评分算法
  - 实现低质量域名过滤
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-5.1: 能够正确识别官方源、主流财经媒体、社交平台
  - `programmatic` TR-5.2: 能够对不同来源给出正确的评分
  - `programmatic` TR-5.3: 能够过滤失效/低质量域名
- **Notes**: 维护域名评分规则列表

## [ ] 任务 6: 结构化输出模块
- **Priority**: P0
- **Depends On**: 任务 2, 任务 4, 任务 5
- **Description**:
  - 实现输出数据结构定义
  - 实现结果集的构建和格式化
  - 实现 trace_id 的生成
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-6.1: 返回的 JSON 数组符合指定格式
  - `programmatic` TR-6.2: 包含所有必要字段
  - `programmatic` TR-6.3: trace_id 格式正确
- **Notes**: 使用 pydantic 进行数据验证

## [ ] 任务 7: 文件下载模块
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 实现文件下载功能
  - 实现本地目录结构管理
  - 支持不同类型文件的下载
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `programmatic` TR-7.1: 能够下载上市公司公告到本地指定目录
  - `programmatic` TR-7.2: 支持 PDF、Excel、Doc 等不同格式的文件
  - `programmatic` TR-7.3: 目录结构管理正确
- **Notes**: 实现断点续传和错误处理

## [ ] 任务 8: 数据库和缓存集成
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**:
  - 实现 PostgreSQL 数据库集成
  - 实现 Redis 缓存集成
  - 实现数据存储和检索逻辑
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic` TR-8.1: 能够连接 PostgreSQL 数据库
  - `programmatic` TR-8.2: 能够连接 Redis 缓存
  - `programmatic` TR-8.3: 能够存储和检索数据
- **Notes**: 使用 SQLAlchemy 进行数据库操作，redis-py 进行缓存操作

## [ ] 任务 9: 性能优化和并发处理
- **Priority**: P1
- **Depends On**: 任务 4
- **Description**:
  - 实现 asyncio 并发请求
  - 实现超时控制
  - 实现代理池和 User-Agent 随机切换
- **Acceptance Criteria Addressed**: AC-8, AC-9, AC-10, AC-11
- **Test Requirements**:
  - `programmatic` TR-9.1: 基础搜索响应在 1 分钟内完成
  - `programmatic` TR-9.2: 深度搜索响应在 3 分钟内完成
  - `programmatic` TR-9.3: 网页抓取阶段使用 asyncio 并发请求
  - `programmatic` TR-9.4: 使用代理池和随机 User-Agent
- **Notes**: 使用 asyncio.gather 实现并发

## [ ] 任务 10: 异常处理和空结果兜底
- **Priority**: P2
- **Depends On**: 任务 2
- **Description**:
  - 实现异常处理逻辑
  - 实现空结果兜底机制
  - 实现日志记录
- **Acceptance Criteria Addressed**: AC-12
- **Test Requirements**:
  - `programmatic` TR-10.1: 能够处理网络错误、超时等异常
  - `programmatic` TR-10.2: 当搜索无结果时，返回建议的搜索词
  - `programmatic` TR-10.3: 日志记录完整且结构化
- **Notes**: 使用 loguru 进行日志记录

## [ ] 任务 11: 数据源管理
- **Priority**: P1
- **Depends On**: 任务 2, 任务 8
- **Description**:
  - 实现全网检索确定数据源的逻辑
  - 设计数据源表结构
  - 实现数据源的存储和维护
- **Acceptance Criteria Addressed**: AC-13
- **Test Requirements**:
  - `programmatic` TR-11.1: 能够通过全网搜索确定数据源
  - `programmatic` TR-11.2: 能够将数据源存储到单独的表中
  - `programmatic` TR-11.3: 能够对数据源进行维护和更新
- **Notes**: 设计合理的数据源表结构

## [ ] 任务 12: 异常分级和邮件通知
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**:
  - 实现异常分级机制
  - 实现邮件通知功能
  - 配置邮件服务器
- **Acceptance Criteria Addressed**: AC-14
- **Test Requirements**:
  - `programmatic` TR-12.1: 能够对异常进行分级
  - `programmatic` TR-12.2: 关键性错误能够通过邮件通知
  - `programmatic` TR-12.3: 邮件通知配置正确
- **Notes**: 配置 EMAIL_NOTIFICATION 环境变量

## [ ] 任务 13: 数据库设计和更新技能集成
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 安装数据库设计及更新技能
  - 设计 PostgreSQL 数据库表结构
  - 设计 Redis 缓存数据结构
  - 实现自动数据库版本更新
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic` TR-13.1: 数据库设计及更新技能安装成功
  - `programmatic` TR-13.2: PostgreSQL 数据库表结构设计合理
  - `programmatic` TR-13.3: Redis 缓存数据结构设计合理
  - `programmatic` TR-13.4: 能够自动进行数据库版本更新
- **Notes**: 确保数据库和缓存设计支持后续的自动更新