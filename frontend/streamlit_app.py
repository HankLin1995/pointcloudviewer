from __future__ import annotations

import logging
import re
import secrets
from pathlib import Path

import streamlit as st

from components.potree_viewer import potree_viewer
from services.archive_service import (
    ArchiveValidationError,
    cleanup_expired_sessions,
    extract_archive,
    remove_directory,
)
from services.ept_service import EptMetadata, EptValidationError, inspect_ept


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_pointcloud_preview")

APP_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = APP_ROOT / "static"
SESSIONS_ROOT = STATIC_ROOT / "sessions"

st.set_page_config(
    page_title="EPT 三維點雲臨時預覽器",
    page_icon="🛰️",
    layout="wide",
)


def format_bytes(value: int) -> str:
    units = ("B", "KB", "MB", "GB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:,.1f} {unit}"
        amount /= 1024
    return f"{amount:,.1f} GB"


def session_id() -> str:
    if "preview_session_id" not in st.session_state:
        st.session_state.preview_session_id = secrets.token_urlsafe(12)
    return st.session_state.preview_session_id


def restore_temporary_preview() -> None:
    requested = st.query_params.get("preview")
    if not requested or "dataset_metadata" in st.session_state:
        return
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,64}", requested):
        return
    candidate = SESSIONS_ROOT / requested
    if not candidate.is_dir():
        return
    try:
        st.session_state.preview_session_id = requested
        st.session_state.dataset_metadata = inspect_ept(candidate)
    except EptValidationError:
        logger.warning("Temporary preview could not be restored session=%s", requested)


def prepare_dataset(uploaded_file) -> EptMetadata:
    identifier = session_id()
    final_root = SESSIONS_ROOT / identifier
    staging_root = SESSIONS_ROOT / f".{identifier}.staging"
    if staging_root.exists():
        remove_directory(staging_root, SESSIONS_ROOT)
    extract_archive(uploaded_file, staging_root)
    try:
        metadata = inspect_ept(staging_root)
        relative_ept = metadata.ept_path.relative_to(staging_root)
        if final_root.exists():
            remove_directory(final_root, SESSIONS_ROOT)
        staging_root.rename(final_root)
        return inspect_ept(final_root / relative_ept.parent)
    except Exception:
        if staging_root.exists():
            remove_directory(staging_root, SESSIONS_ROOT)
        raise


def viewer_dataset(metadata: EptMetadata) -> dict[str, object]:
    ept_relative = metadata.ept_path.relative_to(STATIC_ROOT).as_posix()
    return {
        "eptUrl": f"/app/static/{ept_relative}",
        "name": st.session_state.get("project_name", "臨時點雲預覽"),
        "pointCount": metadata.point_count,
        "epsg": metadata.epsg,
        "sizeBytes": metadata.size_bytes,
    }


cleanup_expired_sessions(SESSIONS_ROOT)
restore_temporary_preview()

st.title("EPT 三維點雲臨時預覽器")
st.caption("上傳 WebODM 的 entwine_pointcloud.zip，直接瀏覽三維點雲並使用量測工具。資料只做臨時預覽。")

with st.sidebar:
    st.header("上傳點雲")
    st.text_input("展示名稱", value="臨時點雲預覽", key="project_name")
    uploaded = st.file_uploader(
        "選擇 entwine_pointcloud.zip",
        type=("zip",),
        help="ZIP 內必須包含 ept.json、ept-data 與 ept-hierarchy。",
    )
    start_preview = st.button(
        "解壓並開啟預覽",
        type="primary",
        use_container_width=True,
        disabled=uploaded is None,
    )
    st.caption("App 休眠、重新部署或工作階段逾時後，暫存資料可能自動消失。")

if start_preview and uploaded is not None:
    try:
        with st.status("正在準備點雲", expanded=True) as status:
            st.write("檢查 ZIP 路徑與容量")
            st.write("解壓縮 EPT 分塊")
            metadata = prepare_dataset(uploaded)
            st.write("讀取 ept.json 並建立預覽")
            st.session_state.dataset_metadata = metadata
            st.query_params["preview"] = session_id()
            status.update(label="點雲已準備完成", state="complete", expanded=False)
        logger.info(
            "Prepared EPT session=%s points=%s size_bytes=%s",
            session_id(),
            metadata.point_count,
            metadata.size_bytes,
        )
    except (ArchiveValidationError, EptValidationError) as error:
        logger.warning("Upload rejected session=%s error=%s", session_id(), error)
        st.error(str(error))
    except Exception as error:
        logger.exception("Unexpected preview preparation failure")
        st.error(f"無法建立預覽：{error}")

metadata = st.session_state.get("dataset_metadata")
if metadata:
    columns = st.columns(4)
    columns[0].metric("點數", f"{metadata.point_count:,}")
    columns[1].metric("座標系統", metadata.epsg)
    columns[2].metric("解壓後容量", format_bytes(metadata.size_bytes))
    height_range = metadata.bounds[5] - metadata.bounds[2]
    columns[3].metric("高度範圍", f"{height_range:,.2f} m")

    st.subheader(st.session_state.get("project_name", "臨時點雲預覽"))
    potree_viewer(dataset=viewer_dataset(metadata), key=f"viewer-{session_id()}")
else:
    st.info("請從左側上傳 entwine_pointcloud.zip，完成驗證後會在這裡顯示三維點雲。")
    st.markdown(
        """
        **支援的操作**

        - 拖曳旋轉、滾輪縮放、右鍵平移
        - 真實色彩、高程色階及地物分類
        - 距離、水平面積、兩點高差與座標量測
        """
    )
