# toxicology-uploader

FastAPI + Docker 服務：上傳 PDF 到 `toxicology-vault/pendings/`，供 MinerU pipeline 處理。

## 功能

- 🌐 Web UI：拖曳或選擇 PDF 上傳（支援多檔）
- 📂 `GET /pendings` — 列出目前 pendings/ 中的 PDF
- 📤 `POST /upload` — 上傳 API（multipart/form-data）
- ❤️ `GET /health` — 健康檢查
- 📖 `GET /docs` — Swagger UI

## 快速啟動

### Docker Compose（推薦）

```bash
# 確保 toxicology-vault/ 在同層目錄
docker compose up --build -d
# 瀏覽 http://localhost:8000
```

### 手動（開發模式）

```bash
pip install -r requirements.txt
PENDINGS_DIR=/path/to/toxicology-vault/pendings uvicorn main:app --reload
```

## 環境變數

| 變數 | 預設值 | 說明 |
|---|---|---|
| `PENDINGS_DIR` | `/vault/pendings` | pendings/ 目錄路徑 |

## 目錄結構

```
toxicology-uploader/
├── main.py              # FastAPI app
├── requirements.txt
├── Dockerfile
├── docker-compose.yml   # 掛載 ../toxicology-vault/pendings
└── README.md
```
