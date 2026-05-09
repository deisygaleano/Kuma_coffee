document.addEventListener("DOMContentLoaded", function () {
  const trigger = document.getElementById("usuario-menu-trigger");
  const modal = document.getElementById("usuario-menu-modal");
  if (!trigger || !modal) return;

  function abrir() {
    modal.removeAttribute("hidden");
    trigger.setAttribute("aria-expanded", "true");
    document.body.classList.add("usuario-modal-abierto");

    const cerrarBtn = modal.querySelector(".usuario-modal__cerrar");
    if (cerrarBtn) cerrarBtn.focus();
  }

  function cerrar() {
    modal.setAttribute("hidden", "");
    trigger.setAttribute("aria-expanded", "false");
    document.body.classList.remove("usuario-modal-abierto");
    trigger.focus();
  }

  trigger.addEventListener("click", function (event) {
    event.stopPropagation();
    if (modal.hasAttribute("hidden")) abrir();
    else cerrar();
  });

  modal.querySelectorAll("[data-cerrar-modal]").forEach(function (elemento) {
    elemento.addEventListener("click", cerrar);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hasAttribute("hidden")) {
      cerrar();
    }
  });
});
