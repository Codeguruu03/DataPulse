/**
 * DataPulse Interactive Dashboard Controller.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Chart instances
  let revenueChart = null;
  let topProductsChart = null;
  let customerSegmentsChart = null;

  // Initialize UI
  loadDashboardData();

  // Modal Controls
  const modal = document.getElementById("pipelineModal");
  const btnTriggerModal = document.getElementById("btnTriggerModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnCancelModal = document.getElementById("btnCancelModal");
  const btnStartPipeline = document.getElementById("btnStartPipeline");

  const inputThreshold = document.getElementById("inputThreshold");
  const thresholdVal = document.getElementById("thresholdVal");
  const inputAnomaly = document.getElementById("inputAnomaly");
  const anomalyVal = document.getElementById("anomalyVal");

  inputThreshold.addEventListener("input", (e) => {
    thresholdVal.innerText = `${e.target.value}.0%`;
  });

  inputAnomaly.addEventListener("input", (e) => {
    anomalyVal.innerText = `${e.target.value}.0%`;
  });

  btnTriggerModal.addEventListener("click", () => {
    modal.style.display = "flex";
  });

  const closeModal = () => {
    modal.style.display = "none";
    document.getElementById("pipelineProgress").style.display = "none";
  };

  btnCloseModal.addEventListener("click", closeModal);
  btnCancelModal.addEventListener("click", closeModal);

  btnStartPipeline.addEventListener("click", async () => {
    const threshold = parseFloat(inputThreshold.value);
    const anomaly = parseFloat(inputAnomaly.value) / 100.0;

    document.getElementById("pipelineProgress").style.display = "block";
    btnStartPipeline.disabled = true;

    try {
      const resp = await fetch("/api/v1/pipeline/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          threshold: threshold,
          anomaly_rate: anomaly,
          auto_generate: true,
        }),
      });

      // Poll pipeline status
      const pollInterval = setInterval(async () => {
        const stResp = await fetch("/api/v1/pipeline/status");
        const statusData = await stResp.json();

        if (statusData.status === "SUCCESS" || statusData.status === "BLOCKED_BY_QUALITY_GATE") {
          clearInterval(pollInterval);
          btnStartPipeline.disabled = false;
          closeModal();
          loadDashboardData(); // Refresh UI
        }
      }, 1000);
    } catch (err) {
      console.error("Error triggering pipeline:", err);
      btnStartPipeline.disabled = false;
    }
  });

  async function loadDashboardData() {
    try {
      // 1. Fetch Executive Summary KPIs
      const summaryResp = await fetch("/api/v1/analytics/summary");
      const summary = await summaryResp.json();

      document.getElementById("kpiRevenue").innerText = `₹${(summary.total_revenue || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
      document.getElementById("kpiOrders").innerText = (summary.total_orders || 0).toLocaleString();
      document.getElementById("kpiCustomers").innerText = (summary.active_customers || 0).toLocaleString();
      document.getElementById("kpiAov").innerText = `₹${(summary.avg_order_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
      
      const qScore = summary.overall_quality_score || 95.0;
      document.getElementById("kpiQuality").innerText = `${qScore.toFixed(2)}%`;
      document.getElementById("kpiQualityStatus").innerText = qScore >= 95.0 ? "✔ PASSED (>=95%)" : "⚠ AT RISK (<95%)";

      // 2. Fetch Monthly Revenue for Chart
      const monthlyResp = await fetch("/api/v1/analytics/monthly-revenue");
      const monthlyData = await monthlyResp.json();
      renderMonthlyRevenueChart(monthlyData.reverse());

      // 3. Fetch Top Products for Chart
      const topProdResp = await fetch("/api/v1/analytics/top-products");
      const topProdData = await topProdResp.json();
      renderTopProductsChart(topProdData);

      // 4. Fetch Customer Segments
      const segResp = await fetch("/api/v1/analytics/customer-segments");
      const segData = await segResp.json();
      renderCustomerSegmentsChart(segData);

      // 5. Fetch Quarantine Audit Records
      const qResp = await fetch("/api/v1/quality/quarantine?dataset=orders&limit=25");
      const qData = await qResp.json();
      renderQuarantineTable(qData);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
    }
  }

  function renderMonthlyRevenueChart(data) {
    const ctx = document.getElementById("monthlyRevenueChart").getContext("2d");
    const labels = data.map((d) => `${d.month_name} ${d.year}`);
    const revenues = data.map((d) => d.total_revenue);
    const orders = data.map((d) => d.total_orders);

    if (revenueChart) revenueChart.destroy();

    revenueChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Gross Revenue (₹)",
            data: revenues,
            backgroundColor: "rgba(0, 240, 255, 0.4)",
            borderColor: "#00f0ff",
            borderWidth: 2,
            borderRadius: 6,
            yAxisID: "y",
          },
          {
            label: "Order Volume",
            data: orders,
            type: "line",
            borderColor: "#ff0080",
            backgroundColor: "rgba(255, 0, 128, 0.2)",
            borderWidth: 3,
            tension: 0.3,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8" } },
          y: { position: "left", grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#00f0ff" } },
          y1: { position: "right", grid: { drawOnChartArea: false }, ticks: { color: "#ff0080" } },
        },
        plugins: {
          legend: { labels: { color: "#f8fafc" } },
        },
      },
    });
  }

  function renderTopProductsChart(data) {
    const ctx = document.getElementById("topProductsChart").getContext("2d");
    const labels = data.slice(0, 5).map((d) => d.product_name);
    const revenues = data.slice(0, 5).map((d) => d.gross_revenue);

    if (topProductsChart) topProductsChart.destroy();

    topProductsChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Revenue (₹)",
            data: revenues,
            backgroundColor: [
              "rgba(0, 240, 255, 0.6)",
              "rgba(121, 40, 202, 0.6)",
              "rgba(255, 0, 128, 0.6)",
              "rgba(0, 230, 118, 0.6)",
              "rgba(255, 179, 0, 0.6)",
            ],
            borderRadius: 6,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8" } },
          y: { grid: { display: false }, ticks: { color: "#f8fafc", font: { size: 11 } } },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });
  }

  function renderCustomerSegmentsChart(data) {
    const ctx = document.getElementById("customerSegmentsChart").getContext("2d");
    
    // Group spend by segment
    const segmentMap = {};
    data.forEach((d) => {
      segmentMap[d.segment] = (segmentMap[d.segment] || 0) + d.aggregate_spend;
    });

    const labels = Object.keys(segmentMap);
    const values = Object.values(segmentMap);

    if (customerSegmentsChart) customerSegmentsChart.destroy();

    customerSegmentsChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: ["#00f0ff", "#7928ca", "#ff0080", "#00e676"],
            borderColor: "#111827",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { color: "#f8fafc", boxWidth: 12 } },
        },
      },
    });
  }

  function renderQuarantineTable(data) {
    const tbody = document.getElementById("quarantineBody");
    const countBadge = document.getElementById("quarantineCountBadge");

    countBadge.innerText = `${data.total_quarantined || 0} Intercepted`;

    if (!data.records || data.records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: #00e676;">✔ Quarantine Zone is Clean. No Corrupted Records.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.records
      .map(
        (r) => `
      <tr>
        <td><span style="color: #94a3b8;">${r.quarantine_id || "Q-001"}</span></td>
        <td><strong>${r.order_id || "<span style='color:red;'>NULL</span>"}</strong></td>
        <td>${r.customer_id || "<span style='color:red;'>NULL</span>"}</td>
        <td>${r.quantity || 0}</td>
        <td>₹${r.unit_price || 0}</td>
        <td>${r.order_date || "N/A"}</td>
        <td><span class="tag-reason">${r.error_reasons || "Invalid row constraints"}</span></td>
      </tr>
    `
      )
      .join("");
  }
});
