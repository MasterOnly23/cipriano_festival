(function () {
  const mode = (window.STATION_MODE || "SALES").toUpperCase();
  const currentOperator = (window.CURRENT_OPERATOR || "Operador").trim();
  const input = document.getElementById("scanInput");
  const pinInput = document.getElementById("overridePin");
  const feedback = document.getElementById("feedback");
  const pizzaId = document.getElementById("pizzaId");
  const pizzaFlavor = document.getElementById("pizzaFlavor");
  const pizzaPrice = document.getElementById("pizzaPrice");
  const pizzaStatus = document.getElementById("pizzaStatus");
  const pizzaTime = document.getElementById("pizzaTime");
  const openCameraBtn = document.getElementById("openCameraBtn");
  const closeCameraBtn = document.getElementById("closeCameraBtn");
  const cameraPanel = document.getElementById("cameraPanel");
  const nativeReaderWrap = document.getElementById("nativeReaderWrap");
  const cameraVideo = document.getElementById("cameraVideo");
  const cameraCanvas = document.getElementById("cameraCanvas");
  const qrReader = document.getElementById("qrReader");
  const cameraMsg = document.getElementById("cameraMsg");
  const activeWaiterName = document.getElementById("activeWaiterName");
  const activeWaiterCode = document.getElementById("activeWaiterCode");
  const clearWaiterBtn = document.getElementById("clearWaiterBtn");
  const pendingPizzaId = document.getElementById("pendingPizzaId");
  const clearPendingBtn = document.getElementById("clearPendingBtn");

  const canUseNativeCamera = !!(navigator.mediaDevices && window.BarcodeDetector);
  const canUseHtml5Qrcode = !!(navigator.mediaDevices && window.Html5Qrcode);

  let cameraStream = null;
  let detector = null;
  let html5Scanner = null;
  let scanning = false;
  let usingHtml5Reader = false;
  let isProcessingCode = false;
  let rafId = null;
  let waitersByCode = {};
  let currentWaiter = null;
  let pendingPizza = null;
  let pendingTimerId = null;
  const pendingTimeoutMs = 45000;

  function keepFocus() {
    if (document.activeElement !== input) {
      input.focus();
    }
  }

  function beep(ok) {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = ok ? 880 : 220;
    gain.gain.value = 0.07;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.08);
  }

  function vibe(ok) {
    if (navigator.vibrate) {
      navigator.vibrate(ok ? 50 : [100, 40, 100]);
    }
  }

  function paintResult(data, isError) {
    feedback.className = `feedback ${isError ? "error" : "ok"}`;
    feedback.textContent = isError ? data.error : data.message;
    if (isError) {
      pizzaStatus.className = "status-pill";
      return;
    }
    const p = data.pizza;
    pizzaId.textContent = p.id || "-";
    pizzaFlavor.textContent = p.flavor || "-";
    pizzaPrice.textContent = p.price || "-";
    pizzaStatus.textContent = p.status || "-";
    const statusClass = (p.status || "").toLowerCase();
    pizzaStatus.className = `status-pill status-${statusClass}`;
    pizzaTime.textContent = new Date().toLocaleTimeString();
  }

  function paintNeutral(message) {
    feedback.className = "feedback neutral";
    feedback.textContent = message;
  }

  function renderWaiterState() {
    if (!activeWaiterName || !activeWaiterCode) {
      return;
    }
    activeWaiterName.textContent = currentWaiter ? currentWaiter.name : "-";
    activeWaiterCode.textContent = currentWaiter ? currentWaiter.code : "-";
  }

  function clearPendingPizza(showMessage = false) {
    pendingPizza = null;
    if (pendingTimerId) {
      clearTimeout(pendingTimerId);
      pendingTimerId = null;
    }
    if (pendingPizzaId) {
      pendingPizzaId.textContent = "-";
    }
    if (showMessage) {
      paintNeutral("Pendiente cancelada.");
    }
  }

  function setPendingPizza(code) {
    pendingPizza = code;
    if (pendingPizzaId) {
      pendingPizzaId.textContent = code;
    }
    if (pendingTimerId) {
      clearTimeout(pendingTimerId);
    }
    pendingTimerId = setTimeout(() => {
      clearPendingPizza();
      paintNeutral("Pendiente expirada. Escanea nuevamente.");
    }, pendingTimeoutMs);
  }

  async function loadWaiters() {
    if (mode !== "SALES") {
      return;
    }
    try {
      const res = await fetch("/api/waiters");
      const data = await res.json();
      if (!res.ok || !data.ok || !Array.isArray(data.waiters)) {
        return;
      }
      const indexed = {};
      for (const waiter of data.waiters) {
        indexed[(waiter.code || "").toUpperCase()] = waiter;
      }
      waitersByCode = indexed;
    } catch (err) {
      // ignore waiter preload errors
    }
  }

  async function sendScan(code) {
    const payload = {
      id: code.trim().toUpperCase(),
      mode: mode,
      actor_name: currentOperator,
      override_pin: pinInput ? pinInput.value.trim() : "",
      waiter_code: mode === "SALES" && currentWaiter ? currentWaiter.code : "",
    };
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    const ok = res.ok && data.ok;
    paintResult(data, !ok);
    beep(ok);
    vibe(ok);
  }

  async function processCode(code) {
    if (!code) {
      return;
    }
    const normalized = code.trim().toUpperCase();
    input.value = normalized;
    if (mode === "SALES" && normalized.startsWith("W-")) {
      const waiter = waitersByCode[normalized];
      if (!waiter) {
        paintResult({ error: `Mesero no encontrado: ${normalized}` }, true);
        beep(false);
        vibe(false);
        input.value = "";
        keepFocus();
        return;
      }
      currentWaiter = waiter;
      renderWaiterState();
      paintNeutral(`Mesero activo: ${waiter.name} (${waiter.code})`);
      if (pendingPizza) {
        try {
          await sendScan(pendingPizza);
          clearPendingPizza();
        } catch (err) {
          paintResult({ error: "Error de red" }, true);
          beep(false);
          vibe(false);
        }
      } else {
        beep(true);
        vibe(true);
      }
      input.value = "";
      keepFocus();
      return;
    }
    if (mode === "SALES" && !currentWaiter) {
      setPendingPizza(normalized);
      paintNeutral(`Pizza pendiente ${normalized}. Escanea QR de mesero para confirmar venta.`);
      beep(true);
      vibe(true);
      input.value = "";
      keepFocus();
      return;
    }
    try {
      await sendScan(input.value);
    } catch (err) {
      paintResult({ error: "Error de red" }, true);
      beep(false);
      vibe(false);
    } finally {
      input.value = "";
      keepFocus();
    }
  }

  function stopNativeCamera() {
    scanning = false;
    usingHtml5Reader = false;
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    if (cameraStream) {
      for (const track of cameraStream.getTracks()) {
        track.stop();
      }
    }
    cameraStream = null;
  }

  async function stopHtml5Camera() {
    scanning = false;
    usingHtml5Reader = false;
    if (html5Scanner) {
      try {
        await html5Scanner.stop();
      } catch (err) {
        // ignore
      }
      try {
        html5Scanner.clear();
      } catch (err) {
        // ignore
      }
    }
    html5Scanner = null;
  }

  async function stopCamera() {
    stopNativeCamera();
    await stopHtml5Camera();
    qrReader.classList.add("hidden");
    nativeReaderWrap.classList.remove("hidden");
    cameraPanel.classList.add("hidden");
    closeCameraBtn.classList.add("hidden");
    openCameraBtn.classList.remove("hidden");
    cameraMsg.textContent = "";
  }

  async function scanFrameLoop() {
    if (!scanning || !detector) {
      return;
    }
    try {
      const ctx = cameraCanvas.getContext("2d");
      const w = cameraVideo.videoWidth;
      const h = cameraVideo.videoHeight;
      if (w > 0 && h > 0) {
        cameraCanvas.width = w;
        cameraCanvas.height = h;
        ctx.drawImage(cameraVideo, 0, 0, w, h);
        const results = await detector.detect(cameraCanvas);
        if (results && results.length > 0 && results[0].rawValue) {
          const code = results[0].rawValue.trim();
          await stopCamera();
          await processCode(code);
          return;
        }
      }
    } catch (err) {
      cameraMsg.textContent = "No se pudo leer aun. Apunta mejor al QR.";
    }
    rafId = requestAnimationFrame(scanFrameLoop);
  }

  async function startNativeCamera() {
    try {
      detector = new BarcodeDetector({
        formats: ["qr_code", "code_128", "ean_13", "ean_8", "upc_a", "upc_e", "code_39"],
      });
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      cameraVideo.srcObject = cameraStream;
      cameraPanel.classList.remove("hidden");
      closeCameraBtn.classList.remove("hidden");
      openCameraBtn.classList.add("hidden");
      cameraMsg.textContent = "Camara activa (lector nativo). Apunta al QR/codigo.";
      scanning = true;
      rafId = requestAnimationFrame(scanFrameLoop);
      return true;
    } catch (err) {
      return false;
    }
  }

  async function startHtml5FallbackCamera() {
    if (!canUseHtml5Qrcode) {
      return false;
    }
    try {
      nativeReaderWrap.classList.add("hidden");
      qrReader.classList.remove("hidden");
      cameraPanel.classList.remove("hidden");
      closeCameraBtn.classList.remove("hidden");
      openCameraBtn.classList.add("hidden");
      cameraMsg.textContent = "Camara activa (html5-qrcode). Apunta al QR/codigo.";

      html5Scanner = new Html5Qrcode("qrReader");
      usingHtml5Reader = true;
      scanning = true;
      await html5Scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 260, height: 260 } },
        async (decodedText) => {
          if (!decodedText || isProcessingCode) {
            return;
          }
          isProcessingCode = true;
          const code = decodedText.trim();
          await stopCamera();
          await processCode(code);
          isProcessingCode = false;
        },
        () => {
          // ignore scan misses
        }
      );
      return true;
    } catch (err) {
      return false;
    }
  }

  async function startCamera() {
    const nativeStarted = canUseNativeCamera ? await startNativeCamera() : false;
    if (nativeStarted) {
      return;
    }

    const fallbackStarted = await startHtml5FallbackCamera();
    if (fallbackStarted) {
      return;
    }

    cameraMsg.textContent = "No se pudo iniciar camara en este navegador/dispositivo.";
    await stopCamera();
  }

  input.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    const code = input.value;
    if (!code) {
      return;
    }
    await processCode(code);
  });
  input.addEventListener("input", () => {
    input.value = input.value.toUpperCase();
  });

  openCameraBtn.addEventListener("click", async () => {
    await startCamera();
  });

  closeCameraBtn.addEventListener("click", async () => {
    await stopCamera();
    keepFocus();
  });
  if (clearPendingBtn) {
    clearPendingBtn.addEventListener("click", () => {
      clearPendingPizza(true);
      keepFocus();
    });
  }
  if (clearWaiterBtn) {
    clearWaiterBtn.addEventListener("click", () => {
      currentWaiter = null;
      renderWaiterState();
      paintNeutral("Mesero activo limpiado.");
      keepFocus();
    });
  }

  if (!canUseNativeCamera && !canUseHtml5Qrcode) {
    cameraMsg.textContent = "Escaneo por camara no soportado en este navegador.";
  } else if (!canUseNativeCamera && canUseHtml5Qrcode) {
    cameraMsg.textContent = "Se usara html5-qrcode para compatibilidad extra.";
  }

  window.addEventListener("beforeunload", () => {
    stopNativeCamera();
    if (html5Scanner) {
      html5Scanner.stop().catch(() => null);
    }
  });

  setInterval(keepFocus, 800);
  renderWaiterState();
  clearPendingPizza();
  loadWaiters();
  keepFocus();
})();
