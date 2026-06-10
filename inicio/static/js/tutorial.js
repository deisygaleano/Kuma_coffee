(function () {
  const overlay = document.getElementById("tutorial-overlay");
  if (!overlay) return;

  const pasos = Array.from(document.querySelectorAll(".tutorial-paso"));
  const dots = Array.from(document.querySelectorAll(".tutorial-dot"));
  const btnSiguiente = document.getElementById("tutorial-siguiente");
  const btnOmitir = document.getElementById("tutorial-omitir");
  const btnCerrar = document.getElementById("tutorial-cerrar");
  let pasoActual = 0;

  function mostrarPaso(idx) {
    pasos.forEach((p) => p.classList.remove("activo"));
    dots.forEach((d) => d.classList.remove("tutorial-dot--activo"));
    pasos[idx].classList.add("activo");
    dots[idx].classList.add("tutorial-dot--activo");
    const esUltimo = idx === pasos.length - 1;
    btnSiguiente.textContent = esUltimo ? "¡Empezar!" : "Siguiente";
  }

  function cerrar() {
    overlay.style.transition = "opacity 0.22s";
    overlay.style.opacity = "0";
    setTimeout(() => overlay.remove(), 240);
  }

  function marcarVisto() {
    const csrf =
      document.cookie
        .split("; ")
        .find((r) => r.startsWith("csrftoken="))
        ?.split("=")[1] || "";
    fetch("/cuentas/tutorial-visto", {
      method: "POST",
      headers: { "X-CSRFToken": csrf },
      credentials: "same-origin",
    }).catch(() => {});
    cerrar();
  }

  btnSiguiente.addEventListener("click", function () {
    if (pasoActual < pasos.length - 1) {
      pasoActual++;
      mostrarPaso(pasoActual);
    } else {
      marcarVisto();
    }
  });

  btnOmitir.addEventListener("click", marcarVisto);
  btnCerrar.addEventListener("click", marcarVisto);

  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) marcarVisto();
  });

  mostrarPaso(0);
})();
