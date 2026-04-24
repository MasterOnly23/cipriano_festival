(function () {
  const dayNumber = document.getElementById("dayNumber");
  const flavorPrefix = document.getElementById("flavorPrefix");
  const flavorName = document.getElementById("flavorName");
  const quantity = document.getElementById("quantity");
  const price = document.getElementById("price");
  const size = document.getElementById("size");
  const startNumber = document.getElementById("startNumber");
  const startNumberAdminPin = document.getElementById("startNumberAdminPin");
  const unlockStartNumberBtn = document.getElementById("unlockStartNumberBtn");
  const startNumberState = document.getElementById("startNumberState");
  const actorName = document.getElementById("actorName");
  const notes = document.getElementById("notes");
  const generateBtn = document.getElementById("generateBtn");
  const batchMsg = document.getElementById("batchMsg");
  const pdfLink = document.getElementById("pdfLink");
  const waiterName = document.getElementById("waiterName");
  const waiterActorName = document.getElementById("waiterActorName");
  const createWaiterBtn = document.getElementById("createWaiterBtn");
  const waiterMsg = document.getElementById("waiterMsg");
  const waiterPdfLink = document.getElementById("waiterPdfLink");
  const showBatchHistoryBtn = document.getElementById("showBatchHistoryBtn");
  const batchHistoryModal = document.getElementById("batchHistoryModal");
  const closeBatchHistoryModalBtn = document.getElementById("closeBatchHistoryModalBtn");
  const closeBatchHistoryFooterBtn = document.getElementById("closeBatchHistoryFooterBtn");
  const batchHistorySearchInput = document.getElementById("batchHistorySearchInput");
  const batchHistoryMsg = document.getElementById("batchHistoryMsg");
  const batchHistoryList = document.getElementById("batchHistoryList");
  const flavorToPrefix = {};
  if (flavorName) {
    for (const option of flavorName.options) {
      const name = (option.value || "").trim().toUpperCase();
      const prefix = (option.dataset.prefix || "").trim().toUpperCase();
      if (name && prefix) {
        flavorToPrefix[name] = prefix;
      }
    }
  }
  let startNumberUnlocked = false;
  let batchHistorySearchTimer = null;

  async function verifyBatchAdminPin(pin) {
    const res = await fetch("/api/batches/verify-admin-pin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: (pin || "").trim() }),
    });
    const data = await res.json();
    return {
      ok: res.ok && !!data.ok,
      error: data.error || "PIN admin invalido",
    };
  }

  function syncPrefixFromFlavor() {
    const selectedFlavor = flavorName.value.trim().toUpperCase();
    flavorPrefix.value = flavorToPrefix[selectedFlavor] || "";
  }

  function setStartNumberMode(unlocked) {
    startNumberUnlocked = unlocked;
    if (unlocked) {
      startNumber.readOnly = false;
      if (startNumber.value.trim().toLowerCase() === "auto") {
        startNumber.value = "";
      }
      startNumber.placeholder = "Ej: 1";
      startNumberState.textContent = "Nro inicial manual habilitado";
      unlockStartNumberBtn.textContent = "Volver a auto";
    } else {
      startNumber.readOnly = true;
      startNumber.value = "auto";
      startNumber.placeholder = "auto";
      startNumberState.textContent = "Nro inicial bloqueado en auto";
      unlockStartNumberBtn.textContent = "Habilitar Nro inicial manual";
    }
  }

  function renderBatchHistory(batches) {
    if (!batchHistoryList) {
      return;
    }
    if (!Array.isArray(batches) || batches.length === 0) {
      batchHistoryList.innerHTML = `<div class="history-empty">No hay lotes para este filtro.</div>`;
      return;
    }
    batchHistoryList.innerHTML = batches
      .map((batch) => {
        const day = batch.day || "";
        const createdAt = batch.created_at ? new Date(batch.created_at).toLocaleString() : "";
        const notes = batch.notes || "Sin notas";
        const code = batch.code || "";
        const codeParts = code.split("-");
        const flavorPrefixLabel = codeParts.length >= 2 ? codeParts[1] : "-";
        const firstItemId = batch.first_item_id || "-";
        const lastItemId = batch.last_item_id || "-";
        return `
          <article class="history-card">
            <div class="history-card-main">
              <strong>${code}</strong>
              <span>Fecha ${day}</span>
              <span>Prefijo sabor ${flavorPrefixLabel}</span>
              <span>Rango ${firstItemId} a ${lastItemId}</span>
              <span>Items ${batch.total_items || 0}</span>
              <span>Operador ${batch.created_by || "-"}</span>
              <span>Creado ${createdAt}</span>
              <span class="history-notes">${notes}</span>
            </div>
            <div class="history-card-actions">
              <a class="btn btn-alt btn-small" href="/api/batches/${batch.code}/labels.pdf" target="_blank" rel="noopener noreferrer">PDF</a>
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function loadBatchHistory(query = "") {
    if (!batchHistoryMsg || !batchHistoryList) {
      return;
    }
    batchHistoryMsg.textContent = "Cargando lotes...";
    const qs = query ? `?q=${encodeURIComponent(query.trim().toUpperCase())}` : "";
    const res = await fetch(`/api/batches${qs}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      batchHistoryMsg.textContent = data.error || "Error al cargar lotes";
      renderBatchHistory([]);
      return;
    }
    renderBatchHistory(data.batches || []);
    batchHistoryMsg.textContent = `${(data.batches || []).length} lote(s) encontrados.`;
  }

  function closeBatchHistoryModal() {
    if (!batchHistoryModal) {
      return;
    }
    batchHistoryModal.classList.add("hidden");
    batchHistoryModal.setAttribute("aria-hidden", "true");
  }

  async function openBatchHistoryModal() {
    if (!batchHistoryModal) {
      return;
    }
    batchHistoryModal.classList.remove("hidden");
    batchHistoryModal.setAttribute("aria-hidden", "false");
    if (batchHistorySearchInput) {
      batchHistorySearchInput.value = "";
      window.setTimeout(() => batchHistorySearchInput.focus(), 40);
    }
    await loadBatchHistory("");
  }

  flavorName.addEventListener("change", syncPrefixFromFlavor);
  startNumberAdminPin.addEventListener("input", () => {
    if (startNumberUnlocked) {
      setStartNumberMode(false);
      batchMsg.textContent = "Nro inicial manual bloqueado hasta volver a validar PIN admin.";
    }
  });
  unlockStartNumberBtn.addEventListener("click", async () => {
    if (startNumberUnlocked) {
      setStartNumberMode(false);
      batchMsg.textContent = "";
      return;
    }
    const pin = startNumberAdminPin.value.trim();
    if (!pin) {
      batchMsg.textContent = "Ingresa PIN admin para habilitar Nro inicial manual.";
      return;
    }
    const pinCheck = await verifyBatchAdminPin(pin);
    if (!pinCheck.ok) {
      setStartNumberMode(false);
      batchMsg.textContent = pinCheck.error;
      return;
    }
    setStartNumberMode(true);
    batchMsg.textContent = "PIN admin validado. Nro inicial manual habilitado.";
  });
  syncPrefixFromFlavor();
  setStartNumberMode(false);

  if (showBatchHistoryBtn) {
    showBatchHistoryBtn.addEventListener("click", async () => {
      await openBatchHistoryModal();
    });
  }
  if (closeBatchHistoryModalBtn) {
    closeBatchHistoryModalBtn.addEventListener("click", closeBatchHistoryModal);
  }
  if (closeBatchHistoryFooterBtn) {
    closeBatchHistoryFooterBtn.addEventListener("click", closeBatchHistoryModal);
  }
  if (batchHistoryModal) {
    batchHistoryModal.addEventListener("click", (event) => {
      if (event.target.dataset.closeBatchHistoryModal === "1") {
        closeBatchHistoryModal();
      }
    });
  }
  if (batchHistorySearchInput) {
    batchHistorySearchInput.addEventListener("input", () => {
      batchHistorySearchInput.value = batchHistorySearchInput.value.toUpperCase();
      if (batchHistorySearchTimer) {
        clearTimeout(batchHistorySearchTimer);
      }
      batchHistorySearchTimer = window.setTimeout(() => {
        loadBatchHistory(batchHistorySearchInput.value);
      }, 180);
    });
  }
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && batchHistoryModal && !batchHistoryModal.classList.contains("hidden")) {
      closeBatchHistoryModal();
    }
  });

  generateBtn.addEventListener("click", async () => {
    batchMsg.textContent = "Generando...";
    pdfLink.classList.add("hidden");

    if (!flavorName.value.trim()) {
      batchMsg.textContent = "Selecciona un sabor.";
      return;
    }
    syncPrefixFromFlavor();
    if (!flavorPrefix.value.trim()) {
      batchMsg.textContent = "El sabor seleccionado no tiene prefijo configurado.";
      return;
    }
    const dayValue = Number(dayNumber.value);
    if (!Number.isInteger(dayValue) || dayValue < 1) {
      batchMsg.textContent = "Dia invalido. Ingresa un numero mayor o igual a 1.";
      return;
    }
    const requestedStartRaw = startNumberUnlocked ? startNumber.value.trim() : "auto";
    if (startNumberUnlocked && !requestedStartRaw) {
      batchMsg.textContent = "Si habilitas Nro inicial manual, debes ingresar un numero.";
      return;
    }

    const payload = {
      day_code: `D${dayValue}`,
      flavor_prefix: flavorPrefix.value.trim().toUpperCase(),
      flavor: flavorName.value.trim().toUpperCase(),
      quantity: Number(quantity.value),
      price: Number(price.value),
      size: size.value.trim().toUpperCase(),
      actor_name: actorName.value.trim(),
      notes: notes.value.trim(),
      start_number: requestedStartRaw || "auto",
      admin_actions_pin: startNumberUnlocked ? startNumberAdminPin.value.trim() : "",
    };

    const res = await fetch("/api/batches/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      batchMsg.textContent = data.error || "Error al generar lote";
      return;
    }
    batchMsg.textContent = `OK ${data.batch_code}: ${data.count} etiquetas (${data.first_id} a ${data.last_id})`;
    pdfLink.href = data.labels_pdf_url;
    pdfLink.textContent = "Descargar etiquetas PDF";
    pdfLink.classList.remove("hidden");
    setStartNumberMode(false);
    startNumberAdminPin.value = "";
  });

  if (createWaiterBtn && waiterName) {
    createWaiterBtn.addEventListener("click", async () => {
      waiterMsg.textContent = "Creando mesero...";
      waiterPdfLink.classList.add("hidden");
      const name = waiterName.value.trim().toUpperCase();
      if (!name) {
        waiterMsg.textContent = "Ingresa nombre del mesero.";
        return;
      }

      const payload = {
        name: name,
        actor_name: waiterActorName ? waiterActorName.value.trim() : "",
      };
      const res = await fetch("/api/waiters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        waiterMsg.textContent = data.error || "Error al crear mesero";
        return;
      }
      waiterMsg.textContent = `OK ${data.waiter.code} - ${data.waiter.name}`;
      waiterPdfLink.href = data.labels_pdf_url;
      waiterPdfLink.textContent = `Descargar QR ${data.waiter.code}`;
      waiterPdfLink.classList.remove("hidden");
      waiterName.value = "";
    });
  }
})();
