/**
 * Pengendali UI Swiss Studio (UI/UX Pro Max) & live SSE untuk seluruh 5 Agent AI.
 */
import { VoxelOffice3D } from "/static/office.js";
import { ZentiraCinemaEngine } from "/static/cinema.js";

const state = {
  agents: [],
  inbox: [],
  unreadCount: 0,
  officeMode: "work",
  modeSeq: 0,
  roofMode: "auto",
  cinemaAspect: "16:9",
  cinemaRecording: false,
  urls: { pc: "http://127.0.0.1:8000", phone: "http://127.0.0.1:8000" },
  activeView: null,
  theme: "day",
  subTabs: { repurpose: "text", leads: "discover", finance: "overview", cs: "reply" },
  cache: {
    trendResult: null,
    repurposeResult: null,
    repurposePrefill: null,
    leadsList: [],
    leadsDiscover: null,
    leadsPitch: null,
    financeOverview: null,
    financeSplit: null,
    financeRemindDraft: null,
    csReply: null,
    csQc: null,
    managerResult: null,
  },
};

const els = {
  canvas: document.getElementById("office-canvas"),
  bubbleLayer: document.getElementById("bubble-layer"),
  fallback: document.getElementById("webgl-fallback"),
  connStatus: document.getElementById("connection-status"),
  liveDot: document.getElementById("live-dot"),
  dock: document.getElementById("agent-dock"),
  drawer: document.getElementById("drawer"),
  drawerAvatar: document.getElementById("drawer-avatar"),
  drawerTitle: document.getElementById("drawer-title"),
  drawerSub: document.getElementById("drawer-subtitle"),
  drawerStatusBar: document.getElementById("drawer-status-bar"),
  drawerStatusPill: document.getElementById("drawer-status-pill"),
  drawerStatusText: document.getElementById("drawer-status-text"),
  btnDrawerIdle: document.getElementById("btn-drawer-idle"),
  drawerBody: document.getElementById("drawer-body"),
  inboxBadge: document.getElementById("inbox-badge"),
  phoneModal: document.getElementById("phone-modal"),
  phoneUrlText: document.getElementById("phone-url-text"),
  toast: document.getElementById("toast"),
  btnTheme: document.getElementById("btn-theme"),
  labelTheme: document.getElementById("label-theme"),
  btnZen: document.getElementById("btn-zen"),
  btnZenExit: document.getElementById("btn-zen-exit"),
  btnCycleLogo: document.getElementById("btn-cycle-logo"),
  brandLogoImg: document.getElementById("brand-logo-img"),
  favicon: document.getElementById("favicon"),
  namesModal: document.getElementById("names-modal"),
  namesFormList: document.getElementById("names-form-list"),
  namesErr: document.getElementById("names-err"),
  officeMenuWrap: document.getElementById("office-menu-wrap"),
  btnOfficeMenu: document.getElementById("btn-office-menu"),
  officeMenuDropdown: document.getElementById("office-menu-dropdown"),
  officeMenuDot: document.getElementById("office-menu-dot"),
  officeMenuLabel: document.getElementById("office-menu-label"),
  canvasWrap: document.getElementById("canvas-wrap"),
  cinemaCanvas: document.getElementById("cinema-canvas"),
  cinemaHud: document.getElementById("cinema-hud"),
  cinemaModeBadge: document.getElementById("cinema-mode-badge"),
  cinemaTime: document.getElementById("cinema-time"),
  cinemaShotLabel: document.getElementById("cinema-shot-label"),
  btnCinemaTour: document.getElementById("btn-cinema-tour"),
  btnCinemaRecord: document.getElementById("btn-cinema-record"),
  btnCinemaStop: document.getElementById("btn-cinema-stop"),
  btnBackupExport: document.getElementById("btn-backup-export"),
  btnBackupImport: document.getElementById("btn-backup-import"),
  backupImportFile: document.getElementById("backup-import-file"),
  btnOfficeLogout: document.getElementById("btn-office-logout"),
  loginOverlay: document.getElementById("login-overlay"),
  loginForm: document.getElementById("login-form"),
  loginPassword: document.getElementById("login-password"),
  loginErr: document.getElementById("login-err"),
};

const AGENT_ICONS = {
  manager: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"/></svg>`,
  trend: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`,
  repurpose: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="m10 8 6 4-6 4V8Z"/></svg>`,
  leads: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
  finance: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/></svg>`,
  cs: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/><path d="m9 12 2 2 4-4"/></svg>`,
};
const DEFAULT_AGENT_ICON = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>`;
const EDIT_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`;

const ZENTIRA_LOGOS = [
  { url: "/static/assets/zentira-1.png", label: "Zentira Emblem 1 (Rounded Z)" },
  { url: "/static/assets/zentira-2.png", label: "Zentira Emblem 2 (Modular 5-Block)" },
  { url: "/static/assets/zentira-3.png", label: "Zentira Emblem 3 (Ribbon Z)" },
  { url: "/static/assets/zentira-4.png", label: "Zentira Emblem 4 (Split Bold Z)" },
];
let activeLogoIdx = Number(localStorage.getItem("zentira_logo_idx") || 0) % ZENTIRA_LOGOS.length;

function applyBrandLogo(idx, notify = false) {
  activeLogoIdx = ((idx % ZENTIRA_LOGOS.length) + ZENTIRA_LOGOS.length) % ZENTIRA_LOGOS.length;
  const chosen = ZENTIRA_LOGOS[activeLogoIdx];
  localStorage.setItem("zentira_logo_idx", String(activeLogoIdx));
  if (els.brandLogoImg) els.brandLogoImg.src = chosen.url;
  if (els.favicon) els.favicon.href = chosen.url;
  if (notify) showToast(`Logo header aktif (${activeLogoIdx + 1}/4): ${chosen.label}`);
}

let office3d = null;
let cinemaEngine = null;
let toastTimer = null;

function formatSec(sec) {
  const s = Math.max(0, Math.floor(sec));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function startCinematicExperience(shouldRenderMP4 = false) {
  if (!office3d || !cinemaEngine) {
    showToast("Kanvas 3D belum siap.");
    return;
  }
  setOfficeDropdownOpen(false);
  closeDrawer();

  const aspect = state.cinemaAspect || "16:9";
  state.cinemaRecording = shouldRenderMP4;

  document.body.classList.add("cinema-mode");
  if (els.cinemaCanvas) els.cinemaCanvas.classList.remove("hidden");
  if (els.canvasWrap) {
    els.canvasWrap.classList.add(
      "cinema-frame",
      aspect === "9:16" ? "cinema-9x16" : "cinema-16x9"
    );
  }
  if (els.cinemaHud) {
    els.cinemaHud.classList.remove("hidden");
    els.cinemaHud.classList.toggle("recording", shouldRenderMP4);
  }
  if (els.cinemaModeBadge) {
    els.cinemaModeBadge.textContent = shouldRenderMP4 ? "RENDER MP4 60FPS" : "PREVIEW SINEMATIK";
  }

  const onProgress = ({ mode, elapsed, total, percent, label }) => {
    if (els.cinemaTime) {
      els.cinemaTime.textContent =
        mode === "render"
          ? `${percent}% (${formatSec(elapsed)} / ${formatSec(total)})`
          : `${formatSec(elapsed)} / ${formatSec(total)}`;
    }
    if (els.cinemaShotLabel) {
      els.cinemaShotLabel.textContent = label;
    }
  };

  const onFinish = (cancelled, result) => {
    document.body.classList.remove("cinema-mode");
    if (els.cinemaCanvas) els.cinemaCanvas.classList.add("hidden");
    if (els.canvasWrap) {
      els.canvasWrap.classList.remove("cinema-frame", "cinema-16x9", "cinema-9x16");
    }
    if (els.cinemaHud) {
      els.cinemaHud.classList.add("hidden");
      els.cinemaHud.classList.remove("recording");
    }
    state.cinemaRecording = false;
    if (result && result.error) {
      showToast(`Kendala render video: ${result.error}`);
    } else if (result && result.filename) {
      showToast(`Video ${result.format} siap! Tersimpan: ${result.filename}`);
    } else {
      showToast(cancelled ? "Tur sinematik dihentikan" : "Tur sinematik selesai!");
    }
  };

  if (shouldRenderMP4) {
    cinemaEngine.startOfflineMP4Render({ aspect, onProgress, onFinish });
  } else {
    cinemaEngine.startPreview({ aspect, onProgress, onFinish });
  }
}

function stopCinematicExperience() {
  if (cinemaEngine && cinemaEngine.active) {
    cinemaEngine.stop();
  }
}

function esc(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function rp(amount) {
  const n = Number(amount || 0);
  const sign = n < 0 ? "-" : "";
  return `${sign}Rp${Math.abs(Math.round(n)).toLocaleString("id-ID")}`;
}

function modelChipHtml(modelUsed) {
  if (!modelUsed) return "";
  const isGroq = String(modelUsed).toLowerCase().includes("groq");
  const cls = isGroq ? "groq" : "gemini";
  return `<span class="model-chip ${cls}" title="Model AI yang memproses laporan ini">AI: ${esc(modelUsed)}</span>`;
}

function showToast(msg) {
  els.toast.textContent = msg;
  els.toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => els.toast.classList.add("hidden"), 2500);
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast("Tersalin ke clipboard");
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
    showToast("Tersalin ke clipboard");
  }
}

async function api(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.detail || `Permintaan gagal (${resp.status})`);
  }
  return data;
}

async function saveOutput(prefix, content) {
  try {
    const res = await api("/api/save-output", {
      method: "POST",
      body: JSON.stringify({ prefix, content }),
    });
    showToast(`Tersimpan di outputs/${res.filename}`);
  } catch (err) {
    showToast(`Gagal simpan: ${err.message}`);
  }
}

function findAgent(id) {
  return state.agents.find((a) => a.id === id) || null;
}

function updateOfficeModeUI() {
  document.querySelectorAll("[data-office-mode]").forEach((btn) => {
    const isAct = btn.dataset.officeMode === state.officeMode;
    btn.classList.toggle("active", isAct);
    btn.setAttribute("aria-checked", isAct ? "true" : "false");
  });
  const modeShort = { work: "Kantor: Masuk", meeting: "Kantor: Meeting", holiday: "Kantor: Libur" };
  if (els.officeMenuLabel) {
    els.officeMenuLabel.textContent = modeShort[state.officeMode] || "Kantor: Masuk";
  }
  if (els.officeMenuDot) {
    els.officeMenuDot.className = `apple-status-dot ${state.officeMode}`;
  }
  const n = state.agents.length || 6;
  if (state.officeMode === "meeting") {
    els.connStatus.textContent = `Sedang Meeting • ${n} Agent di meja`;
  } else if (state.officeMode === "holiday") {
    els.connStatus.textContent = "Kantor Libur • Tim pulang naik Shuttle";
  } else {
    els.connStatus.textContent = `Terhubung live • ${n} Agent aktif`;
  }
}

function setOfficeDropdownOpen(open) {
  if (!els.officeMenuDropdown || !els.btnOfficeMenu) return;
  els.officeMenuDropdown.classList.toggle("hidden", !open);
  els.btnOfficeMenu.classList.toggle("open", open);
  els.btnOfficeMenu.setAttribute("aria-expanded", open ? "true" : "false");
}

function applySnapshot(snap) {
  state.agents = snap.agents || [];
  state.inbox = snap.inbox || [];
  state.unreadCount = snap.unread_count || 0;
  if (snap.office_mode) state.officeMode = snap.office_mode;
  if (typeof snap.mode_seq === "number") state.modeSeq = snap.mode_seq;
  if (snap.urls) {
    state.urls = snap.urls;
    els.phoneUrlText.textContent = snap.urls.phone;
  }

  if (office3d) {
    office3d.syncAgentsState(state.agents);
    office3d.syncOfficeMode(state.officeMode, state.modeSeq);
  }
  updateOfficeModeUI();
  renderDock();
  updateInboxBadge();
  updateDrawerStatusBar();
  // Refresh active drawer title if agent was renamed
  const activeAgent = findAgent(state.activeView);
  if (activeAgent) {
    els.drawerTitle.textContent = `${activeAgent.name} — ${activeAgent.role}`;
  }
  if (state.activeView === "inbox") renderInboxBody();
}

function updateInboxBadge() {
  if (state.unreadCount > 0) {
    els.inboxBadge.textContent = String(state.unreadCount);
    els.inboxBadge.classList.remove("hidden");
  } else {
    els.inboxBadge.classList.add("hidden");
  }
}

function updateDrawerStatusBar() {
  const agent = findAgent(state.activeView);
  if (!agent) {
    els.drawerStatusBar.classList.add("hidden");
    return;
  }
  els.drawerStatusBar.classList.remove("hidden");
  els.drawerStatusPill.className = `status-pill ${agent.status}`;
  const labelMap = {
    idle: "Siaga",
    working: "Bekerja",
    done: "Selesai",
    error: "Kendala",
  };
  els.drawerStatusPill.textContent = labelMap[agent.status] || agent.status;
  els.drawerStatusText.textContent = agent.bubble || "";
  if (els.btnDrawerIdle) {
    const showReset = agent.status === "done" || agent.status === "error";
    els.btnDrawerIdle.classList.toggle("hidden", !showReset);
  }
}

async function dismissAgentToIdle(agentId) {
  try {
    const updated = await api(`/api/agents/${encodeURIComponent(agentId)}/idle`, {
      method: "POST",
    });
    applySnapshot(updated);
  } catch (err) {
    showToast(`Gagal menenangkan agent: ${err.message}`);
  }
}

function renderDock() {
  const statusWord = {
    idle: "Siaga",
    working: "Sedang bekerja",
    done: "Laporan siap",
    error: "Ada kendala",
  };

  const agentButtons = state.agents
    .map((a, idx) => {
      const active = state.activeView === a.id ? "active" : "";
      const iconSvg = AGENT_ICONS[a.id] || DEFAULT_AGENT_ICON;
      const tip = `${a.role} • ${statusWord[a.status] || a.status}`;
      const dividerAfterManager =
        a.id === "manager" && idx < state.agents.length - 1
          ? `<span class="dock-divider" aria-hidden="true"></span>`
          : "";
      return `
        <button class="dock-item ${active}" data-agent="${esc(a.id)}" style="--agent-color:${esc(a.color)}" aria-label="${esc(a.name)} — ${esc(a.role)}">
          <span class="dock-tooltip">${esc(tip)}</span>
          <span class="dock-tile ${esc(a.status)}">
            ${iconSvg}
            <span class="dock-status-pip ${esc(a.status)}"></span>
          </span>
          <span class="dock-name">${esc(a.name)}</span>
        </button>${dividerAfterManager}`;
    })
    .join("");

  els.dock.innerHTML = `
    ${agentButtons}
    <span class="dock-divider" aria-hidden="true"></span>
    <button class="dock-item dock-edit-btn" id="btn-open-names" aria-label="Edit nama agent">
      <span class="dock-tooltip">Ubah nama karyawan AI</span>
      <span class="dock-tile">${EDIT_ICON}</span>
      <span class="dock-name">Nama</span>
    </button>
  `;

  els.dock.querySelectorAll("[data-agent]").forEach((btn) => {
    btn.addEventListener("click", () => openAgentDrawer(btn.dataset.agent));
  });

  const editBtn = document.getElementById("btn-open-names");
  if (editBtn) {
    editBtn.addEventListener("click", openNamesModal);
  }
}

function openNamesModal() {
  els.namesErr.classList.add("hidden");
  els.namesFormList.innerHTML = state.agents
    .map(
      (a) => `
      <div class="name-edit-row">
        <span class="voxel-dot" style="background:${esc(a.color)};width:10px;height:10px"></span>
        <div>
          <div class="name-edit-meta">Agent ${a.number} • ${esc(a.role)}</div>
          <input type="text" maxlength="24" data-rename-agent="${esc(a.id)}" value="${esc(a.name)}" placeholder="Nama custom..." />
        </div>
      </div>`
    )
    .join("");
  els.namesModal.classList.remove("hidden");
}

function closeNamesModal() {
  els.namesModal.classList.add("hidden");
}

function openAgentDrawer(agentId) {
  state.activeView = agentId;
  const agent = findAgent(agentId);
  if (!agent) return;

  if (office3d) office3d.selectAgent(agentId);
  els.drawer.classList.remove("closed");
  els.drawerAvatar.textContent = agent.id === "manager" ? "M" : String(agent.number);
  els.drawerAvatar.style.background = agent.color;
  els.drawerAvatar.style.color = agent.id === "manager" ? "#ffffff" : "#09090b";
  els.drawerTitle.textContent = `${agent.name} — ${agent.role}`;
  els.drawerSub.textContent = agent.subtitle;
  renderDock();
  updateDrawerStatusBar();

  if (agent.unread || agent.status === "done" || agent.status === "error") {
    api("/api/inbox/read", {
      method: "POST",
      body: JSON.stringify({ agent_id: agentId }),
    }).catch(() => {});
  }

  if (agentId === "manager") renderManagerPanel();
  else if (agentId === "trend") renderTrendPanel();
  else if (agentId === "repurpose") renderRepurposePanel();
  else if (agentId === "leads") renderLeadsPanel();
  else if (agentId === "finance") renderFinancePanel();
  else if (agentId === "cs") renderCSPanel();
}

function openInboxDrawer() {
  state.activeView = "inbox";
  els.drawer.classList.remove("closed");
  els.drawerAvatar.textContent = "IN";
  els.drawerAvatar.style.background = "#e4e4e7";
  els.drawerAvatar.style.color = "#09090b";
  els.drawerTitle.textContent = "Inbox Bos";
  els.drawerSub.textContent = "Founder: Raden Satria Jaya Winata • Riwayat laporan tim AI.";
  els.drawerStatusBar.classList.add("hidden");
  renderDock();
  renderInboxBody();

  if (
    state.unreadCount > 0 ||
    state.agents.some((a) => a.status === "done" || a.status === "error")
  ) {
    api("/api/inbox/read", { method: "POST", body: JSON.stringify({}) }).catch(() => {});
  }
}

function closeDrawer() {
  state.activeView = null;
  els.drawer.classList.add("closed");
  if (office3d) office3d.selectAgent(null);
  renderDock();
}

function renderInboxBody() {
  if (!state.inbox.length) {
    els.drawerBody.innerHTML = `
      <div class="card">
        <p class="muted-sm">Belum ada laporan masuk pada sesi ini. Pilih salah satu karyawan di ruangan 3D untuk memulai tugas.</p>
      </div>`;
    return;
  }

  els.drawerBody.innerHTML = `
    <div class="inbox-toolbar">
      <span class="muted-xs"><strong>${state.inbox.length}</strong> laporan tersimpan di sesi ini</span>
      <button class="btn btn-sm btn-danger" id="btn-clear-inbox">Hapus Semua</button>
    </div>
    ${state.inbox
      .map(
        (item, idx) => `
      <div class="item-card">
        <div class="item-head">
          <div>
            <div class="item-title">${esc(item.title)}</div>
            <div class="item-meta">${esc(item.agent_name)} (${esc(item.agent_role)}) • ${esc(item.timestamp)}</div>
            ${modelChipHtml(item.model_used)}
          </div>
          <div class="btn-row">
            <button class="btn btn-sm btn-secondary" data-copy-inbox="${idx}">Salin</button>
            <button class="btn btn-sm btn-danger" data-delete-inbox="${item.id}" title="Hapus laporan ini">Hapus</button>
          </div>
        </div>
        <div class="output-box" style="max-height:170px">${esc(item.markdown)}</div>
      </div>`
      )
      .join("")}`;

  els.drawerBody.querySelectorAll("[data-copy-inbox]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = state.inbox[Number(btn.dataset.copyInbox)];
      if (item) copyText(item.markdown);
    });
  });

  els.drawerBody.querySelectorAll("[data-delete-inbox]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const itemId = Number(btn.dataset.deleteInbox);
      try {
        const updated = await api(`/api/inbox/${itemId}`, { method: "DELETE" });
        applySnapshot(updated);
        showToast("Laporan dihapus dari Inbox");
      } catch (err) {
        showToast(`Gagal menghapus: ${err.message}`);
      }
    });
  });

  const clearBtn = document.getElementById("btn-clear-inbox");
  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      if (!confirm("Hapus seluruh laporan di Inbox Bos?")) return;
      try {
        const updated = await api("/api/inbox", { method: "DELETE" });
        applySnapshot(updated);
        showToast("Seluruh Inbox Bos dikosongkan");
      } catch (err) {
        showToast(`Gagal mengosongkan Inbox: ${err.message}`);
      }
    });
  }
}

// ==========================================
// AGENT MANAJER (ORCHESTRATOR — SATU PINTU)
// ==========================================
function renderManagerPanel() {
  const examples = [
    "Floatee baru ACC, siapin buat tayang dan tagih pelunasan",
    "Cari tren hari ini lalu langsung bikin paket 3 platform dari ide pertama",
    "Cek ringkasan kas dan pengingat jatuh tempo, lalu cari 5 kafe UMKM di Bandung",
  ];
  els.drawerBody.innerHTML = `
    <div class="card">
      <h3>Satu Pintu Perintah Tim Zentira</h3>
      <p class="muted-xs">Tulis 1 instruksi bebas — Manajer otomatis mendelegasikan dan menggerakkan karyawan AI yang tepat di ruangan 3D.</p>
      <div class="field">
        <label for="mgr-cmd">Perintah Bos *</label>
        <textarea id="mgr-cmd" placeholder="Contoh: Floatee baru ACC, siapin buat tayang dan tagih pelunasan"></textarea>
      </div>
      <div class="btn-row">
        ${examples
          .map(
            (ex, idx) =>
              `<button class="btn btn-sm btn-secondary" data-mgr-ex="${idx}">Contoh ${idx + 1}</button>`
          )
          .join("")}
      </div>
      <button class="btn btn-accent" id="btn-mgr-run">Jalankan Delegasi Manajer</button>
    </div>
    <div id="mgr-err" class="error-banner hidden"></div>
    <div id="mgr-out"></div>
  `;

  els.drawerBody.querySelectorAll("[data-mgr-ex]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("mgr-cmd").value = examples[Number(btn.dataset.mgrEx)];
    });
  });

  renderManagerOutput(state.cache.managerResult);

  document.getElementById("btn-mgr-run").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    const errEl = document.getElementById("mgr-err");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Manajer sedang mendelegasikan tim...";
    try {
      const data = await api("/api/agents/manager/run", {
        method: "POST",
        body: JSON.stringify({
          perintah: document.getElementById("mgr-cmd").value,
        }),
      });
      state.cache.managerResult = data;
      renderManagerOutput(data);
      showToast("Semua delegasi Manajer selesai!");
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Jalankan Delegasi Manajer";
    }
  });
}

function renderManagerOutput(data) {
  const wrap = document.getElementById("mgr-out");
  if (!wrap || !data || !data.report) return;
  const r = data.report;
  wrap.innerHTML = `
    <div class="card">
      <div class="item-head">
        <div>
          <h3>Laporan Delegasi (${r.hasil_delegasi.length} Tugas)</h3>
          ${modelChipHtml(data.model_used)}
        </div>
        <div class="btn-row">
          <button class="btn btn-sm btn-secondary" id="copy-mgr-all">Salin Semua</button>
          <button class="btn btn-sm btn-ok" id="save-mgr-all">Simpan</button>
        </div>
      </div>
      <p class="muted-xs"><strong>Rencana:</strong> ${esc(r.ringkasan_rencana)}</p>
      ${r.hasil_delegasi
        .map((item, idx) => {
          const targetMeta = findAgent(item.target_agent);
          const displayName = targetMeta ? `${targetMeta.name} (${targetMeta.role})` : item.target_agent;
          return `
          <div class="item-card">
            <div class="item-head">
              <div>
                <div class="item-title">${idx + 1}. ${esc(displayName)}</div>
                <div class="item-meta">${esc(item.ringkasan_tugas)}</div>
              </div>
              <div class="btn-row">
                <span class="pill ${item.berhasil ? "pill-ok" : "pill-danger"}">${item.berhasil ? "OK" : "Kendala"}</span>
                <button class="btn btn-sm btn-secondary" data-copy-mgr-item="${idx}">Salin</button>
              </div>
            </div>
            <div class="output-box" style="max-height:220px">${esc(item.output_markdown)}</div>
          </div>`;
        })
        .join("")}
    </div>`;

  document.getElementById("copy-mgr-all").onclick = () => copyText(data.markdown);
  document.getElementById("save-mgr-all").onclick = () => saveOutput("manager", data.markdown);
  wrap.querySelectorAll("[data-copy-mgr-item]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = r.hasil_delegasi[Number(btn.dataset.copyMgrItem)];
      if (item) copyText(item.output_markdown);
    });
  });
}

// ==========================================
// AGENT 1: RISET TREN
// ==========================================
function renderTrendPanel() {
  els.drawerBody.innerHTML = `
    <div class="card">
      <h3>Riset Tren Google Trends</h3>
      <div class="row-2">
        <div class="field">
          <label for="trend-geo">Wilayah (Geo)</label>
          <input id="trend-geo" value="ID" />
        </div>
        <div class="field">
          <label for="trend-max-ideas">Maks. Ide Cerita (1-3)</label>
          <input id="trend-max-ideas" type="number" min="1" max="3" value="3" />
        </div>
      </div>
      <label class="check-row">
        <input id="trend-fetch-only" type="checkbox" />
        Ambil tren mentah RSS saja (tanpa AI Gemini)
      </label>
      <button class="btn btn-accent" id="btn-run-trend">Jalankan Riset Tren</button>
    </div>
    <div id="trend-err" class="error-banner hidden"></div>
    <div id="trend-output-wrap"></div>
  `;

  renderTrendOutput(state.cache.trendResult);

  document.getElementById("btn-run-trend").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    const errEl = document.getElementById("trend-err");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Risa sedang meriset...";
    try {
      const data = await api("/api/agents/trend/run", {
        method: "POST",
        body: JSON.stringify({
          geo: document.getElementById("trend-geo").value || "ID",
          max_ideas: Number(document.getElementById("trend-max-ideas").value || 3),
          fetch_only: document.getElementById("trend-fetch-only").checked,
        }),
      });
      state.cache.trendResult = data;
      renderTrendOutput(data);
      showToast("Riset tren selesai");
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Jalankan Riset Tren";
    }
  });
}

function renderTrendOutput(data) {
  const wrap = document.getElementById("trend-output-wrap");
  if (!wrap || !data) return;

  if (data.mode === "full" && data.report && data.report.ide_cerita) {
    const r = data.report;
    wrap.innerHTML = `
      <div class="card">
        <div class="item-head">
          <div>
            <h3>${r.ide_cerita.length} Ide Cerita Denn &amp; Miki</h3>
            ${modelChipHtml(data.model_used)}
          </div>
          <div class="btn-row">
            <button class="btn btn-sm btn-secondary" id="copy-trend-md">Salin</button>
            <button class="btn btn-sm btn-ok" id="save-trend-md">Simpan</button>
          </div>
        </div>
        <p class="muted-xs">${esc(r.ringkasan_filter)}</p>
        ${r.ide_cerita
          .map(
            (idea, idx) => `
          <div class="item-card">
            <div class="item-title">${idx + 1}. ${esc(idea.judul_ide)}</div>
            <div class="item-meta"><strong>Tren:</strong> ${esc(idea.tren_sumber)} • <strong>Durasi:</strong> ${esc(idea.estimasi_durasi)}</div>
            <div class="item-meta"><strong>Hook 3 Detik:</strong> ${esc(idea.hook_3_detik)}</div>
            <div class="item-meta"><strong>Sudut Pandang:</strong> ${esc(idea.sudut_pandang_cerita)}</div>
            <div class="btn-row">
              <button class="btn btn-sm btn-secondary" data-send-to-repurpose="${idx}">Kirim ke Agent 2 (Repurposer) →</button>
            </div>
          </div>`
          )
          .join("")}
      </div>`;

    document.getElementById("copy-trend-md").onclick = () => copyText(data.markdown);
    document.getElementById("save-trend-md").onclick = () => saveOutput("trend", data.markdown);
    wrap.querySelectorAll("[data-send-to-repurpose]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idea = r.ide_cerita[Number(btn.dataset.sendToRepurpose)];
        state.cache.repurposePrefill = {
          title: idea.judul_ide,
          summary: `${idea.hook_3_detik}\n\n${idea.sudut_pandang_cerita}`,
        };
        openAgentDrawer("repurpose");
        showToast("Ide dikirim ke meja Repo (Agent 2)");
      });
    });
    return;
  }

  wrap.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>Daftar Tren Mentah</h3>
        <button class="btn btn-sm btn-secondary" id="copy-trend-raw">Salin</button>
      </div>
      <div class="output-box">${esc(data.markdown)}</div>
    </div>`;
  document.getElementById("copy-trend-raw").onclick = () => copyText(data.markdown);
}

// ==========================================
// AGENT 2: REPURPOSER 3 PLATFORM (+ UPLOAD VIDEO/AUDIO WHISPER)
// ==========================================
function renderRepurposePanel() {
  const tab = state.subTabs.repurpose || "text";
  els.drawerBody.innerHTML = `
    <div class="tabs">
      <button class="tab-btn ${tab === "text" ? "active" : ""}" data-rtab="text">Tulis Ringkasan</button>
      <button class="tab-btn ${tab === "media" ? "active" : ""}" data-rtab="media">Upload Video / Audio</button>
    </div>
    <div id="rep-tab-content"></div>
    <div id="rep-err" class="error-banner hidden"></div>
    <div id="rep-output-wrap"></div>
  `;

  els.drawerBody.querySelectorAll("[data-rtab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.subTabs.repurpose = btn.dataset.rtab;
      renderRepurposePanel();
    });
  });

  if (tab === "media") renderRepurposeMediaTab();
  else renderRepurposeTextTab();

  renderRepurposeOutput(state.cache.repurposeResult);
}

function renderRepurposeTextTab() {
  const pre = state.cache.repurposePrefill || {};
  const wrap = document.getElementById("rep-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>Paket Publikasi 3 Platform</h3>
      <div class="field">
        <label for="rep-title">Judul Kerja (opsional)</label>
        <input id="rep-title" placeholder="Contoh: Jas Hujan 3 Lapis" value="${esc(pre.title || "")}" />
      </div>
      <div class="field">
        <label for="rep-summary">Ringkasan Cerita Video *</label>
        <textarea id="rep-summary" placeholder="Tulis ringkasan singkat cerita video Denn & Miki...">${esc(pre.summary || "")}</textarea>
      </div>
      <div class="field">
        <label for="rep-cta">CTA / Catatan Endorse (opsional)</label>
        <input id="rep-cta" placeholder="Contoh: Cek link di bio / kode promo DENNMIKI10" />
      </div>
      <button class="btn btn-accent" id="btn-run-repurpose">Buat Paket TikTok, IG &amp; Shorts</button>
    </div>
  `;

  document.getElementById("btn-run-repurpose").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    const errEl = document.getElementById("rep-err");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Sedang meracik copy 3 platform...";
    try {
      const data = await api("/api/agents/repurpose/run", {
        method: "POST",
        body: JSON.stringify({
          judul_kerja: document.getElementById("rep-title").value,
          ringkasan: document.getElementById("rep-summary").value,
          cta_tambahan: document.getElementById("rep-cta").value,
        }),
      });
      state.cache.repurposeResult = data;
      renderRepurposeOutput(data);
      showToast("Paket 3 platform siap disalin");
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Buat Paket TikTok, IG & Shorts";
    }
  });
}

function renderRepurposeMediaTab() {
  const wrap = document.getElementById("rep-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>Video / Audio Mentah → 3 Platform Otomatis</h3>
      <p class="muted-xs">Upload video animasi atau rekaman suara Denn &amp; Miki — Groq Whisper gratis otomatis mentranskrip dialognya lalu langsung meracik paket TikTok, IG Reels &amp; YT Shorts!</p>
      <label class="upload-dropzone" id="rep-dropzone" for="rep-media-file">
        <input id="rep-media-file" type="file" accept=".mp4,.mov,.webm,.mp3,.wav,.m4a,.ogg,.flac,video/*,audio/*" />
        <div class="upload-dz-title" id="rep-file-label">Klik atau tarik file Video / Audio ke sini</div>
        <div class="muted-xs">Mendukung .mp4, .mov, .webm, .mp3, .wav, .m4a (maks. 25 MB)</div>
      </label>
      <div class="field">
        <label for="rep-media-title">Judul Kerja (opsional — otomatis dari nama file)</label>
        <input id="rep-media-title" placeholder="Contoh: Episode Kopi Mahal" />
      </div>
      <div class="field">
        <label for="rep-media-cta">CTA / Catatan Endorse (opsional)</label>
        <input id="rep-media-cta" placeholder="Contoh: Cek link di bio / kode promo DENNMIKI10" />
      </div>
      <div class="btn-row">
        <button class="btn btn-accent" style="flex:1" id="btn-rep-media-full">Transkrip &amp; Buat Paket 3 Platform</button>
        <button class="btn btn-secondary" id="btn-rep-media-only" title="Ambil teks transkrip saja lalu pindahkan ke kotak ringkasan untuk diedit">Transkrip Saja</button>
      </div>
    </div>
  `;

  const fileInput = document.getElementById("rep-media-file");
  const fileLabel = document.getElementById("rep-file-label");
  const dropzone = document.getElementById("rep-dropzone");
  let selectedFile = null;

  const setPickedFile = (file) => {
    selectedFile = file || null;
    if (selectedFile) {
      const mb = (selectedFile.size / (1024 * 1024)).toFixed(2);
      fileLabel.textContent = `Terpilih: ${selectedFile.name} (${mb} MB)`;
      dropzone.classList.add("has-file");
    } else {
      fileLabel.textContent = "Klik atau tarik file Video / Audio ke sini";
      dropzone.classList.remove("has-file");
    }
  };

  fileInput.addEventListener("change", () => setPickedFile(fileInput.files?.[0]));
  dropzone.addEventListener("dragover", (ev) => {
    ev.preventDefault();
    dropzone.classList.add("drag-over");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
  dropzone.addEventListener("drop", (ev) => {
    ev.preventDefault();
    dropzone.classList.remove("drag-over");
    const f = ev.dataTransfer?.files?.[0];
    if (f) setPickedFile(f);
  });

  const runMediaUpload = async (transcribeOnly, btnEl, defaultLabel) => {
    const errEl = document.getElementById("rep-err");
    errEl.classList.add("hidden");
    if (!selectedFile) {
      errEl.textContent = "Pilih file video atau audio terlebih dahulu.";
      errEl.classList.remove("hidden");
      return;
    }
    if (selectedFile.size > 25 * 1024 * 1024) {
      errEl.textContent = "Ukuran file melebihi batas maksimal 25 MB.";
      errEl.classList.remove("hidden");
      return;
    }

    const otherBtn = transcribeOnly
      ? document.getElementById("btn-rep-media-full")
      : document.getElementById("btn-rep-media-only");
    btnEl.disabled = true;
    if (otherBtn) otherBtn.disabled = true;
    btnEl.textContent = transcribeOnly
      ? "Mentranskrip audio (Whisper)..."
      : "Transkrip & meracik 3 platform...";

    try {
      const params = new URLSearchParams({
        judul_kerja: document.getElementById("rep-media-title").value || "",
        cta_tambahan: document.getElementById("rep-media-cta").value || "",
        transcribe_only: transcribeOnly ? "true" : "false",
      });
      const resp = await fetch(`/api/agents/repurpose/media?${params.toString()}`, {
        method: "POST",
        headers: {
          "Content-Type": selectedFile.type || "application/octet-stream",
          "X-File-Name": encodeURIComponent(selectedFile.name),
        },
        body: selectedFile,
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(data.detail || `Gagal memproses media (${resp.status})`);
      }

      if (transcribeOnly) {
        state.cache.repurposePrefill = {
          title: document.getElementById("rep-media-title").value || selectedFile.name.replace(/\.[^.]+$/, ""),
          summary: data.transcript || "",
        };
        state.subTabs.repurpose = "text";
        renderRepurposePanel();
        showToast("Transkrip berhasil! Silakan edit lalu buat paket 3 platform.");
      } else {
        state.cache.repurposeResult = data;
        renderRepurposeOutput(data);
        showToast("Video berhasil ditranskrip & dijadikan paket 3 platform!");
      }
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btnEl.disabled = false;
      if (otherBtn) otherBtn.disabled = false;
      btnEl.textContent = defaultLabel;
    }
  };

  document.getElementById("btn-rep-media-full").addEventListener("click", (e) => {
    runMediaUpload(false, e.currentTarget, "Transkrip & Buat Paket 3 Platform");
  });
  document.getElementById("btn-rep-media-only").addEventListener("click", (e) => {
    runMediaUpload(true, e.currentTarget, "Transkrip Saja");
  });
}

function renderRepurposeOutput(data) {
  const wrap = document.getElementById("rep-output-wrap");
  if (!wrap || !data || !data.report) return;
  const r = data.report;
  const platforms = [
    { key: "tiktok", label: "TikTok", copy: r.tiktok },
    { key: "instagram_reels", label: "Instagram Reels", copy: r.instagram_reels },
    { key: "youtube_shorts", label: "YouTube Shorts", copy: r.youtube_shorts },
  ];

  const transcriptCard = data.transcript
    ? `
      <div class="item-card">
        <div class="item-head">
          <div class="item-title">Transkrip Audio/Video ${data.filename ? `(${esc(data.filename)})` : ""}</div>
          <button class="btn btn-sm btn-secondary" id="copy-rep-transcript">Salin Transkrip</button>
        </div>
        <div class="output-box" style="max-height:110px">${esc(data.transcript)}</div>
      </div>`
    : "";

  wrap.innerHTML = `
    <div class="card">
      <div class="item-head">
        <div>
          <h3>Hasil Siap Upload</h3>
          ${modelChipHtml(data.model_used)}
        </div>
        <div class="btn-row">
          <button class="btn btn-sm btn-secondary" id="copy-rep-all">Salin Semua</button>
          <button class="btn btn-sm btn-ok" id="save-rep-all">Simpan</button>
        </div>
      </div>
      <p class="muted-xs">${esc(r.catatan_strategi)}</p>
      ${transcriptCard}
      ${platforms
        .map(
          (p) => `
        <div class="item-card">
          <div class="item-head">
            <div class="item-title">${p.label}</div>
            <button class="btn btn-sm btn-secondary" data-copy-plat="${p.key}">Salin</button>
          </div>
          <div class="item-meta"><strong>Judul:</strong> ${esc(p.copy.judul)}</div>
          <div class="item-meta"><strong>Caption:</strong> ${esc(p.copy.caption)}</div>
          <div class="item-meta"><strong>Hashtag:</strong> ${esc((p.copy.hashtags || []).join(" "))}</div>
          <div class="item-meta"><strong>Pinned Comment:</strong> ${esc(p.copy.pinned_comment)}</div>
        </div>`
        )
        .join("")}
    </div>`;

  document.getElementById("copy-rep-all").onclick = () => copyText(data.markdown);
  document.getElementById("save-rep-all").onclick = () => saveOutput("repurpose", data.markdown);
  const copyTrBtn = document.getElementById("copy-rep-transcript");
  if (copyTrBtn && data.transcript) {
    copyTrBtn.onclick = () => copyText(data.transcript);
  }
  wrap.querySelectorAll("[data-copy-plat]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = r[btn.dataset.copyPlat];
      const txt = `Judul: ${p.judul}\n\n${p.caption}\n\n${(p.hashtags || []).join(" ")}\n\nPinned Comment:\n${p.pinned_comment}`;
      copyText(txt);
    });
  });
}

// ==========================================
// AGENT 3: LEAD HUNTER UMKM
// ==========================================
function renderLeadsPanel() {
  const tab = state.subTabs.leads;
  els.drawerBody.innerHTML = `
    <div class="tabs">
      <button class="tab-btn ${tab === "discover" ? "active" : ""}" data-ltab="discover">Cari Otomatis</button>
      <button class="tab-btn ${tab === "list" ? "active" : ""}" data-ltab="list">Daftar &amp; Pitch WA</button>
    </div>
    <div id="leads-tab-content"></div>
  `;
  els.drawerBody.querySelectorAll("[data-ltab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.subTabs.leads = btn.dataset.ltab;
      renderLeadsPanel();
    });
  });

  if (tab === "discover") renderLeadsDiscoverTab();
  else renderLeadsListTab();
}

function renderLeadsDiscoverTab() {
  const wrap = document.getElementById("leads-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>Pencarian Prospek UMKM (OpenStreetMap)</h3>
      <div class="row-2">
        <div class="field">
          <label for="ld-keyword">Jenis Usaha *</label>
          <input id="ld-keyword" value="kopi" placeholder="kopi, bengkel, laundry, salon" />
        </div>
        <div class="field">
          <label for="ld-city">Kota / Daerah *</label>
          <input id="ld-city" value="Bandung" placeholder="Bandung, Bekasi, Sleman" />
        </div>
      </div>
      <div class="row-2">
        <div class="field">
          <label for="ld-radius">Radius (km)</label>
          <input id="ld-radius" type="number" min="1" max="25" value="5" />
        </div>
        <div class="field">
          <label for="ld-limit">Maks. Hasil</label>
          <input id="ld-limit" type="number" min="1" max="25" value="8" />
        </div>
      </div>
      <label class="check-row">
        <input id="ld-save" type="checkbox" checked />
        Simpan otomatis kandidat tanpa website ke Daftar Prospek
      </label>
      <button class="btn btn-accent" id="btn-ld-discover">Pindai Peta UMKM Sekarang</button>
    </div>
    <div id="ld-err" class="error-banner hidden"></div>
    <div id="ld-results"></div>
  `;

  renderDiscoverResults(state.cache.leadsDiscover);

  document.getElementById("btn-ld-discover").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    const errEl = document.getElementById("ld-err");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Lido sedang memindai peta...";
    try {
      const data = await api("/api/agents/leads/discover", {
        method: "POST",
        body: JSON.stringify({
          keyword: document.getElementById("ld-keyword").value,
          city: document.getElementById("ld-city").value,
          radius_km: Number(document.getElementById("ld-radius").value || 5),
          limit: Number(document.getElementById("ld-limit").value || 8),
          save_leads: document.getElementById("ld-save").checked,
        }),
      });
      state.cache.leadsDiscover = data;
      renderDiscoverResults(data);
      showToast(`Ditemukan ${data.discovered.length} UMKM lokal`);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Pindai Peta UMKM Sekarang";
    }
  });
}

function renderDiscoverResults(data) {
  const box = document.getElementById("ld-results");
  if (!box || !data) return;
  box.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>${data.discovered.length} UMKM (${data.saved_count} baru disimpan)</h3>
        <button class="btn btn-sm btn-ok" id="go-leads-list">Buka Daftar →</button>
      </div>
      ${
        data.discovered.length
          ? data.discovered
              .map(
                (item, i) => `
          <div class="item-card">
            <div class="item-head">
              <div class="item-title">${i + 1}. ${esc(item.nama_usaha)}</div>
              <span class="pill pill-info">${esc(item.kota)}</span>
            </div>
            <div class="item-meta">${esc(item.alamat || "Alamat sesuai peta OSM")}</div>
            <div class="item-meta">${item.kontak ? `Kontak: ${esc(item.kontak)}` : "Kontak belum terisi di OSM"} ${item.sumber_url ? `• <a href="${esc(item.sumber_url)}" target="_blank" rel="noopener">Lihat Peta</a>` : ""}</div>
          </div>`
              )
              .join("")
          : `<p class="muted-sm">Tidak ada kandidat baru ditemukan. Coba perbesar radius atau ganti kata kunci.</p>`
      }
    </div>`;
  const goBtn = document.getElementById("go-leads-list");
  if (goBtn) {
    goBtn.onclick = () => {
      state.subTabs.leads = "list";
      renderLeadsPanel();
    };
  }
}

async function renderLeadsListTab() {
  const wrap = document.getElementById("leads-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>Tambah Prospek Manual</h3>
      <div class="row-2">
        <div class="field"><label for="la-name">Nama Usaha *</label><input id="la-name" placeholder="Warung Kopi Sudut" /></div>
        <div class="field"><label for="la-cat">Kategori *</label><input id="la-cat" placeholder="Kafe / Bengkel" /></div>
      </div>
      <div class="row-2">
        <div class="field"><label for="la-city">Kota</label><input id="la-city" placeholder="Bandung" /></div>
        <div class="field"><label for="la-contact">Kontak (WA/IG)</label><input id="la-contact" placeholder="0812xxx / @ig" /></div>
      </div>
      <div class="field"><label for="la-notes">Catatan Observasi</label><input id="la-notes" placeholder="Rating Maps 4.9, belum punya katalog menu online" /></div>
      <button class="btn btn-secondary" id="btn-la-add">Simpan Prospek</button>
    </div>
    <div id="leads-list-err" class="error-banner hidden"></div>
    <div id="leads-pitch-box"></div>
    <div class="card">
      <div class="item-head">
        <h3>Daftar Prospek Tersimpan</h3>
        <button class="btn btn-sm btn-secondary" id="btn-leads-refresh">Muat Ulang</button>
      </div>
      <div class="row-2">
        <div class="field"><label for="lp-sender">Nama Pengirim</label><input id="lp-sender" placeholder="Opsional" /></div>
        <div class="field"><label for="lp-offer">Penawaran Khusus</label><input id="lp-offer" value="Gratis contoh konsep halaman depan dulu" /></div>
      </div>
      <div id="leads-items-container"><p class="muted-sm">Memuat daftar prospek...</p></div>
    </div>
  `;

  if (state.cache.leadsPitch) renderLeadPitchBox(state.cache.leadsPitch);

  const loadList = async () => {
    const container = document.getElementById("leads-items-container");
    try {
      const data = await api("/api/agents/leads/list");
      state.cache.leadsList = data.leads || [];
      if (!state.cache.leadsList.length) {
        container.innerHTML = `<p class="muted-sm">Belum ada prospek tersimpan. Gunakan tab <strong>Cari Otomatis</strong> atau tambah manual di atas.</p>`;
        return;
      }
      const statuses = ["baru", "dihubungi", "follow_up", "tertarik", "deal", "ditolak"];
      container.innerHTML = state.cache.leadsList
        .map(
          (l) => `
          <div class="item-card">
            <div class="item-head">
              <div>
                <div class="item-title">#${l.id} ${esc(l.nama_usaha)}</div>
                <div class="item-meta">${esc(l.kategori)}${l.kota ? ` • ${esc(l.kota)}` : ""} • ${l.punya_website ? "Sudah ada web" : "Belum punya web"}</div>
              </div>
              <select data-lead-status="${l.id}" style="width:auto;padding:4px 8px;border-radius:7px;border:1px solid var(--border);background:var(--surface-card);color:var(--text-main);font-size:11px;font-weight:600;">
                ${statuses.map((st) => `<option value="${st}" ${l.status === st ? "selected" : ""}>${st}</option>`).join("")}
              </select>
            </div>
            ${l.catatan ? `<div class="item-meta">${esc(l.catatan)}</div>` : ""}
            <div class="btn-row">
              <button class="btn btn-sm" data-pitch-lead="${l.id}">Buat Pesan WA (AI)</button>
              <button class="btn btn-sm btn-danger" data-del-lead="${l.id}">Hapus</button>
            </div>
          </div>`
        )
        .join("");

      container.querySelectorAll("[data-lead-status]").forEach((sel) => {
        sel.addEventListener("change", async () => {
          await api(`/api/agents/leads/${sel.dataset.leadStatus}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: sel.value }),
          });
          showToast(`Status #${sel.dataset.leadStatus} → ${sel.value}`);
        });
      });

      container.querySelectorAll("[data-del-lead]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await api(`/api/agents/leads/${btn.dataset.delLead}`, { method: "DELETE" });
          showToast(`Prospek #${btn.dataset.delLead} dihapus`);
          loadList();
        });
      });

      container.querySelectorAll("[data-pitch-lead]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.pitchLead;
          const errEl = document.getElementById("leads-list-err");
          errEl.classList.add("hidden");
          btn.disabled = true;
          btn.textContent = "Menulis pesan...";
          try {
            const res = await api(`/api/agents/leads/${id}/pitch`, {
              method: "POST",
              body: JSON.stringify({
                sender: document.getElementById("lp-sender").value,
                offer: document.getElementById("lp-offer").value,
                mark_contacted: false,
              }),
            });
            state.cache.leadsPitch = res;
            renderLeadPitchBox(res);
            showToast("Pesan penawaran siap disalin");
          } catch (err) {
            errEl.textContent = err.message;
            errEl.classList.remove("hidden");
          } finally {
            btn.disabled = false;
            btn.textContent = "Buat Pesan WA (AI)";
          }
        });
      });
    } catch (err) {
      container.innerHTML = `<div class="error-banner">${esc(err.message)}</div>`;
    }
  };

  document.getElementById("btn-leads-refresh").onclick = loadList;
  document.getElementById("btn-la-add").onclick = async () => {
    const errEl = document.getElementById("leads-list-err");
    errEl.classList.add("hidden");
    try {
      await api("/api/agents/leads/add", {
        method: "POST",
        body: JSON.stringify({
          nama_usaha: document.getElementById("la-name").value,
          kategori: document.getElementById("la-cat").value,
          kota: document.getElementById("la-city").value,
          kontak: document.getElementById("la-contact").value,
          catatan: document.getElementById("la-notes").value,
        }),
      });
      document.getElementById("la-name").value = "";
      document.getElementById("la-notes").value = "";
      showToast("Prospek ditambahkan");
      loadList();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  };

  loadList();
}

function renderLeadPitchBox(res) {
  const box = document.getElementById("leads-pitch-box");
  if (!box || !res || !res.report) return;
  const r = res.report;
  box.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>Pesan Penawaran — ${esc(r.lead.nama_usaha)}</h3>
        <div class="btn-row">
          <button class="btn btn-sm btn-secondary" id="copy-pitch-main">Salin Pesan</button>
          <button class="btn btn-sm btn-ok" id="save-pitch-all">Simpan</button>
        </div>
      </div>
      <div class="item-meta"><strong>Sudut Pendekatan:</strong> ${esc(r.sudut_pendekatan)}</div>
      <div class="output-box">${esc(r.pesan_utama)}</div>
      <div class="item-meta"><strong>Follow-Up (H+3):</strong> ${esc(r.pesan_followup)}</div>
    </div>`;
  document.getElementById("copy-pitch-main").onclick = () => copyText(r.pesan_utama);
  document.getElementById("save-pitch-all").onclick = () =>
    saveOutput(`lead_pitch_${r.lead.id}`, res.markdown);
}

// ==========================================
// AGENT 4: ADMIN KEUANGAN & PENGINGAT
// ==========================================
function renderFinancePanel() {
  const tab = state.subTabs.finance;
  els.drawerBody.innerHTML = `
    <div class="tabs">
      <button class="tab-btn ${tab === "overview" ? "active" : ""}" data-ftab="overview">Kas &amp; Tagihan</button>
      <button class="tab-btn ${tab === "record" ? "active" : ""}" data-ftab="record">Catat Baru</button>
      <button class="tab-btn ${tab === "split" ? "active" : ""}" data-ftab="split">Bagi Hasil</button>
    </div>
    <div id="fin-tab-content"></div>
  `;
  els.drawerBody.querySelectorAll("[data-ftab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.subTabs.finance = btn.dataset.ftab;
      renderFinancePanel();
    });
  });

  if (tab === "overview") renderFinanceOverviewTab();
  else if (tab === "record") renderFinanceRecordTab();
  else renderFinanceSplitTab();
}

async function renderFinanceOverviewTab() {
  const wrap = document.getElementById("fin-tab-content");
  wrap.innerHTML = `<p class="muted-sm">Memuat ringkasan keuangan...</p>`;
  try {
    const data = await api("/api/agents/finance/overview");
    state.cache.financeOverview = data;
    const s = data.summary;

    wrap.innerHTML = `
      <div class="item-head">
        <span class="muted-xs">Ringkasan seluruh lini usaha</span>
        <button class="btn btn-sm btn-danger" id="btn-fin-reset">Reset Buku Kas</button>
      </div>
      <div class="kpi-grid">
        <div class="kpi-box"><div class="kpi-label">Pemasukan</div><div class="kpi-val" style="color:var(--ok)">${rp(s.total_masuk)}</div></div>
        <div class="kpi-box"><div class="kpi-label">Pengeluaran</div><div class="kpi-val" style="color:var(--danger)">${rp(s.total_keluar)}</div></div>
        <div class="kpi-box"><div class="kpi-label">Saldo Bersih</div><div class="kpi-val">${rp(s.saldo_bersih)}</div></div>
        <div class="kpi-box"><div class="kpi-label">Piutang Klien</div><div class="kpi-val" style="color:var(--warn)">${rp(s.total_piutang_klien)}</div></div>
      </div>

      <div id="fin-draft-err" class="error-banner hidden"></div>
      <div id="fin-draft-box"></div>

      <div class="card">
        <h3>Pengingat DP &amp; Pelunasan Klien</h3>
        <div class="field">
          <label for="fin-bank">Info Rekening (untuk draf WA)</label>
          <input id="fin-bank" placeholder="Contoh: BCA 123456 a.n. Nama Anda" />
        </div>
        ${
          data.reminders.length
            ? data.reminders
                .map((rem) => {
                  const inv = rem.invoice;
                  const pillCls =
                    rem.kategori_urgensi === "terlambat"
                      ? "pill-danger"
                      : rem.kategori_urgensi === "hari_ini" || rem.kategori_urgensi === "segera"
                      ? "pill-warn"
                      : "pill-info";
                  return `
                  <div class="item-card">
                    <div class="item-head">
                      <div>
                        <div class="item-title">#${inv.id} ${esc(inv.klien)} — ${esc(inv.proyek)}</div>
                        <div class="item-meta">Sisa <strong>${rp(inv.sisa_tagihan)}</strong> dari ${rp(inv.total_harga)} • Tenggat: ${esc(inv.jatuh_tempo || "-")}</div>
                      </div>
                      <span class="pill ${pillCls}">${esc(rem.kategori_urgensi)}</span>
                    </div>
                    <div class="btn-row">
                      <button class="btn btn-sm btn-secondary" data-fin-draft="${inv.id}">Draf Tagih WA (AI)</button>
                      <button class="btn btn-sm btn-ok" data-fin-pay="${inv.id}" data-sisa="${inv.sisa_tagihan}">Lunasi (${rp(inv.sisa_tagihan)})</button>
                      <button class="btn btn-sm btn-danger" data-fin-del-inv="${inv.id}">Hapus</button>
                    </div>
                  </div>`;
                })
                .join("")
            : `<p class="muted-sm">Semua tagihan klien sudah lunas atau belum ada tagihan aktif.</p>`
        }
      </div>

      <div class="card">
        <h3>Transaksi Terbaru (${data.transactions.length})</h3>
        ${
          data.transactions.length
            ? data.transactions
                .slice(0, 12)
                .map(
                  (tx) => `
              <div class="item-card">
                <div class="item-head">
                  <div class="item-title" style="color:${tx.jenis === "masuk" ? "var(--ok)" : "var(--danger)"}">${tx.jenis === "masuk" ? "+" : "-"}${rp(tx.nominal)} <span class="muted-xs">(${esc(tx.sumber)}/${esc(tx.kategori)})</span></div>
                  <div class="btn-row" style="align-items:center">
                    <span class="muted-xs">${esc(tx.tanggal)}</span>
                    <button class="btn btn-sm btn-danger" data-fin-del-tx="${tx.id}" title="Hapus transaksi">Hapus</button>
                  </div>
                </div>
                ${tx.keterangan ? `<div class="item-meta">${esc(tx.keterangan)}</div>` : ""}
              </div>`
                )
                .join("")
            : `<p class="muted-sm">Belum ada transaksi tercatat. Gunakan tab <strong>Catat Baru</strong>.</p>`
        }
      </div>
    `;

    if (state.cache.financeRemindDraft) renderFinDraftBox(state.cache.financeRemindDraft);

    document.getElementById("btn-fin-reset").onclick = async () => {
      if (!window.confirm("Yakin hapus semua transaksi & tagihan keuangan kembali ke Rp0?")) {
        return;
      }
      await api("/api/agents/finance/reset", { method: "POST" });
      state.cache.financeRemindDraft = null;
      showToast("Buku kas berhasil di-reset ke Rp0");
      renderFinanceOverviewTab();
    };

    wrap.querySelectorAll("[data-fin-del-tx]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.finDelTx;
        await api(`/api/agents/finance/tx/${id}`, { method: "DELETE" });
        showToast(`Transaksi #${id} dihapus`);
        renderFinanceOverviewTab();
      });
    });

    wrap.querySelectorAll("[data-fin-del-inv]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.finDelInv;
        await api(`/api/agents/finance/invoice/${id}`, { method: "DELETE" });
        showToast(`Tagihan #${id} dihapus`);
        renderFinanceOverviewTab();
      });
    });

    wrap.querySelectorAll("[data-fin-pay]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.finPay;
        const sisa = Number(btn.dataset.sisa);
        await api(`/api/agents/finance/invoice/${id}/pay`, {
          method: "POST",
          body: JSON.stringify({ nominal: sisa, catatan: "Pelunasan via Kantor 3D" }),
        });
        showToast(`Tagihan #${id} lunas`);
        renderFinanceOverviewTab();
      });
    });

    wrap.querySelectorAll("[data-fin-draft]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.finDraft;
        const errEl = document.getElementById("fin-draft-err");
        errEl.classList.add("hidden");
        btn.disabled = true;
        btn.textContent = "Fina menulis pesan...";
        try {
          const res = await api(`/api/agents/finance/invoice/${id}/remind-draft`, {
            method: "POST",
            body: JSON.stringify({ bank: document.getElementById("fin-bank").value }),
          });
          state.cache.financeRemindDraft = res;
          renderFinDraftBox(res);
          showToast("Draf pengingat WA siap disalin");
        } catch (err) {
          errEl.textContent = err.message;
          errEl.classList.remove("hidden");
        } finally {
          btn.disabled = false;
          btn.textContent = "Draf Tagih WA (AI)";
        }
      });
    });
  } catch (err) {
    wrap.innerHTML = `<div class="error-banner">${esc(err.message)}</div>`;
  }
}

function renderFinDraftBox(res) {
  const box = document.getElementById("fin-draft-box");
  if (!box || !res || !res.draft) return;
  box.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>Draf Pengingat — ${esc(res.invoice.klien)}</h3>
        <button class="btn btn-sm btn-secondary" id="copy-fin-draft">Salin WA</button>
      </div>
      <div class="output-box">${esc(res.draft.pesan_pengingat)}</div>
    </div>`;
  document.getElementById("copy-fin-draft").onclick = () => copyText(res.draft.pesan_pengingat);
}

function renderFinanceRecordTab() {
  const wrap = document.getElementById("fin-tab-content");
  wrap.innerHTML = `
    <div id="fin-rec-err" class="error-banner hidden"></div>
    <div class="card">
      <h3>Catat Pemasukan / Pengeluaran</h3>
      <div class="row-2">
        <div class="field">
          <label for="ftx-type">Jenis</label>
          <select id="ftx-type"><option value="masuk">Pemasukan (Masuk)</option><option value="keluar">Pengeluaran (Keluar)</option></select>
        </div>
        <div class="field">
          <label for="ftx-stream">Lini Usaha</label>
          <select id="ftx-stream"><option value="konten">Konten Denn &amp; Miki</option><option value="web_umkm">Jasa Web UMKM</option><option value="umum">Umum</option></select>
        </div>
      </div>
      <div class="row-2">
        <div class="field"><label for="ftx-amount">Nominal (Rp) *</label><input id="ftx-amount" type="number" min="1" placeholder="500000" /></div>
        <div class="field"><label for="ftx-cat">Kategori *</label><input id="ftx-cat" placeholder="endorse / hosting / tools" /></div>
      </div>
      <div class="field"><label for="ftx-notes">Keterangan</label><input id="ftx-notes" placeholder="Catatan singkat transaksi" /></div>
      <button class="btn" id="btn-ftx-save">Simpan Transaksi</button>
    </div>

    <div class="card">
      <h3>Tambah Tagihan DP / Proyek Klien</h3>
      <div class="row-2">
        <div class="field"><label for="finv-client">Nama Klien *</label><input id="finv-client" placeholder="Kedai Kopi Sudut" /></div>
        <div class="field"><label for="finv-project">Nama Proyek *</label><input id="finv-project" placeholder="Website Katalog" /></div>
      </div>
      <div class="row-2">
        <div class="field"><label for="finv-total">Total Harga (Rp) *</label><input id="finv-total" type="number" min="1" placeholder="2000000" /></div>
        <div class="field"><label for="finv-dp">DP Diterima (Rp)</label><input id="finv-dp" type="number" min="0" value="0" /></div>
      </div>
      <div class="row-2">
        <div class="field">
          <label for="finv-stream">Lini Usaha</label>
          <select id="finv-stream"><option value="web_umkm">Jasa Web UMKM</option><option value="konten">Endorse Konten</option><option value="umum">Umum</option></select>
        </div>
        <div class="field"><label for="finv-due">Jatuh Tempo</label><input id="finv-due" type="date" /></div>
      </div>
      <button class="btn btn-ok" id="btn-finv-save">Simpan Tagihan Klien</button>
    </div>
  `;

  document.getElementById("btn-ftx-save").onclick = async () => {
    const errEl = document.getElementById("fin-rec-err");
    errEl.classList.add("hidden");
    try {
      await api("/api/agents/finance/tx", {
        method: "POST",
        body: JSON.stringify({
          jenis: document.getElementById("ftx-type").value,
          sumber: document.getElementById("ftx-stream").value,
          nominal: Number(document.getElementById("ftx-amount").value || 0),
          kategori: document.getElementById("ftx-cat").value,
          keterangan: document.getElementById("ftx-notes").value,
        }),
      });
      showToast("Transaksi dicatat");
      state.subTabs.finance = "overview";
      renderFinancePanel();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  };

  document.getElementById("btn-finv-save").onclick = async () => {
    const errEl = document.getElementById("fin-rec-err");
    errEl.classList.add("hidden");
    try {
      await api("/api/agents/finance/invoice", {
        method: "POST",
        body: JSON.stringify({
          klien: document.getElementById("finv-client").value,
          proyek: document.getElementById("finv-project").value,
          total_harga: Number(document.getElementById("finv-total").value || 0),
          dp: Number(document.getElementById("finv-dp").value || 0),
          sumber: document.getElementById("finv-stream").value,
          jatuh_tempo: document.getElementById("finv-due").value,
        }),
      });
      showToast("Tagihan klien dicatat");
      state.subTabs.finance = "overview";
      renderFinancePanel();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  };
}

function renderFinanceSplitTab() {
  const wrap = document.getElementById("fin-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>Kalkulator Bagi Hasil</h3>
      <div class="row-2">
        <div class="field"><label for="fsp-amount">Total Pendapatan (Rp) *</label><input id="fsp-amount" type="number" value="2000000" /></div>
        <div class="field"><label for="fsp-cost">Biaya Operasional (Rp)</label><input id="fsp-cost" type="number" value="200000" /></div>
      </div>
      <div class="field">
        <label for="fsp-shares">Komposisi Bagi Hasil (total 100%)</label>
        <input id="fsp-shares" value="Saya:60,Partner:40" placeholder="Saya:60,Partner:40" />
      </div>
      <button class="btn" id="btn-fsp-run">Hitung Bagi Hasil</button>
    </div>
    <div id="fsp-err" class="error-banner hidden"></div>
    <div id="fsp-out"></div>
  `;

  if (state.cache.financeSplit) renderSplitOut(state.cache.financeSplit);

  document.getElementById("btn-fsp-run").onclick = async () => {
    const errEl = document.getElementById("fsp-err");
    errEl.classList.add("hidden");
    try {
      const data = await api("/api/agents/finance/split", {
        method: "POST",
        body: JSON.stringify({
          total_pendapatan: Number(document.getElementById("fsp-amount").value || 0),
          biaya_operasional: Number(document.getElementById("fsp-cost").value || 0),
          shares: document.getElementById("fsp-shares").value,
        }),
      });
      state.cache.financeSplit = data;
      renderSplitOut(data);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  };
}

function renderSplitOut(data) {
  const box = document.getElementById("fsp-out");
  if (!box || !data) return;
  box.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>Hasil Perhitungan</h3>
        <button class="btn btn-sm btn-secondary" id="copy-split">Salin</button>
      </div>
      <div class="output-box">${esc(data.markdown)}</div>
    </div>`;
  document.getElementById("copy-split").onclick = () => copyText(data.markdown);
}

// ==========================================
// AGENT 5: ASISTEN CS & QC BRIEF
// ==========================================
function renderCSPanel() {
  const tab = state.subTabs.cs;
  els.drawerBody.innerHTML = `
    <div class="tabs">
      <button class="tab-btn ${tab === "reply" ? "active" : ""}" data-ctab="reply">Balas Klien</button>
      <button class="tab-btn ${tab === "qc" ? "active" : ""}" data-ctab="qc">QC Brief</button>
      <button class="tab-btn ${tab === "rate" ? "active" : ""}" data-ctab="rate">Rate Card</button>
    </div>
    <div id="cs-tab-content"></div>
  `;
  els.drawerBody.querySelectorAll("[data-ctab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.subTabs.cs = btn.dataset.ctab;
      renderCSPanel();
    });
  });

  if (tab === "reply") renderCSReplyTab();
  else if (tab === "qc") renderCSQCTab();
  else renderCSRateCardTab();
}

function renderCSReplyTab() {
  const wrap = document.getElementById("cs-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>Draf Balasan Calon Klien</h3>
      <div class="row-2">
        <div class="field">
          <label for="cs-service">Layanan</label>
          <select id="cs-service">
            <option value="auto">Deteksi Otomatis</option>
            <option value="endorse">Endorse Denn &amp; Miki</option>
            <option value="web_umkm">Jasa Website UMKM</option>
          </select>
        </div>
        <div class="field"><label for="cs-client">Nama Calon Klien</label><input id="cs-client" placeholder="Opsional" /></div>
      </div>
      <div class="field">
        <label for="cs-msg">Pesan Masuk Calon Klien *</label>
        <textarea id="cs-msg" placeholder="Tempel pesan WA/DM/email dari calon klien di sini..."></textarea>
      </div>
      <button class="btn btn-accent" id="btn-cs-reply">Buat Draf Balasan CS</button>
    </div>
    <div id="cs-reply-err" class="error-banner hidden"></div>
    <div id="cs-reply-out"></div>
  `;

  if (state.cache.csReply) renderCSReplyOut(state.cache.csReply);

  document.getElementById("btn-cs-reply").onclick = async (e) => {
    const btn = e.currentTarget;
    const errEl = document.getElementById("cs-reply-err");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Caca menyusun balasan...";
    try {
      const data = await api("/api/agents/cs/reply", {
        method: "POST",
        body: JSON.stringify({
          pesan_klien: document.getElementById("cs-msg").value,
          layanan: document.getElementById("cs-service").value,
          nama_klien: document.getElementById("cs-client").value,
        }),
      });
      state.cache.csReply = data;
      renderCSReplyOut(data);
      showToast("Draf balasan CS siap disalin");
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Buat Draf Balasan CS";
    }
  };
}

function renderCSReplyOut(data) {
  const box = document.getElementById("cs-reply-out");
  if (!box || !data || !data.report) return;
  const r = data.report;
  box.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>Balasan Siap Kirim <span class="pill pill-info">${esc(r.kategori_klien)}</span></h3>
        <div class="btn-row">
          <button class="btn btn-sm btn-secondary" id="copy-cs-draft">Salin</button>
          <button class="btn btn-sm btn-ok" id="save-cs-draft">Simpan</button>
        </div>
      </div>
      <div class="output-box">${esc(r.draf_balasan)}</div>
      ${
        r.perlu_konfirmasi_owner.length
          ? `<div class="item-card"><div class="item-title">Perlu Dicek Owner Sebelum Kirim</div>${r.perlu_konfirmasi_owner.map((n) => `<div class="item-meta">• ${esc(n)}</div>`).join("")}</div>`
          : ""
      }
    </div>`;
  document.getElementById("copy-cs-draft").onclick = () => copyText(r.draf_balasan);
  document.getElementById("save-cs-draft").onclick = () => saveOutput("cs_reply", data.markdown);
}

function renderCSQCTab() {
  const wrap = document.getElementById("cs-tab-content");
  wrap.innerHTML = `
    <div class="card">
      <h3>QC Brief Endorse vs Skrip</h3>
      <div class="field"><label for="qc-brand">Nama Brand (opsional)</label><input id="qc-brand" placeholder="Contoh: Es Teh Segar" /></div>
      <div class="field"><label for="qc-brief">Poin-Poin Brief Klien *</label><textarea id="qc-brief" placeholder="Tempel syarat brief & larangan (don'ts) dari klien..."></textarea></div>
      <div class="field"><label for="qc-script">Skrip Animasi Denn &amp; Miki *</label><textarea id="qc-script" placeholder="Tempel draf skrip endorse Anda di sini..."></textarea></div>
      <button class="btn btn-accent" id="btn-cs-qc">Audit Kelengkapan Brief</button>
    </div>
    <div id="cs-qc-err" class="error-banner hidden"></div>
    <div id="cs-qc-out"></div>
  `;

  if (state.cache.csQc) renderCSQCOut(state.cache.csQc);

  document.getElementById("btn-cs-qc").onclick = async (e) => {
    const btn = e.currentTarget;
    const errEl = document.getElementById("cs-qc-err");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Caca memeriksa skrip...";
    try {
      const data = await api("/api/agents/cs/qc", {
        method: "POST",
        body: JSON.stringify({
          nama_brand: document.getElementById("qc-brand").value,
          brief_klien: document.getElementById("qc-brief").value,
          skrip: document.getElementById("qc-script").value,
        }),
      });
      state.cache.csQc = data;
      renderCSQCOut(data);
      showToast(`Audit QC selesai: ${data.report.status_keseluruhan}`);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Audit Kelengkapan Brief";
    }
  };
}

function renderCSQCOut(data) {
  const box = document.getElementById("cs-qc-out");
  if (!box || !data || !data.report) return;
  const r = data.report;
  const statusCls = r.status_keseluruhan === "LOLOS" ? "pill-ok" : "pill-danger";
  box.innerHTML = `
    <div class="card">
      <div class="item-head">
        <h3>Hasil QC: <span class="pill ${statusCls}">${esc(r.status_keseluruhan)} (${r.skor_persen}%)</span></h3>
        <div class="btn-row">
          <button class="btn btn-sm btn-secondary" id="copy-qc">Salin</button>
          <button class="btn btn-sm btn-ok" id="save-qc">Simpan</button>
        </div>
      </div>
      ${r.daftar_cek
        .map((c, idx) => {
          const p =
            c.status === "TERPENUHI"
              ? "pill-ok"
              : c.status === "SEBAGIAN"
              ? "pill-warn"
              : "pill-danger";
          return `
          <div class="item-card">
            <div class="item-head">
              <div class="item-title">${idx + 1}. ${esc(c.poin_brief)}</div>
              <span class="pill ${p}">${esc(c.status)}</span>
            </div>
            <div class="item-meta"><strong>Bukti:</strong> ${esc(c.bukti_di_skrip)}</div>
            ${c.status !== "TERPENUHI" && c.saran_perbaikan !== "-" ? `<div class="item-meta"><strong>Saran:</strong> ${esc(c.saran_perbaikan)}</div>` : ""}
          </div>`;
        })
        .join("")}
      ${
        r.peringatan_larangan.length
          ? `<div class="error-banner">${r.peringatan_larangan.map((w) => `Peringatan: ${esc(w)}`).join("\n")}</div>`
          : ""
      }
      <div class="item-card">
        <div class="item-title">Rekomendasi Revisi Cepat</div>
        <div class="item-meta">${esc(r.rekomendasi_revisi_cepat)}</div>
      </div>
    </div>`;
  document.getElementById("copy-qc").onclick = () => copyText(data.markdown);
  document.getElementById("save-qc").onclick = () => saveOutput("cs_qc", data.markdown);
}

async function renderCSRateCardTab() {
  const wrap = document.getElementById("cs-tab-content");
  wrap.innerHTML = `<p class="muted-sm">Memuat Rate Card &amp; FAQ...</p>`;
  try {
    const data = await api("/api/agents/cs/rate-card");
    wrap.innerHTML = `
      <div class="card">
        <h3>Edit Rate Card &amp; FAQ Aktif</h3>
        <p class="muted-xs">Disimpan ke <code>data/rate_card.md</code> dan langsung dipakai Caca saat membalas calon klien.</p>
        <div class="field">
          <textarea id="rc-editor" style="min-height:240px">${esc(data.content)}</textarea>
        </div>
        <button class="btn btn-ok" id="btn-save-rc">Simpan Rate Card</button>
      </div>`;
    document.getElementById("btn-save-rc").onclick = async () => {
      await api("/api/agents/cs/rate-card", {
        method: "PUT",
        body: JSON.stringify({ content: document.getElementById("rc-editor").value }),
      });
      showToast("Rate Card & FAQ diperbarui");
    };
  } catch (err) {
    wrap.innerHTML = `<div class="error-banner">${esc(err.message)}</div>`;
  }
}

// ==========================================
// BOOTSTRAP 3D WORLD + SSE
// ==========================================
function connectLiveEvents() {
  const es = new EventSource("/api/events");
  es.onopen = () => {
    els.connStatus.textContent = `Terhubung live • ${state.agents.length || 6} Agent aktif`;
    els.liveDot.style.background = "var(--ok)";
  };
  es.onmessage = (event) => {
    try {
      applySnapshot(JSON.parse(event.data));
    } catch {
      /* ignore keep-alive */
    }
  };
  es.onerror = () => {
    els.connStatus.textContent = "Menyambung ulang ke server...";
    els.liveDot.style.background = "var(--warn)";
  };
}

async function boot() {
  try {
    office3d = new VoxelOffice3D(
      els.canvas,
      els.bubbleLayer,
      (agentId) => {
        openAgentDrawer(agentId);
      },
      (agentId) => {
        dismissAgentToIdle(agentId);
      }
    );
    if (els.cinemaCanvas) {
      cinemaEngine = new ZentiraCinemaEngine(office3d, els.cinemaCanvas);
    }
  } catch (err) {
    els.fallback.textContent = `Gagal memuat 3D WebGL (${err.message}). Anda tetap dapat memakai dock kontrol di bawah.`;
    els.fallback.classList.remove("hidden");
  }

  if (els.btnDrawerIdle) {
    els.btnDrawerIdle.onclick = () => {
      if (state.activeView && state.activeView !== "inbox") {
        dismissAgentToIdle(state.activeView);
      }
    };
  }

  applyBrandLogo(activeLogoIdx, false);
  if (els.btnCycleLogo) {
    els.btnCycleLogo.onclick = () => applyBrandLogo(activeLogoIdx + 1, true);
  }

  document.getElementById("close-drawer").onclick = closeDrawer;
  document.getElementById("btn-inbox").onclick = openInboxDrawer;

  // Camera view presets (synced between desktop topbar and mobile Apple dropdown)
  document.querySelectorAll("[data-cam]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cam = btn.dataset.cam;
      document.querySelectorAll("[data-cam]").forEach((b) => {
        b.classList.toggle("active", b.dataset.cam === cam);
      });
      if (office3d) office3d.setCameraPreset(cam);
      if (els.officeMenuWrap && els.officeMenuWrap.contains(btn)) {
        setOfficeDropdownOpen(false);
      }
    });
  });

  // Apple-style Left Dropdown toggle & outside-click / Escape dismiss
  if (els.btnOfficeMenu) {
    els.btnOfficeMenu.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const isHidden = els.officeMenuDropdown?.classList.contains("hidden");
      setOfficeDropdownOpen(Boolean(isHidden));
    });
  }
  document.addEventListener("click", (ev) => {
    if (
      els.officeMenuWrap &&
      !els.officeMenuWrap.contains(ev.target) &&
      !els.officeMenuDropdown?.classList.contains("hidden")
    ) {
      setOfficeDropdownOpen(false);
    }
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      setOfficeDropdownOpen(false);
      stopCinematicExperience();
    }
  });

  // Cinematic aspect ratio selector (16:9 / 9:16) & tour/record triggers inside Apple dropdown
  document.querySelectorAll("[data-cinema-aspect]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const ratio = btn.dataset.cinemaAspect || "16:9";
      state.cinemaAspect = ratio;
      document.querySelectorAll("[data-cinema-aspect]").forEach((b) => {
        b.classList.toggle("active", b.dataset.cinemaAspect === ratio);
      });
    });
  });
  if (els.btnCinemaTour) {
    els.btnCinemaTour.onclick = () => startCinematicExperience(false);
  }
  if (els.btnCinemaRecord) {
    els.btnCinemaRecord.onclick = () => startCinematicExperience(true);
  }
  if (els.btnCinemaStop) {
    els.btnCinemaStop.onclick = () => stopCinematicExperience();
  }

  // Office operational mode controls (Masuk / Meeting / Libur)
  document.querySelectorAll("[data-office-mode]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const nextMode = btn.dataset.officeMode;
      if (!nextMode) return;
      const prevMode = state.officeMode;
      setOfficeDropdownOpen(false);
      try {
        const updated = await api("/api/office/mode", {
          method: "POST",
          body: JSON.stringify({ mode: nextMode }),
        });
        applySnapshot(updated);
        if (nextMode === "meeting") {
          showToast("Mode Meeting: seluruh tim berkumpul & duduk berdiskusi");
        } else if (nextMode === "holiday") {
          showToast("Mode Libur: Shuttle Van Zentira menjemput tim pulang");
        } else if (prevMode === "holiday") {
          showToast("Mode Masuk: Shuttle Van Zentira mengantar tim ke kantor");
        } else {
          showToast("Mode Kerja: tim kembali ke area kerja & santai");
        }
      } catch (err) {
        showToast(`Gagal ubah mode kantor: ${err.message}`);
      }
    });
  });

  // Smart Roof & Wall Enclosure segmented control inside Apple dropdown
  const roofLabels = {
    auto: "Atap: Auto (mengikuti kamera)",
    closed: "Atap: Tertutup penuh",
    open: "Atap: Terbuka",
  };
  document.querySelectorAll("[data-roof-opt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const chosen = btn.dataset.roofOpt;
      if (!chosen) return;
      state.roofMode = chosen;
      document.querySelectorAll("[data-roof-opt]").forEach((b) => {
        b.classList.toggle("active", b.dataset.roofOpt === chosen);
      });
      if (office3d) office3d.setRoofMode(chosen);
      showToast(roofLabels[chosen] || chosen);
    });
  });

  // Zen mode toggle (hide all chrome for full 3D view/recording)
  els.btnZen.onclick = () => {
    document.body.classList.add("zen-mode");
    els.btnZenExit.classList.remove("hidden");
  };
  els.btnZenExit.onclick = () => {
    document.body.classList.remove("zen-mode");
    els.btnZenExit.classList.add("hidden");
  };

  // Day / Night studio lighting toggle
  els.btnTheme.onclick = () => {
    state.theme = state.theme === "day" ? "night" : "day";
    document.body.dataset.theme = state.theme;
    els.labelTheme.textContent = state.theme === "day" ? "Malam" : "Siang";
    if (office3d) office3d.setTheme(state.theme);
  };

  // Phone Wi-Fi modal
  document.getElementById("btn-phone-url").onclick = () => {
    els.phoneModal.classList.toggle("hidden");
  };
  document.getElementById("close-phone-modal").onclick = () => {
    els.phoneModal.classList.add("hidden");
  };
  document.getElementById("copy-phone-url").onclick = () => {
    copyText(state.urls.phone);
  };

  // Custom team names modal
  document.getElementById("close-names-modal").onclick = closeNamesModal;
  document.getElementById("cancel-names-modal").onclick = closeNamesModal;
  document.getElementById("save-names-btn").onclick = async () => {
    els.namesErr.classList.add("hidden");
    const names = {};
    els.namesFormList.querySelectorAll("[data-rename-agent]").forEach((inp) => {
      names[inp.dataset.renameAgent] = inp.value;
    });
    try {
      const updated = await api("/api/agents/names", {
        method: "PUT",
        body: JSON.stringify({ names }),
      });
      applySnapshot(updated);
      closeNamesModal();
      showToast("Nama tim Zentira berhasil disimpan");
    } catch (err) {
      els.namesErr.textContent = err.message;
      els.namesErr.classList.remove("hidden");
    }
  };

  // Backup & Restore JSON data (kas, tagihan, prospek, nama tim, rate card)
  if (els.btnBackupExport) {
    els.btnBackupExport.onclick = async () => {
      setOfficeDropdownOpen(false);
      try {
        const data = await api("/api/backup/export");
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        const stamp = new Date().toISOString().slice(0, 10);
        a.href = url;
        a.download = `zentira-backup-${stamp}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
        showToast(`Backup data tersimpan (zentira-backup-${stamp}.json)`);
      } catch (err) {
        showToast(`Gagal backup: ${err.message}`);
      }
    };
  }
  if (els.btnBackupImport && els.backupImportFile) {
    els.btnBackupImport.onclick = () => {
      setOfficeDropdownOpen(false);
      els.backupImportFile.value = "";
      els.backupImportFile.click();
    };
    els.backupImportFile.onchange = async () => {
      const f = els.backupImportFile.files?.[0];
      if (!f) return;
      try {
        const parsed = JSON.parse(await f.text());
        const res = await api("/api/backup/import", {
          method: "POST",
          body: JSON.stringify(parsed),
        });
        if (res.state) applySnapshot(res.state);
        showToast("Data backup berhasil dipulihkan!");
      } catch (err) {
        showToast(`Gagal restore backup: ${err.message}`);
      }
    };
  }

  // Cloud Founder Login & Logout flow (active only when OFFICE_PASSWORD is set)
  const loadOfficeSession = async () => {
    try {
      const initial = await api("/api/state");
      applySnapshot(initial);
    } catch (err) {
      els.connStatus.textContent = `Gagal memuat state: ${err.message}`;
    }
    connectLiveEvents();
  };

  if (els.btnOfficeLogout) {
    els.btnOfficeLogout.onclick = async () => {
      setOfficeDropdownOpen(false);
      await api("/api/auth/logout", { method: "POST" }).catch(() => {});
      window.location.reload();
    };
  }

  if (els.loginForm) {
    els.loginForm.onsubmit = async (ev) => {
      ev.preventDefault();
      if (els.loginErr) els.loginErr.classList.add("hidden");
      const btn = document.getElementById("btn-login-submit");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Memverifikasi...";
      }
      try {
        await api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ password: els.loginPassword?.value || "" }),
        });
        if (els.loginOverlay) els.loginOverlay.classList.add("hidden");
        if (els.btnOfficeLogout) els.btnOfficeLogout.classList.remove("hidden");
        await loadOfficeSession();
        showToast("Selamat datang kembali di Zentira HQ!");
      } catch (err) {
        if (els.loginErr) {
          els.loginErr.textContent = err.message;
          els.loginErr.classList.remove("hidden");
        }
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = "Masuk ke Kantor";
        }
      }
    };
  }

  try {
    const auth = await api("/api/auth/status");
    if (auth.protected && els.btnOfficeLogout) {
      els.btnOfficeLogout.classList.remove("hidden");
    }
    if (auth.protected && !auth.authenticated) {
      if (els.loginOverlay) els.loginOverlay.classList.remove("hidden");
      if (els.loginPassword) els.loginPassword.focus();
      return;
    }
  } catch {
    /* lanjutkan mode lokal jika auth status tidak tersedia */
  }

  await loadOfficeSession();
}

boot();
