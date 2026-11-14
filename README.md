# 空拍數位地景

面向民眾的 WebODM EPT 三維點雲展示網站。

## 組成

- FastAPI：公開 API、商業邏輯與靜態資料入口
- SQLite：專案、點雲與標註中繼資料
- Potree：瀏覽器端 EPT 串流與三維呈現
- Streamlit：只透過 API 讀取的內部檢視頁

## 快速啟動

目前工作區已有完整 EPT 資料，可直接執行：

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

開啟：

- 民眾展示頁：http://127.0.0.1:8000
- API 文件：http://127.0.0.1:8000/docs

另一個終端可啟動管理檢視頁：

```powershell
python -m streamlit run admin/app.py
```

管理頁：http://127.0.0.1:8501

## 純 Streamlit 臨時預覽器

這個入口不需要 FastAPI 或 SQLite。使用者上傳完整的
`entwine_pointcloud.zip` 後，資料會暫時解壓至工作階段目錄並載入 Potree：

```powershell
python -m streamlit run frontend/streamlit_app.py
```

本機預覽：http://127.0.0.1:8501

部署到 Streamlit Community Cloud 時，將 Main file path 設為
`frontend/streamlit_app.py`。上傳資料不保證跨重啟保存。
Potree 以 Streamlit 自訂元件載入，因此不需要額外的靜態網站伺服器。

## Docker

```powershell
docker compose up -d --build
```

## 測試

```powershell
python -m pytest -q
```

## 資料與 API 設計

- `docs/database.md`
- `docs/api.md`

點雲檔案不寫入 SQLite；資料庫只保存中繼資料與 EPT 路徑。前端與 Streamlit 都不直接存取資料庫。
