# 东方财富网页递归爬取研究 — 剩余工作计划

## 当前状态

### 已完成的工作
1. **步骤1** ✅ 递归链接发现爬虫 (`poc_eastmoney_link_discovery.py`)
2. **步骤2** ✅ API端点探测爬虫 (`poc_eastmoney_api_discovery.py`)
3. **步骤3** ✅ 13个数据域爬虫验证脚本全部实现：
   - `poc_em_quote.py` — 实时行情+K线+分时+盘口 (6个API)
   - `poc_em_fund_flow.py` — 资金流向 (4个API)
   - `poc_em_lhb.py` — 龙虎榜单 (3个API)
   - `poc_em_margin.py` — 融资融券 (3个API)
   - `poc_em_pledge.py` — 股权质押 (3个API)
   - `poc_em_block_trade.py` — 大宗交易 (3个API)
   - `poc_em_finance.py` — 财务数据三表+业绩+指标+杜邦 (6个API)
   - `poc_em_shareholder.py` — 股东分析+十大股东+机构持仓 (5个API)
   - `poc_em_notice.py` — 公告大全+个股日历 (3个API)
   - `poc_em_research.py` — 研报+盈利预测 (3个API)
   - `poc_em_dividend.py` — 分红送配+限售解禁+增发 (3个API)
   - `poc_em_f10.py` — F10档案全量数据 (8个API)
   - `poc_em_hsgt.py` — 沪深港通 (3个API)
4. **步骤4** 🔄 运行所有爬虫验证脚本并汇总结果（上次中断）

### 待完成的工作
- **步骤4（续）**：重新运行所有13个爬虫脚本，收集验证结果
- **步骤5**：生成研究报告 `docs/eastmoney_crawl_research_report.md`

---

## 实施计划

### 阶段一：运行所有爬虫验证脚本（步骤4续）

按批次运行所有脚本，收集每个API的可用性、数据字段、数据量、响应时间：

**批次1（行情类，4个脚本）：**
```bash
cd /Users/zhangdaohuai/Documents/work/agents/codes/stock_spider
conda run -n agent python tests/functional_test_case/poc_eastmoney.py
conda run -n agent python tests/functional_test_case/poc_em_quote.py
conda run -n agent python tests/functional_test_case/poc_em_fund_flow.py
conda run -n agent python tests/functional_test_case/poc_eastmoney_api_discovery.py
```

**批次2（数据中心类，6个脚本）：**
```bash
conda run -n agent python tests/functional_test_case/poc_em_lhb.py
conda run -n agent python tests/functional_test_case/poc_em_margin.py
conda run -n agent python tests/functional_test_case/poc_em_pledge.py
conda run -n agent python tests/functional_test_case/poc_em_block_trade.py
conda run -n agent python tests/functional_test_case/poc_em_finance.py
conda run -n agent python tests/functional_test_case/poc_em_shareholder.py
```

**批次3（F10+公告+其他，5个脚本）：**
```bash
conda run -n agent python tests/functional_test_case/poc_em_notice.py
conda run -n agent python tests/functional_test_case/poc_em_research.py
conda run -n agent python tests/functional_test_case/poc_em_dividend.py
conda run -n agent python tests/functional_test_case/poc_em_f10.py
conda run -n agent python tests/functional_test_case/poc_em_hsgt.py
```

**批次4（链接发现，1个脚本，耗时较长）：**
```bash
conda run -n agent python tests/functional_test_case/poc_eastmoney_link_discovery.py
```

> 注意：每个脚本内部已有1.5秒限流，批次间无需额外等待。但需注意IP封锁风险，如遇连接重置则暂停5分钟。

### 阶段二：生成研究报告（步骤5）

基于阶段一的运行结果，生成 `docs/eastmoney_crawl_research_report.md`，报告结构：

```markdown
# 东方财富网页可抓取信息研究报告

## 1. 研究概述
- 目标：以海天味业(603288)为基础，递归分析东方财富网页所有可抓取的股票相关实体
- 方法：BFS递归链接发现 + REST API端点探测 + 实际数据验证
- 范围：*.eastmoney.com 域名下所有股票相关页面和API
- 验证日期：2026-05-15

## 2. 网页链接图谱
- 入口页面：https://quote.eastmoney.com/sh603288.html
- 递归深度：3层
- 域名分类统计
- 子页面链接清单

## 3. API端点清单
- 按数据域分类的完整API列表
- 每个API的：URL、请求方法、参数、返回字段、可用性状态
- 总计约50+个API端点

## 4. 可抓取实体清单
按类别列出所有可提取的股票相关实体：
- 行情实体（实时行情、K线、分时、盘口）
- 资金实体（资金流向、融资融券、沪深港通）
- 财务实体（三表、业绩、指标、杜邦分析）
- 股东实体（十大股东、机构持仓、股东增减持）
- 交易实体（龙虎榜、大宗交易、股权质押）
- 公司实体（F10档案、公司概况、核心题材、经营分析）
- 公告实体（公告大全、个股日历、研报）
- 分红实体（分红送配、限售解禁、增发）

## 5. 数据字段详细映射
- 每个实体的字段名、类型、含义、示例值
- push2接口的f编码字段映射表
- datacenter接口的英文字段映射表

## 6. 限流与反爬策略分析
- 各域名的请求频率限制
- IP封锁机制与应对策略
- 请求头要求
- 数据量限制

## 7. 结论与建议
- 可行性评估
- 推荐的数据获取策略
- 风险提示
- 与AkShare/Baostock的互补关系
```

---

## 执行分工

| 步骤 | 负责成员 | 产出 |
|------|----------|------|
| 阶段一：运行脚本 | general_purpose_task × 3（并行3批次） | 每个脚本的运行结果输出 |
| 阶段一：链接发现 | general_purpose_task × 1 | 链接图谱输出 |
| 阶段二：生成报告 | general_purpose_task × 1 | docs/eastmoney_crawl_research_report.md |

---

## 风险与约束

1. **IP封锁**：东方财富对高频请求会封锁IP（返回"Remote end closed connection"），需控制请求频率
2. **非交易时间**：部分接口（分时线、盘口）在非交易时间返回空数据，属正常现象
3. **接口变更**：东方财富API可能随时变更，报告需标注验证日期
4. **杜邦分析接口**：上次验证时返回非JSON内容，可能已下线或变更
5. **链接发现耗时**：3层递归可能发现数百个链接，脚本运行时间较长（约10-15分钟）
