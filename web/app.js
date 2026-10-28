"use strict";
const paths = {
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 3a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.87M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  briefcase: "M3 7h18v14H3zM8 7V3h8v4M3 12c6 4 12 4 18 0M10 13h4",
  sliders:
    "M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6",
  clock: "M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  shield: "M12 22s9-4 9-11V5l-9-3-9 3v6c0 7 9 11 9 11M8 12l3 3 5-6",
  plus: "M12 5v14M5 12h14",
  x: "M6 6l12 12M18 6 6 18",
  search: "M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  upload: "M12 16V3M7 8l5-5 5 5M3 16v5h18v-5",
  download: "M12 3v13M7 11l5 5 5-5M3 17v4h18v-4",
  arrow: "M4 12h16M14 6l6 6-6 6",
  chevron: "M9 5l7 7-7 7",
  left: "M15 5l-7 7 7 7",
  check: "M4 12l5 5L20 6",
  play: "M8 4l13 8-13 8z",
  info: "M12 11v6M12 7h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  file: "M14 2H4v20h16V8zM14 2v6h6M8 13h8M8 17h5",
  star: "m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z",
  logout: "M9 4H3v16h6M10 12h12M17 7l5 5-5 5",
  edit: "m16 3 5 5-12 12-6 1 1-6zM14 5l5 5",
  chart: "M4 20V10M12 20V4M20 20v-7",
  layers: "m12 2 10 6-10 6L2 8zM2 12l10 6 10-6M2 16l10 6 10-6",
  pause: "M8 4v16M16 4v16",
};
const icon = (name) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.file}"/></svg>`;
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const labels = {
  education: "Pendidikan",
  experience: "Pengalaman",
  skills: "Keahlian",
  certifications: "Sertifikasi",
  languages: "Bahasa",
};
const statuses = {
  new: "Belum ditinjau",
  shortlisted: "Shortlist",
  hold: "Pertimbangkan",
  rejected: "Tidak dilanjutkan",
};
const keys = Object.keys(labels);
const state = {
  jobs: [],
  job: null,
  list: null,
  session: null,
  view: "candidates",
  q: "",
  status: "all",
  page: 1,
  request: 0,
  busy: false,
  dirty: false,
};
const content = $("#content");
let suspendedWorkspace = null;
let toastTimer,
  searchTimer,
  controller,
  modalReturnFocus,
  discardAction,
  pendingFiles = [],
  uploadController,
  modalParentDirty = false;
const date = (value) =>
  new Intl.DateTimeFormat("id-ID", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Jakarta",
  }).format(new Date(value)) + " WIB";
const initials = (name) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((x) => x[0])
    .join("")
    .toUpperCase();
const badge = (status) =>
  `<span class="badge ${status === "shortlisted" ? "green" : status === "hold" ? "amber" : status === "rejected" ? "red" : "neutral"}">${status === "shortlisted" ? icon("check") : ""}${statuses[status] || esc(status)}</span>`;

function notify(message) {
  const el = $("#notification");
  el.textContent = message;
  el.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("visible"), 5000);
}

async function api(url, options = {}) {
  const abort = new AbortController();
  const timer = setTimeout(() => abort.abort(), 90000);
  if (options.signal)
    options.signal.addEventListener("abort", () => abort.abort(), {
      once: true,
    });
  try {
    const response = await fetch(url, {
      ...options,
      signal: abort.signal,
      headers: {
        "X-RecruitAI-Request": "1",
        ...(!(options.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...options.headers,
      },
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      if (response.status === 401 && !url.endsWith("/login")) {
        state.session.authenticated = false;
        if (!suspendedWorkspace && (state.dirty || $("#modal").open)) {
          const draft = document.createDocumentFragment();
          while (content.firstChild) draft.append(content.firstChild);
          suspendedWorkspace = { draft, dialogOpen: $("#modal").open };
          $("#modal").close();
        }
        showLogin();
      }
      const detail = Array.isArray(payload.detail)
        ? "Periksa isian Anda. Nama posisi, keahlian, dan bobot wajib valid."
        : payload.detail;
      throw new Error(detail || "Permintaan gagal. Silakan coba kembali.");
    }
    return await response.json();
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "Permintaan dibatalkan atau terlalu lama. Muat ulang untuk memeriksa hasil.",
      );
    if (error instanceof TypeError)
      throw new Error("Koneksi terputus. Periksa jaringan lalu coba kembali.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function syncRoute() {
  const url = new URL(location.href);
  url.searchParams.set("view", state.view);
  if (state.job) url.searchParams.set("job", state.job.id);
  else url.searchParams.delete("job");
  for (const [k, v] of Object.entries({
    status: state.status,
    page: state.page,
  })) {
    if (v === "all" || v === 1) url.searchParams.delete(k);
    else url.searchParams.set(k, v);
  }
  // Candidate names/search are intentionally excluded from browser history.
  history.replaceState(null, "", url.pathname + url.search);
}

function currentJob() {
  return (
    state.jobs.find((j) => j.id === state.job?.id) || state.jobs[0] || null
  );
}
async function loadJobs() {
  state.jobs = await api("/api/jobs");
  state.job = currentJob();
}

function heading(eyebrow, title, description, actions = "") {
  return `<div class="page-heading"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${description}</p></div><div class="actions">${actions}</div></div>`;
}

function jobStrip() {
  return `<section class="job-strip" aria-label="Lowongan aktif"><span class="job-symbol">${icon("briefcase")}</span><div><h3>${esc(state.job.title)}</h3><p>${esc(state.job.department)}<span class="footer-dot">·</span>${esc(state.job.location)}</p></div><span class="badge green"><i></i>Aktif</span><label class="sr-only" for="job-select">Pilih lowongan</label><select class="job-select" id="job-select">${state.jobs.map((j) => `<option value="${j.id}" ${j.id === state.job.id ? "selected" : ""}>${esc(j.title)}</option>`).join("")}</select></section>`;
}
function bindJobSelect() {
  $("#job-select")?.addEventListener("change", (e) => {
    const job = state.jobs.find((j) => j.id === e.target.value);
    e.target.value = state.job.id;
    guardPageChange(() => {
      state.job = job;
      state.page = 1;
      state.q = "";
      render();
    });
  });
}

function rail() {
  return `<aside class="rail" aria-label="Konteks analisis"><section class="rail-panel"><div class="rail-title"><h3>Prioritas penilaian</h3>${icon("sliders")}</div><p>Disesuaikan dengan kebutuhan posisi ini.</p><div class="weight-list">${keys.map((k) => `<div class="weight-row"><div class="weight-label"><span>${labels[k]}</span><strong>${Math.round(state.job.weights[k])}%</strong></div><div class="weight-track"><progress value="${state.job.weights[k]}" max="100" aria-label="Bobot ${labels[k]}"></progress></div></div>`).join("")}</div><button class="button full" id="edit-weights">Sesuaikan kriteria ${icon("arrow")}</button></section><section class="rail-panel method-panel"><div class="method-label">DI BALIK PENILAIAN</div><h3>Satu peringkat.<br>Tiga sudut pandang.</h3><p>Setiap kandidat dibandingkan lewat tiga metode, lalu digabung menjadi peringkat yang dapat ditelusuri.</p><div class="method-tags"><span>SAW</span><span>Weighted Product</span><span>TOPSIS</span></div><div class="method-foot">${icon("shield")}<span>Skor menunjukkan kesesuaian bukti, bukan jaminan kinerja kandidat.</span></div></section></aside>`;
}

async function render() {
  const id = ++state.request;
  controller?.abort();
  controller = new AbortController();
  state.view = ["candidates", "jobs", "criteria", "activity"].includes(
    state.view,
  )
    ? state.view
    : "candidates";
  const viewLabels = {
    candidates: "Kandidat",
    jobs: "Lowongan",
    criteria: "Kriteria seleksi",
    activity: "Aktivitas",
  };
  document.title = `${viewLabels[state.view]} · RecruitAI`;
  $("#breadcrumb").textContent = viewLabels[state.view];
  $$("nav a").forEach((a) => {
    a.classList.toggle("active", a.dataset.view === state.view);
    if (a.dataset.view === state.view) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  syncRoute();
  content.setAttribute("aria-busy", "true");
  try {
    if (state.view === "jobs") renderJobs();
    else if (state.view === "activity") {
      const items = await api("/api/audit", { signal: controller.signal });
      if (id !== state.request) return;
      renderActivity(items);
    } else if (!state.job) renderWelcome();
    else if (state.view === "criteria") renderCriteria();
    else {
      const data = await api(
        `/api/jobs/${state.job.id}/candidates?${new URLSearchParams({ q: state.q, status: state.status, page: state.page })}`,
        { signal: controller.signal },
      );
      if (id !== state.request) return;
      state.list = data;
      state.page = data.page;
      syncRoute();
      renderCandidates();
    }
  } catch (error) {
    if (id !== state.request) return;
    if (!state.session.authenticated) return;
    content.innerHTML =
      heading(
        "RUANG KERJA",
        "Koneksi perlu diperiksa",
        "Data Anda tetap tersimpan.",
      ) +
      `<section class="panel empty">${icon("info")}<h2>Ruang kerja belum dapat dimuat</h2><p>${esc(error.message)}</p><button class="button primary" id="retry">Coba kembali</button></section>`;
    $("#retry").onclick = () => render();
  } finally {
    if (id === state.request) {
      content.setAttribute("aria-busy", "false");
      if (document.activeElement === document.body)
        $("#main").focus({ preventScroll: true });
    }
  }
}

function renderWelcome() {
  content.innerHTML =
    heading(
      "RUANG SELEKSI",
      "Temukan kecocokan. Pahami alasannya.",
      "Ruang yang tenang untuk keputusan rekrutmen yang lebih terarah.",
    ) +
    `<section class="panel empty">${icon("briefcase")}<h2>Mulai dari posisi yang Anda cari.</h2><p>Tentukan kebutuhan posisi, tambahkan CV, lalu tinjau kandidat berdasarkan bukti yang relevan.</p><div class="actions"><button class="button primary" id="new-job">${icon("plus")}Buat lowongan pertama</button><button class="button" id="demo">Jelajahi data contoh ${icon("arrow")}</button></div><small class="activity-note">Data contoh berisi profil fiktif dan hanya dimuat atas pilihan Anda.</small></section>`;
  $("#new-job").onclick = () => jobForm();
  $("#demo").onclick = async (e) => {
    await action(e.currentTarget, async () => {
      await api("/api/demo", { method: "POST" });
      await loadJobs();
      await render();
      notify("Data contoh fiktif dimuat.");
    });
  };
}

function renderCandidates() {
  const d = state.list;
  $("#nav-count").textContent = d.count;
  const demo = d.items.some((c) => c.source === "demo");
  const actions = `<button class="button" id="export" ${!d.run ? "disabled" : ""}>${icon("download")}Ekspor hasil</button><button class="button primary" id="upload">${icon("plus")}Tambah kandidat</button>`;
  const metrics = [
    ["users", "Total kandidat", d.count, "profil", "Di lowongan ini"],
    [
      "star",
      "Masuk shortlist",
      d.counts.shortlisted,
      "kandidat",
      "Dipilih oleh tim Anda",
    ],
    [
      "clock",
      "Menunggu tinjauan",
      d.counts.new,
      "kandidat",
      "Siap untuk Anda pelajari",
    ],
    [
      "chart",
      "Analisis terakhir",
      d.run ? "Selesai" : "—",
      "",
      d.run ? date(d.run.created_at) : "Belum ada analisis",
    ],
  ];
  content.innerHTML =
    heading(
      "RUANG SELEKSI",
      "Kandidat yang tepat, lebih dekat.",
      "Baca potensinya. Bandingkan buktinya. Tentukan langkah berikutnya.",
      actions,
    ) +
    (demo
      ? `<div class="notice demo-banner"><span>Anda sedang melihat profil contoh fiktif.</span><span>Mode eksplorasi</span></div>`
      : "") +
    jobStrip() +
    `<section class="metrics" aria-label="Ringkasan seleksi">${metrics.map(([i, l, v, u, n]) => `<div class="metric"><div class="metric-label">${icon(i)}${l}</div><div class="metric-value">${v}<span class="unit">${u}</span></div><div class="metric-note">${n}</div></div>`).join("")}</section>` +
    (d.stale
      ? `<div class="notice"><span>Kandidat atau kriteria telah berubah. Peringkat yang tampil berasal dari analisis sebelumnya.</span><button class="text-button" id="rerun">Analisis ulang ${icon("arrow")}</button></div>`
      : "") +
    `<div class="work-grid"><section class="table-panel"><div class="table-heading"><div><h3>Daftar kandidat <span class="subtle-count">${d.count} profil</span></h3><p>${d.run ? "Diurutkan berdasarkan hasil analisis gabungan." : "Tambahkan kandidat dan mulai perbandingan."}</p></div><button class="text-button" id="analyze" ${d.count < 2 ? "disabled" : ""}>${icon("play")}Jalankan analisis</button></div><div class="filter-tabs" aria-label="Filter status kandidat">${[
      ["all", "Semua kandidat", d.count],
      ["shortlisted", "Shortlist", d.counts.shortlisted],
      ["new", "Belum ditinjau", d.counts.new],
      ["hold", "Pertimbangkan", d.counts.hold],
      ["rejected", "Tidak dilanjutkan", d.counts.rejected],
    ]
      .map(
        ([s, l, c]) =>
          `<button data-status="${s}" aria-pressed="${state.status === s}">${l}<span class="count">${c}</span></button>`,
      )
      .join(
        "",
      )}</div><div class="table-toolbar"><div class="search">${icon("search")}<label class="sr-only" for="search">Cari nama atau keahlian</label><input type="search" id="search" placeholder="Cari nama atau keahlian…" value="${esc(state.q)}" maxlength="120" autocomplete="off"><button class="icon-button" id="clear-search" aria-label="Hapus pencarian" ${state.q ? "" : "hidden"}>${icon("x")}</button></div><span>${icon("layers")} Peringkat gabungan</span></div><div class="table-scroll">${d.items.length ? candidateTable(d.items) : `<div class="empty">${icon("users")}<h3>${d.count ? "Tidak ada kandidat yang cocok" : "Belum ada kandidat"}</h3><p>${d.count ? "Coba kata kunci lain atau reset filter." : "Unggah CV berbasis teks atau tambahkan profil secara manual."}</p><button class="button" id="empty-action">${d.count ? "Reset filter" : "Tambah kandidat"}</button></div>`}</div><div class="table-foot"><span>${d.total ? `${(d.page - 1) * 10 + 1}–${Math.min(d.page * 10, d.total)} dari ${d.total} kandidat` : "0 kandidat"}</span><div class="pagination"><button class="icon-button" id="prev-page" aria-label="Halaman sebelumnya" ${d.page === 1 ? "disabled" : ""}>${icon("left")}</button><span class="page-number">${d.page} / ${Math.max(1, Math.ceil(d.total / 10))}</span><button class="icon-button" id="next-page" aria-label="Halaman berikutnya" ${d.page * 10 >= d.total ? "disabled" : ""}>${icon("chevron")}</button></div></div></section>${rail()}</div><div class="info-strip">${icon("info")}Identitas, usia, gender, dan foto tidak digunakan untuk menghitung skor.</div>`;
  bindJobSelect();
  $("#upload").onclick = () => uploadDialog();
  $("#edit-weights").onclick = () => navigate("criteria");
  $("#analyze").onclick = (e) => run(e.currentTarget);
  if ($("#rerun")) $("#rerun").onclick = (e) => run(e.currentTarget);
  $("#export").onclick = () => {
    location.href = `/api/jobs/${state.job.id}/export`;
  };
  $$(".filter-tabs button").forEach(
    (b) =>
      (b.onclick = () => {
        state.status = b.dataset.status;
        state.page = 1;
        render();
      }),
  );
  $$(".candidate-name, [data-open]").forEach(
    (b) =>
      (b.onclick = () =>
        profileDialog(
          d.items.find((c) => c.id === (b.dataset.id || b.dataset.open)),
        )),
  );
  $("#prev-page").onclick = () => {
    state.page--;
    render();
  };
  $("#next-page").onclick = () => {
    state.page++;
    render();
  };
  if ($("#empty-action"))
    $("#empty-action").onclick = () => {
      if (d.count) {
        state.q = "";
        state.status = "all";
        state.page = 1;
        render();
      } else uploadDialog();
    };
  const search = $("#search");
  let composing = false;
  const commit = () => {
    clearTimeout(searchTimer);
    state.q = search.value;
    state.page = 1;
    render().then(() => {
      const fresh = $("#search");
      fresh?.focus();
      fresh?.setSelectionRange?.(state.q.length, state.q.length);
    });
  };
  search.addEventListener("compositionstart", () => {
    composing = true;
    clearTimeout(searchTimer);
  });
  search.addEventListener("compositionend", () => {
    composing = false;
    commit();
  });
  search.addEventListener("input", () => {
    $("#clear-search").hidden = !search.value;
    clearTimeout(searchTimer);
    if (!composing) searchTimer = setTimeout(commit, 300);
  });
  search.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.isComposing) {
      e.preventDefault();
      commit();
    }
  });
  $("#clear-search").onclick = () => {
    clearTimeout(searchTimer);
    search.value = "";
    commit();
  };
}

function candidateTable(items) {
  return `<table><caption class="sr-only">Kandidat untuk ${esc(state.job.title)}. Skor bukan probabilitas keberhasilan.</caption><thead><tr><th scope="col">Rank</th><th scope="col">Kandidat</th><th scope="col">Kesesuaian</th><th scope="col">Status tinjauan</th><th scope="col"><span class="sr-only">Tindakan</span></th></tr></thead><tbody>${items
    .map((c, i) => {
      const r = c.result;
      return `<tr><td><span class="rank ${r?.rank <= 3 ? "top" : ""}">${r ? String(r.rank).padStart(2, "0") : "—"}</span></td><td><div class="candidate-cell"><span class="avatar a${i % 4}">${esc(initials(c.profile.name))}</span><div><button class="candidate-name" data-id="${c.id}">${esc(c.profile.name)}</button><small>${esc(c.profile.headline || "Profil kandidat")}</small></div></div></td><td>${r ? `<div class="score-cell"><strong>${r.score.toFixed(0)}<span class="sr-only"> persen</span></strong><span class="score-track" aria-hidden="true">${Array.from({ length: 16 }, (_, n) => `<i class="${n < Math.round((r.score / 100) * 16) ? "filled" : ""} ${r.score >= 80 ? "high" : ""}"></i>`).join("")}</span></div>` : '<span class="subtle-count">Belum dianalisis</span>'}</td><td>${badge(c.status)}</td><td><button class="icon-button" data-open="${c.id}" aria-label="Tinjau ${esc(c.profile.name)}">${icon("chevron")}</button></td></tr>`;
    })
    .join("")}</tbody></table>`;
}

async function action(button, fn) {
  if (state.busy) return;
  state.busy = true;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  try {
    await fn();
  } catch (error) {
    notify(error.message);
  } finally {
    state.busy = false;
    if (button.isConnected) {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  }
}
async function run(button) {
  await action(button, async () => {
    button.textContent = "Menganalisis…";
    await api(`/api/jobs/${state.job.id}/analyze`, { method: "POST" });
    await render();
    notify("Analisis selesai. Tinjau bukti sebelum menentukan keputusan.");
  });
  if (button.isConnected) button.innerHTML = icon("play") + "Jalankan analisis";
}

function renderJobs() {
  if (!state.jobs.length) {
    renderWelcome();
    return;
  }
  content.innerHTML =
    heading(
      "KEBUTUHAN TIM",
      "Setiap posisi punya ukurannya.",
      "Kelola kebutuhan dan konteks penilaian untuk setiap lowongan.",
      `<button class="button primary" id="new-job">${icon("plus")}Buat lowongan</button>`,
    ) +
    `<div class="job-list">${state.jobs.map((j) => `<article class="panel job-card"><div class="job-symbol">${icon("briefcase")}</div><span class="eyebrow">${esc(j.department)}</span><h2>${esc(j.title)}</h2><p>${esc(j.location)}</p><div class="job-meta"><span class="badge green"><i></i>Aktif</span><span class="badge neutral">${j.candidate_count} kandidat</span></div><p>${esc(j.required_skills.join(" · "))}</p><div class="actions"><button class="text-button" data-edit="${j.id}">${icon("edit")}Edit lowongan</button><button class="button" data-job="${j.id}">Lihat kandidat ${icon("arrow")}</button></div></article>`).join("")}</div>`;
  $("#new-job").onclick = () => jobForm();
  $$("[data-edit]").forEach(
    (b) =>
      (b.onclick = () =>
        jobForm(state.jobs.find((j) => j.id === b.dataset.edit))),
  );
  $$("[data-job]").forEach(
    (b) =>
      (b.onclick = () => {
        state.job = state.jobs.find((j) => j.id === b.dataset.job);
        state.page = 1;
        state.status = "all";
        state.q = "";
        navigate("candidates");
      }),
  );
}

function field(
  id,
  label,
  value = "",
  type = "text",
  help = "",
  attributes = "",
) {
  return `<div class="field"><label for="${id}">${label}</label><input id="${id}" name="${id}" type="${type}" value="${esc(value)}" ${attributes} ${help ? `aria-describedby="${id}-help"` : ""}>${help ? `<small id="${id}-help">${help}</small>` : ""}</div>`;
}
function area(id, label, value = "", help = "") {
  return `<div class="field"><label for="${id}">${label}</label><textarea id="${id}" name="${id}" rows="4" maxlength="8000" ${help ? `aria-describedby="${id}-help"` : ""}>${esc(value)}</textarea>${help ? `<small id="${id}-help">${help}</small>` : ""}</div>`;
}
function selectField(id, label, values, current) {
  return `<div class="field"><label for="${id}">${label}</label><select id="${id}" name="${id}">${values.map(([v, l]) => `<option value="${v}" ${v === current ? "selected" : ""}>${l}</option>`).join("")}</select></div>`;
}
const split = (value) =>
  value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
function formError(form, message, id) {
  const error = $(".form-error", form);
  error.textContent = message;
  if (id) {
    const input = $("#" + id, form);
    input.setAttribute("aria-invalid", "true");
    input.setAttribute("aria-describedby", error.id);
    input.focus();
  } else error.focus();
}
function watchDirty(form) {
  form.addEventListener("input", () => {
    state.dirty = true;
  });
  form.addEventListener("change", () => {
    state.dirty = true;
  });
}
function showModal(title, html, eyebrow = "RUANG SELEKSI") {
  modalReturnFocus = document.activeElement;
  $("#modal-title").textContent = title;
  $("#modal-eyebrow").textContent = eyebrow;
  $("#modal-body").innerHTML = html;
  state.dirty = false;
  $("#modal").showModal();
}
function finishModal() {
  state.dirty = modalParentDirty;
  modalParentDirty = false;
  $("#modal").close();
  modalReturnFocus?.focus();
}
function confirmDiscard(next) {
  if (!state.dirty) {
    next();
    return;
  }
  discardAction = next;
  const body = $("#modal-body");
  if ($("#discard-panel")) return;
  const box = document.createElement("section");
  box.id = "discard-panel";
  box.className = "notice";
  box.innerHTML =
    '<span>Perubahan belum disimpan. Tutup tanpa menyimpan?</span><button class="button" id="keep-editing">Lanjut edit</button><button class="button" id="discard">Abaikan</button>';
  body.prepend(box);
  $("#keep-editing").onclick = () => {
    box.remove();
    $("input,textarea,button", body)?.focus();
  };
  $("#discard").onclick = () => {
    state.dirty = false;
    discardAction();
  };
  $("#keep-editing").focus();
}

function jobForm(job = null) {
  showModal(
    job ? "Edit lowongan" : "Posisi apa yang Anda cari?",
    `<form id="job-form" novalidate>${field("title", "Nama posisi", job?.title || "", "text", "", 'required maxlength="120"')}<div class="form-grid">${field("department", "Tim / departemen", job?.department || "Product & Engineering", "text", "", 'maxlength="80"')}${field("location", "Lokasi dan cara kerja", job?.location || "Jakarta · Hybrid", "text", "", 'maxlength="120"')}</div>${field("skills", "Keahlian yang dibutuhkan", job?.required_skills.join(", ") || "", "text", "Pisahkan dengan koma. Contoh: React, TypeScript, Testing", 'required maxlength="2000"')}<div class="form-grid">${field("experience", "Pengalaman minimum (bulan)", job?.required_experience_months ?? 36, "number", "", 'min="0" max="480"')}${selectField(
      "education",
      "Pendidikan minimum",
      [
        ["", "Tanpa persyaratan"],
        ["SMA", "SMA / SMK"],
        ["D3", "Diploma"],
        ["S1", "Sarjana (S1)"],
        ["S2", "Magister (S2)"],
        ["S3", "Doktor (S3)"],
      ],
      job?.required_education_level ?? "S1",
    )}</div>${field("languages", "Bahasa yang dibutuhkan", job?.required_languages.join(", ") || "Indonesia", "text", "Kosongkan jika tidak menjadi persyaratan.", 'maxlength="500"')}${field("certifications", "Sertifikasi yang dibutuhkan", job?.required_certifications.join(", ") || "", "text", "Opsional. Pisahkan dengan koma.", 'maxlength="1000"')}${area("description", "Konteks pekerjaan", job?.description || "")}<div class="form-error" id="job-error" role="alert" tabindex="-1"></div><div class="form-footer"><button type="button" class="button" id="cancel-job">Batal</button><button class="button primary" type="submit">${job ? "Simpan perubahan" : "Buat lowongan"} ${icon("arrow")}</button></div></form>`,
    "KEBUTUHAN TIM",
  );
  const form = $("#job-form");
  watchDirty(form);
  $("#cancel-job").onclick = () => confirmDiscard(finishModal);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(form);
    const title = f.get("title").trim();
    const skills = split(f.get("skills"));
    const months = Number(f.get("experience"));
    if (title.length < 3)
      return formError(form, "Nama posisi minimal 3 karakter.", "title");
    if (!skills.length)
      return formError(form, "Isi setidaknya satu keahlian.", "skills");
    if (!Number.isInteger(months) || months < 0 || months > 480)
      return formError(form, "Isi durasi 0–480 bulan.", "experience");
    const body = {
      title,
      department: f.get("department"),
      location: f.get("location"),
      description: f.get("description"),
      required_skills: skills,
      required_experience_months: months,
      required_education_level: f.get("education"),
      required_languages: split(f.get("languages")),
      required_certifications: split(f.get("certifications")),
      ...(job ? { version: job.version, weights: job.weights } : {}),
    };
    const button = $("[type=submit]", form);
    button.disabled = true;
    try {
      const saved = await api(job ? `/api/jobs/${job.id}` : "/api/jobs", {
        method: job ? "PUT" : "POST",
        body: JSON.stringify(body),
      });
      finishModal();
      state.job = saved;
      await loadJobs();
      await render();
      notify(
        job
          ? "Lowongan diperbarui. Jalankan ulang analisis untuk menerapkan perubahan."
          : "Lowongan dibuat. Tambahkan kandidat pertama Anda.",
      );
    } catch (error) {
      formError(form, error.message);
    } finally {
      button.disabled = false;
    }
  };
}

function renderCriteria() {
  content.innerHTML =
    heading(
      "KRITERIA SELEKSI",
      "Prioritas yang mencerminkan kebutuhan.",
      "Atur kontribusi setiap kriteria. Semua perubahan dapat ditelusuri.",
    ) +
    jobStrip() +
    `<div class="criteria-layout"><form class="panel form-panel" id="criteria-form" novalidate><div>${keys.map((k) => `<div class="weight-editor"><label for="weight-${k}">${labels[k]}<output id="out-${k}" for="weight-${k}">${Math.round(state.job.weights[k])}%</output></label><input id="weight-${k}" name="${k}" type="range" min="0" max="100" step="1" value="${Math.round(state.job.weights[k])}" aria-describedby="hint-${k}"><small id="hint-${k}">${{ education: "Jenjang pendidikan sesuai persyaratan posisi.", experience: "Durasi pengalaman terhadap kebutuhan minimum.", skills: "Cakupan keahlian yang disebutkan dalam profil.", certifications: "Sertifikasi yang secara eksplisit dipersyaratkan.", languages: "Bahasa yang dibutuhkan dalam pekerjaan." }[k]}</small></div>`).join("")}</div><div class="criteria-total"><span>Total bobot</span><strong id="weight-total">100%</strong></div><div class="form-error" id="criteria-error" role="alert" tabindex="-1"></div><div class="form-footer"><button type="button" class="button" id="reset-weights">Pulihkan bobot tersimpan</button><button class="button primary" type="submit">Simpan kriteria ${icon("check")}</button></div></form><aside class="panel form-panel criteria-copy"><div><h3>Ukuran yang jelas.</h3><p>Bobot menentukan kontribusi terhadap kesesuaian persyaratan dan perbandingan antar kandidat. Total harus 100% sebelum disimpan.</p><h3>Nilai bukti yang tersedia.</h3><p>Keahlian dicocokkan secara eksplisit, dengan alias istilah umum. Kemiripan istilah saja tidak dianggap sebagai kompetensi yang terbukti.</p></div><div><h3>Data kosong perlu ditinjau.</h3><p>Informasi yang belum ditemukan diberi penanda verifikasi. Skor awalnya konservatif; periksa profil sebelum mengambil keputusan.</p><h3>Hasil tidak berubah diam-diam.</h3><p>Setelah menyimpan, jalankan analisis ulang. Analisis sebelumnya tetap tersimpan beserta kriteria yang digunakan.</p></div></aside></div>`;
  bindJobSelect();
  const form = $("#criteria-form");
  watchDirty(form);
  const update = () => {
    let sum = 0;
    keys.forEach((k) => {
      const v = Number($(`#weight-${k}`).value);
      sum += v;
      $(`#out-${k}`).textContent = v + "%";
    });
    $("#weight-total").textContent = sum + "%";
  };
  keys.forEach((k) => ($(`#weight-${k}`).oninput = update));
  update();
  $("#reset-weights").onclick = () => {
    state.dirty = false;
    renderCriteria();
  };
  form.onsubmit = async (e) => {
    e.preventDefault();
    const weights = Object.fromEntries(
      keys.map((k) => [k, Number($(`#weight-${k}`).value)]),
    );
    if (Object.values(weights).reduce((a, b) => a + b, 0) !== 100)
      return formError(
        form,
        "Total bobot harus tepat 100%. Sesuaikan slider sebelum menyimpan.",
      );
    const b = $("[type=submit]", form);
    b.disabled = true;
    try {
      const body = { ...state.job, weights };
      state.job = await api(`/api/jobs/${state.job.id}`, {
        method: "PUT",
        body: JSON.stringify(body),
      });
      state.dirty = false;
      await loadJobs();
      await render();
      notify(
        "Kriteria disimpan. Jalankan ulang analisis untuk memperbarui peringkat.",
      );
    } catch (error) {
      formError(form, error.message);
    } finally {
      b.disabled = false;
    }
  };
}

function renderActivity(items) {
  content.innerHTML =
    heading(
      "JEJAK KEPUTUSAN",
      "Setiap langkah punya catatan.",
      "Riwayat perubahan dan analisis di ruang kerja ini.",
    ) +
    `<div class="panel">${items.length ? items.map((a) => `<div class="activity-row">${icon(a.action.includes("Analisis") ? "chart" : a.action.includes("Kandidat") ? "users" : "clock")}<div><strong>${esc(a.action)}</strong><small>Referensi ${esc(a.subject)}</small></div><time datetime="${esc(a.created_at)}">${date(a.created_at)}</time></div>`).join("") : `<div class="empty">${icon("clock")}<h3>Belum ada aktivitas</h3><p>Perubahan lowongan, profil, tinjauan, dan analisis akan tercatat di sini.</p></div>`}</div><p class="activity-note">Menampilkan maksimal 100 aktivitas terbaru. Waktu ditampilkan dalam WIB. Aktor: tim rekrutmen pada ruang kerja bersama ini.</p>`;
}

function profileDialog(candidate) {
  const c = candidate,
    p = c.profile,
    r = c.result;
  showModal(
    "Tinjau kandidat",
    `<div class="profile-heading"><span class="avatar">${esc(initials(p.name))}</span><div><h3>${esc(p.name)}</h3><p>${esc(p.headline || "Profil kandidat")}</p>${badge(c.status)}</div><div class="profile-score"><strong>${r ? r.score.toFixed(0) + "%" : "—"}</strong><small>Kesesuaian persyaratan</small></div></div>${state.list.stale ? '<div class="notice">Hasil analisis belum mengikuti perubahan terbaru.</div>' : ""}<div class="profile-meta"><div><small>Pengalaman</small>${p.experience_months === null ? "Perlu verifikasi" : p.experience_months + " bulan"}</div><div><small>Pendidikan</small>${esc(p.education || "Perlu verifikasi")}</div><div><small>Sumber profil</small>${{ demo: "Contoh fiktif", manual: "Input manual", local: "PDF · lokal", groq: "PDF · Groq AI" }[c.source] || "PDF"}</div></div><div class="profile-section"><h3>Ringkasan profil</h3><p>${esc(p.summary || "Belum ada ringkasan. Periksa profil dan lengkapi bukti kandidat.")}</p></div><button class="text-button" id="edit-profile">${icon("edit")}Verifikasi / edit profil</button><div class="profile-section"><h3>Keahlian di profil</h3><div class="skill-tags">${p.skills.map((s) => `<span>${esc(s)}</span>`).join("") || "<small>Belum ada keahlian tercatat.</small>"}</div></div>${r ? `<div class="profile-section"><h3>Bukti terhadap kebutuhan posisi</h3><p>${r.evidence.matched.length} dari ${state.job.required_skills.length} keahlian sesuai: ${esc(r.evidence.matched.join(", ") || "belum ada")}.</p>${r.evidence.missing.length ? `<p>Belum ditemukan: ${esc(r.evidence.missing.join(", "))}.</p>` : ""}${r.evidence.missing_certifications.length ? `<p>Sertifikasi belum ditemukan: ${esc(r.evidence.missing_certifications.join(", "))}.</p>` : ""}${r.evidence.missing_languages.length ? `<p>Bahasa belum ditemukan: ${esc(r.evidence.missing_languages.join(", "))}.</p>` : ""}${r.evidence.unknown.length ? `<div class="notice">${esc(r.evidence.unknown.join(" · "))}</div>` : ""}</div><div class="profile-section"><h3>Rincian penilaian</h3>${keys.map((k) => `<div class="dimension"><span>${labels[k]}</span><progress value="${r.dimensions[k] * 100}" max="100" aria-label="${labels[k]} ${Math.round(r.dimensions[k] * 100)} persen"></progress><span>${Math.round(r.dimensions[k] * 100)}%</span></div>`).join("")}<p class="activity-note">Peringkat gabungan #${r.rank}. SAW #${r.algorithms.saw_rank}, WP #${r.algorithms.wp_rank}, TOPSIS #${r.algorithms.topsis_rank}. Skor bukan probabilitas diterima.</p></div>` : '<div class="notice">Jalankan analisis untuk melihat rincian penilaian kandidat.</div>'}<form id="review-form" novalidate><div class="profile-section"><h3>Langkah berikutnya</h3><div class="review-controls">${Object.entries(
      statuses,
    )
      .map(
        ([s, l]) =>
          `<button type="button" class="button" data-review="${s}" aria-pressed="${s === c.status}">${l}</button>`,
      )
      .join(
        "",
      )}</div></div>${area("review-note", "Catatan tinjauan", c.note, "Wajib diisi jika kandidat tidak dilanjutkan. Jangan masukkan data sensitif yang tidak relevan.")}<div class="form-error" id="review-error" role="alert" tabindex="-1"></div><div class="form-footer"><button type="button" class="button" id="close-profile">Tutup</button><button type="submit" class="button primary">Simpan tinjauan ${icon("check")}</button></div></form>`,
    "PROFIL & BUKTI",
  );
  let status = c.status;
  const form = $("#review-form");
  watchDirty(form);
  $$("[data-review]").forEach(
    (b) =>
      (b.onclick = () => {
        status = b.dataset.review;
        state.dirty = true;
        $$("[data-review]").forEach((x) =>
          x.setAttribute("aria-pressed", x === b),
        );
      }),
  );
  $("#close-profile").onclick = () => confirmDiscard(finishModal);
  $("#edit-profile").onclick = () =>
    confirmDiscard(() => {
      finishModal();
      manualForm(c);
    });
  form.onsubmit = async (e) => {
    e.preventDefault();
    const note = $("#review-note").value;
    if (status === "rejected" && !note.trim())
      return formError(
        form,
        "Tuliskan alasan sebelum menyimpan keputusan.",
        "review-note",
      );
    const b = $("[type=submit]", form);
    b.disabled = true;
    try {
      await api(`/api/candidates/${c.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status, note, version: c.version }),
      });
      finishModal();
      await render();
      notify("Tinjauan kandidat disimpan.");
    } catch (error) {
      formError(form, error.message);
    } finally {
      b.disabled = false;
    }
  };
}

function manualForm(candidate = null) {
  const p = candidate?.profile;
  showModal(
    candidate ? "Verifikasi profil kandidat" : "Tambahkan profil kandidat",
    `<form id="profile-form" novalidate>${field("name", "Nama kandidat", p?.name || "", "text", "", 'required maxlength="120"')}${field("headline", "Posisi / ringkasan singkat", p?.headline || "", "text", "", 'maxlength="160"')}${field("profile-skills", "Keahlian", p?.skills.join(", ") || "", "text", "Pisahkan dengan koma. Isi hanya keahlian yang didukung CV.", 'maxlength="4000"')}<div class="form-grid">${field("months", "Total pengalaman (bulan)", p?.experience_months ?? "", "number", "Kosongkan jika belum dapat diverifikasi.", 'min="0" max="600"')}${selectField(
      "profile-education",
      "Pendidikan",
      [
        ["", "Belum diverifikasi"],
        ["SMA", "SMA / SMK"],
        ["D3", "Diploma"],
        ["S1", "Sarjana (S1)"],
        ["S2", "Magister (S2)"],
        ["S3", "Doktor (S3)"],
      ],
      p?.education || "",
    )}</div>${field("profile-languages", "Bahasa", p?.languages.join(", ") || "", "text", "Contoh: Indonesia, Inggris", 'maxlength="500"')}${field("profile-certs", "Sertifikasi", p?.certifications.join(", ") || "", "text", "", 'maxlength="2000"')}${area("summary", "Ringkasan bukti", p?.summary || "")}<div class="form-error" id="profile-error" role="alert" tabindex="-1"></div><div class="form-footer"><button class="button" type="button" id="cancel-profile">Batal</button><button class="button primary" type="submit">${candidate ? "Simpan profil" : "Tambah kandidat"} ${icon("check")}</button></div></form>`,
    "BUKTI KANDIDAT",
  );
  const form = $("#profile-form");
  watchDirty(form);
  $("#cancel-profile").onclick = () => confirmDiscard(finishModal);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(form);
    const name = f.get("name").trim();
    const months = f.get("months") === "" ? null : Number(f.get("months"));
    if (!name) return formError(form, "Nama kandidat wajib diisi.", "name");
    if (
      months !== null &&
      (!Number.isInteger(months) || months < 0 || months > 600)
    )
      return formError(
        form,
        "Isi durasi 0–600 bulan atau kosongkan.",
        "months",
      );
    const body = {
      name,
      headline: f.get("headline"),
      skills: split(f.get("profile-skills")),
      experience_months: months,
      education: f.get("profile-education"),
      languages: split(f.get("profile-languages")),
      certifications: split(f.get("profile-certs")),
      summary: f.get("summary"),
    };
    const b = $("[type=submit]", form);
    b.disabled = true;
    try {
      await api(
        candidate
          ? `/api/candidates/${candidate.id}/profile?version=${candidate.version}`
          : `/api/jobs/${state.job.id}/candidates`,
        { method: candidate ? "PUT" : "POST", body: JSON.stringify(body) },
      );
      finishModal();
      await loadJobs();
      await render();
      notify(
        candidate
          ? "Profil disimpan. Jalankan ulang analisis."
          : "Kandidat ditambahkan.",
      );
    } catch (error) {
      formError(form, error.message);
    } finally {
      b.disabled = false;
    }
  };
}

function uploadDialog() {
  pendingFiles = [];
  showModal(
    "Kenali kandidat berikutnya.",
    `<p class="page-subtitle">Tambahkan CV ke ${esc(state.job.title)}. Periksa hasil ekstraksi sebelum menjalankan analisis.</p><div class="dropzone" id="dropzone">${icon("upload")}<h3>Letakkan CV di sini</h3><p>atau pilih berkas dari perangkat Anda.</p><input class="file-input" id="files" type="file" accept="application/pdf,.pdf" multiple><label class="button" for="files">${icon("plus")}Pilih berkas PDF</label><small>PDF berbasis teks · maks. 10 MB / berkas · 20 halaman</small></div><label class="check-line"><input id="use-ai" type="checkbox" ${state.session.ai_available ? "" : "disabled"}><span>Gunakan bantuan AI eksternal (Groq)<small>${state.session.ai_available ? "Jika dipilih, teks CV dikirim ke Groq untuk ekstraksi. Pastikan Anda berwenang memproses data kandidat." : "Belum dikonfigurasi. Ekstraksi lokal tetap tersedia tanpa mengirim CV ke luar."}</small></span></label><div id="upload-list" aria-live="polite"></div><div class="form-error" id="upload-error" role="alert"></div><div class="form-footer"><button class="text-button" id="manual">Tambah profil manual</button><button class="button" id="cancel-upload">Tutup</button><button class="button primary" id="start-upload" disabled>Proses CV ${icon("arrow")}</button></div>`,
    "TAMBAH KANDIDAT",
  );
  const zone = $("#dropzone");
  const list = $("#upload-list");
  function draw() {
    list.innerHTML = pendingFiles
      .map(
        (f, i) =>
          `<div class="upload-item"><span>${esc(f.file.name)}<small class="${f.error ? "error" : f.done ? "success" : ""}">${esc(f.error || f.message || "Siap diproses")}</small></span>${!f.done ? `<button class="icon-button" data-remove="${i}" aria-label="Hapus ${esc(f.file.name)} dari antrean">${icon("x")}</button>` : icon("check")}</div>`,
      )
      .join("");
    $$("[data-remove]").forEach(
      (b) =>
        (b.onclick = () => {
          pendingFiles.splice(Number(b.dataset.remove), 1);
          draw();
        }),
    );
    $("#start-upload").disabled = !pendingFiles.some(
      (f) => !f.done && !f.error,
    );
  }
  function add(files) {
    for (const file of [...files].slice(0, 20)) {
      if (pendingFiles.length >= 20) break;
      if (
        pendingFiles.some(
          (x) => x.file.name === file.name && x.file.size === file.size,
        )
      )
        continue;
      pendingFiles.push({
        file,
        error:
          file.size > 10 * 1024 * 1024
            ? "Berkas melebihi 10 MB."
            : !file.name.toLowerCase().endsWith(".pdf")
              ? "Pilih berkas PDF."
              : "",
      });
    }
    draw();
    state.dirty = pendingFiles.length > 0;
  }
  $("#files").onchange = (e) => add(e.target.files);
  zone.ondragover = (e) => {
    e.preventDefault();
    zone.classList.add("dragging");
  };
  zone.ondragleave = () => zone.classList.remove("dragging");
  zone.ondrop = (e) => {
    e.preventDefault();
    zone.classList.remove("dragging");
    add(e.dataTransfer.files);
  };
  $("#manual").onclick = () =>
    confirmDiscard(() => {
      finishModal();
      manualForm();
    });
  $("#cancel-upload").onclick = () => confirmDiscard(finishModal);
  $("#start-upload").onclick = async () => {
    const b = $("#start-upload");
    b.disabled = true;
    b.textContent = "Memproses…";
    $("#modal-close").disabled = true;
    $("#cancel-upload").textContent = "Batalkan proses";
    uploadController = new AbortController();
    $("#cancel-upload").onclick = () => uploadController.abort();
    $("#manual").disabled = true;
    $("#files").disabled = true;
    for (const f of pendingFiles) {
      if (f.done || f.error || uploadController.signal.aborted) continue;
      const form = new FormData();
      form.append("file", f.file);
      form.append("use_ai", $("#use-ai").checked ? "true" : "false");
      f.message = "Sedang diproses…";
      draw();
      b.disabled = true;
      $$("[data-remove]").forEach((x) => (x.disabled = true));
      try {
        await api(`/api/jobs/${state.job.id}/upload`, {
          method: "POST",
          body: form,
          signal: uploadController.signal,
        });
        f.done = true;
        f.message = "Profil ditambahkan · periksa hasil ekstraksi";
      } catch (error) {
        f.error = error.message;
      }
      draw();
      b.disabled = true;
    }
    $("#modal-close").disabled = false;
    $("#cancel-upload").textContent = "Selesai";
    $("#cancel-upload").onclick = async () => {
      finishModal();
      await loadJobs();
      await render();
    };
    $("#manual").disabled = false;
    $("#files").disabled = false;
    b.textContent = "Proses CV";
    b.disabled = true;
    state.dirty = false;
    await loadJobs();
    await render();
  };
}

function guardPageChange(next) {
  if (state.dirty) {
    if ($("#modal").open) {
      confirmDiscard(() => {
        finishModal();
        next();
      });
      return;
    }
    modalParentDirty = true;
    showModal(
      "Perubahan belum disimpan.",
      `<p class="page-subtitle">Simpan kriteria terlebih dahulu, atau abaikan perubahan untuk berpindah halaman.</p><div class="form-footer"><button class="button" id="stay">Lanjut edit</button><button class="button primary" id="leave">Abaikan perubahan</button></div>`,
    );
    $("#stay").onclick = finishModal;
    $("#leave").onclick = () => {
      modalParentDirty = false;
      finishModal();
      next();
    };
    return;
  }
  next();
}
async function navigate(view) {
  if (!state.session?.authenticated) {
    $("#password")?.focus();
    return;
  }
  clearTimeout(searchTimer);
  guardPageChange(() => {
    state.view = view;
    render();
  });
}

function showLogin() {
  content.setAttribute("aria-busy", "false");
  content.innerHTML = `<section class="panel login-panel"><span class="eyebrow">RECRUITAI WORKSPACE</span><h2>Selamat datang kembali.</h2><p>Masuk untuk mengakses kandidat dan hasil seleksi.</p><form id="login-form" novalidate>${field("password", "Kata sandi ruang kerja", "", "password", "", 'autocomplete="current-password" required')}<button class="text-button" type="button" id="show-password" aria-pressed="false">Tampilkan kata sandi</button><div class="form-error" id="login-error" role="alert" tabindex="-1"></div><button class="button primary" type="submit">Masuk ke ruang kerja ${icon("arrow")}</button></form></section>`;
  $("#show-password").onclick = (e) => {
    const input = $("#password");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    e.currentTarget.textContent = show
      ? "Sembunyikan kata sandi"
      : "Tampilkan kata sandi";
    e.currentTarget.setAttribute("aria-pressed", show);
  };
  $("#login-form").onsubmit = async (e) => {
    e.preventDefault();
    const b = $("[type=submit]", e.currentTarget);
    b.disabled = true;
    try {
      await api("/api/login", {
        method: "POST",
        body: JSON.stringify({ password: $("#password").value }),
      });
      if (suspendedWorkspace) {
        state.session = await api("/api/session");
        content.replaceChildren(suspendedWorkspace.draft);
        if (suspendedWorkspace.dialogOpen) $("#modal").showModal();
        suspendedWorkspace = null;
        notify("Sesi dipulihkan. Periksa isian lalu simpan kembali.");
      } else await start();
    } catch (error) {
      formError(e.target, error.message, "password");
    } finally {
      b.disabled = false;
    }
  };
}

async function start() {
  try {
    state.session = await api("/api/session");
    if (!state.session.authenticated) {
      showLogin();
      return;
    }
    $("#logout").hidden = state.session.local_only;
    $("#session-label").textContent = state.session.local_only
      ? "Ruang kerja lokal"
      : "Sesi terlindungi";
    await loadJobs();
    const url = new URL(location.href);
    state.view = url.searchParams.get("view") || "candidates";
    state.job =
      state.jobs.find((j) => j.id === url.searchParams.get("job")) ||
      state.jobs[0] ||
      null;
    state.status = ["all", ...Object.keys(statuses)].includes(
      url.searchParams.get("status"),
    )
      ? url.searchParams.get("status")
      : "all";
    state.page = Math.max(1, Number(url.searchParams.get("page")) || 1);
    await render();
  } catch (error) {
    content.innerHTML = `<section class="panel empty"><h2>Ruang kerja belum terhubung</h2><p>${esc(error.message)}</p><button class="button" id="start-retry">Coba kembali</button></section>`;
    $("#start-retry").onclick = start;
  }
}

$$("[data-icon]").forEach((el) => (el.innerHTML = icon(el.dataset.icon)));
$$("nav a").forEach(
  (a) =>
    (a.onclick = (e) => {
      e.preventDefault();
      navigate(a.dataset.view);
    }),
);
$(".brand").onclick = (e) => {
  e.preventDefault();
  navigate("candidates");
};
$("#modal-close").onclick = () => confirmDiscard(finishModal);
$("#modal").addEventListener("cancel", (e) => {
  e.preventDefault();
  if (!$("#modal-close").disabled) confirmDiscard(finishModal);
});
$("#logout").onclick = async () => {
  await api("/api/logout", { method: "POST" });
  location.reload();
};
window.addEventListener("beforeunload", (e) => {
  if (state.dirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});
window.addEventListener("offline", () =>
  notify("Koneksi terputus. Isian yang terbuka tetap tersedia."),
);
start();
