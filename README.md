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

### 🟢 方案 1：Seed Cluster + Workload Clusters 分離（推薦方案）
#### 🔥 架構概念：
用 3~5 台 BM 先起一組 Seed Cluster（K8s），這個 Cluster 永遠是 scheduler 與 provision 系統的居住地。
Workload Clusters 都由這個 Seed Cluster 透過 virtflow-scheduler 動態生成。
Seed Cluster 自己不參與被調度（exclude 自己）。

#### 📌 優點：

項目	說明
穩定性	高。因為 scheduler 自己不會影響自己，cluster control plane 與 workload 分開。
擴展性	好。Seed Cluster 穩定存在，能支援多個 workload clusters，cluster 數量和規模皆可彈性增長。
維運成本	適中。一開始手動起 Seed Cluster，但之後不用一直碰，focus 在 scheduler 與 provision 開發。
開發成本	低。Scheduler logic 開發單純，無需考慮自身重啟影響（no recursive scheduling problem）。
資源利用率	稍低於理想（因為 Seed Cluster 是 reserved，不參與其他 cluster VM host）。
故障隔離	佳。Workload clusters 出問題不影響 scheduler，只有 Seed Cluster 本身出問題時影響 scheduler。
彈性復原	容易。如果 Seed Cluster 壞了，可以用 PXE + Ansible 快速重建（因為是固定 inventory）。
#### 🚩 缺點：
必須預留一些 BM，只給 Seed Cluster 使用（但這其實是 trade-off for stability）。

初始建置時需花一點時間部署這個 Seed Cluster，但這是一勞永逸。

## 🟡 方案 2：Non-K8s 外部服務部署（RabbitMQ + SQLite + virtflow-scheduler on baremetal/docker-compose）
### 🔥 架構概念：
virtflow-scheduler 跟 RabbitMQ 不跑在 K8s，而是跑在 Docker (Compose / systemd) 直接在 BM or VM 上。

用這套非 K8s 管理的系統去起 Workload Cluster。

#### 📌 優點：

項目	說明
穩定性	高。scheduler 本體跟 K8s 無關，不怕自己的 scheduling 影響自身運作。
維運成本	低初期（不用先建一個 k8s），但非 K8s 系統長期維運不如 K8s native 管理方便。
開發成本	略高（需要自己維護非 k8s 的 deployment / health-check / HA）。
資源利用率	高（BM 不需要 reserve 給 Seed Cluster，全部可動態調度）。
擴展性	一般（非 K8s native，擴展到多站點或多 scheduler 需要自行實作 HA / Leader Election）。
故障隔離	好。scheduler crash 不會影響任何 cluster（反之亦然），但自身 HA 需手動處理（如 keepalived）。
彈性復原	普通。因為非 k8s，沒有 built-in operator / deployment 來自動復原，需要自己實作 systemd / health-check 重啟。
#### 🚩 缺點：
跟你目前 K8s infra 維運習慣脫節（你需要維護一個非 K8s 的架構）。

長遠來看，當系統規模變大，會想回頭變成 k8s native。

## 🔵 方案 3：共生（第一組 Cluster 同時承載 scheduler）
### 🔥 架構概念：
最小化手動建置一組 K8s Cluster，scheduler 就住在這裡。

這組 cluster 同時也是 VM hosting 的 target（但是 scheduler 邏輯 exclude 自己）。

#### 📌 優點：

項目	說明
開發成本	最低（scheduler 跟 workload cluster 是同一個平台，無需多餘維運其他系統）。
資源利用率	高（因為 scheduler 跟 workload 共用一組 BM）。
初期部署簡單	快速部署，無需多一套 Seed Cluster。
#### 🚩 缺點（這是最大痛點）：

項目	說明
穩定性	低（如果 scheduler 不小心排自己 cluster 上的 BM 出去，可能自斷生路）。
維運成本	高（每次調度邏輯變動都要小心不要破壞自己）。
擴展性	中（scale-out 時需要考慮 master-node resource 是否足夠，否則會干擾 scheduler 運作）。
彈性復原	普通。除非你額外做 HA Scheduler Deployment，否則 scheduler 掛了就影響整個 provisioning。
📊 總結比較表：

指標	Seed Cluster 分離（方案1）	Non-K8s 外部服務（方案2）	共生（方案3）
穩定性	⭐⭐⭐⭐☆	⭐⭐⭐⭐☆	⭐⭐☆☆☆
擴展性	⭐⭐⭐⭐☆	⭐⭐⭐☆☆	⭐⭐⭐☆☆
維運成本	⭐⭐⭐☆☆	⭐⭐☆☆☆	⭐⭐⭐☆☆
開發成本	⭐⭐⭐☆☆	⭐⭐☆☆☆	⭐⭐⭐⭐☆
資源利用率	⭐⭐⭐☆☆	⭐⭐⭐⭐☆	⭐⭐⭐⭐☆
故障隔離	⭐⭐⭐⭐☆	⭐⭐⭐⭐☆	⭐⭐☆☆☆
彈性復原	⭐⭐⭐⭐☆	⭐⭐☆☆☆	⭐⭐☆☆☆


## 🤝 貢獻與參與

歡迎 PR 或開 issue 提出想法、回饋與建議！

---

如需更多細節，請參閱 [virtflow-scheduler GitHub](https://github.com/dy850078/virtflow-scheduler)。
