(function () {
  const pinInput = document.getElementById("adminPin");
  const verifyPinBtn = document.getElementById("verifyPinBtn");
  const pinStatus = document.getElementById("pinStatus");
  const pizzaIdInput = document.getElementById("pizzaIdInput");
  const adminStatusSelect = document.getElementById("adminStatusSelect");
  const setStatusBtn = document.getElementById("setStatusBtn");
  const statusMsg = document.getElementById("statusMsg");
  const undoBtn = document.getElementById("undoBtn");
  const undoMsg = document.getElementById("undoMsg");

  let pinVerified = false;

  function setPinState(verified, text) {
    pinVerified = verified;
    pinStatus.textContent = text;
    pinStatus.style.color = verified ? "#14532d" : "#7f1d1d";
    setStatusBtn.disabled = !verified;
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

  setPinState(false, "Bloqueado");
})();
