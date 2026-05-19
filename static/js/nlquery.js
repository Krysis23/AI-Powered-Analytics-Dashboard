document.getElementById("btn-nl").addEventListener("click", askQuestion);
document.getElementById("nl-input").addEventListener("keydown", e => {
  if (e.key === "Enter") askQuestion();
});

async function askQuestion() {
  const question = document.getElementById("nl-input").value.trim();
  if (!question) return;

  const btn = document.getElementById("btn-nl");
  btn.textContent = "Thinking..."; btn.disabled = true;

  const res = await fetch("/api/nl-query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });
  const data = await res.json();
  btn.textContent = "Ask"; btn.disabled = false;

  if (data.error) {
    document.getElementById("nl-result").innerHTML =
      `<p class="error">${data.error}</p>`;
    return;
  }

  renderTable(data.table, data.columns, "nl-result");

  if (data.chart) {
    const fig = JSON.parse(data.chart);
    Plotly.newPlot("nl-chart", fig.data, fig.layout, { responsive: true });
  }
}