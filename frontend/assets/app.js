import * as THREE from "/potree_component/vendor/potree/libs/three.js/build/three.module.js";

const PROJECT_SLUG = "webodm-demo";
const state = { viewer: null, pointcloud: null, project: null, dataset: null };

const elements = {
  title: document.querySelector("#project-title"),
  subtitle: document.querySelector("#project-subtitle"),
  description: document.querySelector("#project-description"),
  pointCount: document.querySelector("#point-count"),
  epsg: document.querySelector("#epsg"),
  loading: document.querySelector("#loading-panel"),
  loadingDetail: document.querySelector("#loading-detail"),
  error: document.querySelector("#error-panel"),
  errorMessage: document.querySelector("#error-message"),
  toast: document.querySelector("#toast"),
  aboutDialog: document.querySelector("#about-dialog"),
  measurementToggle: document.querySelector("#measurement-toggle"),
  measurementPanel: document.querySelector("#measurement-panel"),
  measurementStatus: document.querySelector("#measurement-status"),
};

const measurementTools = {
  distance: {
    label: "距離",
    instruction: "在點雲上依序按左鍵標記路徑，完成後按右鍵。結果以公尺顯示。",
    options: { showDistances: true, showArea: false, closed: false, name: "距離" },
  },
  area: {
    label: "面積",
    instruction: "沿著範圍邊界按左鍵標記至少三點，完成後按右鍵。結果為水平投影面積。",
    options: { showDistances: true, showArea: true, closed: true, name: "面積" },
  },
  height: {
    label: "高差",
    instruction: "依序點選低點與高點，系統會顯示兩點的垂直高差。",
    options: { showDistances: false, showHeight: true, showArea: false, closed: false, maxMarkers: 2, name: "高差" },
  },
  point: {
    label: "座標",
    instruction: "點選地景中的一個位置，畫面會顯示該點的 X、Y、Z 座標。",
    options: { showDistances: false, showCoordinates: true, showArea: false, closed: true, maxMarkers: 1, name: "座標" },
  },
};

function formatNumber(value) {
  return new Intl.NumberFormat("zh-TW", { notation: "compact", maximumFractionDigits: 2 }).format(value);
}

function formatBytes(value) {
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`API 回應 ${response.status}`);
  return response.json();
}

function renderMetadata(project, dataset) {
  document.title = `${project.title}｜互動式 3D 點雲`;
  elements.title.textContent = project.title;
  elements.subtitle.textContent = project.subtitle;
  elements.description.textContent = project.description;
  elements.pointCount.textContent = formatNumber(dataset.point_count);
  elements.pointCount.title = `${dataset.point_count.toLocaleString("zh-TW")} 點，${formatBytes(dataset.size_bytes)}`;
  elements.epsg.textContent = `EPSG:${dataset.epsg}`;
}

function initViewer() {
  if (!window.Potree) throw new Error("Potree 顯示元件未載入");
  window.THREE = THREE;
  const viewer = new Potree.Viewer(document.querySelector("#potree-render-area"));
  viewer.setEDLEnabled(true);
  viewer.setFOV(58);
  viewer.setPointBudget(window.innerWidth < 720 ? 700_000 : 1_800_000);
  viewer.setBackground("gradient");
  viewer.setDescription("");
  viewer.loadSettingsFromURL();
  state.viewer = viewer;
}

function loadPointCloud(dataset) {
  return new Promise((resolve, reject) => {
    elements.loadingDetail.textContent = "串流載入點雲節點…";
    Potree.loadPointCloud(dataset.ept_url, dataset.name, (event) => {
      if (!event?.pointcloud) {
        reject(new Error("點雲檔案無法解析"));
        return;
      }
      const pointcloud = event.pointcloud;
      state.viewer.scene.addPointCloud(pointcloud);
      pointcloud.material.size = 1;
      pointcloud.material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
      pointcloud.material.shape = Potree.PointShape.CIRCLE;
      pointcloud.material.activeAttributeName = "rgba";
      state.viewer.fitToScreen(0.55);
      state.pointcloud = pointcloud;
      resolve(pointcloud);
    });
  });
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  window.setTimeout(() => elements.toast.classList.remove("is-visible"), 2200);
}

function setMeasurementPanel(open) {
  elements.measurementPanel.hidden = !open;
  elements.measurementToggle.setAttribute("aria-expanded", String(open));
}

function cancelMeasurementInsertion() {
  state.viewer?.dispatchEvent({ type: "cancel_insertions" });
  document.querySelectorAll("[data-measure-tool]").forEach((button) => button.classList.remove("is-active"));
}

function startMeasurement(type, button) {
  if (!state.viewer || !state.pointcloud) {
    showToast("點雲尚未載入完成");
    return;
  }
  const tool = measurementTools[type];
  cancelMeasurementInsertion();
  state.viewer.measuringTool.startInsertion(tool.options);
  button.classList.add("is-active");
  elements.measurementStatus.textContent = tool.instruction;
  showToast(`已啟用${tool.label}量測`);
}

function setColorMode(mode, button) {
  if (!state.pointcloud) return;
  state.pointcloud.material.activeAttributeName = mode;
  document.querySelectorAll("[data-color-mode]").forEach((item) => item.classList.remove("is-active"));
  button.classList.add("is-active");
  const labels = { rgba: "真實色彩", elevation: "高程色階", classification: "地物分類" };
  showToast(`已切換為${labels[mode]}`);
}

function bindControls() {
  document.querySelectorAll("[data-color-mode]").forEach((button) => {
    button.addEventListener("click", () => setColorMode(button.dataset.colorMode, button));
  });
  document.querySelector("#point-size").addEventListener("input", (event) => {
    if (state.pointcloud) state.pointcloud.material.size = Number(event.target.value);
  });
  document.querySelector("#reset-view").addEventListener("click", () => {
    state.viewer?.fitToScreen(0.55);
    showToast("已回到全景");
  });
  document.querySelector("#fullscreen-button").addEventListener("click", async () => {
    if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
    else await document.exitFullscreen();
  });
  document.querySelector("#about-button").addEventListener("click", () => elements.aboutDialog.showModal());
  elements.measurementToggle.addEventListener("click", () => {
    setMeasurementPanel(elements.measurementPanel.hidden);
  });
  document.querySelector("#measurement-close").addEventListener("click", () => setMeasurementPanel(false));
  document.querySelectorAll("[data-measure-tool]").forEach((button) => {
    button.addEventListener("click", () => startMeasurement(button.dataset.measureTool, button));
  });
  document.querySelector("#clear-measurements").addEventListener("click", () => {
    cancelMeasurementInsertion();
    state.viewer?.scene.removeAllMeasurements();
    elements.measurementStatus.textContent = "所有量測已清除。選擇工具即可重新開始。";
    showToast("已清除全部量測");
  });
  document.querySelector("#share-button").addEventListener("click", async () => {
    try {
      if (navigator.share) await navigator.share({ title: document.title, url: location.href });
      else {
        await navigator.clipboard.writeText(location.href);
        showToast("網址已複製");
      }
    } catch (error) {
      if (error.name !== "AbortError") showToast("暫時無法分享");
    }
  });
  document.querySelector("#retry-button").addEventListener("click", () => location.reload());
  window.addEventListener("keydown", (event) => {
    if (event.key.toLowerCase() === "r" && !event.ctrlKey && !event.metaKey) state.viewer?.fitToScreen(0.55);
    if (event.key === "Escape" && !elements.aboutDialog.open) {
      cancelMeasurementInsertion();
      elements.measurementStatus.textContent = "量測已取消；既有結果仍保留在畫面上。";
    }
  });
}

function showError(error) {
  console.error(error);
  elements.loading.classList.add("is-hidden");
  elements.error.hidden = false;
  elements.errorMessage.textContent = `${error.message}。請確認服務與點雲資料後重新載入。`;
}

async function start() {
  bindControls();
  try {
    elements.loadingDetail.textContent = "讀取專案資訊…";
    const [project, dataset] = await Promise.all([
      fetchJson(`/api/v1/projects/${PROJECT_SLUG}`),
      fetchJson(`/api/v1/projects/${PROJECT_SLUG}/point-cloud`),
    ]);
    state.project = project;
    state.dataset = dataset;
    renderMetadata(project, dataset);
    initViewer();
    await loadPointCloud(dataset);
    elements.loading.classList.add("is-hidden");
  } catch (error) {
    showError(error);
  }
}

start();
