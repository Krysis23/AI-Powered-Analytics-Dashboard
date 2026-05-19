const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");

// drag-drop styling
dropZone.addEventListener("dragover", e => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => uploadFile(fileInput.files[0]));

// click on drop zone opens file picker
dropZone.addEventListener("click", () => fileInput.click());

async function uploadFile(file) {
  if (!file) return;

  const status = document.getElementById("upload-status");
  status.textContent = "Uploading...";
  status.classList.remove("hidden");

  const fd = new FormData();
  fd.append("file", file);

  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const data = await res.json();

  if (data.error) {
    status.textContent = "Error: " + data.error;
    status.classList.add("error");
    return;
  }

  status.innerHTML = `Loaded <strong>${data.rows.toLocaleString()}</strong> rows × <strong>${data.cols}</strong> columns`;
  status.classList.add("success");

  // store columns globally for chart selects
  window.COLUMNS = data.columns;

  // show preview table
  renderTable(data.preview, data.columns, "preview-table");

  // load profile then reveal next section
  await loadProfile();

  // at the bottom of uploadFile(), after loadProfile()
  populateChartSelects(data.columns);
}

async function loadProfile() {
  const res = await fetch("/api/profile");
  const data = await res.json();

  if (data.error) {
    console.error("Profile error:", data.error);
    return;
  }

  // summary stats row
  const stats = document.getElementById("profile-stats");
  const totalMissing = data.reduce((sum, p) => sum + p.missing_count, 0);
  stats.innerHTML = `
    <div class="stat-card"><div class="stat-val">${data.length}</div><div class="stat-lbl">Columns</div></div>
    <div class="stat-card"><div class="stat-val">${totalMissing.toLocaleString()}</div><div class="stat-lbl">Missing values</div></div>
    <div class="stat-card"><div class="stat-val">${data.filter(p => p.inferred_type === 'numeric').length}</div><div class="stat-lbl">Numeric cols</div></div>
    <div class="stat-card"><div class="stat-val">${data.filter(p => p.inferred_type === 'categorical').length}</div><div class="stat-lbl">Categorical cols</div></div>
    <div class="stat-card"><div class="stat-val">${data.filter(p => p.inferred_type === 'datetime').length}</div><div class="stat-lbl">Date cols</div></div>
  `;

  // column detail table
  const tableContainer = document.getElementById("profile-table");
  tableContainer.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Column</th>
          <th>Type</th>
          <th>Missing %</th>
          <th>Unique</th>
          <th>Min</th>
          <th>Max</th>
          <th>Sample values</th>
        </tr>
      </thead>
      <tbody>
        ${data.map(p => `
          <tr>
            <td><strong>${p.name}</strong></td>
            <td><span class="type-badge type-${p.inferred_type}">${p.inferred_type}</span></td>
            <td>${p.missing_pct}%</td>
            <td>${p.n_unique.toLocaleString()}</td>
            <td>${p.min_val ?? "—"}</td>
            <td>${p.max_val ?? "—"}</td>
            <td style="font-size:11px;color:#64748b">${p.sample_values.slice(0,3).join(", ")}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

  // reveal profile and clean sections
  showSection("section-profile");
  showSection("section-clean");
}

function renderTable(rows, cols, containerId) {
  const el = document.getElementById(containerId);
  if (!rows || !rows.length) { el.innerHTML = ""; return; }
  let html = "<table><thead><tr>" +
    cols.map(c => `<th>${c}</th>`).join("") +
    "</tr></thead><tbody>" +
    rows.map(r => "<tr>" +
      cols.map(c => `<td>${r[c] ?? ""}</td>`).join("") +
      "</tr>").join("") +
    "</tbody></table>";
  el.innerHTML = html;
  el.classList.remove("hidden");
}

function showSection(id) {
  document.getElementById(id).classList.remove("hidden");
}