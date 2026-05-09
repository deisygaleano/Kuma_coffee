document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("modalEliminar");
  const modalTexto = document.getElementById("modalTexto");
  const formEliminar = document.getElementById("formEliminar");
  const cerrarBotones = document.querySelectorAll("[data-cerrar-modal]");
  const eliminarBotones = document.querySelectorAll("[data-eliminar-producto]");

  if (!modal || !modalTexto || !formEliminar) return;

  function abrirModal(id, nombre) {
    modalTexto.textContent =
      '¿Seguro que deseas eliminar "' + nombre + '"? Esta acción no se puede deshacer.';
    formEliminar.action = "/catalogo/admin/productos/" + id + "/eliminar/";
    modal.classList.add("activo");
  }

  function cerrarModal() {
    modal.classList.remove("activo");
  }

  eliminarBotones.forEach(function (boton) {
    boton.addEventListener("click", function () {
      abrirModal(boton.dataset.pk, boton.dataset.nombre);
    });
  });

  cerrarBotones.forEach(function (boton) {
    boton.addEventListener("click", cerrarModal);
  });

  modal.addEventListener("click", function (event) {
    if (event.target === modal) cerrarModal();
  });
});
