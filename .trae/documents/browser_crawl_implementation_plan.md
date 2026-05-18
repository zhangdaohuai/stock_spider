# 降低API依赖 — 浏览器爬取方案实施计划

## 一、背景与目标

### 1.1 当前问题

| 问题 | 影响 | 严重度 |
|------|------|--------|
| push2/push2his域名IP封锁 | 实时行情、K线、分时、盘口、资金流向全部不可用 | 🔴 严重 |
| datacenter reportName 80%失效 | 龙虎榜、融资融券(个股级)、股东等数据不可获取 | 🔴 严重 |
| API接口随时变更 | reportName、过滤字段、返回格式可能随时变化 | 🟡 中等 |
| F10部分接口返回非JSON | 核心题材、股本结构、公司大事、关联个股4个接口异常 | 🟡 中等 |

### 1.2 目标

**降低API依赖，使用浏览器自动化工具（DrissionPage）直接爬取页面渲染后的数据**，绕过API封锁和reportName失效问题。

### 1.3 方案选型

| 工具 | 优势 | 劣势 | 决策 |
|------|------|------|------|
| **DrissionPage** | 无需ChromeDriver、API简洁、内置反爬、双模式(浏览器+HTTP) | 社区较新 | ✅ 主力工具 |
| **Playwright** | 已安装(v1.52.0)、多浏览器支持、稳定 | API较繁琐、需浏览器驱动 | ✅ 备选/XHR拦截 |
| **requests** | 高效、轻量 | 无法绕过IP封锁、依赖API | ⚠️ 仅用于可用API |

**核心策略**：
- DrissionPage浏览器模式：爬取SPA页面渲染后的HTML表格数据
- DrissionPage SessionPage模式：用于仍可用的HTTP API（替代requests）
- Playwright：用于XHR拦截（发现隐藏API端点，如龙虎榜）

---

## 二、DrissionPage方案研究（基于知乎文章及官方文档）

### 2.1 DrissionPage核心能力

```python
from DrissionPage import ChromiumPage, ChromiumOptions

# 初始化浏览器（无需ChromeDriver）
co = ChromiumOptions().set_headless(True)  # 无头模式
page = ChromiumPage(addr_driver_opts=co)

# 访问东方财富页面
page.get('https://quote.eastmoney.com/sh603288.html')

# 等待动态内容加载
page.wait.ele_loaded('.quotetable', timeout=10)

# 定位表格并提取数据
table = page.ele('.quotetable').ele('tag:table')
rows = table.eles('tag:tr')
for row in rows:
    tds = row.eles('tag:td')
    data = [td.text for td in tds]
```

### 2.2 东方财富页面数据提取策略

| 页面类型 | URL模式 | 数据位置 | 提取方式 |
|---------|---------|---------|---------|
| 行情主页 | `quote.eastmoney.com/sh{code}.html` | `.quotetable` CSS类 | 表格行遍历 |
| 数据中心 | `data.eastmoney.com/{module}/` | 各模块表格 | 表格行遍历+翻页 |
| F10档案 | `emweb.securities.eastmoney.com/PC_HSF10/...` | AJAX渲染后的DOM | 等待+元素定位 |
| 公告页面 | `np-anotice-stock.eastmoney.com/...` | 列表DOM | 元素遍历 |

### 2.3 关键优势

1. **绕过IP封锁**：浏览器模式使用真实Chrome，请求特征与普通用户一致
2. **不依赖reportName**：直接读取渲染后的HTML，无需知道API参数
3. **自动处理动态内容**：等待JS执行完成后提取数据
4. **内置反爬能力**：模拟真实用户行为、随机延迟、指纹伪装

---

## 三、实施步骤

### 步骤1：安装DrissionPage并验证基础功能

**目标**：安装DrissionPage，验证能否正常启动浏览器并访问东方财富页面

**产出**：`tests/functional_test_case/poc_drissionpage_basic.py`

**验证项**：
1. DrissionPage安装成功
2. 无头模式启动Chrome
3. 访问东方财富行情页
4. 提取页面标题和基本元素
5. 提取行情表格数据

### 步骤2：创建行情数据浏览器爬虫

**目标**：使用DrissionPage浏览器模式爬取行情主页数据，替代被封锁的push2 API

**产出**：`tests/functional_test_case/poc_em_browser_quote.py`

**覆盖数据**：
| 数据 | 页面URL | 提取方式 |
|------|---------|---------|
| 实时行情 | `quote.eastmoney.com/sh603288.html` | 页面DOM元素 |
| K线数据 | 行情页K线标签 | Canvas/SVG或表格 |
| 分时线 | 行情页分时标签 | Canvas数据点 |
| 五档盘口 | 行情页盘口区域 | DOM元素 |
| 资金流向 | 行情页资金标签 | 表格数据 |

**注意**：行情页K线/分时可能使用Canvas绘制，数据不在DOM中。需验证是否可通过：
- 页面内嵌的JavaScript变量获取
- 监听XHR请求获取API响应
- 使用Playwright拦截网络请求

### 步骤3：创建数据中心浏览器爬虫

**目标**：使用DrissionPage浏览器模式爬取数据中心各模块页面

**产出**：`tests/functional_test_case/poc_em_browser_datacenter.py`

**覆盖数据**：
| 数据 | 页面URL | 提取方式 |
|------|---------|---------|
| 龙虎榜 | `data.eastmoney.com/stock/lhb/` | 表格+翻页 |
| 融资融券 | `data.eastmoney.com/rzrq/` | 表格+翻页 |
| 大宗交易 | `data.eastmoney.com/dzjy/` | 表格+翻页 |
| 股权质押 | `data.eastmoney.com/gpzy/` | 表格+翻页 |
| 股东分析 | `data.eastmoney.com/gdfx/` | 表格+翻页 |
| 业绩报表 | `data.eastmoney.com/bbsj/` | 表格+翻页 |
| 分红送配 | `data.eastmoney.com/yjfp/` | 表格+翻页 |
| 沪深港通 | `data.eastmoney.com/hsgt/` | 表格+翻页 |
| 研究报告 | `data.eastmoney.com/report/` | 表格+翻页 |

### 步骤4：创建F10档案浏览器爬虫

**目标**：使用DrissionPage浏览器模式爬取F10档案页面，解决部分API返回非JSON的问题

**产出**：`tests/functional_test_case/poc_em_browser_f10.py`

**覆盖数据**：
| 数据 | 页面URL | 提取方式 |
|------|---------|---------|
| 公司概况 | F10公司概况标签 | DOM元素 |
| 经营分析 | F10经营分析标签 | 表格 |
| 核心题材 | F10核心题材标签 | DOM元素(之前API失败) |
| 股本结构 | F10股本结构标签 | 表格(之前API失败) |
| 公司大事 | F10公司大事标签 | 列表(之前API失败) |
| 财务分析 | F10财务分析标签 | 表格 |
| 资本运作 | F10资本运作标签 | 表格 |
| 关联个股 | F10关联个股标签 | 表格(之前API失败) |
| 股东研究 | F10股东研究标签 | 表格 |

### 步骤5：创建XHR拦截脚本（Playwright）

**目标**：使用Playwright拦截浏览器XHR请求，发现隐藏的API端点

**产出**：`tests/functional_test_case/poc_em_xhr_intercept.py`

**覆盖场景**：
| 场景 | 页面 | 目标 |
|------|------|------|
| 龙虎榜API发现 | `data.eastmoney.com/stock/lhb/` | 找到龙虎榜的真实reportName |
| 行情页API发现 | `quote.eastmoney.com/sh603288.html` | 找到push2的替代端点 |
| F10 API发现 | F10各标签页 | 找到返回非JSON接口的正确参数 |

### 步骤6：运行所有新脚本并收集结果

**目标**：按批次运行所有新创建的浏览器爬虫脚本，收集验证结果

**运行顺序**：
1. `poc_drissionpage_basic.py` — 基础功能验证
2. `poc_em_browser_quote.py` — 行情数据
3. `poc_em_browser_datacenter.py` — 数据中心
4. `poc_em_browser_f10.py` — F10档案
5. `poc_em_xhr_intercept.py` — XHR拦截

### 步骤7：更新研究报告文档

**目标**：基于验证结果，更新 `docs/eastmoney_crawl_research_report.md`

**更新内容**：
1. 新增"浏览器爬取方案"章节
2. 更新各数据域的可行性评估
3. 添加DrissionPage爬取结果
4. 更新实体清单（补充通过浏览器获取的实体）
5. 更新推荐数据获取策略
6. 添加浏览器爬取vs API爬取的对比表

### 步骤8：更新功能测试指南

**目标**：更新 `docs/functional_test_guide.md`，添加浏览器爬虫脚本的使用说明

**更新内容**：
1. 新增DrissionPage安装说明
2. 新增浏览器爬虫脚本的使用方法
3. 新增Playwright XHR拦截脚本的使用方法
4. 更新故障排查章节（浏览器相关问题的排查）

---

## 四、技术要点

### 4.1 DrissionPage安装

```bash
pip install DrissionPage
```

### 4.2 无头模式配置

```python
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.set_headless(True)        # 无头模式
co.set_argument('--no-sandbox')  # Linux兼容
co.set_argument('--disable-gpu')
co.set_lang('zh-CN')

page = ChromiumPage(addr_driver_opts=co)
```

### 4.3 数据提取模式

**模式A：表格数据提取**（适用于数据中心页面）
```python
page.get(url)
page.wait.ele_loaded('tag:table', timeout=10)
table = page.ele('tag:table')
rows = table.eles('tag:tr')
for row in rows:
    cells = row.eles('tag:td')
    if cells:
        data = [cell.text.strip() for cell in cells]
```

**模式B：DOM元素提取**（适用于行情页、F10页面）
```python
page.get(url)
page.wait.ele_loaded('.price', timeout=10)
price = page.ele('.price').text
name = page.ele('.name').text
```

**模式C：XHR拦截**（适用于发现隐藏API）
```python
# 使用Playwright
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 监听网络请求
    api_requests = []
    def handle_request(request):
        if 'datacenter' in request.url or 'push2' in request.url:
            api_requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })

    page.on('request', handle_request)
    page.goto('https://data.eastmoney.com/stock/lhb/')
    page.wait_for_load_state('networkidle')
```

### 4.4 翻页处理

```python
def crawl_all_pages(page: ChromiumPage, base_url: str) -> list[dict]:
    """爬取所有页面的数据"""
    page.get(base_url)
    all_data: list[dict] = []

    while True:
        # 提取当前页数据
        table = page.ele('tag:table')
        rows = table.eles('tag:tr')
        for row in rows:
            # ... 提取数据

        # 查找"下一页"按钮
        next_btn = page.ele('text:下一页', timeout=3)
        if next_btn and 'disabled' not in (next_btn.attr('class') or ''):
            next_btn.click()
            time.sleep(random.uniform(2, 4))  # 随机延迟
        else:
            break

    return all_data
```

### 4.5 反爬策略

| 策略 | 实现方式 |
|------|---------|
| 随机延迟 | `time.sleep(random.uniform(2, 4))` |
| 指纹伪装 | `ChromiumOptions` 设置UA、语言、分辨率 |
| 模拟人类行为 | 随机滚动、鼠标移动 |
| 请求间隔 | 每页间隔2-4秒 |
| Cookie管理 | 浏览器自动管理 |

---

## 五、风险与约束

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 行情页K线使用Canvas绘制 | 无法直接从DOM提取K线数据 | 使用Playwright拦截XHR获取API数据 |
| DrissionPage与Chrome版本不兼容 | 浏览器无法启动 | 使用auto_install()自动匹配 |
| 数据中心页面结构变更 | 选择器失效 | 使用多种定位策略(CSS/XPath/文本) |
| 无头模式被检测 | 页面返回验证码 | 切换有头模式或添加更多伪装参数 |
| 爬取速度较慢 | 浏览器渲染比API慢 | 仅在API不可用时使用浏览器模式 |

---

## 六、执行分工

| 步骤 | 负责成员 | 产出 |
|------|----------|------|
| 步骤1 | general_purpose_task | poc_drissionpage_basic.py |
| 步骤2 | general_purpose_task | poc_em_browser_quote.py |
| 步骤3 | general_purpose_task | poc_em_browser_datacenter.py |
| 步骤4 | general_purpose_task | poc_em_browser_f10.py |
| 步骤5 | general_purpose_task | poc_em_xhr_intercept.py |
| 步骤6 | integration-test-engineer | 运行结果汇总 |
| 步骤7 | general_purpose_task | 更新研究报告 |
| 步骤8 | general_purpose_task | 更新测试指南 |

---

## 七、验收标准

1. ✅ DrissionPage安装成功，基础功能验证通过
2. ✅ 行情页浏览器爬虫能获取实时行情数据（绕过IP封锁）
3. ✅ 数据中心浏览器爬虫能获取至少5个模块的表格数据
4. ✅ F10浏览器爬虫能获取之前API失败的4个接口的数据
5. ✅ XHR拦截脚本能发现龙虎榜的真实API端点
6. ✅ 研究报告更新完成，包含浏览器爬取方案章节
7. ✅ 功能测试指南更新完成，包含新脚本使用说明
