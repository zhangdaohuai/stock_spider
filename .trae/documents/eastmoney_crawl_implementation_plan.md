# 东方财富网页递归爬取研究 — 实施计划

## 一、当前状态总结

### 已完成的工作
1. ✅ 递归链接发现爬虫 (`poc_eastmoney_link_discovery.py`)
2. ✅ API端点探测爬虫 (`poc_eastmoney_api_discovery.py`)
3. ✅ 13个数据域爬虫验证脚本（共50+个API端点）
4. ✅ reportName综合探测脚本 (`poc_em_reportname_discovery.py`)
5. ✅ 研究报告初稿 (`docs/eastmoney_crawl_research_report.md`)

### 关键发现（上一轮验证结果）
| 发现 | 详情 |
|------|------|
| push2/push2his域名IP封锁 | 实时行情、K线、分时、盘口、资金流向全部无法访问 |
| datacenter旧reportName 80%失效 | 22/27个旧reportName返回"报表配置不存在" |
| 从JS文件中发现新reportName | 31个新reportName，其中12个验证可用 |
| F10部分接口返回非JSON | 核心题材、股本结构、公司大事、关联个股4个接口异常 |
| 公告接口正常 | np-anotice-stock域名完全可用 |

### 待解决的问题
1. **爬虫脚本使用旧reportName**：poc_em_lhb、poc_em_margin、poc_em_block_trade、poc_em_dividend、poc_em_shareholder、poc_em_research、poc_em_hsgt 等脚本仍使用已失效的旧reportName
2. **龙虎榜接口缺失**：JS文件中未找到龙虎榜的reportName，需用Playwright拦截XHR
3. **股东/融资融券过滤字段不同**：新reportName不支持SECURITY_CODE过滤
4. **链接发现脚本未完整运行**：上次运行因IP封锁中断

---

## 二、实施计划

### 步骤1：更新所有爬虫脚本使用新reportName

将已验证可用的新reportName更新到对应脚本中：

| 脚本 | 旧reportName(已失效) | 新reportName(已验证) | 变更说明 |
|------|---------------------|---------------------|---------|
| poc_em_block_trade.py | RPT_DABLOCK_TRADE | RPT_DATA_BLOCKTRADE | 替换 |
| poc_em_block_trade.py | RPT_DABLOCK_TRADEMKT | RPT_BLOCKTRADE_ACSTA | 替换 |
| poc_em_block_trade.py | RPT_DABLOCK_BUYBRANCH | RPT_BLOCKTRADE_OPERATEDEPTSTATISTICS | 替换 |
| poc_em_dividend.py | RPT_DIVIDEND_PLAN | RPT_SHAREBONUS_DET | 替换，排序列改为REPORT_DATE |
| poc_em_research.py | RPT_RESEARCH_DET | RPT_WEB_RESPREDICT | 替换 |
| poc_em_research.py | RPT_EARNS_FORECAST_DET | RPT_WEB_RESPREDICT | 合并 |
| poc_em_research.py | RPT_EARNS_FORECAST_RANK | RPT_ANALYST_INDEX_RANK | 替换 |
| poc_em_hsgt.py | RPT_MUTUAL_STOCK_NORTH | RPT_MUTUAL_HOLDRANK_NEW | 替换 |
| poc_em_hsgt.py | RPT_HSGT_INDIVIDUAL_INFO | RPT_MUTUAL_HOLDRANK_NEW | 合并 |
| poc_em_margin.py | RPT_RZRQ_LSHJ | RPTA_RZRQ_LSHJ | 替换，改为市场级数据 |
| poc_em_margin.py | RPT_RZRQ_SHZJHZ | RPTA_WEB_RZRQ_LSSH | 替换，改为市场级数据 |
| poc_em_shareholder.py | RPT_F10_EH_HOLDERSNUM | RPT_FREEHOLDERS_BASIC_INFONEW | 替换，去掉SECURITY_CODE过滤 |
| poc_em_shareholder.py | RPT_F10_EH_INSTITUTION | 暂无个股级替代 | 标注不可用 |
| poc_em_shareholder.py | RPT_F10_EH_HOLDERSCHG | RPT_COOPFREEHOLDERS_ANALYSISNEW | 替换，去掉SECURITY_CODE过滤 |

**负责成员**：module-engineer × 2（并行修改）

### 步骤2：创建龙虎榜Playwright拦截脚本

龙虎榜页面JS中未找到reportName，需使用Playwright拦截XHR请求来发现实际API：

- 安装/确认playwright可用
- 编写脚本：访问 `https://data.eastmoney.com/stock/lhb/` 页面
- 拦截所有XHR请求，提取包含 `datacenter-web.eastmoney.com` 的请求
- 记录完整的URL、参数、响应
- 以海天味业为参数验证

**文件**：`tests/functional_test_case/poc_em_lhb_playwright.py`

**负责成员**：general_purpose_task

### 步骤3：创建股东数据过滤方式研究脚本

新reportName不支持SECURITY_CODE过滤，需研究正确的过滤字段：

- 请求不带过滤的数据，分析返回字段
- 尝试不同的过滤字段：HOLDER_CODE、SECUCODE、INNER_CODE等
- 验证能否按个股过滤获取海天味业的股东数据

**文件**：`tests/functional_test_case/poc_em_shareholder_filter.py`

**负责成员**：general_purpose_task

### 步骤4：创建push2域名代理/直连测试脚本

研究push2域名IP封锁的解决方案：

- 测试通过系统代理(127.0.0.1:7890)访问push2
- 测试通过不同代理配置访问
- 如果代理可用，更新行情类脚本支持代理模式

**文件**：`tests/functional_test_case/poc_em_push2_proxy.py`

**负责成员**：general_purpose_task

### 步骤5：运行所有更新后的脚本并收集结果

按批次运行所有脚本：
- 批次1：更新后的datacenter脚本（6个）
- 批次2：F10+公告脚本（3个）
- 批次3：行情类脚本（4个，含代理测试）
- 批次4：新脚本（龙虎榜Playwright、股东过滤、push2代理）
- 批次5：链接发现脚本

**负责成员**：integration-test-engineer

### 步骤6：更新研究报告

基于步骤5的运行结果，更新 `docs/eastmoney_crawl_research_report.md`：

- 更新验证日期
- 更新API端点可用性状态
- 添加新发现的reportName和过滤方式
- 添加龙虎榜接口信息
- 更新push2域名解决方案
- 完善实体清单

**负责成员**：general_purpose_task

---

## 三、执行分工

| 步骤 | 负责成员 | 产出 |
|------|----------|------|
| 步骤1 | module-engineer × 2（并行） | 更新后的6个爬虫脚本 |
| 步骤2 | general_purpose_task × 1 | poc_em_lhb_playwright.py |
| 步骤3 | general_purpose_task × 1 | poc_em_shareholder_filter.py |
| 步骤4 | general_purpose_task × 1 | poc_em_push2_proxy.py |
| 步骤5 | integration-test-engineer × 1 | 运行结果汇总 |
| 步骤6 | general_purpose_task × 1 | 更新后的研究报告 |

---

## 四、风险与约束

1. **IP封锁持续**：push2/push2his域名可能长期封锁，代理方案需验证
2. **Playwright依赖**：龙虎榜拦截脚本需要安装playwright及浏览器驱动
3. **过滤字段不确定**：股东数据的过滤方式可能需要多次尝试
4. **接口随时变更**：东方财富API可能随时变更，报告需标注验证日期
5. **限流要求**：每次请求间隔≥1秒，单脚本运行时间控制在5分钟内
