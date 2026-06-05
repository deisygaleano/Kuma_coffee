(function () {
  const DURACION_MS = 5000;

  function ocultarMensaje(elemento) {
    elemento.classList.add("mensajes-flash__item--oculto");
    window.setTimeout(function () {
      elemento.remove();
      const contenedor = document.querySelector("[data-mensajes-flash]");
      if (contenedor && !contenedor.querySelector("[data-mensaje-flash]")) {
        contenedor.remove();
      }
    }, 320);
  }

  document.querySelectorAll("[data-mensaje-flash]").forEach(function (elemento) {
    window.setTimeout(function () {
      ocultarMensaje(elemento);
    }, DURACION_MS);
  });
})();
