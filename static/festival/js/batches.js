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
  const flavorToPrefix = {
    DIAVOLA: "DIA",
    "DIAVOLA A MI MANERA": "DAM",
    "JAMON Y QUESO": "JYQ",
    "HAMBURGUESA CLASICA": "BUR",
  };
  let startNumberUnlocked = false;

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

  flavorName.addEventListener("change", syncPrefixFromFlavor);
  startNumberAdminPin.addEventListener("input", () => {
    if (!startNumberAdminPin.value.trim() && startNumberUnlocked) {
      setStartNumberMode(false);
    }
  });
  unlockStartNumberBtn.addEventListener("click", () => {
    if (startNumberUnlocked) {
      setStartNumberMode(false);
      return;
    }
    const pin = startNumberAdminPin.value.trim();
    if (!pin) {
      batchMsg.textContent = "Ingresa PIN admin para habilitar Nro inicial manual.";
      return;
    }
    setStartNumberMode(true);
    batchMsg.textContent = "";
  });
  syncPrefixFromFlavor();
  setStartNumberMode(false);

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
