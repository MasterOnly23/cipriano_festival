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
  const showWaiterHistoryBtn = document.getElementById("showWaiterHistoryBtn");
  const waiterHistoryModal = document.getElementById("waiterHistoryModal");
  const closeWaiterHistoryModalBtn = document.getElementById("closeWaiterHistoryModalBtn");
  const closeWaiterHistoryFooterBtn = document.getElementById("closeWaiterHistoryFooterBtn");
  const waiterHistorySearchInput = document.getElementById("waiterHistorySearchInput");
  const waiterHistoryMsg = document.getElementById("waiterHistoryMsg");
  const waiterHistoryList = document.getElementById("waiterHistoryList");
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
  let waiterHistorySearchTimer = null;

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(`${name}=`)) {
        return decodeURIComponent(trimmed.slice(name.length + 1));
      }
    }
    return "";
  }

  function jsonHeaders() {
    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }
    return headers;
  }

  async function verifyBatchAdminPin(pin) {
    const res = await fetch("/api/batches/verify-admin-pin", {
      method: "POST",
      headers: jsonHeaders(),
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

  function renderWaiterHistory(groups) {
    if (!waiterHistoryList) {
      return;
    }
    if (!Array.isArray(groups) || groups.length === 0) {
      waiterHistoryList.innerHTML = `<div class="history-empty">No hay meseros para este filtro.</div>`;
      return;
    }

    const html = groups
      .map((group) => {
        const waiters = Array.isArray(group.waiters) ? group.waiters : [];
        const waiterCards = waiters.length
          ? waiters
              .map((waiter) => {
                const code = escapeHtml(waiter.code || "");
                const name = escapeHtml(waiter.name || "");
                return `
                  <article class="history-card">
                    <div class="history-card-main">
                      <strong>${code}</strong>
                      <span>${name}</span>
                    </div>
                    <div class="history-card-actions">
                      <a class="btn btn-alt btn-small" href="/api/waiters/labels.pdf?codes=${encodeURIComponent(waiter.code || "")}&branding=${encodeURIComponent(group.branding || "")}" target="_blank" rel="noopener noreferrer">QR</a>
                    </div>
                  </article>
                `;
              })
              .join("")
          : `<div class="history-empty">No hay meseros en este branding.</div>`;
        return `
          <section class="history-group">
            <div class="history-group-head">
              <strong>${escapeHtml(group.label || group.branding || "")}</strong>
              <span>${waiters.length} mesero(s)</span>
            </div>
            <div class="history-list">${waiterCards}</div>
          </section>
        `;
      })
      .join("");
    waiterHistoryList.innerHTML = html;
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

  async function loadWaiterHistory(query = "") {
    if (!waiterHistoryMsg || !waiterHistoryList) {
      return;
    }
    waiterHistoryMsg.textContent = "Cargando meseros...";
    const qs = query ? `?q=${encodeURIComponent(query.trim().toUpperCase())}` : "";
    const res = await fetch(`/api/waiters/grouped${qs}`);
    const data = await res.json().catch(() => ({
      ok: false,
      error: "Error del servidor al cargar meseros",
    }));
    if (!res.ok || !data.ok) {
      waiterHistoryMsg.textContent = data.error || "Error al cargar meseros";
      renderWaiterHistory([]);
      return;
    }
    renderWaiterHistory(data.groups || []);
    const total = (data.groups || []).reduce((sum, group) => sum + ((group.waiters || []).length), 0);
    waiterHistoryMsg.textContent = `${total} mesero(s) encontrados.`;
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

  function closeWaiterHistoryModal() {
    if (!waiterHistoryModal) {
      return;
    }
    waiterHistoryModal.classList.add("hidden");
    waiterHistoryModal.setAttribute("aria-hidden", "true");
  }

  async function openWaiterHistoryModal() {
    if (!waiterHistoryModal) {
      return;
    }
    waiterHistoryModal.classList.remove("hidden");
    waiterHistoryModal.setAttribute("aria-hidden", "false");
    if (waiterHistorySearchInput) {
      waiterHistorySearchInput.value = "";
      window.setTimeout(() => waiterHistorySearchInput.focus(), 40);
    }
    await loadWaiterHistory("");
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
  if (showWaiterHistoryBtn) {
    showWaiterHistoryBtn.addEventListener("click", async () => {
      await openWaiterHistoryModal();
    });
  }
  if (closeWaiterHistoryModalBtn) {
    closeWaiterHistoryModalBtn.addEventListener("click", closeWaiterHistoryModal);
  }
  if (closeWaiterHistoryFooterBtn) {
    closeWaiterHistoryFooterBtn.addEventListener("click", closeWaiterHistoryModal);
  }
  if (waiterHistoryModal) {
    waiterHistoryModal.addEventListener("click", (event) => {
      if (event.target.dataset.closeWaiterHistoryModal === "1") {
        closeWaiterHistoryModal();
      }
    });
  }
  if (waiterHistorySearchInput) {
    waiterHistorySearchInput.addEventListener("input", () => {
      waiterHistorySearchInput.value = waiterHistorySearchInput.value.toUpperCase();
      if (waiterHistorySearchTimer) {
        clearTimeout(waiterHistorySearchTimer);
      }
      waiterHistorySearchTimer = window.setTimeout(() => {
        loadWaiterHistory(waiterHistorySearchInput.value);
      }, 180);
    });
  }
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && batchHistoryModal && !batchHistoryModal.classList.contains("hidden")) {
      closeBatchHistoryModal();
    }
    if (event.key === "Escape" && waiterHistoryModal && !waiterHistoryModal.classList.contains("hidden")) {
      closeWaiterHistoryModal();
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
    const priceValue = Number(price.value);
    if (!Number.isFinite(priceValue) || priceValue <= 0) {
      batchMsg.textContent = "Precio invalido. Ingresa un valor mayor a 0.";
      return;
    }

    const payload = {
      day_code: `D${dayValue}`,
      flavor_prefix: flavorPrefix.value.trim().toUpperCase(),
      flavor: flavorName.value.trim().toUpperCase(),
      quantity: Number(quantity.value),
      price: priceValue,
      size: size.value.trim().toUpperCase(),
      actor_name: actorName.value.trim(),
      notes: notes.value.trim(),
      start_number: requestedStartRaw || "auto",
      admin_actions_pin: startNumberUnlocked ? startNumberAdminPin.value.trim() : "",
    };

    const res = await fetch("/api/batches/generate", {
      method: "POST",
      headers: jsonHeaders(),
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
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({
        ok: false,
        error: "Error del servidor al crear mesero",
      }));
      if (!res.ok || !data.ok) {
        waiterMsg.textContent = data.error || "Error al crear mesero";
        return;
      }
      waiterMsg.textContent = `OK ${data.waiter.code} - ${data.waiter.name}`;
      waiterPdfLink.href = data.labels_pdf_url;
      waiterPdfLink.textContent = `Descargar QR ${data.waiter.code}`;
      waiterPdfLink.classList.remove("hidden");
      waiterName.value = "";
      if (waiterHistoryModal && !waiterHistoryModal.classList.contains("hidden")) {
        await loadWaiterHistory(waiterHistorySearchInput ? waiterHistorySearchInput.value : "");
      }
    });
  }
})();
