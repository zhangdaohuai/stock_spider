---
name: K6 Performance Testing
description: 全链路压测与性能测试 - 使用 Grafana K6 进行负载测试、压力测试、峰值测试和浸泡测试
version: 1.0.0
author: QA_Jerry (based on Grafana k6 official docs)
license: MIT
testingTypes: [performance, load, stress]
frameworks: [k6]
languages: [javascript, typescript]
domains: [api, web, microservices]
agents: [claude-code, cursor, github-copilot, windsurf, codex, aider, continue, cline, zed, bolt]
---

# K6 Performance Testing Skill

你是一位专业的性能测试工程师，专精于使用 **Grafana K6** 进行全链路压测和性能调优。当用户需要编写、执行或调试 K6 性能测试时，请遵循以下详细指南。

## 核心原则

1. **目标导向** — 每次测试必须明确性能基线、预期目标和验收标准
2. **渐进式负载** — 从低负载开始，逐步递增，避免瞬间冲击生产环境
3. **真实场景模拟** — 使用思考时间（think time）、随机数据和真实用户行为模式
4. **可观测性** — 结合阈值（Thresholds）+ 指标（Metrics）+ 自定义指标全面监控
5. **自动化集成** — 无缝对接 CI/CD 流水线，实现持续性能验证

## 项目结构

```
k6/
  scripts/
    smoke.js                    # 冒烟测试（轻量级健康检查）
    load.js                     # 负载测试（正常流量模拟）
    stress.js                   # 压力测试（超出容量边界）
    spike.js                    # 峰值测试（突发流量）
    soak.js                     # 浸泡测试（长时间稳定性）
    api/
      user-api.js               # 用户 API 压测
      search-api.js             # 搜索 API 压测
      order-api.js              # 订单 API 压测
    scenarios/
      constant-load.js          # 恒定负载场景
      ramping-up.js             # 逐步加压场景
      spike-test.js             # 尖峰场景
    browser/
      checkout-flow.js          # 浏览器端性能测试
  utils/
    helpers.js                  # 通用工具函数
    data-generator.js           # 测试数据生成器
    metrics-collector.js        # 自定义指标收集
  fixtures/
    test-data.json              # 静态测试数据
    user-tokens.json            # 用户认证令牌
  config/
    environments.js             # 环境配置（dev/staging/prod）
    thresholds.js               # 阈值定义
    options.js                  # 可复用选项
  outputs/
    influxdb.js                 # InfluxDB 输出配置
    cloud.js                     # Grafana Cloud 配置
    prometheus.js               # Prometheus 输出配置
k6.config.ts                     # TypeScript 配置（如使用 k6 + OTel）
```

## 快速开始

### 安装 K6

```bash
# macOS
brew install k6

# 或下载二进制文件
# https://grafana.com/docs/k6/latest/set-up/install/k6-install/

# 验证安装
k6 version
```

### 第一个测试脚本

```javascript
import { check } from 'k6';
import http from 'k6/http';

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // 30秒内爬升到 20 用户
    { duration: '1m', target: 20 },     // 保持 20 用户 1分钟
    { duration: '20s', target: 0 },     // 20秒内降到 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% 的请求在 500ms 内完成
    http_req_failed: ['rate<0.01'],     // 错误率低于 1%
  },
};

export default function () {
  const res = http.get('https://test-api.k6.io/public/crocodiles/1/');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

### 运行测试

```bash
# 本地运行
k6 run scripts/load.js

# 指定环境变量
K6_ENV=staging k6 run scripts/load.js

# 输出到 InfluxDB（用于 Grafana 展示）
k6 run --out influxdb=http://localhost:8086/k6db scripts/load.js

# 输出到 Prometheus
k6 run --out prometheus=scripts/outputs/prometheus.js scripts/load.js
```

## 核心概念详解

### 1️⃣ Options 配置（测试选项）

#### 基础配置

```javascript
export const options = {
  // 扩展名（VUs 总数上限）
  vus: 10,

  // 持续时间
  duration: '5m',

  // 阈值定义
  thresholds: {
    // 响应时间：p(95) < 500ms, p(99) < 1000ms
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],

    // 错误率：< 1%
    'http_req_failed': ['rate<0.01'],

    // 吞吐量：> 100 req/s
    'http_reqs': ['rate>100'],
  },
};
```

#### Stages（阶段性负载）

```javascript
export const options = {
  stages: [
    // 阶段1：预热（ramp-up）
    { duration: '2m', target: 100 },  // 2分钟内爬升到 100 VU

    // 阶段2：高负载稳定期
    { duration: '5m', target: 100 },  // 保持 100 VU 5分钟

    // 阶段3：加压（ramp-up to peak）
    { duration: '2m', target: 200 },  // 爬升到 200 VU

    // 阶段4：峰值保持
    { duration: '5m', target: 200 },  // 保持 200 VU 5分钟

    // 阶段5：恢复（recovery）
    { duration: '2m', target: 0 },    // 降到 0
  ],

  thresholds: {
    // 在高负载阶段仍需满足的性能要求
    'http_req_duration{stage:high_load}': ['p(95)<800'],
  },
};
```

#### Scenarios（多场景编排）

```javascript
export const options = {
  scenarios: {
    // 场景1：普通用户浏览（恒定负载）
    browsing: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
      gracefulStop: '30s',
      exec: 'browsing',
      tags: { scenario_type: 'normal' },
    },

    // 场景2：抢购活动（尖峰负载）
    flash_sale: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 1000 },   // 30秒到 1000 VU
        { duration: '1m', target: 1000 },    // 保持 1分钟
        { duration: '30s', target: 0 },      // 恢复
      ],
      gracefulRampDown: '30s',
      exec: 'flashSale',
      tags: { scenario_type: 'peak' },
    },

    // 场景3：API 压测（固定吞吐量）
    api_stress: {
      executor: 'constant-arrival-rate',
      rate: 1000,                // 每秒 1000 个请求
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 100,      // 预分配 100 VU
      maxVUs: 200,              // 最大 200 VU
      exec: 'apiStress',
      tags: { scenario_type: 'stress' },
    },
  },

  thresholds: {
    // 不同场景可以有不同的阈值
    'http_req_duration{scenario_type:normal}': ['p(95)<300'],
    'http_req_duration{scenario_type:peak}': ['p(95)<1000'],
    'http_req_duration{scenario_type:stress}': ['p(90)<500'],
  },
};

// 场景函数
export function browsing() {
  // 普通用户浏览逻辑
}

export function flashSale() {
  // 抢购逻辑
}

export function apiStress() {
  // API 压力测试逻辑
}
```

### 2️⃣ Thresholds（阈值）

阈值是 K6 最强大的功能之一，用于自动判断测试是否通过。

#### 内置指标阈值

```javascript
export const options = {
  thresholds: {
    // === 响应时间相关 ===

    // p(95) < 500ms：95%的请求在500ms内完成
    'http_req_duration': ['p(95)<500'],

    // p(99) < 1000ms：99%的请求在1s内完成
    'http_req_duration': ['p(99)<1000'],

    // 平均响应时间 < 300ms
    'http_req_duration': ['avg<300'],

    // 最大响应时间 < 2000ms（允许偶尔慢请求）
    'http_req_duration': ['max<2000'],

    // === 错误率相关 ===

    // HTTP 请求错误率 < 1%
    'http_req_failed': ['rate<0.01'],

    // === 吞吐量相关 ===

    // 每秒请求数 > 100
    'http_reqs': ['rate>100'],

    // 数据接收速率 > 50KB/s
    'http_data_received': ['rate>51200'],

    // === 并发相关 ===

    // 当前并发用户数检查
    'vus': ['value>0'],  // 确保有活跃用户

    // === 自定义指标阈值 ===

    // 自定义成功率 > 95%
    'my_custom_success_rate': ['rate>0.95'],

    // 自定义业务指标
    'order_creation_time': ['p(90)<2000'],
  },
};
```

#### 跨条件阈值（高级用法）

```javascript
export const options = {
  thresholds: {
    // 多个条件必须全部通过（AND 逻辑）
    'http_req_duration': [
      'p(95)<500',   // 条件1：p(95) < 500ms
      'p(99)<1000',  // 条件2：p(99) < 1000ms
      'avg<300',     // 条件3：avg < 300ms
    ],

    // 只要通过一个条件即可（OR 逻辑）- 使用多个阈值数组
    // （实际中通常用 AND，OR 需要自定义处理）
  },
};
```

#### 阈值 abort 行为

```javascript
export const options = {
  thresholds: {
    // abortOnFailure: true — 阈值失败时立即中止测试
    'http_req_failed': [
      { threshold: 'rate<0.01', abortOnFailure: true, delayAbortEval: '10s' },
    ],

    // delayAbortEval: '10s' — 允许前10秒的预热阶段不检查阈值
  },
};
```

### 3️⃣ Metrics（指标）

#### 内置系统指标

| 指标名称 | 类型 | 描述 |
|---------|------|------|
| `http_req_duration` | Trend | HTTP 请求总耗时（TCP连接 + TLS + 发送 + 等待 + 接收） |
| `http_req_waiting` | Trend | 等待服务器响应首字节的时间（TTFB） |
| `http_req_sending` | Trend | 发送请求所需时间 |
| `http_req_receiving` | Trend | 接收响应所需时间 |
| `http_req_failed` | Rate | 失败的 HTTP 请求率 |
| `http_reqs` | Rate | 每秒完成的 HTTP 请求数 |
| `vus` | Gauge | 当前活跃虚拟用户数 |
| `vus_max` | Gauge | 最大预设虚拟用户数 |
| `data_received` | Rate | 接收的数据量（bytes/s） |
| `data_sent` | Rate | 发送的数据量（bytes/s） |
| `iterations` | Rate | VU 执行默认函数的次数/s |
| `iteration_duration` | Trend | 完成一次完整迭代所需时间 |
| `checks` | Rate | check() 成功率 |
| `group_duration` | Trend | 分组耗时 |

#### 自定义指标

```javascript
import { Counter, Gauge, Rate, Trend } from 'k6/metrics';

// 计数器：统计订单创建总数
export const orderCounter = new Counter('orders_created');

// 仪表盘：当前购物车商品数
export const cartItemsGauge = new Gauge('cart_items');

// 成功率：支付成功比例
export const paymentSuccessRate = new Rate('payment_success_rate');

// 趋势：订单创建耗时
export const orderCreationTime = new Trend('order_creation_time');

export default function () {
  // 业务逻辑...

  // 订单创建成功后记录指标
  const startTime = Date.now();
  const res = createOrder(orderData);
  const endTime = Date.now();

  if (res.status === 201) {
    orderCounter.add(1);                          // 计数器 +1
    cartItemsGauge.add(getCartItemCount());       // 更新仪表盘
    paymentSuccessRate.add(1);                    // 记录成功
    orderCreationTime.add(endTime - startTime);   // 记录耗时
  } else {
    paymentSuccessRate.add(0);                    // 记录失败
  }
}
```

### 4️⃣ 测试类型与场景模板

#### 🚬 Smoke Test（冒烟测试）

```javascript
// scripts/smoke.js
import { check } from 'k6';
import http from 'k6/http';

export const options = {
  vus: 1,
  duration: '10s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0'],
    checks: ['rate==1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // 健康检查
  const healthRes = http.get(`${BASE_URL}/health`);

  check(healthRes, {
    'health check status 200': (r) => r.status === 200,
    'health response time < 200ms': (r) => r.timings.duration < 200,
  });

  // 关键 API 端点抽样检查
  const usersRes = http.get(`${BASE_URL}/api/users?page=1&size=10`);

  check(usersRes, {
    'users list status 200': (r) => r.status === 200,
    'users has data': (r) => JSON.parse(r.body).data.length > 0,
  });
}
```

#### 📊 Load Test（负载测试）

```javascript
// scripts/load.js
import { check, sleep } from 'k6';
import http from 'k6/http';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // 预热
    { duration: '5m', target: 50 },   // 稳定负载
    { duration: '2m', target: 100 },  // 加压
    { duration: '5m', target: 100 },  // 高负载稳定
    { duration: '1m', target: 0 },    // 降温
  ],
  thresholds: {
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
    http_req_failed: ['rate<0.05'],
    checks: ['rate>0.95'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const PAGES = [1, 2, 3, 4, 5];

export default function () {
  // 场景1：浏览商品列表（60%概率）
  if (Math.random() < 0.6) {
    browseProducts();
  }

  // 场景2：搜索商品（25%概率）
  else if (Math.random() < 0.85) {
    searchProduct();
  }

  // 场景3：查看商品详情（15%概率）
  else {
    viewProductDetail();
  }

  // 思考时间：1-3秒（模拟真实用户操作间隔）
  sleep(randomIntBetween(1, 3));
}

function browseProducts() {
  const page = randomItem(PAGES);
  const res = http.get(`${BASE_URL}/api/products?page=${page}&size=20`, {
    tags: { name: 'browse_products' },
  });

  check(res, {
    'products list status 200': (r) => r.status === 200,
    'products has items': (r) => {
      const body = JSON.parse(r.body);
      return body.data && body.data.length > 0;
    },
  });
}

function searchProduct() {
  const queries = ['手机', '电脑', '耳机', '键盘'];
  const query = randomItem(queries);
  const res = http.get(`${BASE_URL}/api/search?q=${encodeURIComponent(query)}`, {
    tags: { name: 'search_product' },
  });

  check(res, {
    'search status 200': (r) => r.status === 200,
    'search has results': (r) => {
      const body = JSON.parse(r.body);
      return body.results && body.results.length >= 0;
    },
  });
}

function viewProductDetail() {
  const productId = randomIntBetween(1, 1000);
  const res = http.get(`${BASE_URL}/api/products/${productId}`, {
    tags: { name: 'view_product_detail' },
  });

  check(res, {
    'product detail status': (r) =>
      r.status === 200 || r.status === 404,  // 允许404（商品可能不存在）
  });
}
```

#### 🔥 Stress Test（压力测试）

```javascript
// scripts/stress.js
import { check, sleep } from 'k6';
import http from 'k6/http';
import { Trend } from 'k6/metrics';

// 自定义指标：跟踪系统在极限状态下的表现
const responseTimeUnderStress = new Trend('response_time_under_stress');
const errorRateUnderStress = new Trend('error_rate_under_stress');

export const options = {
  stages: [
    { duration: '1m', target: 100 },    // 正常基准
    { duration: '2m', target: 250 },    // 超出正常负载
    { duration: '3m', target: 500 },    // 高负载
    { duration: '2m', target: 750 },    // 接近极限
    { duration: '1m', target: 1000 },   // 极限压力
    { duration: '1m', target: 0 },      // 恢复
  ],
  thresholds: {
    // 即使在高压力下，核心API也要尽量可用
    'http_req_duration{type:core_api}': [
      'p(95)<2000',  // 放宽标准
      'p(99)<5000',  // 允许极端情况
    ],
    // 错误率在极限情况下可以适当放宽
    'http_req_failed{type:core_api}': ['rate<0.15'],
    // 但核心功能不能完全不可用
    'checks{type:core_api}': ['rate>0.85'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // 核心API：用户认证
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: `user_${__VU}`,
    password: 'testpass123',
  }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { type: 'core_api' },
  });

  responseTimeUnderStress.add(loginRes.timings.duration);

  check(loginRes, {
    'login status 200 or 429': (r) =>
      r.status === 200 || r.status === 429,  // 允许限流
    'login not 500': (r) => r.status !== 500,  // 不允许服务器错误
  });

  if (loginRes.status === 200) {
    const token = loginRes.json('token');

    // 核心API：获取用户信息
    const userRes = http.get(`${BASE_URL}/api/users/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
      tags: { type: 'core_api' },
    });

    check(userRes, {
      'user info loaded': (r) => r.status === 200,
    });
  }

  sleep(0.5);  // 压力测试下减少思考时间
}
```

#### ⚡ Spike Test（峰值/尖峰测试）

```javascript
// scripts/spike.js
import { check, sleep } from 'k6';
import http from 'k6/http';

export const options = {
  stages: [
    { duration: '30s', target: 10 },     // 基线：10用户
    { duration: '15s', target: 10 },     // 保持基线
    { duration: '10s', target: 1000 },   // ⚡ 突然飙升到 1000 用户！
    { duration: '20s', target: 1000 },   // 保持峰值
    { duration: '30s', target: 50 },     // 快速下降
    { duration: '20s', target: 0 },      // 恢复
  ],
  thresholds: {
    // 峰值期间系统不应崩溃
    'http_req_failed': ['rate<0.20'],  // 允许一定错误率
    'http_req_duration': ['p(99)<10000'],  // 10s超时保护
    // 峰值过后应快速恢复
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // 模拟抢购场景：热门商品下单
  const productId = 1;  // 热门商品ID
  const res = http.post(`${BASE_URL}/api/orders`, JSON.stringify({
    product_id: productId,
    quantity: 1,
  }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'flash_order' },
  });

  check(res, {
    'order created or rate limited': (r) =>
      [200, 201, 429].includes(r.status),  // 成功或限流都可接受
    'no server error': (r) => ![500, 502, 503].includes(r.status),
  });

  sleep(Math.random() * 0.5);  // 高并发下极短延迟
}
```

#### 🛁 Soak Test（浸泡/稳定性测试）

```javascript
// scripts/soak.js
import { check, sleep } from 'k6';
import http from 'k6/http';
import { Counter, Rate, Trend } from 'k6/metrics';

// 长期运行指标
export const memoryLeaks = new Trend('memory_usage_estimate');
export const longRunningErrors = new Rate('long_running_error_rate');
export const totalRequestsSoak = new Counter('soak_total_requests');

export const options = {
  stages: [
    // 缓慢启动，避免初始冲击
    { duration: '5m', target: 50 },
    // 长时间稳定运行（模拟生产环境数小时）
    { duration: '4h', target: 50 },
    // 缓慢停止
    { duration: '10m', target: 0 },
  ],
  thresholds: {
    // 长期运行的严格要求
    'http_req_duration': ['p(95)<600', 'max<5000'],
    'http_req_failed': ['rate<0.01'],  // 4小时内错误率必须很低
    'checks': ['rate>0.98'],
    // 内存泄漏检测（间接）：长期运行响应时间不应显著增加
    'soak_response_time_trend': ['avg<400'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const startTime = Date.now();

  totalRequestsSoak.add(1);

  // 循环执行多种操作
  const operations = [
    () => {
      const res = http.get(`${BASE_URL}/api/products`);
      check(res, { 'products ok': (r) => r.status === 200 });
    },
    () => {
      const res = http.get(`${BASE_URL}/api/users/${(__VU % 100) + 1}`);
      check(res, { 'user ok': (r) => r.status === 200 || r.status === 404 });
    },
    () => {
      const res = http.get(`${BASE_URL}/health`);
      check(res, { 'health ok': (r) => r.status === 200 });
    },
  ];

  const operation = operations[__ITER % operations.length];
  operation();

  const endTime = Date.now();
  memoryLeaks.add(endTime - startTime);

  // 模拟真实用户的较长思考时间
  sleep(Math.random() * 5 + 3);  // 3-8秒
}
```

### 5️⃣ HTTP 高级用法

#### 认证与会话管理

```javascript
import { check } from 'k6';
import http from 'k6/http';

export const options = {
  vus: 10,
  duration: '30s',
};

const BASE_URL = 'http://localhost:8000';

// Setup：获取Token（只执行一次）
export function setup() {
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'admin',
    password: 'adminpass',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  const token = loginRes.json('access_token');
  return { token };
}

// 使用 setup 返回的数据
export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`,
  };

  const res = http.get(`${BASE_URL}/api/users/me`, { headers });

  check(res, {
    'authenticated request': (r) => r.status === 200,
  });
}
```

#### 参数化与数据驱动

```javascript
import { SharedArray } from 'k6/data';
import { check, sleep } from 'k6';
import http from 'k6/http';

// 从 CSV/JSON 文件读取测试数据（共享数组，所有VU共享）
const testData = new SharedArray('testUsers', function () {
  // 这里会在初始化阶段执行一次
  return JSON.parse(open('./fixtures/test-users.json')).users;
});

export const options = {
  vus: 10,
  duration: '1m',
};

export default function () {
  // 每个VU循环使用不同的用户数据
  const user = testData[__VU % testData.length];

  const res = http.post(`http://localhost:8000/api/users/login`, JSON.stringify({
    email: user.email,
    password: user.password,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'login successful': (r) => r.status === 200,
    'has token': (r) => r.json('access_token') !== undefined,
  });

  sleep(1);
}
```

#### 请求分组与标签

```javascript
import { group, check, sleep } from 'k6';
import http from 'k6/http';

export default function () {
  // 分组：将相关的请求组织在一起
  group('User Registration Flow', function () {

    group('Step 1: Get CSRF Token', function () {
      const csrfRes = http.get('https://example.com/csrf-token', {
        tags: { flow: 'registration', step: 'csrf' },
      });
      check(csrfRes, { 'csrf obtained': (r) => r.status === 200 });
    });

    group('Step 2: Submit Registration', function () {
      const regRes = http.post('https://example.com/register', {
        username: `user_${__VU}_${__ITER}`,
        email: `user${__VU}@test.com`,
        password: 'Test1234!',
      }, {
        tags: { flow: 'registration', step: 'submit' },
      });
      check(regRes, {
        'registration success': (r) => r.status === 201,
        'welcome email sent': (r) =>
          r.html().find('div.alert-success').length > 0,
      });
    });

  });

  sleep(1);
}
```

#### Cookie 管理

```javascript
import { check } from 'k6';
import http from 'k6/http';

export default function () {
  const jar = http.cookieJar();

  // 设置Cookie
  jar.set({ url: 'http://example.com', name: 'session_id', value: 'abc123' });

  // 后续请求会自动携带Cookie
  const res = http.get('http://example.com/dashboard', { cookies: { jar } });

  check(res, {
    'dashboard accessible with cookie': (r) => r.status === 200,
  });
}
```

### 6️⃣ 输出与可视化

#### InfluxDB + Grafana（推荐方案）

```javascript
// outputs/influxdb.js
import { InfluxDB } from 'k6/output';

const influxdb = new InfluxDB({
  // InfluxDB 连接配置
  url: 'http://localhost:8086',
  bucket: 'k6db',
  org: 'myorg',
  token: 'your-influxdb-token',

  // 数据保留策略
  retention: '7d',

  // 自定义标签
  tags: {
    project: 'smart_search',
    environment: __ENV.K6_ENV || 'staging',
    test_type: __ENV.TEST_TYPE || 'load',
  },
});

export default function (data) {
  influxdb.consume(data);
}
```

运行命令：
```bash
k6 run --out script=outputs/influxdb.js scripts/load.js
```

#### Prometheus 输出

```javascript
// outputs/prometheus.js
import { Pushgateway } from 'k6/output';

const pg = new Pushgateway({
  url: 'http://localhost:9091',
});

export default function (data) {
  pg.consume(data);
}
```

#### Grafana Cloud 输出

```javascript
// outputs/cloud.js
import { K6Cloud } from 'k6/output';

const cloud = new K6Cloud({
  token: __ENV.K6_CLOUD_TOKEN,

  // 项目标识
  project_id: 12345,

  // 自定义信息
  name: `${__ENV.TEST_TYPE || 'load'}-test-${new Date().toISOString()}`,
});

export default function (data) {
  cloud.consume(data);
}
```

#### JSON 输出（调试用）

```bash
# 输出摘要到JSON
k6 run --summary-export=results.json --out json=results/raw.json scripts/load.js
```

### 7️⃣ CI/CD 集成

#### GitHub Actions 示例

```yaml
# .github/workflows/k6-performance.yml
name: K6 Performance Test

on:
  pull_request:
    types: [opened, synchronize]
  push:
    branches: [main]

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D693
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run smoke tests
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}
        run: k6 run k6/scripts/smoke.js

      - name: Run load tests
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}
          K6_CLOUD_TOKEN: ${{ secrets.K6_CLOUD_TOKEN }}
        run: k6 run k6/scripts/load.js --out cloud

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: k6-results
          path: results/
```

#### Docker 中运行 K6

```dockerfile
# Dockerfile
FROM grafana/k6:latest
COPY k6/ /k6/
WORKDIR /k6
ENTRYPOINT ["k6", "run"]
```

```bash
# 运行
docker build -t k6-tests .
docker run --rm -it \
  -e BASE_URL=https://staging.example.com \
  -v $(pwd)/results:/k6/results \
  k6-tests scripts/load.js --summary-export=results/summary.json
```

### 8️⃣ 最佳实践清单

#### ✅ 必须遵循的原则

1. **始终设置 Thresholds**
   ```javascript
   export const options = {
     thresholds: {
       http_req_duration: ['p(95)<500'],  // ✅ 必须有
     },
   };
   ```

2. **使用环境变量管理配置**
   ```javascript
   const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
   const TEST_DATA_SIZE = parseInt(__ENV.DATA_SIZE) || 100;
   ```

3. **合理设置思考时间**
   ```javascript
   sleep(randomIntBetween(1, 3));  // ✅ 模拟真实用户
   // 避免 sleep(0) 或不调用 sleep
   ```

4. **使用 Tags 标记关键请求**
   ```javascript
   http.get(url, { tags: { name: 'critical_api_call' } });
   ```

5. **Setup/Teardown 清理测试数据**
   ```javascript
   export function teardown(data) {
     // 删除测试期间创建的数据
     http.del(`${BASE_URL}/api/test-data/${data.testId}`, {
       headers: { 'X-Admin-Token': ADMIN_TOKEN }
     });
   }
   ```

#### ❌ 应该避免的反模式

1. **不要硬编码敏感信息**
   ```javascript
   // ❌ 错误
   const password = 'super_secret_password';

   // ✅ 正确
   const password = __ENV.TEST_PASSWORD;
   ```

2. **不要忽略错误处理**
   ```javascript
   // ❌ 错误
   const res = http.get(url);

   // ✅ 正确
   const res = http.get(url, { timeout: '30s' });
   check(res, {
     'request successful': (r) => r.status === 200,
     'or acceptable error': (r) => [429, 503].includes(r.status),
   });
   ```

3. **不要在循环中进行同步等待**
   ```javascript
   // ❌ 错误
   for (let i = 0; i < 100; i++) {
     http.get(url);
     sleep(1);  // 串行执行，效率低
   }

   // ✅ 正确：让 K6 的调度器并行处理
   export const options = { vus: 100, duration: '1m' };
   export default function () {
     http.get(url);
     sleep(1);
   }
   ```

4. **不要在生产环境直接运行高压测试**
   ```bash
   # ❌ 错误：直接对生产环境施压
   k6 run stress.js  # 如果 BASE_URL=https://prod.example.com

   # ✅ 正确：先在 staging 验证，再在 prod 小范围测试
   K6_ENV=staging k6 run load.js
   # 经过充分验证后才：
   K6_ENV=prod k6 run smoke.js  # 仅冒烟测试
   ```

### 9️⃣ 性能问题诊断指南

#### 响应时间长

1. **拆解耗时组件**
   ```javascript
   import { check } from 'k6';
   import http from 'k6/http';

   export default function () {
     const res = http.get('https://api.example.com/data');

     console.log(`Total: ${res.timings.duration}ms`);
     console.log(`  Connecting: ${res.timings.connecting}ms`);
     console.log(`  TLS Handshake: ${res.timings.tls_handshaking}ms`);
     console.log(`  Sending: ${res.timings.sending}ms`);
     console.log(`  Waiting (TTFB): ${res.timings.waiting}ms`);
     console.log(`  Receiving: ${res.timings.receiving}ms`);

     // 重点查看 waiting（TTFB）— 服务器处理时间
     if (res.timings.waiting > 1000) {
       console.warn('⚠️  Server processing time too high!');
     }
   }
   ```

2. **检查点定位瓶颈**
   - TTFB 高 → 服务器端瓶颈（数据库查询、复杂计算）
   - Receiving 高 → 响应体过大（需要分页/压缩）
   - Connecting/TLS 高 → 网络问题或连接池未复用

#### 错误率高

1. **捕获并分析错误响应**
   ```javascript
   export default function () {
     const res = http.get(url);

     if (res.error_code) {
       // 网络层错误
       console.error(`Network error: ${res.error}`);
     } else if (res.status >= 400) {
       // 应用层错误
       console.error(`HTTP ${res.status}: ${res.status_text}`);
       console.error(`Response body: ${res.body.substring(0, 200)}`);

       // 统计错误类型
       if (res.status === 429) {
         console.warn('⚠️  Rate limited — consider reducing load');
       } else if (res.status === 503) {
         console.error('❌ Service unavailable — server overloaded');
       }
     }
   }
   ```

2. **常见原因排查**
   - **429 Too Many Requests**: 限流触发 → 降低 VU 数或增加 rate limit
   - **502 Bad Gateway**: 网关/反向代理问题 → 检查 Nginx/ALB 配置
   - **503 Service Unavailable**: 服务过载 → 检查服务器资源（CPU/内存）
   - **Connection Timeout**: 服务器无响应 → 可能已宕机或网络不通

#### 吞吐量上不去

1. **检查 VU 利用率**
   ```javascript
   // 如果 http_reqs/s 远低于 vus * (1 / iteration_duration)
   // 说明 VU 大部分时间在等待（sleep 或 I/O阻塞）
   ```

2. **优化方向**
   - 减少 sleep 时间
   - 增加 VU 数
   - 使用 `constant-arrival-rate` executor 替代 `constant-vus`
   - 检查是否有外部依赖成为瓶颈（第三方API、数据库等）

### 🔟 完整示例：电商全链路压测

```javascript
// k6/scripts/e2e-commerce.js
import { check, sleep, group } from 'k6';
import http from 'k6/http';
import { randomIntBetween, randomItem, uuidv4 } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { Counter, Rate, Trend } from 'k6/metrics';

// 业务指标
export const ordersCreated = new Counter('orders_created_total');
export const paymentsCompleted = new Rate('payments_success_rate');
export const checkoutDuration = new Trend('checkout_flow_duration');

export const options = {
  scenarios: {
    // 场景1：浏览用户（70%流量）
    browsers: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '3m', target: 700 },
        { duration: '10m', target: 700 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browseFlow',
      tags: { user_type: 'browser' },
    },

    // 场景2：购买用户（30%流量）
    buyers: {
      executor: 'per-vu-iterations',
      vus: 100,
      iterations: 10,
      maxDuration: '15m',
      exec: 'buyFlow',
      tags: { user_type: 'buyer' },
    },
  },

  thresholds: {
    // 浏览场景阈值
    'http_req_duration{user_type:browser}': ['p(95)<600'],
    'http_req_failed{user_type:browser}': ['rate<0.02'],

    // 购买场景阈值（更严格）
    'http_req_duration{user_type:buyer}': ['p(95)<1200', 'p(99)<2500'],
    'http_req_failed{user_type:buyer}': ['rate<0.01'],

    // 业务指标阈值
    'payments_success_rate': ['rate>0.95'],
    'checkout_flow_duration': ['p(90)<5000', 'p(95)<8000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const PRODUCTS = Array.from({ length: 50 }, (_, i) => i + 1);

function getToken() {
  const loginRes = http.post(`${BASE_URL}/auth/token`, JSON.stringify({
    grant_type: 'password',
    username: `perf_test_${__VU}`,
    password: 'PerfTest123!',
  }), { headers: { 'Content-Type': 'application/json' } });

  return loginRes.json('access_token');
}

// ===== 浏览流程 =====
export function browseFlow() {
  group('Homepage', function () {
    const homeRes = http.get(`${BASE_URL}/`, { tags: { page: 'home' } });
    check(homeRes, { 'homepage loaded': (r) => r.status === 200 });
  });

  sleep(randomIntBetween(1, 3));

  group('Product Listing', function () {
    const page = randomIntBetween(1, 10);
    const listRes = http.get(
      `${BASE_URL}/products?page=${page}&category=all`,
      { tags: { page: 'listing' } }
    );
    check(listRes, {
      'product list loaded': (r) => r.status === 200,
      'has products': (r) => JSON.parse(r.body).items.length > 0,
    });
  });

  sleep(randomIntBetween(2, 5));

  group('Product Detail', function () {
    const productId = randomItem(PRODUCTS);
    const detailRes = http.get(
      `${BASE_URL}/products/${productId}`,
      { tags: { page: 'detail' } }
    );
    check(detailRes, {
      'product detail loaded': (r) =>
        r.status === 200 || r.status === 404,
    });
  });

  sleep(randomIntBetween(2, 4));
}

// ===== 购买流程 =====
export function buyFlow() {
  const startTime = Date.now();
  const token = getToken();

  try {
    group('Search Product', function () {
      const searchRes = http.get(
        `${BASE_URL}/search?q=laptop`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
          tags: { flow: 'buy', step: 'search' },
        }
      );
      check(searchRes, { 'search results': (r) => r.status === 200 });
    });

    sleep(randomIntBetween(1, 2));

    group('Add to Cart', function () {
      const addCartRes = http.post(
        `${BASE_URL}/cart/items`,
        JSON.stringify({
          product_id: randomItem(PRODUCTS),
          quantity: 1,
        }),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          tags: { flow: 'buy', step: 'add_cart' },
        }
      );
      check(addCartRes, {
        'item added to cart': (r) => r.status === 201,
      });
    });

    sleep(randomIntBetween(1, 3));

    group('Checkout', function () {
      const checkoutRes = http.post(
        `${BASE_URL}/orders`,
        JSON.stringify({
          shipping_address: {
            street: 'Test Street 123',
            city: 'Test City',
            zip: '12345',
            country: 'US',
          },
          payment_method: 'credit_card',
        }),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          tags: { flow: 'buy', step: 'checkout' },
        }
      );

      const isSuccessful = check(checkoutRes, {
        'order created': (r) => r.status === 201,
        'order ID returned': (r) => r.json('id') !== undefined,
      });

      if (isSuccessful) {
        ordersCreated.add(1);
        const orderId = checkoutRes.json('id');

        group('Payment', function () {
          const payRes = http.post(
            `${BASE_URL}/orders/${orderId}/pay`,
            JSON.stringify({
              method: 'card',
              card_token: 'tok_test_visa_4242',
            }),
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
              tags: { flow: 'buy', step: 'payment' },
            }
          );

          const paySuccess = check(payRes, {
            'payment processed': (r) => [200, 202].includes(r.status),
          });

          paymentsCompleted.add(paySuccess ? 1 : 0);
        });
      }
    });

  } catch (e) {
    console.error(`Buy flow error for VU ${__VU}:`, e.message);
  } finally {
    const endTime = Date.now();
    checkoutDuration.add(endTime - startTime);
  }

  sleep(randomIntBetween(3, 8));
}
```

运行命令：
```bash
# 完整电商压测
K6_ENV=staging k6 run k6/scripts/e2e-commerce.js \
  --out influxdb=k6/outputs/influxdb.js \
  --summary-export=k6/results/ecommerce-summary.json
```

---

## 📚 相关资源

- **K6 官方文档**: https://grafana.com/docs/k6/latest/
- **K6 示例脚本库**: https://grafana.com/docs/k6/latest/examples/
- **Grafana Cloud K6**: https://grafana.com/cloud/testing/k6/
- **K6 Studio（GUI工具）**: https://grafana.com/docs/k6-studio/
- **K6 扩展市场**: https://grafana.com/docs/k6/latest/extensions/

## 🎯 触发条件

当用户提到以下关键词时，启用此 Skill：

- "压测"、"压力测试"、"负载测试"
- "性能测试"、"performance test"
- "k6"、"k6 testing"
- "全链路压测"、"接口压测"
- "并发测试"、"高可用测试"
- "峰值测试"、"尖峰测试"
- "稳定性测试"、"浸泡测试"
- "SLO"、"SLA"、"性能基线"
- "吞吐量"、"TPS"、"QPS"、"RT"
