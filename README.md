# virtflow-scheduler

Bare Metal 自動化部署系統中的 VM 調度元件，根據資源需求（CPU, Memory）、Pool 分群、Dedicated 條件，從多台 BM 中挑選最適合建立 VM 的機器。

## 📁 專案結構

```
virtflow-scheduler/
├── app/
│   ├── api/
│   │   ├── endpoints.py
│   │   └── node-endpoints.py
│   ├── core/
│   │   ├── config.py
│   │   └── worker.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── algorithm.py
│   │   ├── node.py
│   │   └── scheduler.py
│   └── main.py
├── curl-command
├── Makefile
├── README.md
└── requirements.txt
```

## 🧠 架構圖

```text
                +--------------------------+
                |     Developer Trigger    |
                +------------+-------------+
                             |
                             v
                    +--------+--------+
                    |    FastAPI API   |
                    +--------+--------+
                             |
                +------------+-------------+
                |  Scheduling Worker Loop  |
                +------------+-------------+
                             |
                             v
                 +-----------+-----------+
                 |   Node Cache Manager  |
                 +-----------+-----------+
                             |
                +------------+-------------+
                |    Algorithm Service     |
                +------------+-------------+
                             |
                             v
               +-----------------------------+
               |  Best-fit Bare Metal Server |
               +-----------------------------+
```

## 📖 情境圖

使用者從前端或工具觸發 API，例如請求：

```json
curl -X POST "http://127.0.0.1:8080/schedule" \
     -H "Content-Type: application/json" \
     -d '{
           "requested_cpu": 4,
           "requested_memory": 8192,
           "requested_pool": "default",
           "dedicated": false
         }'
```

1. FastAPI 接收請求，寫入 `asyncio.Queue`
2. 背景 `worker` 處理請求
3. 從 `node.py` 取得所有 BM 資訊
4. 經過：
   - `pre_filter()` Based on pool/dedicated
   - `filter_nodes()` Based on CPU/Memory Resource
   - `score_nodes()` Based on  CPU/Memory utilization VM Quota 綜合評分
5. 回傳最適 BM

## 🚀 使用方式

### 安裝依賴

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 使用 Makefile 啟動

```bash
make node-up   # 啟動模擬節點 API
make api-up    # 啟動主排程 API
```

## 🔍 Swagger (API Docs)

啟動後開啟瀏覽器：

```
http://localhost:8080/docs
```

你將看到自動產生的 Swagger UI，可互動測試 API。

## 📡 API 規格

### POST `/schedule`

提交排程請求，系統會從節點中選擇最適機器。

#### Request Body

```json
{
  "requested_cpu": 8,
  "requested_memory": 16384,
  "requested_pool": "general",
  "dedicated": false
}
```

#### Response

```json
{
  "task_id": "f235b1d4-0ad0-4e2a-a9b7-62f8e2a6c128"
}
```

### GET `/result/{task_id}`

查詢排程結果

#### 成功 Response

```json
{
  "status": "completed",
  "result": {
    "name": "bm-001",
    "ip": "10.0.0.1"
  }
}
```

#### 處理中 Response

```json
{
  "status": "processing"
}
```

#### 失敗 Response

```json
{
  "status": "failed",
  "error": "No available nodes"
}
```

## 🧪 測試指令 (cURL)

```bash
curl -X POST http://localhost:8080/schedule -H "Content-Type: application/json" -d '{
  "requested_cpu": 8,
  "requested_memory": 16384,
  "requested_pool": "ai",
  "dedicated": true
}'
```


## 🗂️ Virtflow-Scheduler Backlog


### 🐇 RabbitMQ Task Queue

| 狀態 | 類別 | 功能項目 | 說明 |
|------|------|----------|------|
| ⏳ 待開發 | 任務佇列 | 整合 RabbitMQ 作為主任務佇列 | 使用 aio-pika 建立 connection、queue、consumer |
| ⏳ 待開發 | 任務發送 | 替代 asyncio queue 的 enqueue 動作 | 發佈任務至指定 routing key 的 queue（如 `task.schedule`） |
| ⏳ 待開發 | 任務接收 | 改寫 `worker.py` 為 RabbitMQ 消費者 | 負責從 queue 拿任務、執行、處理失敗與 retry |
| ⏳ 待開發 | Queue 建立邏輯 | 在 app 啟動時自動建立 queue/exchange | 使用 durable queue + topic exchange |
| ⏳ 待開發 | 任務狀態儲存 | 任務消費前/後狀態寫入 DB 或快取 | 支援查詢任務目前進度 |
| ⏳ 待開發 | 失敗容錯 | 支援 retry 機制與 Dead Letter Queue | 可設定最大重試次數，失敗通知 admin/log |
| ⏳ 待開發 | DevOps 支援 | 提供 RabbitMQ docker-compose 或 helm | 作為 local dev + K8s dev ready solution |

### 🆙 Upgrade Integration 

| 狀態 | 類別 | 功能項目 | 說明 |
|------|------|----------|------|
| ⏳ 待開發 | K8s Upgrade 整合 | Spare Node Provisioning API | 新增 `/spare/prepare` 接口觸發備援 VM |
| ⏳ 待開發 | Scheduler | prepare_spare() 核心邏輯 | 根據 BM 資源選擇部署點並回傳任務 |
| ⏳ 待開發 | Pipeline 整合 | 觸發 Ansible / GitLab 建立 VM | 將任務轉換為 VM 建立流程 |
| ⏳ 待開發 | Cluster 驗證 | Spare Node Ready 健康檢查 | 驗證 VM 是否成功加入 K8s 並 Ready |
| ⏳ 待開發 | 通知系統 | Webhook 通知 UpgradeCtrl | 任務成功完成時 POST 通知對方系統 |
| ⏳ 待開發 | 任務管理 | 任務狀態儲存與查詢 | 支援以 UUID 查任務狀態，並可記錄歷史 |
| ⏳ 待開發 | 容錯機制 | Timeout / Retry 處理 | 任務卡住或失敗時自動重試或標記失敗 |
| ⏳ 待開發 | 資源回收 | 升級完成釋放 spare node | 根據策略自動移除備援 VM |
| ⏳ 待開發 | 安全性 | Webhook 認證（HMAC） | 避免偽冒通知，增加 webhook 簽名驗證 |
| ⏳ 待開發 | 彈性通知 | 支援多 Webhook Receiver | 可設定多個 webhook endpoint |
| ⏳ 待開發 | 發布機制 | 將 webhook 換為 Event Bus | 若擴大可轉 Kafka/NATS 等 async 發布 |

## 部屬策略
### 🟢 方案 1：Seed Cluster + Workload Clusters 分離（推薦）
#### 架構概念：
預先手動部署一組 Seed Cluster（建議 3~5 台 Baremetal VM）。

virtflow-scheduler / RabbitMQ / Inventory / PXE / VM Provisioner 均部署在這組 Seed Cluster。

這組 Seed Cluster 專門負責其他 Workload Cluster 的 VM 選擇與生成，不參與被調度。

#### 優點：
- 穩定性高（不怕自斷生路）

- 多Cluster擴展容易（multi-cluster friendly）

- 故障隔離佳

- 重建 Seed Cluster 相對容易（PXE + Ansible）

#### 缺點：
- 需要預留一些 Baremetal，專門給 Seed Cluster 使用

- 初始建置 Seed Cluster 需要一點人力

### 🟡 方案 2：Non-K8s 外部服務部署
#### 架構概念：
virtflow-scheduler + RabbitMQ + SQLite 不跑在 Kubernetes，而是部署在 Docker / systemd 的 VM 或 Baremetal 上。

用來管理其他 K8s Cluster 的 VM 建置。

#### 優點：
- 不需要預先有 Kubernetes Cluster
- Bootstrap 最直接，快速啟動

- Scheduler 完全不受自身調度邏輯影響

#### 缺點：
- 與 K8s native 工具脫節（維運上無法用 Deployment / StatefulSet 等標準資源）

- HA 機制需自行實作（如 keepalived, corosync/pacemaker）

- 當規模變大時可能回頭想轉回 K8s native

### 🔵 方案 3：共生（第一組 Cluster 同時承載 Scheduler）
#### 架構概念：
建立一個最小化的 K8s Cluster（手動或自動 PXE + Ansible）。

virtflow-scheduler 跟 workload cluster 同居一個 cluster，透過排程邏輯排除自己。

#### 優點：
- 開發成本最低（部署與運行平台一致）

- 不需要額外維護 Seed Cluster

- 資源利用率高（不用預留 BM）

#### 缺點：
- 容易踩到自己（排錯難度高）

- Scheduler 一旦出錯有可能影響自己的 cluster hosting

- 擴展到多 cluster 時不夠靈活

Criteria | Seed Cluster Separation (Option 1) | Non-K8s External Service (Option 2) | Co-located Scheduler (Option 3)
|------|---------|---------|---------|
Stability | ⭐⭐⭐⭐☆ (High, control plane isolated) | ⭐⭐⭐⭐☆ (High, independent from K8s scheduling) | ⭐⭐☆☆☆ (Low, risk of self-impact if scheduler selects itself)
Scalability | ⭐⭐⭐⭐☆ (Supports multi-cluster expansion easily) | ⭐⭐⭐☆☆ (Manual HA and scaling needed) | ⭐⭐⭐☆☆ (Moderate, scale depends on master resource)
Operation Cost | ⭐⭐⭐☆☆ (Moderate, need to maintain Seed Cluster) | ⭐⭐☆☆☆ (Lower, but harder to maintain long-term) | ⭐⭐⭐☆☆ (Need careful logic for self-exclusion)
Development Cost | ⭐⭐⭐☆☆ (Simple, no self-scheduling issues) | ⭐⭐☆☆☆ (Slightly higher, maintain your own HA logic) | ⭐⭐⭐⭐☆ (Lowest, everything on one cluster)
Resource Utilization | ⭐⭐⭐☆☆ (Some BM reserved for Seed Cluster) | ⭐⭐⭐⭐☆ (No reservation needed, full BM utilization) | ⭐⭐⭐⭐☆ (Shared BM, high utilization)
Fault Isolation | ⭐⭐⭐⭐☆ (Workload issues don't affect scheduler) | ⭐⭐⭐⭐☆ (Good, but HA must be handled manually) | ⭐⭐☆☆☆ (Low, potential self-scheduling failure)
Resilience / Recovery | ⭐⭐⭐⭐☆ (Easy to rebuild Seed Cluster if needed) | ⭐⭐☆☆☆ (Manual recovery process required) | ⭐⭐☆☆☆ (HA and recovery complex, self-risk)


## 🤝 貢獻與參與

歡迎 PR 或開 issue 提出想法、回饋與建議！

---

如需更多細節，請參閱 [virtflow-scheduler GitHub](https://github.com/dy850078/virtflow-scheduler)。
