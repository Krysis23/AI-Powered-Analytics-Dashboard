function populateChartSelects(cols) {
  const selects = ["chart-x", "chart-y", "chart-color"];
  selects.forEach((id, i) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const blank = i > 0 ? [`<option value="">— none —</option>`] : [];
    sel.innerHTML = blank.concat(
      cols.map(c => `<option value="${c}">${c}</option>`)
    ).join("");
  });
}

document.getElementById("btn-chart").addEventListener("click", async () => {
  const chartType = document.getElementById("chart-type").value;
  const x         = document.getElementById("chart-x").value;
  const y         = document.getElementById("chart-y").value || null;
  const color     = document.getElementById("chart-color").value || null;

  // basic validation
  if (!x) {
    alert("Please select an X axis column");
    return;
  }

  // bar, line, pie need a Y axis
  if (["bar", "line", "pie"].includes(chartType) && !y) {
    alert(`${chartType} chart needs a Y axis column`);
    return;
  }

  const btn = document.getElementById("btn-chart");
  btn.textContent = "Generating...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/chart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chart_type: chartType,
        x:          x,
        y:          y,
        color:      color,
        title:      `${chartType}: ${x}${y ? " vs " + y : ""}`
      })
    });

    const data = await res.json();

    if (data.error) {
      alert("Chart error: " + data.error);
      return;
    }

    // parse the Plotly JSON string and render
    const fig = JSON.parse(data.chart);
    const container = document.getElementById("chart-container");
    container.innerHTML = ""; // clear previous chart
    Plotly.newPlot(container, fig.data, fig.layout, { responsive: true });

  } catch (err) {
    alert("Request failed: " + err.message);
    console.error(err);
  } finally {
    btn.textContent = "Generate chart";
    btn.disabled = false;
  }
});