# 当前项目目录研究与建议

**研究日期**: 2026-05-18  
**研究范围**: 项目根目录、`docs/`、`tests/functional_test_case/`、`.trae/specs/`、`.trae/documents/`、Git 状态  
**结论口径**: 本次没有运行外部网络验证脚本，避免触发数据源反爬或依赖本机网络状态；结论基于当前文件内容的静态审阅。

## 1. 总体判断

当前仓库更像是一个 **A 股数据采集系统的需求 + 技术预研 + PoC 验证仓库**，还不是一个可运行的生产代码项目。

更准确地说，项目目前处在 **前期核心方案和关键技能验证阶段**：正在验证数据源边界、爬取方式、浏览器自动化能力、反爬风险和可获取实体范围；尚未进入方案总结、方案定稿和正式开发阶段。

已经沉淀得比较充分的是：

- 原始需求与 PRD：`docs/prd/Original requirement.md`、`docs/prd/stock_spider_prd.md`
- 东方财富网页/API 调研报告：`docs/eastmoney_crawl_research_report.md`
- 功能验证脚本使用指南：`docs/functional_test_guide.md`
- 26 个功能验证 PoC 脚本：`tests/functional_test_case/*.py`
- Trae 生成的规格、任务与计划文档：`.trae/specs/`、`.trae/documents/`

但生产实现基本还没有落地：

- `src/` 为空
- `libs/` 为空
- `sql/` 为空
- 没有 `pyproject.toml` / `requirements.txt` / `environment.yml`
- 没有 `config/`、`stock_crawler/`、`alembic/`、部署脚本或正式测试套件
- `README.md` 只有两行，无法指导新成员运行或开发

因此，我对项目当前阶段的定义是：**核心方案与关键技能验证进行中，正式工程化实现尚未开始；下一阶段应先做验证结果收敛和方案确定，再进入代码开发**。

## 2. 目录理解

### 2.1 根目录

| 路径 | 当前状态 | 理解 |
| --- | --- | --- |
| `README.md` | 极简 | 只说明项目名，缺少项目说明、运行方式、依赖安装、验证脚本说明 |
| `mypy.ini` | 仅忽略 AkShare/Baostock 类型缺失 | 有类型检查意识，但目前没有正式包可检查 |
| `poc_10jqka.py` | Git 未跟踪 | 同花顺、问财、pytdx、AkShare 的额外 PoC，尚未纳入 `tests/functional_test_case/` |
| `src/` | 空目录 | 预留正式源码目录 |
| `libs/` | 空目录 | 预留公共库目录，但目前没有内容 |
| `sql/` | 空目录 | 预留 SQL/迁移脚本目录，但目前没有内容 |
| `.mypy_cache/` | 本地缓存 | 已被 `.gitignore` 忽略，不应提交 |

### 2.2 `docs/`

| 路径 | 内容 |
| --- | --- |
| `docs/prd/Original requirement.md` | 原始需求：A 股分钟级全量采集、2016 回溯、ST/退市/A+H、五档盘口、AkShare/Baostock、JSON 配置、PostgreSQL、无界面、后台长期运行、日志邮件告警、上证/深证网页实时监控 |
| `docs/prd/stock_spider_prd.md` | 已细化 PRD：三数据源适配、1 分钟 + 5 分钟混合策略、日线、盘口、指数监控、完整性检查、PostgreSQL 表结构、部署和验收标准 |
| `docs/eastmoney_crawl_research_report.md` | 东方财富页面和 API 调研：链接图谱、API 端点、reportName、F10、公告、浏览器方案、限流和反爬结论 |
| `docs/functional_test_guide.md` | PoC 脚本运行指南、依赖、代理问题、脚本说明、已验证结论和推荐运行顺序 |
| `docs/Program Design Document/` | 空目录 |

`docs/` 是当前项目最有价值的部分，已经包含了比较完整的需求和数据源边界事实。

### 2.3 `tests/functional_test_case/`

这里不是传统意义上的自动化测试目录，而是 **开发前技术验证脚本集合**。脚本主要通过 `print` 输出验证结果，不是 `pytest` 风格断言测试。

脚本大致分为这些组：

| 类别 | 代表脚本 | 作用 |
| --- | --- | --- |
| 基础数据源验证 | `poc_baostock.py`、`poc_baostock_extra.py`、`poc_akshare_api.py`、`poc_akshare_quick.py`、`poc_eastmoney.py` | 验证 AkShare、Baostock、东方财富直接 API 的能力边界 |
| 东方财富 API 探测 | `poc_em_quote.py`、`poc_em_fund_flow.py`、`poc_em_finance.py` 等 | 验证行情、资金流、财务、股东、公告、研报、分红、沪深港通等端点 |
| 链接和 reportName 发现 | `poc_eastmoney_link_discovery.py`、`poc_eastmoney_api_discovery.py`、`poc_em_reportname_discovery.py` | 从网页和 JS 中发现可用 API/reportName |
| 浏览器自动化验证 | `poc_drissionpage_basic.py`、`poc_em_browser_quote.py`、`poc_em_browser_datacenter.py`、`poc_em_browser_f10.py`、`poc_em_xhr_intercept.py` | 用 DrissionPage/Playwright 验证 SPA 页面、DOM 提取和 XHR 拦截 |

这些脚本为正式实现提供了事实依据，但要进入生产代码，还需要抽象出共享请求层、限流、重试、字段映射和统一数据模型。

### 2.4 `.trae/`

`.trae/specs/stock_crawler/` 描述了一个 `stock_crawler` 模块的完整设计，并且 `tasks.md`、`checklist.md` 把大量任务标记为完成。

但当前仓库没有对应实现文件，例如：

- 没有 `stock_crawler/` 包
- 没有 `requirements.txt` 或 `pyproject.toml`
- 没有 `config.json` 模板
- 没有 SQLAlchemy 模型、Alembic 脚本
- 没有 launchd/systemd 脚本

这是当前仓库最大的状态不一致点。要么这些任务只是计划误标完成，要么实现代码在其他分支/目录中没有合入当前仓库。

另外，`.trae/specs/smart_search/` 和 `.trae/documents/stock_crawler_srs.md` 里存在更大范围的搜索、新闻、论坛、LLM、FastAPI、Redis 等需求，这与 `docs/prd/stock_spider_prd.md` 中明确排除的范围不一致。后续需要确认哪个文档是当前阶段的权威范围。

## 3. 我对业务目标的理解

项目目标是构建一个无界面的 A 股数据采集引擎，用于长期无人值守运行。

核心目标包括：

- 采集 A 股分钟级 K 线
- 首次运行时做历史回溯和数据补全
- 采集日 K 线
- 采集指定股票的五档/十档盘口快照
- 标记 ST、退市风险、A+H 股等特殊股票属性
- 每分钟监控上证指数、深证成指
- 所有数据写入 PostgreSQL
- 支持 macOS 和 Ubuntu 后台运行
- 有严格日志分级，严重错误邮件通知
- 运行前先检查历史数据完整性，不完整则补采

当前 PRD 已经把范围收敛为“数据采集引擎”，并排除了 LLM 分析、论坛监测、新闻采集、研报管理、Web API 服务。这是一个合理收敛。

## 4. 数据源理解

### 4.1 Baostock

适合作为历史结构化行情数据的主力来源。

已验证/文档结论：

- 匿名登录可用
- 日线数据完整，含 `isST`
- 5 分钟 K 线可用
- 分钟线最早大约到 2020-01-02，无法覆盖 2016 年
- 不支持实时行情
- 不支持 1 分钟 K 线
- 不支持港股
- 不支持 ETF
- 指数分钟线返回空

我的判断：Baostock 可以承担日线、5 分钟历史、ST 标记、交易日历、股票基础信息；不应承担实时或 1 分钟全量任务。

### 4.2 AkShare

适合作为免费聚合数据源和补充来源。

已验证/文档结论：

- A 股列表、实时行情、日线、近期分钟线可用
- `stock_zh_a_hist_min_em` 的 1 分钟线仅最近 5 个交易日
- `stock_bid_ask_em` 可获取盘口数据
- ST、退市股票、港股接口可用
- 底层大量依赖东方财富，容易受到东方财富反爬影响

我的判断：AkShare 很适合用于日线补充、实时快照、盘口、ST/退市列表、港股补充。但如果按“全市场逐只股票每分钟拉 1 分钟 K 线”的方式使用，免费接口大概率无法满足实时性。

### 4.3 东方财富

适合作为直接 API 探测和部分低频/补充数据源，但需要严肃处理反爬。

已验证/文档结论：

- `push2` / `push2his` 响应快，但当前网络环境曾出现 IP 封锁
- `datacenter-web` 可访问，但旧 `reportName` 大量失效，需要维护新映射
- `emweb.securities.eastmoney.com` 的 F10 接口部分可用
- 公告接口可用
- 浏览器模式可以绕过部分 API 不可用或非 JSON 的问题

我的判断：东方财富直接 API 可以用于指数监控和 API 发现，但不应在没有代理、退避、熔断和备用源的情况下承担高频核心链路。浏览器自动化更适合低频数据发现、F10/数据中心补充，不适合高频生产采集。

### 4.4 A 股历史分钟线免费方案专项搜索与验证

本节是 2026-05-18 根据“全网搜索中国 A 股历史分钟线免费下载方案”的补充研究，目标是判断是否存在可作为本项目核心依赖的可靠免费源。

新增验证脚本：

```text
tests/codex/functional_test_case/poc_a_share_minute_free_sources.py
```

脚本特点：

- 小样本验证，不做批量下载
- 默认验证 Baostock、AkShare、东方财富直接接口、pytdx
- 同花顺非官方端点需要显式加 `--include-unofficial`
- 输出 JSON 到 `tests/codex/functional_test_case/output/`
- 当前 `output/*.json` 已通过 `.gitignore` 忽略，作为本地验证产物，不作为源码提交对象

本次用 `conda run -n agent` 联网验证过的关键命令：

```bash
conda run -n agent python tests/codex/functional_test_case/poc_a_share_minute_free_sources.py --providers baostock --timeout 10 --sleep 0.5
conda run -n agent python tests/codex/functional_test_case/poc_a_share_minute_free_sources.py --providers akshare,eastmoney --timeout 10 --sleep 2
conda run -n agent python tests/codex/functional_test_case/poc_a_share_minute_free_sources.py --providers ths --include-unofficial --ths-years 2024 --timeout 8 --sleep 1
```

#### 搜索候选源

| 方案 | 免费性 | 搜索/文档依据 | 本次判断 |
| --- | --- | --- | --- |
| Baostock | 免费、无 token、匿名登录 | PyPI 项目说明写明 “Free china stock market data”，并提供 `query_history_k_data_plus` 示例 | 可作为免费 5/15/30/60 分钟历史源，但不支持 1 分钟，且实测分钟线从 2020-01-02 起才有数据 |
| AkShare / 东方财富包装 | 免费、无 key | AKShare 文档列出 `stock_zh_a_hist_min_em`，并明确 1 分钟数据返回近 5 个交易日且不复权 | 不能作为长期历史 1 分钟源；本机验证还遇到东方财富远端断开 |
| 东方财富 push2his 直接接口 | 免费但非官方网页 API | 项目既有 PoC 已验证其接口形态；AKShare 底层也大量使用东方财富 | 高反爬风险。本次直接请求 `klt=1` 时，即使用 2020 日期也返回 2026 当天数据；后续请求被远端断开 |
| pytdx / 通达信公共行情服务器 | 免费包、公共行情服务器、无 SLA | pytdx 文档说明 `get_security_bars` 支持 1 分钟/5 分钟等 K 线，单次最多 800 条 | 理论可探测近期/分页历史，但本机 3 个公共 host 均连接超时，尚不能确认可靠性 |
| 同花顺网页端点 | 免费但非官方 | 全网有资料声称存在 v6/v2 JSONP K 线端点 | 研究项。本次 v2 年度端点返回的是日线，不是分钟线；v6 候选路径也不构成可靠全历史 1 分钟下载证明 |
| Tushare | 注册可用，但历史分钟线不是免费通用权限 | Tushare 权限页写明“股票历史分钟 1/5/15/30/60 分钟，2009 年，单独 2000 元/年” | 不属于无门槛免费方案 |
| JoinQuant / RiceQuant / QMT | 账号/平台/客户端型 | JoinQuant 文档支持分钟频率；QMT XtData 支持 `download_history_data` / `get_market_data_ex` 和 `1m` 周期 | 可作为平台或客户端方案评估，但不是独立、无门槛、可直接批量下载的免费源 |

#### 本次实测结论

| 数据源 | 实测结果 | 可靠性判断 |
| --- | --- | --- |
| Baostock | `frequency=1` 返回 `请求数据类型不正确`；`frequency=5/15/30/60` 在 2016、2019 返回 0 行，在 2020-01-02 和 2024-01-02 返回完整日内条数：5 分钟 48 条、15 分钟 16 条、30 分钟 8 条、60 分钟 4 条 | 免费历史 5 分钟及以上：可用；免费历史 1 分钟：不可用；2016 分钟线：不可用 |
| AkShare | 版本 1.18.60 可导入；旧 2020 的 1 分钟窗口返回 0 行；近期与 5 分钟请求出现 `RemoteDisconnected` | 不能作为长期历史分钟线核心源，只能作为近期/备用探测 |
| 东方财富直接接口 | `klt=1` 曾在 `beg=20200102` 时返回 2026-05-18 当天 1 分钟数据，说明 1 分钟请求不按历史日期返回；后续 `push2his` 请求被远端断开 | 不可靠，且有明显反爬/IP 封锁风险 |
| pytdx | pytdx 已安装，但测试 host `119.147.212.81:7709`、`47.103.48.45:7709`、`121.14.110.194:7709` 均连接超时 | 暂未验证通过；需要扩展 host 池和不同网络环境再测 |
| 同花顺非官方端点 | `v2/line/hs_000001/01/2024.js` 返回 242 行，跨度 2024-01-02 到 2024-12-31，判定为日线；`v6/line/hs_000001/11/last.js` 返回 1763 行但时间 token 为日期级；`v6/line/hs_000001/60/last.js` 返回 140 行且是近期小时级 | 不足以证明存在可靠免费全历史 1 分钟下载；只能保留为逆向研究项 |

#### 专项结论

没有找到“无门槛、免费、可批量下载、稳定覆盖中国 A 股 2016 至今 1 分钟历史 K 线”的可靠方案。

当前可落地的免费方案应降级为：

- **Baostock**：承担 A 股 5/15/30/60 分钟历史数据，起点按实测定为 2020-01-02。
- **AkShare / 东方财富**：只用于近期分钟线、实时行情或辅助验证，不能作为历史全量分钟线主源。
- **pytdx**：继续作为候选验证，但必须先解决公共服务器连通性、分页深度和稳定性问题。
- **同花顺非官方接口**：只作为研究项，不进入正式方案，除非后续确认接口政策、字段含义、分钟粒度和长期稳定性。

如果项目仍坚持“2016-01-01 起全市场 1 分钟历史线”，建议直接进入付费/授权/本地历史数据导入方案评估。可评估方向包括 Tushare 历史分钟权限、QMT/券商客户端历史数据、商业数据商或一次性历史分钟线数据包。

参考资料：

- [AKShare 股票数据文档](https://akshare.akfamily.xyz/data/stock/stock.html)
- [Baostock PyPI 项目页](https://pypi.org/project/baostock/)
- [Pytdx 行情接口文档](https://pytdx-docs.readthedocs.io/zh-cn/latest/pytdx_hq/)
- [Tushare pro_bar 文档](https://tushare.pro/document/1?doc_id=109)
- [Tushare 权限与频次说明](https://tushare.pro/document/1?doc_id=290)
- [JoinQuant 指数数据 get_price 说明](https://www.joinquant.com/help/data/index?f=home)
- [QMT XtData 行情模块说明](https://qmt.hxquant.com/?id=13)

## 5. 关键风险与缺口

### 5.1 实现缺口

当前缺少正式源码和工程骨架，这是第一优先级问题。没有包结构、依赖、配置、数据库迁移和调度入口，就无法从 PoC 进入可运行系统。

建议先不要继续扩展更多 PoC，除非是为了回答阻塞性数据源问题。下一步应开始工程化落地。

### 5.2 需求可行性缺口

“全量 A 股 1 分钟 K 线实时采集”在当前免费数据源组合下风险很高。

原因：

- Baostock 不支持 1 分钟实时
- AkShare 1 分钟接口通常按单只股票查询，且需要限流
- 5400+ 股票如果逐只请求，不可能稳定在 60 秒窗口内完成
- 东方财富直接接口存在 IP 封锁风险

建议把“1 分钟全量实时 K 线”拆成两个方案之一：

- 免费源 MVP：全市场 5 分钟历史 + 全市场实时行情快照 + 重点股票 1 分钟/盘口
- 生产级目标：引入更适合高频全量行情的数据源，例如付费行情、交易所授权数据、稳定行情网关或成熟本地行情源

### 5.3 历史回溯口径不清

原始需求写“数据回溯到 2016-01-01”，但当前验证结论表明 Baostock 分钟线只能到 2020-01-02 左右。PRD 已把 5 分钟 K 线起点写成 2020-01-02，日线起点写成 2016-01-01。

这里需要明确：

- 2016 起点是否只要求日线？
- 分钟线接受从 2020-01-02 起吗？
- 如果分钟线必须从 2016 起，是否允许使用付费数据或历史数据导入？

### 5.4 盘口采集频率不匹配

PRD 里写盘口默认 60 秒采集，指定股票上限 100 支；同时又估算 `stock_bid_ask_em` 单只约 3 秒，100 支一轮约 5 分钟。

这两者互相冲突。需要调整为：

- 100 支股票时，采集周期至少 5 分钟以上
- 如果要 60 秒一轮，股票数需要大幅降低，或者更换批量盘口数据源

### 5.5 “多账号”概念需要重定义

原始需求提到多账号，但当前数据源里：

- Baostock 是匿名登录
- AkShare 通常无需账号
- 东方财富公开 API 无账号

真正需要管理的可能不是账号，而是：

- 数据源配额
- IP/代理池
- endpoint 限流
- 冷却窗口
- 熔断和降级策略

建议把“账号管理”抽象为 `QuotaIdentity` 或 `SourceQuota`，避免为了不存在的账号机制设计过重系统。

### 5.6 PoC 与自动化测试混在一起

`tests/functional_test_case/` 当前是人工运行脚本，不是 CI 可执行测试。

建议保留这些 PoC，但新增正式测试层：

- 单元测试：字段映射、代码格式转换、交易时间判断、配置解析
- 集成测试：用少量真实接口或录制响应验证 adapter
- 契约测试：检查各数据源返回字段是否变化
- 性能/容量测试：写入吞吐、分区查询、断点续传

### 5.7 文档范围存在冲突

当前至少有三套范围：

- 原始需求：基础实时数据爬虫
- PRD：收敛为 A 股实时数据采集引擎，不含 LLM/新闻/论坛/API 服务
- `.trae` SRS / `smart_search`：包含 FastAPI、Redis、LLM、搜索、新闻、论坛等更大系统

建议明确当前迭代只以 `docs/prd/stock_spider_prd.md` 为准，其他文档作为背景资料，不作为当前开发范围。

## 6. 建议的落地路线

### 阶段 0：确认范围和约束

先确认三个硬问题：

1. 1 分钟全量 A 股是否必须实时完成？
2. 分钟线历史是否必须从 2016-01-01 起？
3. 是否允许引入付费/授权/本地行情源？

如果这三个问题不确认，后面架构很容易围绕不可实现的指标做设计。

### 阶段 1：补齐工程骨架

建议先提交最小可运行骨架：

```text
src/stock_spider/
  __init__.py
  main.py
  config/
  adapters/
  storage/
  scheduler/
  models/
  services/
  utils/
tests/
  unit/
  integration/
config/
  config.example.json
sql/
  migrations/
```

同时补齐：

- `pyproject.toml` 或 `requirements.txt`
- `README.md`
- `.env.example`
- 基础日志配置
- 最小启动命令
- 类型检查、格式化、测试命令

### 阶段 2：把 PoC 收敛成 adapter

优先实现这些正式接口：

- `BaostockAdapter`
  - 股票列表
  - 交易日历
  - 日线
  - 5 分钟 K 线
  - ST 标记
- `AkShareAdapter`
  - 股票列表
  - 日线备用
  - 近期 1 分钟 K 线
  - 实时行情快照
  - 盘口
  - ST/退市/港股
- `EastmoneyAdapter`
  - 指数实时行情
  - 低频补充接口

所有 adapter 都应返回统一领域模型，不要让 pandas DataFrame 直接穿透到业务层。

### 阶段 3：先做可控 MVP

建议第一个可运行版本只做：

- 股票主数据同步
- 交易日历同步
- 日线 2016 至今
- 5 分钟 K 线 2020 至今
- 上证/深证指数每分钟监控
- 指定少量股票盘口采集
- 采集进度表和断点续传

暂缓：

- 全市场 1 分钟实时 K 线
- 大规模浏览器自动化生产采集
- 研报/公告/新闻/论坛/LLM
- 多账号复杂轮换

### 阶段 4：数据库和容量验证

在写完整调度前，先验证 PostgreSQL 能否承受目标数据量：

- 分区表写入吞吐
- 单股票时间序列查询性能
- 某日全市场扫描性能
- upsert 去重成本
- 分区创建和归档策略
- 磁盘空间估算

PRD 中估算 5 分钟 K 线可能达到数十亿行级别，这不是普通小表设计能自然承受的规模，需要尽早验证。

### 阶段 5：调度、监控和部署

在 adapter、storage 稳定后，再接入：

- APScheduler 或自研轻量调度
- 交易时段判断
- 失败重试、退避、熔断
- 数据源健康检查
- 日志轮转
- CRITICAL 邮件通知
- launchd / systemd

## 7. 我建议优先修改的文件/目录

按优先级排序：

1. `README.md`：补充项目目标、当前状态、安装、运行 PoC、注意事项
2. `pyproject.toml`：固化依赖和开发工具
3. `src/stock_spider/`：创建正式源码包
4. `config/config.example.json`：把 PRD 配置样例落地
5. `sql/` 或 `alembic/`：创建初始数据库迁移
6. `tests/unit/`：先覆盖无需联网的核心逻辑
7. `tests/functional_test_case/`：保留 PoC，但抽出共享工具，减少重复
8. `.trae/specs/stock_crawler/tasks.md`：修正完成状态，避免误导后续开发
9. `poc_10jqka.py`：确认是否纳入 `tests/functional_test_case/`，或保留为本地草稿

## 8. 需要你确认的问题

1. `.trae/specs/stock_crawler/tasks.md` 标记的已完成任务，是否有实现代码在其他分支、其他目录或未提交？
2. 当前阶段是否以 `docs/prd/stock_spider_prd.md` 为唯一权威范围？还是要继续包含 `.trae` 中的 `smart_search`、新闻、论坛、LLM、FastAPI、Redis？
3. “分钟级数据回溯到 2016-01-01”是否是硬性要求？如果是，是否接受付费或外部历史数据导入？
4. “全量 A 股 1 分钟实时采集”是否必须覆盖 5400+ 股票？如果必须，是否接受更换数据源？
5. 五档盘口默认 60 秒采集时，监控股票数量上限是否可以从 100 支下调？
6. PostgreSQL 是否已有目标实例、磁盘预算和备份策略？
7. 未跟踪的 `poc_10jqka.py` 是否要纳入仓库，并作为同花顺/通达信补充数据源研究？

## 9. 推荐下一步

我建议下一步先做 **工程骨架 + 最小 MVP**，不要继续扩大调研范围。

最小 MVP 的清晰边界是：

- Baostock 拉日线和 5 分钟历史
- AkShare 拉股票列表、ST/退市、盘口少量股票
- 东方财富拉上证/深证指数
- PostgreSQL 入库
- 进度表支持断点续传
- 只做命令行后台程序，不做 Web API

这个版本跑通后，再根据真实吞吐和稳定性决定是否扩展到 1 分钟全量、浏览器补充采集或更多数据域。
