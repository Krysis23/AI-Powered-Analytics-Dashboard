// slider label
const slider = document.getElementById("null-threshold");
slider.addEventListener("input", () => {
  document.getElementById("thresh-val").textContent = slider.value;
});

document.getElementById("btn-clean").addEventListener("click", async () => {
  const config = {
    drop_duplicate_rows: document.getElementById("drop-dupes").checked,
    parse_dates:         document.getElementById("parse-dates").checked,
    drop_id_cols:        document.getElementById("drop-ids").checked,
    remove_outliers:     document.getElementById("remove-outliers").checked,
    null_strategy:       document.getElementById("null-strategy").value,
    null_threshold:      parseInt(slider.value),
    outlier_z_threshold: 3.0
  };

  const btn = document.getElementById("btn-clean");
  btn.textContent = "Cleaning..."; btn.disabled = true;

  const res = await fetch("/api/clean", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
  const data = await res.json();
  btn.textContent = "Apply cleaning"; btn.disabled = false;

  if (data.error) { alert(data.error); return; }

  const report = document.getElementById("clean-report");
  report.innerHTML = `
    <div class="report-summary">
      <span class="pill">${data.rows_before.toLocaleString()} → ${data.rows_after.toLocaleString()} rows</span>
      ${data.cols_dropped.length ? `<span class="pill warn">Dropped cols: ${data.cols_dropped.join(", ")}</span>` : ""}
    </div>
    <ul>${data.steps.map(s => `<li>✓ ${s}</li>`).join("")}</ul>
  `;
  report.classList.remove("hidden");
  document.getElementById("btn-download").classList.remove("hidden");

  window.COLUMNS = data.columns;
  // after clean succeeds
  
  populateChartSelects(data.columns);
  showSection("section-charts");
  showSection("section-nl");
});