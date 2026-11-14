# Streamlit 臨時點雲預覽器設計

## 需求

- 使用者上傳 WebODM 產生的 `entwine_pointcloud.zip`。
- 系統只提供當次工作階段預覽，不保證永久保存。
- 上傳完成後直接顯示 Potree 三維點雲及距離、面積、高差、座標量測工具。
- 不使用 FastAPI、SQLite 或外部物件儲存。

## 架構

Streamlit 負責上傳介面、ZIP 驗證、暫存解壓及嵌入檢視器。Potree 以 Streamlit
自訂元件提供，確保 CSS、JavaScript 及解碼 Worker 具有正確 MIME；EPT 分塊則從
Streamlit 靜態檔案路徑讀取。

```text
st.file_uploader
  -> archive_service 安全解壓
  -> ept_service 驗證 ept.json
  -> static/sessions/<session-id>/
  -> potree_component/index.html
  -> Potree.loadPointCloud
```

## 驗證規則

- ZIP 內必須只有一組有效的 EPT 根目錄。
- EPT 根目錄必須包含 `ept.json`、`ept-data` 及 `ept-hierarchy`。
- 拒絕絕對路徑、父目錄跳脫、符號連結、過多檔案及超過限制的解壓縮容量。
- 先解壓至 staging 目錄，驗證成功後再切換成工作階段目錄，避免顯示半套資料。

## 生命週期

資料只放在 Streamlit 執行環境的 `static/sessions`。同一工作階段重新上傳時會取代舊資料；
網址中的隨機 preview 代碼可在檔案仍存在時恢復預覽，逾時資料則由清理程序移除。
Community Cloud 重啟或重新部署時，資料可能消失，符合本功能的臨時預覽定位。

## 部署入口

Streamlit Community Cloud 的入口檔案設定為 `frontend/streamlit_app.py`。
