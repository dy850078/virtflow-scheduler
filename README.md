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

## 🛠 未來規劃

- 加入實體硬體 API 整合
- 任務 queue 改為 RabbitMQ / Redis
- 優化排程算法（多目標 / 權重調整）
- 支援多租戶 / 多 Region 排程

## 🤝 貢獻與參與

歡迎 PR 或開 issue 提出想法、回饋與建議！

---

如需更多細節，請參閱 [virtflow-scheduler GitHub](https://github.com/dy850078/virtflow-scheduler)。