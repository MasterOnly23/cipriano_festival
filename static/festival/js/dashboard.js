(function () {
  const eventsBody = document.getElementById("eventsBody");
  const pinInput = document.getElementById("adminPin");
  const undoBtn = document.getElementById("undoBtn");
  const adminMsg = document.getElementById("adminMsg");
  const prevPageBtn = document.getElementById("prevPageBtn");
  const nextPageBtn = document.getElementById("nextPageBtn");
  const pageInfo = document.getElementById("pageInfo");
  const filterMode = document.getElementById("filterMode");
  const filterStatus = document.getElementById("filterStatus");
  const filterPizzaId = document.getElementById("filterPizzaId");
  const filterDateFrom = document.getElementById("filterDateFrom");
  const filterDateTo = document.getElementById("filterDateTo");
  const filterFlavor = document.getElementById("filterFlavor");
  const filterWaiter = document.getElementById("filterWaiter");
  const applyFiltersBtn = document.getElementById("applyFiltersBtn");
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");
  const exportSalesBtn = document.getElementById("exportSalesBtn");

  let currentPage = 1;
  const pageSize = 20;
  let latestPagination = null;
  const filters = {
    mode: "",
    to_status: "",
    pizza_id: "",
    date_from: "",
    date_to: "",
    flavor: "",
    waiter_name: "",
  };

  function setCount(id, value) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = value ?? 0;
    }
  }

  function renderEvents(events) {
    eventsBody.innerHTML = "";
    if (!events || events.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td colspan="6">Sin movimientos para estos filtros.</td>`;
      eventsBody.appendChild(tr);
      return;
    }
    for (const ev of events) {
      const modeClass = (ev.mode || "").toLowerCase();
      const toStatusClass = (ev.to_status || "").toLowerCase();
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td data-label="Hora">${new Date(ev.created_at).toLocaleTimeString()}</td>
        <td data-label="ID">${ev.pizza_id}</td>
        <td data-label="Modo"><span class="mode-badge mode-${modeClass}">${ev.mode}</span></td>
        <td data-label="Transicion">${ev.from_status} -> <span class="status-pill status-${toStatusClass}">${ev.to_status}</span></td>
        <td data-label="Operador">${ev.actor_name || "-"}</td>
        <td data-label="Mesero">${ev.waiter_name || "-"}</td>
      `;
      eventsBody.appendChild(tr);
    }
  }

  function updatePaginationUi() {
    if (!latestPagination) {
      pageInfo.textContent = "Pagina 1";
      prevPageBtn.disabled = true;
      nextPageBtn.disabled = true;
      return;
    }
    pageInfo.textContent = `Pagina ${latestPagination.page} de ${latestPagination.total_pages} (${latestPagination.total_items} registros)`;
    prevPageBtn.disabled = !latestPagination.has_previous;
    nextPageBtn.disabled = !latestPagination.has_next;
  }

  function buildQuery() {
    const params = new URLSearchParams();
    params.set("page", String(currentPage));
    params.set("page_size", String(pageSize));
    if (filters.mode) {
      params.set("mode", filters.mode);
    }
    if (filters.to_status) {
      params.set("to_status", filters.to_status);
    }
    if (filters.pizza_id) {
      params.set("pizza_id", filters.pizza_id);
    }
    if (filters.date_from) {
      params.set("date_from", filters.date_from);
    }
    if (filters.date_to) {
      params.set("date_to", filters.date_to);
    }
    if (filters.flavor) {
      params.set("flavor", filters.flavor);
    }
    if (filters.waiter_name) {
      params.set("waiter_name", filters.waiter_name);
    }
    return params.toString();
  }

  function syncFiltersFromInputs() {
    filters.mode = filterMode.value.trim().toUpperCase();
    filters.to_status = filterStatus.value.trim().toUpperCase();
    filters.pizza_id = filterPizzaId.value.trim().toUpperCase();
    filters.date_from = filterDateFrom.value.trim();
    filters.date_to = filterDateTo.value.trim();
    filters.flavor = filterFlavor.value.trim().toUpperCase();
    filters.waiter_name = filterWaiter.value.trim().toUpperCase();
  }

  async function loadDashboard() {
    const res = await fetch(`/api/dashboard?${buildQuery()}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      return;
    }
    const c = data.counts;
    setCount("kpi-preparacion", c.PREPARACION);
    setCount("kpi-lista", c.LISTA);
    setCount("kpi-vendida", c.VENDIDA);
    setCount("kpi-cancelada", c.CANCELADA);
    setCount("kpi-merma", c.MERMA);
    const revenue = Number(data.revenue_sold || 0);
    setCount("kpi-revenue", `$${revenue.toLocaleString("es-AR")}`);
    renderEvents(data.latest);
    latestPagination = data.pagination || null;
    if (latestPagination && currentPage !== latestPagination.page) {
      currentPage = latestPagination.page;
    }
    updatePaginationUi();
  }

  if (undoBtn && pinInput && adminMsg) {
    undoBtn.addEventListener("click", async () => {
      adminMsg.textContent = "Procesando...";
      const payload = {
        pin: pinInput.value.trim(),
      };
      const res = await fetch("/api/admin/undo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        adminMsg.textContent = data.error || "Error";
        return;
      }
      adminMsg.textContent = data.message;
      await loadDashboard();
    });
  }

  prevPageBtn.addEventListener("click", async () => {
    if (!latestPagination || !latestPagination.has_previous) {
      return;
    }
    currentPage -= 1;
    await loadDashboard();
  });

  nextPageBtn.addEventListener("click", async () => {
    if (!latestPagination || !latestPagination.has_next) {
      return;
    }
    currentPage += 1;
    await loadDashboard();
  });

  applyFiltersBtn.addEventListener("click", async () => {
    syncFiltersFromInputs();
    currentPage = 1;
    await loadDashboard();
  });

  clearFiltersBtn.addEventListener("click", async () => {
    filterMode.value = "";
    filterStatus.value = "";
    filterPizzaId.value = "";
    filterDateFrom.value = "";
    filterDateTo.value = "";
    filterFlavor.value = "";
    filterWaiter.value = "";
    syncFiltersFromInputs();
    currentPage = 1;
    await loadDashboard();
  });

  filterPizzaId.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    syncFiltersFromInputs();
    currentPage = 1;
    await loadDashboard();
  });
  filterPizzaId.addEventListener("input", () => {
    filterPizzaId.value = filterPizzaId.value.toUpperCase();
  });
  filterWaiter.addEventListener("input", () => {
    filterWaiter.value = filterWaiter.value.toUpperCase();
  });

  exportSalesBtn.addEventListener("click", () => {
    syncFiltersFromInputs();
    const params = new URLSearchParams();
    if (filters.date_from) {
      params.set("date_from", filters.date_from);
    }
    if (filters.date_to) {
      params.set("date_to", filters.date_to);
    }
    if (filters.flavor) {
      params.set("flavor", filters.flavor);
    }
    if (filters.waiter_name) {
      params.set("waiter_name", filters.waiter_name);
    }
    window.location.href = `/api/dashboard/sales-export.xls?${params.toString()}`;
  });

  loadDashboard();
  setInterval(loadDashboard, 3000);
})();
