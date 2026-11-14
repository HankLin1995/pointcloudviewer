from __future__ import annotations

import os

import httpx
import streamlit as st
import streamlit.components.v1 as components


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
PUBLIC_APP_URL = os.getenv("PUBLIC_APP_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="數位地景管理台", page_icon="🛰️", layout="wide")
st.title("數位地景管理台")
st.caption("此管理頁只透過 FastAPI 讀取資料，不直接存取 SQLite。")


def get_json(path: str) -> dict:
    with httpx.Client(timeout=10) as client:
        response = client.get(f"{API_BASE_URL}{path}")
        response.raise_for_status()
        return response.json()


try:
    health = get_json("/api/v1/health")
    projects = get_json("/api/v1/projects")["items"]
except (httpx.HTTPError, KeyError) as error:
    st.error(f"無法連線後端 API：{error}")
    st.stop()

status_columns = st.columns(3)
status_columns[0].metric("API 狀態", health["status"])
status_columns[1].metric("SQLite", health["database"])
status_columns[2].metric("點雲", health["pointcloud"])

if not projects:
    st.info("目前沒有已發布的專案。")
    st.stop()

project_options = {item["title"]: item["slug"] for item in projects}
selected_title = st.selectbox("公開專案", project_options)
slug = project_options[selected_title]
project = get_json(f"/api/v1/projects/{slug}")
dataset = get_json(f"/api/v1/projects/{slug}/point-cloud")

left, right = st.columns([2, 1])
with left:
    st.subheader(project["title"])
    st.write(project["description"])
    st.link_button("另開民眾展示頁", PUBLIC_APP_URL)
with right:
    st.metric("點數", f"{dataset['point_count']:,}")
    st.metric("EPT 容量", f"{dataset['size_bytes'] / 1024 / 1024:.1f} MB")
    st.code(f"EPSG:{dataset['epsg']}", language=None)

st.divider()
st.subheader("即時預覽")
components.iframe(PUBLIC_APP_URL, height=720, scrolling=False)
