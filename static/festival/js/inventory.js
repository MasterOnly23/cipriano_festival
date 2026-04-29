(function () {
  const batchInput = document.getElementById("inventoryBatch");
  const statusSelect = document.getElementById("inventoryStatus");
  const locationSelect = document.getElementById("inventoryLocation");
  const applyBtn = document.getElementById("inventoryApplyBtn");
  const clearBtn = document.getElementById("inventoryClearBtn");
  const msg = document.getElementById("inventoryMsg");
  const body = document.getElementById("inventoryBody");

  function locationLabel(value) {
    if (value === "MAIN") {
      return "Principal";
    }
    if (value === "SECONDARY") {
      return "Secundario";
    }
    return value || "-";
  }

  function renderRows(ranges) {
    if (!Array.isArray(ranges) || ranges.length === 0) {
      body.innerHTML = `<tr><td colspan="6">Sin items para este filtro.</td></tr>`;
      return;
    }
    body.innerHTML = ranges
      .map((row) => {
        const rangeLabel = row.first_id === row.last_id ? row.first_id : `${row.first_id} -> ${row.last_id}`;
        return `
          <tr>
            <td data-label="Lote">${row.batch_code || "-"}</td>
            <td data-label="Rango">${rangeLabel}</td>
            <td data-label="Cantidad">${row.count || 0}</td>
            <td data-label="Sabor">${row.flavor || "-"}</td>
            <td data-label="Estado">${row.status || "-"}</td>
            <td data-label="Local">${locationLabel(row.location)}</td>
          </tr>
        `;
      })
      .join("");
  }

  async function loadInventory() {
    msg.textContent = "Cargando inventario...";
    const params = new URLSearchParams();
    const batch = batchInput.value.trim().toUpperCase();
    const status = statusSelect.value.trim().toUpperCase();
    const location = locationSelect.value.trim().toUpperCase();
    if (batch) {
      params.set("batch", batch);
    }
    if (status) {
      params.set("status", status);
    }
    if (location) {
      params.set("location", location);
    }
    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`/api/inventory${qs}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      msg.textContent = data.error || "Error al cargar inventario";
      renderRows([]);
      return;
    }
    const ranges = data.ranges || [];
    renderRows(ranges);
    msg.textContent = `${ranges.length} rango(s) encontrados.`;
  }

  if (batchInput) {
    batchInput.addEventListener("input", () => {
      batchInput.value = batchInput.value.toUpperCase();
    });
  }
  applyBtn.addEventListener("click", loadInventory);
  clearBtn.addEventListener("click", () => {
    batchInput.value = "";
    statusSelect.value = "";
    locationSelect.value = "";
    loadInventory();
  });

  loadInventory();
})();
