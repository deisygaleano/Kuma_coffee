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

  const fotoInput = document.getElementById("usuario-foto-input");
  const fotoForm = document.getElementById("usuario-foto-form");
  const fotoAcciones = document.getElementById("usuario-foto-acciones");
  const confirmarEliminarPanel = document.getElementById("usuario-foto-confirmar");
  const cancelarEliminarBtn = document.getElementById("usuario-foto-cancelar-eliminar");
  const confirmarEliminarBtn = document.getElementById("usuario-foto-confirmar-eliminar");
  const estadoFoto = document.getElementById("usuario-foto-estado");
  const modalAvatar = document.getElementById("usuario-modal-avatar");
  const navbarAvatar = document.getElementById("usuario-navbar-avatar");
  const cambiarLabel = document.getElementById("usuario-foto-cambiar");
  const iniciales = modal.dataset.usuarioIniciales || "";

  const iconoEliminarSvg =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
    '<polyline points="3 6 5 6 21 6"/>' +
    '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>' +
    '<path d="M10 11v6M14 11v6"/>' +
    '<path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>' +
    "</svg>";

  function obtenerCsrf() {
    return fotoForm
      ? fotoForm.querySelector("[name=csrfmiddlewaretoken]")?.value || ""
      : "";
  }

  function obtenerFormularioEliminar() {
    return document.getElementById("usuario-foto-eliminar-form");
  }

  function enlazarBotonEliminar(boton) {
    if (!boton || boton.dataset.enlazado === "1") return;
    boton.dataset.enlazado = "1";
    boton.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      mostrarConfirmacionEliminar(true);
    });
  }

  function crearFormularioEliminar() {
    if (!fotoForm || !fotoAcciones || obtenerFormularioEliminar()) {
      enlazarBotonEliminar(document.getElementById("usuario-foto-eliminar-btn"));
      return obtenerFormularioEliminar();
    }

    const formulario = document.createElement("form");
    formulario.id = "usuario-foto-eliminar-form";
    formulario.method = "post";
    formulario.action = fotoForm.action;
    formulario.className = "usuario-modal__foto-form";

    formulario.innerHTML =
      '<input type="hidden" name="csrfmiddlewaretoken" value="' +
      obtenerCsrf() +
      '">' +
      '<input type="hidden" name="accion" value="eliminar">' +
      '<button type="button" id="usuario-foto-eliminar-btn" class="usuario-modal__foto-icono usuario-modal__foto-icono--eliminar" title="Eliminar foto" aria-label="Eliminar foto">' +
      iconoEliminarSvg +
      "</button>";

    fotoAcciones.appendChild(formulario);
    formulario.addEventListener("submit", function (event) {
      event.preventDefault();
    });
    enlazarBotonEliminar(formulario.querySelector("#usuario-foto-eliminar-btn"));
    return formulario;
  }

  function quitarFormularioEliminar() {
    const formulario = obtenerFormularioEliminar();
    if (formulario) {
      formulario.remove();
    }
  }

  function mostrarBotonEliminar(mostrar) {
    if (mostrar) {
      crearFormularioEliminar();
    } else {
      quitarFormularioEliminar();
    }
  }

  function mostrarEstadoFoto(mensaje, esError) {
    if (!estadoFoto) return;
    estadoFoto.textContent = mensaje;
    estadoFoto.hidden = false;
    estadoFoto.classList.toggle("usuario-modal__foto-estado--error", Boolean(esError));
    estadoFoto.classList.toggle("usuario-modal__foto-estado--ok", !esError);
  }

  function actualizarAvatares(fotoUrl) {
    const cacheBust = fotoUrl ? `${fotoUrl}?t=${Date.now()}` : "";
    const tieneFoto = Boolean(fotoUrl);

    if (modalAvatar) {
      if (tieneFoto) {
        modalAvatar.innerHTML =
          `<img src="${cacheBust}" alt="" class="usuario-modal__avatar-img" />`;
      } else {
        modalAvatar.textContent = iniciales;
      }
    }

    if (navbarAvatar) {
      if (tieneFoto) {
        navbarAvatar.innerHTML =
          `<img src="${cacheBust}" alt="" class="avatar-usuario__img" />`;
      } else {
        navbarAvatar.textContent = iniciales;
      }
    }

    mostrarBotonEliminar(tieneFoto);

    if (cambiarLabel) {
      const texto = tieneFoto ? "Cambiar foto" : "Agregar foto";
      cambiarLabel.title = texto;
      cambiarLabel.setAttribute("aria-label", texto);
    }
  }

  function enviarFoto(formulario) {
    const formData = new FormData(formulario);

    return fetch(formulario.action, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (response) {
        return response
          .json()
          .catch(function () {
            return { ok: false, mensaje: "No se pudo actualizar la foto." };
          })
          .then(function (data) {
            return { response: response, data: data };
          });
      })
      .then(function (result) {
        if (!result.response.ok || !result.data.ok) {
          mostrarEstadoFoto(result.data.mensaje || "No se pudo actualizar la foto.", true);
          return;
        }

        const tieneFoto = Boolean(result.data.tiene_foto && result.data.foto_url);
        actualizarAvatares(tieneFoto ? result.data.foto_url : null);
        mostrarEstadoFoto(result.data.mensaje, false);
        if (fotoInput) {
          fotoInput.value = "";
        }
      })
      .catch(function () {
        mostrarEstadoFoto("No se pudo actualizar la foto. Intenta de nuevo.", true);
      });
  }

  function mostrarConfirmacionEliminar(mostrar) {
    if (!confirmarEliminarPanel) return;
    confirmarEliminarPanel.hidden = !mostrar;
  }

  if (fotoForm && fotoInput) {
    fotoForm.addEventListener("submit", function (event) {
      event.preventDefault();
    });

    fotoInput.addEventListener("change", function () {
      if (fotoInput.files && fotoInput.files.length > 0) {
        enviarFoto(fotoForm);
      }
    });
  }

  const eliminarFormInicial = obtenerFormularioEliminar();
  if (eliminarFormInicial) {
    eliminarFormInicial.addEventListener("submit", function (event) {
      event.preventDefault();
    });
    enlazarBotonEliminar(document.getElementById("usuario-foto-eliminar-btn"));
  }

  if (cancelarEliminarBtn) {
    cancelarEliminarBtn.addEventListener("click", function () {
      mostrarConfirmacionEliminar(false);
    });
  }

  if (confirmarEliminarBtn) {
    confirmarEliminarBtn.addEventListener("click", function () {
      const formulario = obtenerFormularioEliminar();
      if (!formulario) return;
      mostrarConfirmacionEliminar(false);
      enviarFoto(formulario);
    });
  }
});
