// Build a simple motion magnitude chart if data embedded in page existed.
// This example just fetches last events from a lightweight endpoint (not implemented here).
// For demo, render empty chart.
document.addEventListener('DOMContentLoaded', () => {
  const ctx = document.getElementById('motionChart');
  if (!ctx) return;
  const chart = new Chart(ctx, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'Motion magnitude', data: [] }] },
    options: { responsive: true, maintainAspectRatio: false }
  });
});
