(function () {
  const pinInput = document.getElementById("adminPin");
  const verifyPinBtn = document.getElementById("verifyPinBtn");
  const pinStatus = document.getElementById("pinStatus");
  const pizzaIdInput = document.getElementById("pizzaIdInput");
  const adminStatusSelect = document.getElementById("adminStatusSelect");
  const setStatusBtn = document.getElementById("setStatusBtn");
  const statusMsg = document.getElementById("statusMsg");
  const flavorNameInput = document.getElementById("flavorNameInput");
  const flavorPrefixInput = document.getElementById("flavorPrefixInput");
  const createFlavorBtn = document.getElementById("createFlavorBtn");
  const flavorMsg = document.getElementById("flavorMsg");
  const flavorTableBody = document.getElementById("flavorTableBody");
  const flavorModal = document.getElementById("flavorModal");
  const closeFlavorModalBtn = document.getElementById("closeFlavorModalBtn");
  const cancelFlavorBtn = document.getElementById("cancelFlavorBtn");
  const saveFlavorBtn = document.getElementById("saveFlavorBtn");
  const editFlavorNameInput = document.getElementById("editFlavorNameInput");
  const editFlavorPrefixInput = document.getElementById("editFlavorPrefixInput");
  const editFlavorMsg = document.getElementById("editFlavorMsg");
  const showInactiveFlavorsBtn = document.getElementById("showInactiveFlavorsBtn");
  const inactiveFlavorsModal = document.getElementById("inactiveFlavorsModal");
  const closeInactiveFlavorsModalBtn = document.getElementById("closeInactiveFlavorsModalBtn");
  const closeInactiveFlavorFooterBtn = document.getElementById("closeInactiveFlavorFooterBtn");
  const inactiveFlavorSearchInput = document.getElementById("inactiveFlavorSearchInput");
  const inactiveFlavorMsg = document.getElementById("inactiveFlavorMsg");
  const inactiveFlavorList = document.getElementById("inactiveFlavorList");
  const confirmActionModal = document.getElementById("confirmActionModal");
  const confirmActionText = document.getElementById("confirmActionText");
  const closeConfirmActionModalBtn = document.getElementById("closeConfirmActionModalBtn");
  const confirmActionCancelBtn = document.getElementById("confirmActionCancelBtn");
  const confirmActionOkBtn = document.getElementById("confirmActionOkBtn");
  const transferStartId = document.getElementById("transferStartId");
  const transferEndId = document.getElementById("transferEndId");
  const transferNote = document.getElementById("transferNote");
  const transferBtn = document.getElementById("transferBtn");
  const returnBtn = document.getElementById("returnBtn");
  const transferMsg = document.getElementById("transferMsg");
  const undoBtn = document.getElementById("undoBtn");
  const undoMsg = document.getElementById("undoMsg");

  let pinVerified = false;
  let editingFlavorId = null;
  let inactiveSearchTimer = null;
  let confirmActionResolve = null;

  function setPinState(verified, text) {
    pinVerified = verified;
    pinStatus.textContent = text;
    pinStatus.style.color = verified ? "#14532d" : "#7f1d1d";
    setStatusBtn.disabled = !verified;
    if (createFlavorBtn) {
      createFlavorBtn.disabled = !verified;
    }
    if (transferBtn) {
      transferBtn.disabled = !verified;
    }
    if (returnBtn) {
      returnBtn.disabled = !verified;
    }
    undoBtn.disabled = !verified;
  }

  async function verifyPin() {
    const pin = pinInput.value.trim();
    if (!pin) {
      setPinState(false, "PIN requerido");
      return false;
    }

    const res = await fetch("/api/admin/verify-pin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: pin }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setPinState(false, data.error || "PIN invalido");
      return false;
    }
    setPinState(true, "PIN verificado");
    return true;
  }

  verifyPinBtn.addEventListener("click", async () => {
    await verifyPin();
  });

  pinInput.addEventListener("input", () => {
    setPinState(false, "Bloqueado");
  });
  pizzaIdInput.addEventListener("input", () => {
    pizzaIdInput.value = pizzaIdInput.value.toUpperCase();
  });
  if (flavorNameInput) {
    flavorNameInput.addEventListener("input", () => {
      flavorNameInput.value = flavorNameInput.value.toUpperCase();
    });
  }
  if (flavorPrefixInput) {
    flavorPrefixInput.addEventListener("input", () => {
      flavorPrefixInput.value = flavorPrefixInput.value.toUpperCase();
    });
  }
  if (editFlavorNameInput) {
    editFlavorNameInput.addEventListener("input", () => {
      editFlavorNameInput.value = editFlavorNameInput.value.toUpperCase();
    });
  }
  if (editFlavorPrefixInput) {
    editFlavorPrefixInput.addEventListener("input", () => {
      editFlavorPrefixInput.value = editFlavorPrefixInput.value.toUpperCase();
    });
  }
  if (transferStartId) {
    transferStartId.addEventListener("input", () => {
      transferStartId.value = transferStartId.value.toUpperCase();
    });
  }
  if (transferEndId) {
    transferEndId.addEventListener("input", () => {
      transferEndId.value = transferEndId.value.toUpperCase();
    });
  }

  function getFlavorActionsMenuMarkup(flavor) {
    return `
      <div class="row-action-menu">
        <button
          type="button"
          class="row-action-trigger"
          aria-haspopup="true"
          aria-expanded="false"
          aria-label="Abrir acciones"
        >
          <img src="/static/assets/icons/menu-puntos-vertical.svg" alt="" class="row-action-trigger-icon">
        </button>
        <div class="row-action-dropdown hidden">
          <button
            type="button"
            class="row-action-item edit-flavor-btn"
            data-flavor-id="${flavor.id}"
            data-flavor-name="${flavor.name}"
            data-flavor-prefix="${flavor.prefix}"
          >
            <img src="/static/assets/icons/editar.svg" alt="" class="row-action-icon">
            <span>Editar</span>
          </button>
          <button
            type="button"
            class="row-action-item row-action-item-warn deactivate-flavor-btn"
            data-flavor-id="${flavor.id}"
            data-flavor-name="${flavor.name}"
          >
            <img src="/static/assets/icons/cerrar.svg" alt="" class="row-action-icon">
            <span>Desactivar</span>
          </button>
        </div>
      </div>
    `;
  }

  function appendFlavorRow(flavor) {
    if (!flavorTableBody) {
      return;
    }
    const emptyRow = flavorTableBody.querySelector("td[colspan='3']");
    if (emptyRow) {
      emptyRow.parentElement.remove();
    }
    const tr = document.createElement("tr");
    tr.dataset.flavorId = flavor.id;
    tr.dataset.flavorName = flavor.name;
    tr.dataset.flavorPrefix = flavor.prefix;
    tr.innerHTML = `
      <td data-label="Sabor" class="flavor-name-cell">${flavor.name}</td>
      <td data-label="Prefijo" class="flavor-prefix-cell">${flavor.prefix}</td>
      <td data-label="Acciones" class="flavor-actions-cell">
        ${getFlavorActionsMenuMarkup(flavor)}
      </td>
    `;
    flavorTableBody.appendChild(tr);
  }

  function updateFlavorRow(flavor) {
    if (!flavorTableBody) {
      return;
    }
    const row = flavorTableBody.querySelector(`tr[data-flavor-id="${flavor.id}"]`);
    if (!row) {
      appendFlavorRow(flavor);
      return;
    }
    row.dataset.flavorName = flavor.name;
    row.dataset.flavorPrefix = flavor.prefix;
    const nameCell = row.querySelector(".flavor-name-cell");
    const prefixCell = row.querySelector(".flavor-prefix-cell");
    const editBtn = row.querySelector(".edit-flavor-btn");
    const deactivateBtn = row.querySelector(".deactivate-flavor-btn");
    if (nameCell) {
      nameCell.textContent = flavor.name;
    }
    if (prefixCell) {
      prefixCell.textContent = flavor.prefix;
    }
    if (editBtn) {
      editBtn.dataset.flavorId = flavor.id;
      editBtn.dataset.flavorName = flavor.name;
      editBtn.dataset.flavorPrefix = flavor.prefix;
    }
    if (deactivateBtn) {
      deactivateBtn.dataset.flavorId = flavor.id;
      deactivateBtn.dataset.flavorName = flavor.name;
    }
  }

  function ensureFlavorEmptyState() {
    if (!flavorTableBody) {
      return;
    }
    const rows = flavorTableBody.querySelectorAll("tr[data-flavor-id]");
    if (rows.length > 0) {
      return;
    }
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="3">Sin sabores configurados.</td>`;
    flavorTableBody.appendChild(tr);
  }

  function removeFlavorRow(flavorId) {
    if (!flavorTableBody) {
      return;
    }
    const row = flavorTableBody.querySelector(`tr[data-flavor-id="${flavorId}"]`);
    if (row) {
      row.remove();
    }
    ensureFlavorEmptyState();
  }

  function renderInactiveFlavors(flavors) {
    if (!inactiveFlavorList) {
      return;
    }
    if (!Array.isArray(flavors) || flavors.length === 0) {
      inactiveFlavorList.innerHTML = `<div class="inactive-empty">No hay sabores desactivados para este filtro.</div>`;
      return;
    }
    inactiveFlavorList.innerHTML = flavors
      .map(
        (flavor) => `
          <article class="inactive-flavor-card" data-inactive-flavor-id="${flavor.id}">
            <div class="inactive-flavor-copy">
              <strong>${flavor.name}</strong>
              <span>Prefijo ${flavor.prefix}</span>
            </div>
            <div class="action-stack">
              <button type="button" class="btn btn-alt btn-small reactivate-flavor-btn" data-flavor-id="${flavor.id}" data-flavor-name="${flavor.name}">
                Reactivar
              </button>
              <button type="button" class="btn btn-danger btn-small hard-delete-flavor-btn" data-flavor-id="${flavor.id}" data-flavor-name="${flavor.name}">
                Eliminar
              </button>
            </div>
          </article>
        `
      )
      .join("");
  }

  async function loadInactiveFlavors(query = "") {
    if (!inactiveFlavorList || !inactiveFlavorMsg) {
      return;
    }
    inactiveFlavorMsg.textContent = "Cargando sabores desactivados...";
    const qs = query ? `?q=${encodeURIComponent(query.trim().toUpperCase())}` : "";
    const res = await fetch(`/api/flavors/inactive${qs}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      inactiveFlavorMsg.textContent = data.error || "Error al cargar sabores desactivados";
      renderInactiveFlavors([]);
      return;
    }
    renderInactiveFlavors(data.flavors || []);
    inactiveFlavorMsg.textContent = `${(data.flavors || []).length} sabor(es) desactivado(s).`;
  }

  function closeInactiveFlavorsModal() {
    if (!inactiveFlavorsModal) {
      return;
    }
    inactiveFlavorsModal.classList.add("hidden");
    inactiveFlavorsModal.setAttribute("aria-hidden", "true");
  }

  async function openInactiveFlavorsModal() {
    if (!inactiveFlavorsModal) {
      return;
    }
    inactiveFlavorsModal.classList.remove("hidden");
    inactiveFlavorsModal.setAttribute("aria-hidden", "false");
    if (inactiveFlavorSearchInput) {
      inactiveFlavorSearchInput.value = "";
      window.setTimeout(() => inactiveFlavorSearchInput.focus(), 40);
    }
    await loadInactiveFlavors("");
  }

  function closeConfirmActionModal(result = false) {
    if (!confirmActionModal) {
      return;
    }
    confirmActionModal.classList.add("hidden");
    confirmActionModal.setAttribute("aria-hidden", "true");
    if (confirmActionResolve) {
      confirmActionResolve(result);
      confirmActionResolve = null;
    }
  }

  function askForConfirmation(message, confirmLabel = "Confirmar", confirmClass = "btn") {
    if (!confirmActionModal || !confirmActionText || !confirmActionOkBtn) {
      return Promise.resolve(false);
    }
    confirmActionText.textContent = message;
    confirmActionOkBtn.textContent = confirmLabel;
    confirmActionOkBtn.className = confirmClass;
    confirmActionModal.classList.remove("hidden");
    confirmActionModal.setAttribute("aria-hidden", "false");
    return new Promise((resolve) => {
      confirmActionResolve = resolve;
      window.setTimeout(() => confirmActionOkBtn.focus(), 40);
    });
  }

  function closeFlavorModal() {
    if (!flavorModal) {
      return;
    }
    flavorModal.classList.add("hidden");
    flavorModal.setAttribute("aria-hidden", "true");
    editingFlavorId = null;
    if (editFlavorMsg) {
      editFlavorMsg.textContent = "";
    }
  }

  function openFlavorModal(flavorId, name, prefix) {
    if (!flavorModal || !editFlavorNameInput || !editFlavorPrefixInput) {
      return;
    }
    editingFlavorId = flavorId;
    editFlavorNameInput.value = (name || "").toUpperCase();
    editFlavorPrefixInput.value = (prefix || "").toUpperCase();
    if (editFlavorMsg) {
      editFlavorMsg.textContent = "";
    }
    flavorModal.classList.remove("hidden");
    flavorModal.setAttribute("aria-hidden", "false");
    window.setTimeout(() => editFlavorNameInput.focus(), 40);
  }

  if (createFlavorBtn && flavorNameInput && flavorPrefixInput && flavorMsg) {
    createFlavorBtn.addEventListener("click", async () => {
      flavorMsg.textContent = "";
      if (!pinVerified && !(await verifyPin())) {
        flavorMsg.textContent = "No autorizado. Verifica PIN.";
        return;
      }
      const payload = {
        name: flavorNameInput.value.trim().toUpperCase(),
        prefix: flavorPrefixInput.value.trim().toUpperCase(),
      };
      if (!payload.name || !payload.prefix) {
        flavorMsg.textContent = "Nombre y prefijo son requeridos.";
        return;
      }
      const res = await fetch("/api/flavors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        flavorMsg.textContent = data.error || "Error al crear sabor";
        return;
      }
      appendFlavorRow(data.flavor);
      flavorMsg.textContent = `Sabor creado: ${data.flavor.name}`;
      flavorNameInput.value = "";
      flavorPrefixInput.value = "";
    });
  }

  if (flavorTableBody) {
    flavorTableBody.addEventListener("click", (event) => {
      const triggerButton = event.target.closest(".row-action-trigger");
      if (triggerButton) {
        const menu = triggerButton.closest(".row-action-menu");
        const dropdown = menu ? menu.querySelector(".row-action-dropdown") : null;
        const isOpen = dropdown && !dropdown.classList.contains("hidden");
        document.querySelectorAll(".row-action-dropdown").forEach((node) => node.classList.add("hidden"));
        document.querySelectorAll(".row-action-trigger").forEach((node) => node.setAttribute("aria-expanded", "false"));
        if (dropdown && !isOpen) {
          dropdown.classList.remove("hidden");
          triggerButton.setAttribute("aria-expanded", "true");
        }
        return;
      }
      const editButton = event.target.closest(".edit-flavor-btn");
      if (editButton) {
        document.querySelectorAll(".row-action-dropdown").forEach((node) => node.classList.add("hidden"));
        document.querySelectorAll(".row-action-trigger").forEach((node) => node.setAttribute("aria-expanded", "false"));
        openFlavorModal(editButton.dataset.flavorId, editButton.dataset.flavorName, editButton.dataset.flavorPrefix);
        return;
      }
      const deactivateButton = event.target.closest(".deactivate-flavor-btn");
      if (!deactivateButton) {
        return;
      }
      const flavorId = deactivateButton.dataset.flavorId;
      const flavorName = deactivateButton.dataset.flavorName || flavorId;
      window.setTimeout(async () => {
        document.querySelectorAll(".row-action-dropdown").forEach((node) => node.classList.add("hidden"));
        document.querySelectorAll(".row-action-trigger").forEach((node) => node.setAttribute("aria-expanded", "false"));
        flavorMsg.textContent = "";
        if (!pinVerified && !(await verifyPin())) {
          flavorMsg.textContent = "No autorizado. Verifica PIN.";
          return;
        }
        const confirmed = await askForConfirmation(`Desactivar sabor ${flavorName}?`, "Desactivar", "btn btn-warn");
        if (!confirmed) {
          return;
        }
        const res = await fetch(`/api/flavors/${flavorId}/deactivate`, {
          method: "POST",
        });
        const data = await res.json();
        if (!res.ok || !data.ok) {
          flavorMsg.textContent = data.error || "Error al desactivar sabor";
          return;
        }
        removeFlavorRow(flavorId);
        flavorMsg.textContent = `Sabor desactivado: ${flavorName}`;
      }, 0);
    });
  }

  if (saveFlavorBtn && editFlavorNameInput && editFlavorPrefixInput && editFlavorMsg) {
    saveFlavorBtn.addEventListener("click", async () => {
      editFlavorMsg.textContent = "";
      if (!editingFlavorId) {
        editFlavorMsg.textContent = "Sabor invalido.";
        return;
      }
      if (!pinVerified && !(await verifyPin())) {
        editFlavorMsg.textContent = "No autorizado. Verifica PIN.";
        return;
      }
      const payload = {
        name: editFlavorNameInput.value.trim().toUpperCase(),
        prefix: editFlavorPrefixInput.value.trim().toUpperCase(),
      };
      if (!payload.name || !payload.prefix) {
        editFlavorMsg.textContent = "Nombre y prefijo son requeridos.";
        return;
      }
      const res = await fetch(`/api/flavors/${editingFlavorId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        editFlavorMsg.textContent = data.error || "Error al editar sabor";
        return;
      }
      updateFlavorRow(data.flavor);
      flavorMsg.textContent = `Sabor actualizado: ${data.flavor.name}`;
      closeFlavorModal();
    });
  }

  if (showInactiveFlavorsBtn) {
    showInactiveFlavorsBtn.addEventListener("click", async () => {
      if (!pinVerified && !(await verifyPin())) {
        flavorMsg.textContent = "No autorizado. Verifica PIN.";
        return;
      }
      await openInactiveFlavorsModal();
    });
  }

  if (closeFlavorModalBtn) {
    closeFlavorModalBtn.addEventListener("click", closeFlavorModal);
  }
  if (cancelFlavorBtn) {
    cancelFlavorBtn.addEventListener("click", closeFlavorModal);
  }
  if (flavorModal) {
    flavorModal.addEventListener("click", (event) => {
      if (event.target.dataset.closeFlavorModal === "1") {
        closeFlavorModal();
      }
    });
  }
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && flavorModal && !flavorModal.classList.contains("hidden")) {
      closeFlavorModal();
    }
    if (event.key === "Escape" && inactiveFlavorsModal && !inactiveFlavorsModal.classList.contains("hidden")) {
      closeInactiveFlavorsModal();
    }
    if (event.key === "Escape" && confirmActionModal && !confirmActionModal.classList.contains("hidden")) {
      closeConfirmActionModal(false);
    }
    if (event.key === "Escape") {
      document.querySelectorAll(".row-action-dropdown").forEach((node) => node.classList.add("hidden"));
      document.querySelectorAll(".row-action-trigger").forEach((node) => node.setAttribute("aria-expanded", "false"));
    }
  });
  document.addEventListener("click", (event) => {
    if (event.target.closest(".row-action-menu")) {
      return;
    }
    document.querySelectorAll(".row-action-dropdown").forEach((node) => node.classList.add("hidden"));
    document.querySelectorAll(".row-action-trigger").forEach((node) => node.setAttribute("aria-expanded", "false"));
  });
  if (closeConfirmActionModalBtn) {
    closeConfirmActionModalBtn.addEventListener("click", () => closeConfirmActionModal(false));
  }
  if (confirmActionCancelBtn) {
    confirmActionCancelBtn.addEventListener("click", () => closeConfirmActionModal(false));
  }
  if (confirmActionOkBtn) {
    confirmActionOkBtn.addEventListener("click", () => closeConfirmActionModal(true));
  }
  if (confirmActionModal) {
    confirmActionModal.addEventListener("click", (event) => {
      if (event.target.dataset.closeConfirmModal === "1") {
        closeConfirmActionModal(false);
      }
    });
  }

  if (closeInactiveFlavorsModalBtn) {
    closeInactiveFlavorsModalBtn.addEventListener("click", closeInactiveFlavorsModal);
  }
  if (closeInactiveFlavorFooterBtn) {
    closeInactiveFlavorFooterBtn.addEventListener("click", closeInactiveFlavorsModal);
  }
  if (inactiveFlavorsModal) {
    inactiveFlavorsModal.addEventListener("click", (event) => {
      if (event.target.dataset.closeInactiveModal === "1") {
        closeInactiveFlavorsModal();
      }
    });
  }
  if (inactiveFlavorSearchInput) {
    inactiveFlavorSearchInput.addEventListener("input", () => {
      inactiveFlavorSearchInput.value = inactiveFlavorSearchInput.value.toUpperCase();
      if (inactiveSearchTimer) {
        clearTimeout(inactiveSearchTimer);
      }
      inactiveSearchTimer = window.setTimeout(() => {
        loadInactiveFlavors(inactiveFlavorSearchInput.value);
      }, 180);
    });
  }
  if (inactiveFlavorList) {
    inactiveFlavorList.addEventListener("click", async (event) => {
      const reactivateButton = event.target.closest(".reactivate-flavor-btn");
      if (reactivateButton) {
        if (!pinVerified && !(await verifyPin())) {
          inactiveFlavorMsg.textContent = "No autorizado. Verifica PIN.";
          return;
        }
        const flavorId = reactivateButton.dataset.flavorId;
        const flavorName = reactivateButton.dataset.flavorName || flavorId;
        const res = await fetch(`/api/flavors/${flavorId}/reactivate`, { method: "POST" });
        const data = await res.json();
        if (!res.ok || !data.ok) {
          inactiveFlavorMsg.textContent = data.error || "Error al reactivar sabor";
          return;
        }
        appendFlavorRow(data.flavor);
        inactiveFlavorMsg.textContent = `Sabor reactivado: ${flavorName}`;
        await loadInactiveFlavors(inactiveFlavorSearchInput ? inactiveFlavorSearchInput.value : "");
        return;
      }

      const deleteButton = event.target.closest(".hard-delete-flavor-btn");
      if (!deleteButton) {
        return;
      }
      if (!pinVerified && !(await verifyPin())) {
        inactiveFlavorMsg.textContent = "No autorizado. Verifica PIN.";
        return;
      }
      const flavorId = deleteButton.dataset.flavorId;
      const flavorName = deleteButton.dataset.flavorName || flavorId;
      const confirmed = await askForConfirmation(
        `Eliminar definitivamente sabor ${flavorName}? Esta accion no se puede deshacer.`,
        "Eliminar",
        "btn btn-danger"
      );
      if (!confirmed) {
        return;
      }
      const res = await fetch(`/api/flavors/${flavorId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        inactiveFlavorMsg.textContent = data.error || "Error al eliminar sabor";
        return;
      }
      inactiveFlavorMsg.textContent = `Sabor eliminado: ${flavorName}`;
      await loadInactiveFlavors(inactiveFlavorSearchInput ? inactiveFlavorSearchInput.value : "");
    });
  }

  setStatusBtn.addEventListener("click", async () => {
    statusMsg.textContent = "";
    if (!pinVerified && !(await verifyPin())) {
      statusMsg.textContent = "No autorizado. Verifica PIN.";
      return;
    }

    const payload = {
      id: pizzaIdInput.value.trim().toUpperCase(),
      to_status: adminStatusSelect.value,
      pin: pinInput.value.trim(),
    };
    if (!payload.id) {
      statusMsg.textContent = "ID requerido.";
      return;
    }

    const res = await fetch("/api/admin/status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      statusMsg.textContent = data.error || "Error al aplicar estado";
      return;
    }
    statusMsg.textContent = `OK ${data.pizza.id} => ${data.pizza.status}`;
    pizzaIdInput.value = "";
  });

  undoBtn.addEventListener("click", async () => {
    undoMsg.textContent = "";
    if (!pinVerified && !(await verifyPin())) {
      undoMsg.textContent = "No autorizado. Verifica PIN.";
      return;
    }

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
      undoMsg.textContent = data.error || "Error en deshacer";
      return;
    }
    undoMsg.textContent = data.message;
  });

  async function submitLocationMove(url, successFallback) {
    transferMsg.textContent = "";
    if (!pinVerified && !(await verifyPin())) {
      transferMsg.textContent = "No autorizado. Verifica PIN.";
      return;
    }
    const payload = {
      start_id: transferStartId.value.trim().toUpperCase(),
      end_id: transferEndId.value.trim().toUpperCase(),
      note: transferNote ? transferNote.value.trim() : "",
      pin: pinInput.value.trim(),
    };
    if (!payload.start_id || !payload.end_id) {
      transferMsg.textContent = "ID inicial y final son requeridos.";
      return;
    }
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      transferMsg.textContent = data.error || "Error en movimiento entre locales";
      return;
    }
    transferMsg.textContent = data.message || successFallback;
    transferStartId.value = "";
    transferEndId.value = "";
    if (transferNote) {
      transferNote.value = "";
    }
  }

  if (transferBtn && transferStartId && transferEndId && transferMsg) {
    transferBtn.addEventListener("click", async () => {
      await submitLocationMove("/api/admin/transfer-to-secondary", "Transferencia registrada.");
    });
  }

  if (returnBtn && transferStartId && transferEndId && transferMsg) {
    returnBtn.addEventListener("click", async () => {
      await submitLocationMove("/api/admin/return-to-main", "Devolucion registrada.");
    });
  }

  setPinState(false, "Bloqueado");
})();
