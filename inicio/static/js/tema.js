(function () {
  var STORAGE_KEY = "kuma-tema";

  function obtenerTema() {
    try {
      return localStorage.getItem(STORAGE_KEY) || "oscuro";
    } catch (e) {
      return "oscuro";
    }
  }

  function aplicarTema(tema) {
    var root = document.documentElement;
    var esClaro = tema === "claro";

    if (esClaro) {
      root.setAttribute("data-theme", "light");
    } else {
      root.removeAttribute("data-theme");
    }

    document.querySelectorAll("[data-tema-toggle]").forEach(function (btn) {
      btn.setAttribute("aria-pressed", esClaro ? "true" : "false");
      btn.setAttribute(
        "aria-label",
        esClaro ? "Cambiar a tema oscuro" : "Cambiar a tema claro"
      );
      btn.title = esClaro ? "Tema claro activo" : "Tema oscuro activo";
    });
  }

  function alternarTema() {
    var nuevo = obtenerTema() === "claro" ? "oscuro" : "claro";
    try {
      localStorage.setItem(STORAGE_KEY, nuevo);
    } catch (e) {}
    aplicarTema(nuevo);
  }

  function enlazarToggle() {
    document.querySelectorAll("[data-tema-toggle]").forEach(function (btn) {
      if (btn.dataset.temaListo === "1") return;
      btn.dataset.temaListo = "1";
      btn.addEventListener("click", alternarTema);
    });
  }

  aplicarTema(obtenerTema());

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      aplicarTema(obtenerTema());
      enlazarToggle();
    });
  } else {
    aplicarTema(obtenerTema());
    enlazarToggle();
  }

  window.kumaTema = {
    alternar: alternarTema,
    aplicar: aplicarTema,
    obtener: obtenerTema,
  };
})();
