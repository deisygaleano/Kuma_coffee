document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".cantidad-control").forEach(function (control) {
    const input = control.querySelector(".cantidad-control__input");
    if (!input) return;

    control.querySelectorAll("[data-cantidad-btn]").forEach(function (boton) {
      boton.addEventListener("click", function () {
        const accion = boton.dataset.cantidadBtn;
        const minimo = parseInt(input.getAttribute("min") || "1", 10);
        const maximo = parseInt(input.getAttribute("max") || "", 10);
        const valorActual = parseInt(input.value || minimo, 10);
        let nuevoValor = accion === "sumar" ? valorActual + 1 : valorActual - 1;

        if (nuevoValor < minimo) nuevoValor = minimo;
        if (!Number.isNaN(maximo) && nuevoValor > maximo) nuevoValor = maximo;

        input.value = nuevoValor;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
  });
});
